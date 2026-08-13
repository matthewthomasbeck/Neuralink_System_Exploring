##################################################################################
# Copyright (c) 2025 Matthew Thomas Beck                                         #
#                                                                                #
# Licensed under the Creative Commons Attribution-NonCommercial 4.0              #
# International (CC BY-NC 4.0). Personal and educational use is permitted.       #
# Commercial use by companies or for-profit entities is prohibited.              #
##################################################################################





############################################################
############### IMPORT / CREATE DEPENDENCIES ###############
############################################################


########## MANDATORY DEPENDENCIES ##########

##### mandatory libraries #####

import threading
import time
import os
import logging
from collections import deque
import numpy as np
import cv2

##### mandatory dependencies #####

from utilities.log import initialize_logging
import utilities.config as config

##### (pre)initialize all utilities #####

LOGGER = initialize_logging()
CAMERA_PROCESS = None
ROBOT_ID = None
JOINT_MAP = {}
DETECTION_MODEL = None
DETECTION_INPUT_LAYER = None
DETECTION_OUTPUT_LAYER = None


########## PREPARE ROBOT ##########

##### prepare real robot #####

def set_real_robot_dependencies():  # function to initialize real robot dependencies

    ##### import necessary functions #####

    from utilities.camera import initialize_camera  # import to start camera logic
    from utilities import inference

    ##### initialize global variables #####

    global CAMERA_PROCESS, ROBOT_ID, JOINT_MAP
    global DETECTION_MODEL, DETECTION_INPUT_LAYER, DETECTION_OUTPUT_LAYER

    ##### initialize PREVIOUS_POSITIONS for physical robot (1 robot) #####

    config.PREVIOUS_POSITIONS = []
    robot_history = deque(maxlen=5)
    for _ in range(5):
        robot_history.append(np.zeros(12, dtype=np.float32))
    config.PREVIOUS_POSITIONS.append(robot_history)

    ##### initialize camera process #####

    CAMERA_PROCESS = initialize_camera()  # create camera process
    if CAMERA_PROCESS is None:
        logging.error("(control_logic.py): Failed to initialize CAMERA_PROCESS for robot!\n")

    ##### initialize person detection model #####

    model_path = config.INFERENCE_CONFIG['CNN_PATH']
    if os.path.isfile(model_path):
        DETECTION_MODEL, DETECTION_INPUT_LAYER, DETECTION_OUTPUT_LAYER = inference.load_and_compile_model(model_path)
        if DETECTION_MODEL is None:
            logging.warning("(control_logic.py): Person detection model failed to load.\n")
    else:
        logging.warning(f"(control_logic.py): Person detection model not found at {model_path}.\n")

    ##### initialize PREVIOUS_ORIENTATIONS for physical robot (1 robot) #####

    config.PREVIOUS_ORIENTATIONS = []
    orientation_history = deque(maxlen=5)
    for _ in range(5):
        orientation_history.append(np.zeros(6, dtype=np.float32))  # 6 values: shift, move, translate, yaw, roll, pitch
    config.PREVIOUS_ORIENTATIONS.append(orientation_history)


########## PREPARE ROBOT ##########

##### prepare robot with correct dependencies #####

set_real_robot_dependencies()

##### post-initialization dependencies #####

from movement.movement_coordinator import *
from utilities.camera import decode_real_frame
from utilities import inference





#########################################
############### RUN ROBOT ###############
#########################################


########## STATE MACHINE LOOPS ##########

##### set global variables #####

IMAGELESS_GAIT = True  # set global variable for imageless gait
IS_COMPLETE = True  # boolean that tracks if the robot is done moving, independent of it being neutral or not
IS_NEUTRAL = False  # set global neutral standing boolean
CURRENT_LEG = 'FL'  # set global current leg


##### physical loop #####

def _physical_loop():  # central function that runs robot in real life

    ##### set/initialize variables #####

    global IS_COMPLETE, IS_NEUTRAL, CURRENT_LEG  # declare as global as these will be edited by function
    mjpeg_buffer = b''  # initialize buffer for MJPEG frames

    ##### run robotic logic #####

    try:  # try to run robot startup sequence
        neutral_position(1)
        time.sleep(3)
        IS_NEUTRAL = True  # set is_neutral to True

    except Exception as e:  # if there is an error, log error
        logging.error(f"(control_logic.py): Failed to move to neutral standing position in runRobot: {e}\n")

    ##### keep camera loop alive #####

    try:  # try to run main robotic process

        while True:  # central loop to entire process, commenting out of importance

            mjpeg_buffer, streamed_frame, inference_frame = decode_real_frame(
                CAMERA_PROCESS,
                mjpeg_buffer
            )

            person_detected, target_cx, largest_box_area, box_width = inference.run_person_detection(
                DETECTION_MODEL,
                DETECTION_INPUT_LAYER,
                DETECTION_OUTPUT_LAYER,
                inference_frame,
                run_inference=True
            )

            if config.INFERENCE_CONFIG.get('SHOW_SCREEN', False) and inference_frame is not None:
                try:
                    cv2.imshow("SSDLite detection", inference_frame)
                    cv2.waitKey(1)
                except Exception as e:
                    logging.warning(f"(control_logic.py): cv2.imshow failed: {e}\n")
                    config.INFERENCE_CONFIG['SHOW_SCREEN'] = False

            frame_width = inference_frame.shape[1] if inference_frame is not None else 0
            retract_if_too_close(person_detected, box_width, frame_width)

    except KeyboardInterrupt:  # if user ends program...
        logging.info("(control_logic.py): KeyboardInterrupt received, exiting.\n")

    except Exception as e:  # if something breaks and only God knows what it is...
        logging.error(f"(control_logic.py): Unexpected exception in main loop: {e}\n")
        exit(1)


########## MISCELLANEOUS CONTROL FUNCTIONS ##########

def restart_process():  # restart this service every 30 minutes
    start_time = time.time()
    while True:
        elapsed = time.time() - start_time
        if elapsed >= 1800:  # 30 minutes = 1800 seconds
            os.system('sudo systemctl restart neuralink_system_exploring.service')
            start_time = time.time()  # reset timer after restart
        time.sleep(1)  # check every second


########## RUN ROBOTIC PROCESS ##########

restart_thread = threading.Thread(target=restart_process, daemon=True)
restart_thread.start()
_physical_loop()  # run robot process
