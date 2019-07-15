import socket
import threading
import cv2 as cv

class Tello:
    """
    Handles connection to the DJI Tello drone
    """

    def __init__(self, local_ip, local_port, is_dummy=False, tello_ip='192.168.10.1', tello_port=8889):
        """
        Initializes connection with Tello and sends both command and streamon instructions
        in order to start it and begin receiving video feed.
        """
        self.background_frame_read = None
        self.response = None
        self.abort_flag = False
        self.is_dummy = is_dummy

        if not is_dummy:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

            self.tello_address = (tello_ip, tello_port)
            self.local_address = (local_ip, local_port)

            self.send_command('command')
            # self.socket.sendto(b'command', self.tello_address)
            print('[INFO] Sent Tello: command')
            self.send_command('streamon')
            # self.socket.sendto(b'streamon', self.tello_address)
            print('[INFO] Sent Tello: streamon')
            self.send_command('takeoff')
            # self.socket.sendto(b'takeoff', self.tello_address)
            print('[INFO] Sent Tello: takeoff')
            self.move_up(160)

            # thread for receiving cmd ack
            self.receive_thread = threading.Thread(target=self._receive_thread)
            self.receive_thread.daemon = True

            self.receive_thread.start()

    def __del__(self):
        """
        Stops communication with Tello
        """
        if not self.is_dummy:
            self.socket.close()

    def _receive_thread(self):
        """
        Listen to responses from the Tello.
        Runs as a thread, sets self.response to whatever the Tello last returned.
        """
        while True:
            try:
                self.response, ip = self.socket.recvfrom(3000)
            except socket.error as exc:
                print (f"Caught exception socket.error: {exc}")

    def send_command(self, command):
        """
        Send a command to the Tello and wait for a response.
        :param command: Command to send.
        :return (str): Response from Tello.
        """
        self.abort_flag = False
        timer = threading.Timer(0.5, self.set_abort_flag)

        self.socket.sendto(command.encode('utf-8'), self.tello_address)

        timer.start()
        while self.response is None:
            if self.abort_flag is True:
                break
        timer.cancel()
        
        if self.response is None:
            response = 'none_response'
        else:
            response = self.response.decode('utf-8')

        self.response = None

        return response

    def send_command_without_response(self, command):
        """
        Sends a command without expecting a response. Useful when sending a lot of commands.
        """
        if not self.is_dummy:
            self.socket.sendto(command.encode('utf-8'), self.tello_address)

    def set_abort_flag(self):
        """
        Sets self.abort_flag to True.

        Used by the timer in Tello.send_command() to indicate to that a response
        timeout has occurred.
        """
        self.abort_flag = True

    def move_up(self, dist):
        """
        Sends up command to Tello and returns its response.
        :param dist: Distance in centimeters in the range 20 - 500.
        :return (str): Response from Tello
        """
        self.send_command_without_response(f'up {dist}')

    def move_down(self, dist):
        """
        Sends down command to Tello and returns its response.
        :param dist: Distance in centimeters in the range 20 - 500.
        :return (str): Response from Tello
        """
        self.send_command_without_response(f'down {dist}')

    def move_right(self, dist):
        """
        Sends right command to Tello and returns its response.
        :param dist: Distance in centimeters in the range 20 - 500.
        :return (str): Response from Tello
        """
        self.send_command_without_response(f'right {dist}')

    def move_left(self, dist):
        """
        Sends left command to Tello and returns its response.
        :param dist: Distance in centimeters in the range 20 - 500.
        :return (str): Response from Tello
        """
        self.send_command_without_response(f'left {dist}')

    def move_forward(self, dist):
        """
        Sends forward command to Tello without expecting a return.
        :param dist: Distance in centimeters in the range 20 - 500.
        """
        self.send_command_without_response(f'forward {dist}')

    def move_backward(self, dist):
        """
        Sends backward command to Tello without expecting a return.
        :param dist: Distance in centimeters in the range 20 - 500.
        """
        self.send_command_without_response(f'back {dist}')

    def rotate_cw(self, deg):
        """
        Sends cw command to Tello in order to rotate clock-wise
        :param deg: Degrees bewteen 0 - 360.
        :return (str): Response from Tello
        """
        self.send_command_without_response(f'cw {deg}')

    def rotate_ccw(self, deg):
        """
        Sends ccw command to Tello in order to rotate clock-wise
        :param deg: Degrees bewteen 0 - 360.
        :return (str): Response from Tello
        """
        self.send_command_without_response(f'ccw {deg}')
    
    def get_udp_video_address(self):
        """
        Gets the constructed udp video address for the drone
        :return (str): The constructed udp video address
        """
        return f'udp://{self.tello_address[0]}:11111'

    def get_frame_read(self):
        """
        Get the BackgroundFrameRead object from the camera drone. Then, you just need to call
        backgroundFrameRead.frame to get the actual frame received by the drone.
        :return (BackgroundFrameRead): A BackgroundFrameRead with the video data.
        """
        if self.background_frame_read is None:
            if self.is_dummy:
                self.background_frame_read = BackgroundFrameRead(self, 0).start()
            else:
                self.background_frame_read = BackgroundFrameRead(self, self.get_udp_video_address()).start()
        return self.background_frame_read

    def get_video_capture(self):
        """
        Get the VideoCapture object from the camera drone
        :return (VideoCapture): The VideoCapture object from the video feed from the drone.
        """
        if self.cap is None:
            if self.is_dummy:
                self.cap = cv.VideoCapture(0)
            else:
                self.cap = cv.VideoCapture(self.get_udp_video_address())

        if not self.cap.isOpened():
            if self.is_dummy:
                self.cap.open(0)
            else:
                self.cap.open(self.get_udp_video_address())

        return self.cap

    def end(self):
        """
        Call this method when you want to end the tello object
        """
        # print(self.send_command('battery?'))
        if not self.is_dummy:
            self.send_command('land')
        if self.background_frame_read is not None:
            self.background_frame_read.stop()
        # It appears that the VideoCapture destructor releases the capture, hence when 
        # attempting to release it manually, a segmentation error occurs.
        # if self.cap is not None:
        #     self.cap.release()

class BackgroundFrameRead:
    """
    This class read frames from a VideoCapture in background. Then, just call backgroundFrameRead.frame to get the
    actual one.
    """

    def __init__(self, tello, address):
        """
        Initializes the Background Frame Read class with a VideoCapture of the specified
        address and the first frame read.
        :param tello: An instance of the Tello class
        :param address: The UDP address through which the video will be streaming
        """
        tello.cap = cv.VideoCapture(address)
        self.cap = tello.cap

        if not self.cap.isOpened():
            self.cap.open(address)

        self.grabbed, self.frame = self.cap.read()
        self.stopped = False

    def start(self):
        """
        Starts the background frame read thread.
        :return (BackgroundFrameRead): The current BrackgroundFrameRead
        """
        threading.Thread(target=self.update_frame, args=()).start()
        return self

    def update_frame(self):
        """
        Sets the current frame to the next frame read from the source.
        """
        while not self.stopped:
            if not self.grabbed or not self.cap.isOpened():
                self.stop()
            else:
                (self.grabbed, self.frame) = self.cap.read()

    def stop(self):
        """
        Stops the frame reading.
        """
        self.stopped = True
