##################################################################################
# Copyright (c) 2025 Matthew Thomas Beck                                         #
#                                                                                #
# Licensed under the Creative Commons Attribution-NonCommercial 4.0              #
# International (CC BY-NC 4.0). Personal and educational use is permitted.       #
# Commercial use by companies or for-profit entities is prohibited.              #
##################################################################################





##########################################################
############### IMPORT/CREATE DEPENDENCIES ###############
##########################################################


########## IMPORT DEPENDENCIES ##########

##### import necessary libraries #####

import logging # import logging library for debugging





#####################################################
############### CREATE CONFIGURATIONS ###############
#####################################################


########## UTILITY CONFIGURATIONS ##########

RL_NOT_CNN = True # boolean to switch between testing and RL models (true is RL, false is testing)

##### set logging configuration #####

LOG_CONFIG = {
    'LOG_PATH': "/home/matthewthomasbeck/Projects/Neuralink_System_Exploring/neuralink_system_exploring.log", # path to log file DO NOT CHANGE
    'LOG_LEVEL': logging.DEBUG # set log level to logging.<DEBUG, INFO, WARNING, ERROR, or CRITICAL>
}

########## CAMERA CONFIGURATION ##########

##### set camera configuration #####

CAMERA_CONFIG = {
    'FOV': 75, # degrees
    'CAMERA_WIDTH': 4608,
    'CAMERA_HEIGHT': 2592,
    'FOV_HORIZONTAL': 66,  # degrees
    'FOV_VERTICAL': 41,  # degrees
    'PIXEL_SIZE_UM': 1.4,  # pixel size in micrometers
    'DEPTH_OF_FIELD': 0.1,  # depth of field distance in meters
    'APERTURE_RATIO': 1.8,
    'WIDTH': 640, # width of the camera image
    'HEIGHT': 480, # height of the camera image
    'FRAME_RATE': 15, # picam fps
    'CROP_FRACTION': 0.5, # fraction of the image to crop from each side (0.0 to 1.0)
    'OUTPUT_WIDTH': 128, # width of the ML image
    'OUTPUT_HEIGHT': 48, # height of the image for ML inference
}


########## INFERENCE CONFIGURATIONS ##########

##### set ML configurations #####

INFERENCE_CONFIG = {
    'TPU_NAME': "MYRIAD",  # literal device name in code
    'CNN_PATH': "/home/matthewthomasbeck/Projects/Neuralink_System_Exploring/model/person-detection-0200.xml",  # person detection
    'SHOW_SCREEN': True,  # cv2.imshow preview for RustDesk / local debugging
}

PERSON_PROXIMITY_CONFIG = {
    'RETRACT_STEP_RAD': 0.05,  # radians to retract each joint per frame while a person is detected
    'NEUTRAL_STEP_RAD': 0.05,  # radians to step back toward neutral when no person is detected
}


########## MAESTRO CONFIGURATION ##########

MAESTRO_CONFIG = {
    'SERIAL_PATH': "/dev/serial0", # set serial port name to first available
    'SERIAL_BAUD_RATE': 9600, # set baud rate for serial connection
    'SERIAL_TIMEOUT': 1 # set timeout for serial connection
}


########## PHYSICAL CONFIGURATION ##########

##### 2-DOF arm: servo 11 = upper, servo 10 = lower (270° hobby servos) #####

SERVO_CONFIG = {
    'upper': {
        'servo': 11,
        'FULL_FRONT': 1921.50,
        'FULL_BACK': 1310.00,
        'NEUTRAL': 1615.75,
        'CURRENT': 1615.75,
        'FULL_FRONT_ANGLE': 0.654,
        'FULL_BACK_ANGLE': -0.654,
        'CURRENT_ANGLE': 0.0,
        'NEUTRAL_ANGLE': 0.0,
    },
    'lower': {
        'servo': 10,
        'FULL_FRONT': 2000.00,
        'FULL_BACK': 1231.75,
        'NEUTRAL': 1615.875,
        'CURRENT': 1615.875,
        'FULL_FRONT_ANGLE': 0.698,
        'FULL_BACK_ANGLE': -0.698,
        'CURRENT_ANGLE': 0.0,
        'NEUTRAL_ANGLE': 0.0,
    },
}

PREVIOUS_POSITIONS = [] # array of previous positions
PREVIOUS_ORIENTATIONS = [] # array of previous orientations (shift, move, translate, yaw, roll, pitch)
