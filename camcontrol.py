# Camera control module

# Python modules
import base64
import logging
import tempfile
import time

# GPhoto2 module
import gphoto2 as gp


class DSLRManager:

    TEMP_FILES_PREFIX = "astrocamweb"

    DEFAULT_CONFIG_ELEMS = [
        "iso",
        "aperture",
        "shutterspeed",
        "drivemode",
        "meteringmode",
        "aeb",
        "whitebalance",
        "colorspace",
        "picturestyle",
        "imageformat",
    ]

    def __init__(self, config_elems=DEFAULT_CONFIG_ELEMS, debug=False):
        self.config = None
        self.config_elems = config_elems
        self.debug = debug
        if debug:
            logging.basicConfig(level=logging.DEBUG)
        else:
            logging.basicConfig(level=logging.INFO)
        self.init_camera()

    def init_camera(self):
        logging.info("Initializing camera")
        self.cam = gp.Camera()
        self.cam.init()
        self.config = self.cam.get_config()
        # Set capturetarget as SD card
        self.config.get_child_by_name("capturetarget").set_value("Memory card")
        self.cam.set_config(self.config)

    def get_summary(self):
        return self.cam.get_summary()

    def get_config(self):
        logging.info("Reading camera config")
        config_data = {}
        for elem_name in self.config_elems:
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
        logging.debug("Camera configuration read: %s", config_data)
        return config_data

    def set_config(self, config):
        logging.info("Setting camera config")
        logging.debug("Camera config to be set: %s", config)

        # Refresh configuration
        self.config = self.cam.get_config()

        # Set each value
        for key, value in config.items():
            elem = self.config.get_child_by_name(key)
            elem.set_value(value)

        # Apply camera configuration
        self.cam.set_config(self.config)

        return {"success": True}

    def capture_image(self):
        logging.info("Capturing image")
        # Launch capture
        path = self.cam.capture(gp.GP_CAPTURE_IMAGE)
        # Wait for JPG file to be written if needed
        evtype, evdata = self.cam.wait_for_event(10)
        if evtype == gp.GP_EVENT_FILE_ADDED:
            path = evdata

        data = self.load_image_from_camera(path)

        return {
            "success": True,
            "imagedata": base64.b64encode(data).decode(),
        }

    def capture_image_bulb(self, seconds):
        logging.info("Capturing bulb %s seconds", seconds)
        # Set bulb mode
        self.config.get_child_by_name("shutterspeed").set_value("bulb")
        self.cam.set_config(self.config)

        # Inmediate remote release
        self.config.get_child_by_name("eosremoterelease").set_value("Immediate")
        self.cam.set_config(self.config)

        # Wait the specified number of seconds
        time.sleep(seconds)

        # Release button
        self.config.get_child_by_name("eosremoterelease").set_value("Release 3")
        self.cam.set_config(self.config)

        # By default, data is empty
        data = None

        # Load image only if image format is JPEG or RAW + JPEG
        if self.config.get_child_by_name("imageformat").get_value() != "RAW":
            timeout = time.time()
            while True:
                evtype, evdata = self.cam.wait_for_event(100)
                if evtype == gp.GP_EVENT_FILE_ADDED:
                    path = evdata
                    if path.name.lower().endswith("jpg"):
                        image_data = self.load_image_from_camera(path)
                        data = base64.b64encode(image_data).decode()
                        break
                # If time is greater than the number of seconds of the take + 10 we abort
                if time.time() - timeout > seconds + 10:
                    break

        return {
            "success": True,
            "imagedata": data,
        }

    def load_image_from_camera(self, path):
        logging.info("Loading image from camera: %s %s", path.folder, path.name)
        camera_file = self.cam.file_get(path.folder, path.name, gp.GP_FILE_TYPE_NORMAL)
        fd, tmp_path = tempfile.mkstemp(prefix=self.TEMP_FILES_PREFIX)
        camera_file.save(tmp_path)

        with open(tmp_path, "rb") as fd:
            data = fd.read()
            fd.close()

        return data

    def quit(self):
        logging.info("Exiting")
        self.cam.exit()
