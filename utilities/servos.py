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

import logging # import logging for debugging

##### import necessary functions #####

from utilities.maestro import initialize_maestro # import maestro initialization functions
import utilities.config as config





########## CREATE DEPENDENCIES ##########

##### create maestro object #####

MAESTRO = initialize_maestro() # create maestro object





#############################################################
############### FUNDAMENTAL MOVEMENT FUNCTION ###############
#############################################################


########## MOVE A SINGLE SERVO ##########

def set_target(channel, target, speed, acceleration): # function to set target position of a singular servo

    ##### move a servo to a desired position using its number and said position #####

    logging.debug(f"(servos.py): Attempting to move servo {channel} to target {target} with speed {speed} and acceleration {acceleration}...\n")

    try: # attempt to move desired servo

        if MAESTRO is None or isinstance(MAESTRO, int):
            logging.error("(servos.py): Maestro is not connected; cannot move servo.\n")
            return

        target = int(round(target * 4)) # convert target from microseconds to quarter-microseconds
        speed = max(0, min(16383, speed)) # ensure speed is within valid range
        acceleration = max(0, min(255, acceleration)) # ensure acceleration is within valid range
        speed_command = bytearray([0x87, channel, speed & 0x7F, (speed >> 7) & 0x7F]) # create speed command
        MAESTRO.write(speed_command) # send speed command to maestro

        # create acceleration command
        accel_command = bytearray([0x89, channel, acceleration & 0x7F, (acceleration >> 7) & 0x7F])
        MAESTRO.write(accel_command) # send acceleration command to maestro
        command = bytearray([0x84, channel, target & 0x7F, (target >> 7) & 0x7F]) # create target position command
        MAESTRO.write(command) # send target position command to maestro
        MAESTRO.flush()

    except Exception as e:
        logging.error(f"(servos.py): Failed to move servo: {e}\n")


########## ANGLE TO TARGET ##########

def map_angle_to_servo_position(angle, joint_data): # map radian to pwm

    ##### set variables #####

    full_back_angle = joint_data['FULL_BACK_ANGLE']  # radian position for FULL_BACK PWM
    full_front_angle = joint_data['FULL_FRONT_ANGLE']  # radian position for FULL_FRONT PWM
    full_back_pwm = joint_data['FULL_BACK']  # value for full back position
    full_front_pwm = joint_data['FULL_FRONT']  # value for full front position
    angle_range = full_front_angle - full_back_angle #
    pwm_range = full_front_pwm - full_back_pwm

    logging.debug(f"(servos.py): Mapping radian {angle} to servo position...\n")

    ##### map angle to pwm #####

    if abs(angle_range) < 1e-6: # if dividing by zero...
        logging.error(f"(servos.py): Invalid angle range: {angle_range}")
        return full_back_pwm

    pwm = full_back_pwm + (angle - full_back_angle) * (pwm_range / angle_range) # map via interpolation

    if full_back_pwm < full_front_pwm: # if back value scalar less than front value scalar...
        pwm = max(full_back_pwm, min(full_front_pwm, pwm)) # clamp pwm to valid range

    else: # if back value scalar greater than front value scalar...
        pwm = max(full_front_pwm, min(full_back_pwm, pwm)) # clamp pwm to valid range

    logging.debug(f"(servos.py): Angle {angle:.3f} rad -> PWM {pwm:.1f} (range: {full_back_pwm} to {full_front_pwm})\n")
    logging.debug(f"(servos.py): Angle range: {full_back_angle:.3f} to {full_front_angle:.3f} rad\n")

    return int(round(pwm)) # return calculated pulse width


########## RADIAN TO SERVO SPEED ##########

def map_radian_to_servo_speed(radian_speed): # function to map radian speed to servo speed

    ##### map radian speed to servo speed #####

    logging.debug(f"(servos.py): Mapping radian speed {radian_speed} to servo speed...\n")

    radian_speed = max(0.0, min(9.52, radian_speed)) # clamp radian speed to valid range (0 to 9.52 rad/s)
    servo_speed = (radian_speed / 9.52) * 16383 # map radian speed to servo speed (0 to 16383)
    servo_speed = int(round(servo_speed)) # round servo speed to nearest integer
    servo_speed = max(0, min(16383, servo_speed)) # ensure servo speed is within valid range

    logging.debug(f"(servos.py): Radian speed {radian_speed:.3f} rad/s -> Servo speed {servo_speed}\n")

    return servo_speed


########## MOVE NAMED JOINT ##########

def move_joint(joint_name, target_angle, speed=9.5):

    servo_data = config.SERVO_CONFIG[joint_name]
    pwm = map_angle_to_servo_position(target_angle, servo_data)
    servo_speed = map_radian_to_servo_speed(speed)
    set_target(servo_data['servo'], pwm, servo_speed, 255)
    config.SERVO_CONFIG[joint_name]['CURRENT'] = pwm
    config.SERVO_CONFIG[joint_name]['CURRENT_ANGLE'] = target_angle


########## NEUTRAL POSITION ##########

def go_to_neutral(speed=9.5):

    logging.info("(servos.py): Moving upper + lower servos to neutral...\n")
    for joint_name in ('upper', 'lower'):
        try:
            move_joint(joint_name, config.SERVO_CONFIG[joint_name]['NEUTRAL_ANGLE'], speed)
        except Exception as e:
            logging.error(f"(servos.py): Failed to move {joint_name} to neutral: {e}\n")
