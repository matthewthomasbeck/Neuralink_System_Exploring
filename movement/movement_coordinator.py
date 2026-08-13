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


########## IMPORT DEPENDENCIES ##########

##### import config #####

import utilities.config as config # import configuration data for servos and link lengths

##### import necessary libraries #####

import time # import time for proper sequencing
import threading # import threading for thread management
import random # import random for random angle radians
import logging # import logging for error handling

##### import necessary functions #####

from utilities.servos import move_joint, go_to_neutral
from utilities.inference import load_and_compile_model, run_gait_adjustment_standard, run_gait_adjustment_blind, \
    run_person_detection # load function/models for gait adjustment and person detection

if config.RL_NOT_CNN:
    # TODO Be aware that multiple models loaded on one NCS2 may be an issue... might be worth benching one of these
    #STANDARD_RL_MODEL, STANDARD_INPUT_LAYER, STANDARD_OUTPUT_LAYER = load_and_compile_model(
        #config.INFERENCE_CONFIG['STANDARD_RL_PATH'])
    BLIND_RL_MODEL, BLIND_INPUT_LAYER, BLIND_OUTPUT_LAYER = load_and_compile_model(
        config.INFERENCE_CONFIG['BLIND_RL_PATH'])
elif not config.RL_NOT_CNN:
    CNN_MODEL, CNN_INPUT_LAYER, CNN_OUTPUT_LAYER = load_and_compile_model(config.INFERENCE_CONFIG['CNN_PATH'])


########## CREATE DEPENDENCIES ##########

##### simulation variables (set by control_logic.py) #####

ROBOT_ID = None
JOINT_MAP = {}





##############################################################
############### MOVEMENT COORDINATOR FUNCTIONS ###############
##############################################################


########## CENTRAL GAIT FUNCTION ##########

def move_direction(commands, camera_frames, intensity, imageless_gait): # function to trot forward

    ##### preprocess commands and intensity #####

    if isinstance(commands, list): # if new format...
        # Filter out tilt commands (arrowup/arrowdown) and create RL model input
        rl_commands = []
        tilt_command = None

        ##### extract movement commands #####

        if commands[0] is not None:  # forward/backward
            rl_commands.append(commands[0])
        if commands[1] is not None:  # left/right
            rl_commands.append(commands[1])
        if commands[2] is not None:  # rotation
            rl_commands.append(commands[2])
        if commands[3] is not None:  # tilt (store for later use if needed)
            tilt_command = commands[3]

        commands = rl_commands

    else: # if old format...
        commands = sorted(commands.split('+')) # alphabetize commands so they are uniform

    ##### orientation vector (zeros — no accelerometer) #####

    orientation = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]

    ##### run inference before moving #####

    try: # try to run a model
        if config.RL_NOT_CNN: # if running gait adjustment (production)...

            ##### run RL model(s) #####

            logging.debug("Inference input:\n")
            logging.debug(f"(movement_coordinator.py): Commands: {commands}\n")
            logging.debug(f"(movement_coordinator.py): Intensity: {intensity}\n")
            logging.debug(f"(movement_coordinator.py): Orientation: {orientation}\n")

            if not imageless_gait: # if not using imageless gait adjustment...
                # TODO use the blind model until I get image support going
                target_angles, movement_rates = run_gait_adjustment_blind(  # run blind
                    BLIND_RL_MODEL,
                    BLIND_INPUT_LAYER,
                    BLIND_OUTPUT_LAYER,
                    commands,
                    intensity,
                    orientation
                )

            else: # if using imageless gait adjustment...
                target_angles, movement_rates = run_gait_adjustment_blind( # run blind
                    BLIND_RL_MODEL,
                    BLIND_INPUT_LAYER,
                    BLIND_OUTPUT_LAYER,
                    commands,
                    intensity,
                    orientation
                )

            logging.debug("(movement_coordinator.py): Inference Results:\n")
            logging.debug(f"(movement_coordinator.py): Target angles: {target_angles}\n")
            logging.debug(f"(movement_coordinator.py): Movement rates: {movement_rates}\n")

            ##### move joints and update current position #####

            thread_joint_movement(
                config.SERVO_CONFIG,
                target_angles,
                movement_rates
            )

        else: # if running person detection (testing)...
            run_person_detection(
                CNN_MODEL,
                CNN_INPUT_LAYER,
                CNN_OUTPUT_LAYER,
                frame,
                run_inference=False
            )
        logging.info(f"(movement_coordinator.py): Ran AI for command(s) {commands} with intensity {intensity}\n")

    except Exception as e: # if either model fails...
        logging.error(f"(movement_coordinator.py): Failed to run AI for command: {e}\n")

    ##### force robot to slow down so the raspberry doesn't crash #####

    time.sleep(0.0875) # only allow inference to run at rate # was 0.175


########## THREAD JOINT MOVEMENT ##########

def thread_joint_movement(current_servo_config, target_angles, movement_rates): # function to move upper + lower

    joint_threads = []
    for joint_name in ('upper', 'lower'):
        if joint_name not in target_angles:
            continue
        speed = 1.0
        if isinstance(movement_rates, dict):
            speed = movement_rates.get(joint_name, 1.0)
            if isinstance(speed, dict):
                speed = speed.get('speed', 1.0)
        t = threading.Thread(
            target=move_joint,
            args=(joint_name, target_angles[joint_name], speed)
        )
        joint_threads.append(t)
        t.start()
    for t in joint_threads:
        t.join()


########## RANDOM ACTION FUNCTION ##########

def get_random_action(state, commands, intensity): # used to generate random movement for testing

    ##### set variables #####

    target_angles = {}
    mid_angles = {}
    movement_rates = {}

    ##### generate random angles and rates #####

    for joint_name in ('upper', 'lower'):

        servo_data = config.SERVO_CONFIG[joint_name]
        full_back_angle = servo_data['FULL_BACK_ANGLE']
        full_front_angle = servo_data['FULL_FRONT_ANGLE']
        min_angle = min(full_back_angle, full_front_angle)
        max_angle = max(full_back_angle, full_front_angle)

        target_angles[joint_name] = random.uniform(min_angle, max_angle)
        mid_angles[joint_name] = random.uniform(min_angle, max_angle)
        movement_rates[joint_name] = 1.0

    return target_angles, mid_angles, movement_rates


########## NEUTRAL POSITION FUNCTION ##########

def neutral_position(intensity):

    try:
        go_to_neutral()
    except Exception as e:
        logging.error(f"(movement_coordinator.py): Failed to move servos to neutral position: {e}\n")
