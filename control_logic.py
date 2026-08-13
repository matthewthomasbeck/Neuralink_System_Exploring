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

##### mandatory dependencies #####

from utilities.log import initialize_logging
import utilities.config as config

##### (pre)initialize all utilities #####

LOGGER = initialize_logging()
CAMERA_PROCESS = None
ROBOT_ID = None
JOINT_MAP = {}


########## PREPARE ROBOT ##########

##### prepare real robot #####

def set_real_robot_dependencies():  # function to initialize real robot dependencies

    ##### import necessary functions #####

    from utilities.camera import initialize_camera  # import to start camera logic

    ##### initialize global variables #####

    global CAMERA_PROCESS, ROBOT_ID, JOINT_MAP

    ##### initialize PREVIOUS_POSITIONS for physical robot (1 robot) #####

    config.PREVIOUS_POSITIONS = []
    robot_history = deque(maxlen=5)
    for _ in range(5):
        robot_history.append(np.zeros(12, dtype=np.float32))
    config.PREVIOUS_POSITIONS.append(robot_history)

    ##### initialize cameras (PiCam CSI + C270 USB) #####

    CAMERA_PROCESS = initialize_camera()
    if CAMERA_PROCESS is None:
        logging.error("(control_logic.py): Failed to initialize cameras!\n")

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
from utilities.camera import get_latest_frames





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

    ##### run robotic logic #####

    try:  # try to run robot startup sequence
        neutral_position(1)
        time.sleep(3)
        IS_NEUTRAL = True  # set is_neutral to True

    except Exception as e:  # if there is an error, log error
        logging.error(f"(control_logic.py): Failed to move to neutral standing position in runRobot: {e}\n")

    ##### keep camera loop alive #####

    try:  # try to run main robotic process

        last_status = 0.0
        while True:  # central loop to entire process, commenting out of importance

            picam_frame, logi_frame = get_latest_frames(CAMERA_PROCESS)

            now = time.time()
            if now - last_status >= 5.0:
                picam_ok = picam_frame is not None
                logi_ok = logi_frame is not None
                logging.info(f"(control_logic.py): frames picam={picam_ok} c270={logi_ok}\n")
                last_status = now

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
