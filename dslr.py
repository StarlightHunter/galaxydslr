# Camera control module

# Python modules
import base64
import logging
import time

# GPhoto2 module
import gphoto2 as gp


class DSLRManager:
    """DSLR manager class"""

    CONFIG_ELEMS = [
        "aperture",
        "iso",
        "shutterspeed",
        "drivemode",
        "aeb",
        "whitebalance",
        "colorspace",
        "picturestyle",
        "imageformat",
        "capturetarget",
    ]

    camera = None
    config = None
    webapp = None
    locked = False

    def __init__(self, webapp=None):
        if webapp:
            self.webapp = webapp
            self.logger = webapp.logger
        else:
            self.logger = logging.getLogger()

    def _update_config(self):
        self.locked = True
        self.camera.set_config(self.config)
        self.locked = False

    def _read_config(self):
        self.locked = True
        self.config = self.camera.get_config()
        self.locked = False

    def setup(self):
        self.camera = None
        self.config = None
        self.locked = False

    def get_camera_list(self):
        camera_list = list(gp.Camera.autodetect())
        if camera_list:
            camera_list.sort(key=lambda x: x[0])
        current = None
        if self.camera:
            current = self.camera.get_port_info().get_path()
        return {"choices": camera_list, "current": current}

    def connect_camera(self, port):
        self.camera = gp.Camera()
        # Search ports for camera port name
        port_info_list = gp.PortInfoList()
        port_info_list.load()
        idx = port_info_list.lookup_path(port)
        self.camera.set_port_info(port_info_list[idx])
        self.camera.init()
        # Get camera configuration
        self.config = self.camera.get_config()

    def disconnect_camera(self):
        """Disconnect from camera"""
        try:
            self.camera.exit()
        except Exception:
            pass
        self.setup()

    def get_summary(self):
        return self.camera.get_summary()

    def get_config(self):
        if not self.camera:
            self.logger.info("Not reading camera config. Camera is not set.")
            return None
        self.logger.info("Reading camera config")
        self._read_config()
        config_data = {}
        for elem_name in self.CONFIG_ELEMS:
            elem = self.config.get_child_by_name(elem_name)
            choices = []
            current = None
            value = elem.get_value()
            choice_count = elem.count_choices()
            for n in range(choice_count):
                choice = elem.get_choice(n)
                if choice:
                    choices.append(choice)
                    if choice == value:
                        current = choice
            config_data[elem_name] = {"choices": choices, "current": current}
        self.logger.debug("Camera configuration read: %s", config_data)
        return config_data

    def set_config(self, config):
        self.logger.info("Setting camera config")
        self.logger.debug("Camera config to set: %s", config)

        # Refresh configuration
        self._read_config()

        # Set each value
        for key, value in config.items():
            self.logger.debug("Setting camera parameter: %s -> %s", key, value)
            elem = self.config.get_child_by_name(key)
            elem.set_value(value)

        # Apply camera configuration
        self._update_config()

    def capture_image_bulb(self, seconds):
        self.logger.info("Capturing bulb %s seconds", seconds)
        # Set bulb mode
        self.config.get_child_by_name("shutterspeed").set_value("bulb")
        self._update_config()

        # Inmediate remote release
        self.config.get_child_by_name("eosremoterelease").set_value("Immediate")
        self._update_config()

        # Wait the specified number of seconds
        time.sleep(seconds)

        # Release button
        self.config.get_child_by_name("eosremoterelease").set_value("Release 3")
        self._update_config()

        # By default, data is empty
        data = None

        # Load image only if image format is JPEG or RAW + JPEG
        if self.config.get_child_by_name("imageformat").get_value() != "RAW":
            timeout = time.time()
            while True:
                evtype, evdata = self.camera.wait_for_event(100)
                if evtype == gp.GP_EVENT_FILE_ADDED:
                    path = evdata
                    if path.name.lower().endswith("jpg"):
                        image_data = self.load_image_from_camera(path)
                        data = base64.b64encode(image_data).decode()
                        break
                # If time is greater than the number of seconds of the take + 10 we abort
                if time.time() - timeout > seconds + 10:
                    break
        return data

    def load_image_from_camera(self, path):
        self.locked = True
        self.logger.info("Loading image from camera: %s %s", path.folder, path.name)
        camera_file = self.camera.file_get(
            path.folder, path.name, gp.GP_FILE_TYPE_NORMAL
        )
        file_data = camera_file.get_data_and_size()
        self.locked = False
        return file_data


if __name__ == "__main__":
    import pprint

    m = DSLRManager()
    cameras = m.get_camera_list()
    if cameras:
        print("Detected cameras: %s" % cameras)
        cam = cameras["choices"][0]
        print("Connecting to camera {} on port {}".format(cam[0], cam[1]))
        m.connect_camera(cam[1])
        print(m.get_summary())
        print("Reading configuration")
        pprint.pprint(m.get_config())
        print("Setting configuration")
        config = {
            "iso": "100",
            "shutterspeed": "bulb",
            "drivemode": "Single",
            "meteringmode": "Evaluative",
            "aeb": "off",
            "whitebalance": "Daylight",
            "colorspace": "sRGB",
            "picturestyle": "Faithful",
            "imageformat": "RAW + Large Fine JPEG",
            "capturetarget": "Memory card",
        }
        pprint.pprint(config)
        m.set_config(config)
        print("Reading configuration again")
        pprint.pprint(m.get_config())
        print("Disconnecting from camera")
        m.disconnect_camera()
    else:
        print("No cameras detected")
