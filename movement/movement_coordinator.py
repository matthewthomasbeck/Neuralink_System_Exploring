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

import utilities.config as config
import logging

from utilities.servos import move_joint, go_to_neutral





##############################################################
############### MOVEMENT COORDINATOR FUNCTIONS ###############
##############################################################


########## NEUTRAL POSITION ##########

def neutral_position(intensity=1):

    try:
        go_to_neutral()
    except Exception as e:
        logging.error(f"(movement_coordinator.py): Failed to move servos to neutral position: {e}\n")


########## RETRACT IF PERSON IS TOO CLOSE ##########

def retract_if_too_close(person_detected, box_width, frame_width):

    if not person_detected or frame_width <= 0:
        return

    width_ratio = box_width / float(frame_width)
    threshold = config.PERSON_PROXIMITY_CONFIG['WIDTH_RATIO_THRESHOLD']
    step = config.PERSON_PROXIMITY_CONFIG['RETRACT_STEP_RAD']

    logging.debug(
        f"(movement_coordinator.py): proximity width_ratio={width_ratio:.3f} "
        f"threshold={threshold:.3f} box_width={box_width}px frame_width={frame_width}px\n"
    )

    if width_ratio <= threshold:
        return

    logging.info(
        f"(movement_coordinator.py): Person too close ({width_ratio:.1%} of frame width) — retracting servos.\n"
    )

    for joint_name in ('upper', 'lower'):
        servo_data = config.SERVO_CONFIG[joint_name]
        current = servo_data['CURRENT_ANGLE']
        back = servo_data['FULL_BACK_ANGLE']
        if current < back:
            target = min(current + step, back)
        else:
            target = max(current - step, back)
        try:
            move_joint(joint_name, target)
        except Exception as e:
            logging.error(f"(movement_coordinator.py): Failed to retract {joint_name}: {e}\n")
