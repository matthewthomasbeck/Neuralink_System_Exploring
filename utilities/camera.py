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

import utilities.config as config

##### import necessary libraries #####

import subprocess # import subprocess to run rpicam command
import logging # import logging for logging messages
import time # add time for waiting
import threading
import numpy # add numpy for decoding frames
import cv2  # add cv2 for decoding frames





################################################
############### CAMERA FUNCTIONS ###############
################################################


########## USB LATEST-FRAME GRABBER ##########

class LogiGrabber:

    def __init__(self, device, width, height, frame_rate):
        self.device = device
        self.lock = threading.Lock()
        self.frame = None
        self.running = True
        self.cap = cv2.VideoCapture(device, cv2.CAP_V4L2)
        if not self.cap.isOpened():
            raise RuntimeError(f"Failed to open {device}")

        self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        self.cap.set(cv2.CAP_PROP_FPS, frame_rate)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()

    def _loop(self):
        while self.running:
            ok, frame = self.cap.read()
            if not ok:
                time.sleep(0.05)
                continue
            with self.lock:
                self.frame = frame

    def get_frame(self):
        with self.lock:
            if self.frame is None:
                return None
            return self.frame.copy()

    def stop(self):
        self.running = False
        if self.cap is not None:
            self.cap.release()


########## INITIALIZE CAMERAS ##########

def initialize_camera( # starts PiCam CSI + C270 USB
        robot_id=0,
        width=config.CAMERA_CONFIG['WIDTH'],
        height=config.CAMERA_CONFIG['HEIGHT'],
        frame_rate=config.CAMERA_CONFIG['FRAME_RATE']
):

    logging.debug("(camera.py): Initializing cameras...\n")
    _kill_existing_camera_processes()

    picam = _start_camera_process(robot_id, width, height, frame_rate)
    if picam is None:
        logging.error("(camera.py): PiCam initialization failed.\n")

    logi = None
    try:
        logi = LogiGrabber(
            config.CAMERA_CONFIG['LOGI_DEVICE'],
            config.CAMERA_CONFIG['LOGI_WIDTH'],
            config.CAMERA_CONFIG['LOGI_HEIGHT'],
            config.CAMERA_CONFIG['LOGI_FRAME_RATE']
        )
        logging.info(f"(camera.py): C270 opened on {config.CAMERA_CONFIG['LOGI_DEVICE']}.\n")
    except Exception as e:
        logging.error(f"(camera.py): Failed to open C270: {e}\n")

    if picam is None and logi is None:
        return None

    return {
        'picam': picam,
        'picam_buffer': b'',
        'logi': logi,
    }


########## TERMINATE EXISTING CAMERA PIPELINES ##########

def _kill_existing_camera_processes(): # function to kill existing camera processes if they exist

    try:
        logging.debug("(camera.py): Checking for existing camera processes...\n")
        subprocess.run(["pkill", "-9", "-f", "rpicam-vid"]) # use pkill for each process type
        subprocess.run(["pkill", "-9", "-f", "rpicam-jpeg"])
        subprocess.run(["pkill", "-9", "-f", "libcamera"])
        logging.info("(camera.py): Successfully killed existing camera processes.\n")
        time.sleep(0.5)  # give time for processes to exit

    except Exception as e:
        logging.error(f"(camera.py): Failed to terminate existing camera processes: {e}\n")


########## CREATE CAMERA PIPELINE ##########

def _start_camera_process(robot_id, width, height, frame_rate): # function to start camera process for opencv

    try:
        real_camera = subprocess.Popen(  # open an rpicam vid process
            [
                "rpicam-vid",
                "--width", str(width),
                "--height", str(height),
                "--framerate", str(frame_rate),
                "--timeout", "0",
                "--output", "-",
                "--codec", "mjpeg",
                "--nopreview"
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            bufsize=0
        )
        time.sleep(0.2)
        if real_camera.poll() is not None:
            stderr = real_camera.stderr.read().decode()
            logging.error(f"(camera.py): Camera process failed to start. Stderr: {stderr}\n")
            return None
        logging.info(f"(camera.py): PiCam initialized successfully with PID {real_camera.pid}.\n")
        return real_camera

    except Exception as e:
        logging.error(f"(camera.py): Failed to start camera process: {e}\n")
        return None


########## DECODE PICAM FRAME ##########

def decode_real_frame(camera_process, mjpeg_buffer):

    try:
        chunk = camera_process.stdout.read(4096)
        if not chunk:
            return mjpeg_buffer, None, None

        mjpeg_buffer += chunk
        start_idx = mjpeg_buffer.find(b'\xff\xd8')
        end_idx = mjpeg_buffer.find(b'\xff\xd9')

        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            streamed_frame = mjpeg_buffer[start_idx:end_idx + 2]
            mjpeg_buffer = mjpeg_buffer[end_idx + 2:]
            inference_frame = cv2.imdecode(numpy.frombuffer(streamed_frame, dtype=numpy.uint8), cv2.IMREAD_COLOR)
            return mjpeg_buffer, streamed_frame, inference_frame

        if len(mjpeg_buffer) > 65536: # if buffer overflow...
            mjpeg_buffer = b'' # reset buffer to avoid overflow
        return mjpeg_buffer, None, None

    except Exception as e:
        logging.error(f"(camera.py): Failed to decode frame: {e}\n")
        return mjpeg_buffer, None, None


########## GET LATEST FRAMES FROM BOTH CAMERAS ##########

def get_latest_frames(cameras):

    picam_frame = None
    logi_frame = None

    if cameras is None:
        return None, None

    if cameras.get('picam') is not None:
        cameras['picam_buffer'], _, picam_frame = decode_real_frame(
            cameras['picam'],
            cameras['picam_buffer']
        )

    if cameras.get('logi') is not None:
        logi_frame = cameras['logi'].get_frame()

    return picam_frame, logi_frame
