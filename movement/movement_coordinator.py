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

_LAST_ARM_ACTION = None





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

    if frame_width <= 0:
        return

    width_ratio = (box_width / float(frame_width)) if person_detected else 0.0
    threshold = config.PERSON_PROXIMITY_CONFIG['WIDTH_RATIO_THRESHOLD']
    too_close = person_detected and width_ratio >= threshold

    if too_close:
        _set_arm_action(
            'retract',
            f"(movement_coordinator.py): Person too close "
            f"({width_ratio:.1%} of frame width) — retracting servos.\n"
        )
        _nudge_joints_toward('FULL_BACK_ANGLE', config.PERSON_PROXIMITY_CONFIG['RETRACT_STEP_RAD'])
        return

    _set_arm_action(
        'neutral',
        f"(movement_coordinator.py): Person not occupying {threshold:.0%} of frame "
        f"(width_ratio={width_ratio:.1%}) — returning servos to neutral.\n"
    )
    _nudge_joints_toward('NEUTRAL_ANGLE', config.PERSON_PROXIMITY_CONFIG['NEUTRAL_STEP_RAD'])


def _set_arm_action(action, message):

    global _LAST_ARM_ACTION
    if action != _LAST_ARM_ACTION:
        logging.info(message)
        _LAST_ARM_ACTION = action


def _nudge_joints_toward(limit_key, step):

    for joint_name in ('upper', 'lower'):
        servo_data = config.SERVO_CONFIG[joint_name]
        current = servo_data['CURRENT_ANGLE']
        limit = servo_data[limit_key]
        if abs(current - limit) < 1e-6:
            continue
        if current < limit:
            target = min(current + step, limit)
        else:
            target = max(current - step, limit)
        try:
            move_joint(joint_name, target)
        except Exception as e:
            logging.error(f"(movement_coordinator.py): Failed to move {joint_name} toward {limit_key}: {e}\n")
