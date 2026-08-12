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

##### import necessary libraries #####

import logging


########## CREATE DEPENDENCIES ##########

##### setup variables #####

BUS = None  # I2C bus disabled — no accelerometer hardware access





#######################################################
############### ACCELEROMETER FUNCTIONS ###############
#######################################################


########## INITIALIZE ACCELEROMETER ##########

def initialize_accelerometer(): # function to initialize accelerometer
    logging.info("(accelerometer.py): Accelerometer disabled — skipping hardware init.\n")
    return None


########## READ ALL DATA ##########

def get_all_data(): # function to read all data from accelerometer (and gyroscope)
    # Hardware access disabled — return zeros so gait/inference still has a stable orientation vector
    return 0.0, 0.0, 0.0, 0.0, 0.0, 0.0


########## READ INDIVIDUAL DATA ##########

def get_orientation_datapoint(addr): # function to read orientation data from accelerometer (and gyroscope)
    return 0
