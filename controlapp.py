"""Control application"""

import time


class Control:
    """
    Control class
    """

    # Control status modes
    STATUS_IDLE = 0
    STATUS_CAPTURING = 1
    STATUS_DITHERING = 2
    STATUS_STOPPING = 3

    # Loop delay in seconds
    LOOP_DELAY = 0.5

    cached_camera_list = None
    cached_camera_config = None

    def __init__(self, webapp):
        self.webapp = webapp
        self.current_status = self.STATUS_IDLE
        self.current_capture = 0
        self.last_image = None
        self.last_capture = 0
        self.capture_parms = None
        self.dither_status = None

    def run(self):
        while True:
            self.loop_iteration()
            time.sleep(self.LOOP_DELAY)

    def loop_iteration(self):
        self.webapp.logger.debug("Control: Looping")
        # Control loop
        if self.current_status == self.STATUS_CAPTURING:
            if self.current_capture == self.capture_parms["captures"]:
                print("Finished capturing process")
                self.current_status = self.STATUS_STOPPING
            else:
                self.current_capture += 1
                print(
                    "Stared capturing image {}/{}".format(
                        self.current_capture, self.capture_parms["captures"]
                    )
                )
                # Capture image
                self.last_image = self.webapp.dslr.capture_image_bulb(
                    self.capture_parms["exposure"]
                )
                self.last_capture = self.current_capture
                time.sleep(self.capture_parms["exposure"])
                print(
                    "Finished capturing image {}/{}".format(
                        self.current_capture, self.capture_parms["captures"]
                    )
                )
                # Check dithering
                if self.current_capture < self.capture_parms["captures"]:
                    if self.current_capture % self.capture_parms["dither_n"] == 0:
                        self.current_status = self.STATUS_DITHERING
                        try:
                            self.webapp.guider.start_dither(
                                dither_px=self.capture_parms["dither_px"],
                                settle_px=self.capture_parms["settle_px"],
                                settle_time=self.capture_parms["settle_time"],
                                settle_timeout=self.capture_parms["settle_timeout"],
                            )
                        except Exception as e:
                            print("Error starting dithering: ", e)
        if self.current_status == self.STATUS_DITHERING:
            print("Dithering")
            try:
                settled, settling = self.webapp.guider.check_settled()
                if settled:
                    # Continue capturing
                    self.dither_status = None
                    self.current_status = self.STATUS_CAPTURING
                else:
                    self.dither_status = {
                        "dist": settling.Distance,
                        "px": settling.SettlePx,
                        "time": settling.Time,
                        "settle_time": settling.SettleTime,
                    }
                    print("Dithering status: %s" % self.dither_status)
            except Exception as e:
                # TODO: Status error and error messages
                print("Dithering error: ", e)
        if self.current_status == self.STATUS_STOPPING:
            print("Stopping captures")
            self.current_status = self.STATUS_IDLE
            print("Stopped captures")

    def process_message(self, message):
        self.webapp.logger.debug("Control: Message received: %s", message)

    def capture_start(
        self,
        exposure,
        captures,
        dither,
        dither_n,
        dither_px,
        settle_px,
        settle_time,
        settle_timeout,
    ):
        # Cache camera list and current camera config
        self.cached_camera_list = self.webapp.dslr.get_camera_list()
        self.cached_camera_config = self.webapp.dslr.get_config()

        # Initialize capture configuration parameters
        self.capture_parms = {
            "exposure": exposure,
            "captures": captures,
            "dither": dither,
            "dither_n": dither_n,
            "dither_px": dither_px,
            "settle_px": settle_px,
            "settle_time": settle_time,
            "settle_timeout": settle_timeout,
        }
        # Initialize capture status parameters
        self.current_capture = 0
        self.last_image = None
        self.last_capture = 0
        self.current_status = self.STATUS_CAPTURING

    def capture_stop(self):
        self.current_status = self.STATUS_STOPPING

    def get_capture_status(self):
        return {
            "current_status": self.current_status,
            "current_capture": self.current_capture,
            "last_capture": self.last_capture,
            "capture_parms": self.capture_parms,
            "dither_status": self.dither_status,
        }

    def get_capture_image(self):
        return self.last_image
