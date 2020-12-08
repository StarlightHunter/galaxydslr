"""Web application interface"""

from flask import Flask, jsonify, render_template, request, send_from_directory

from controlapp import Control
from dslr import DSLRManager
from guiding import GuiderHelper


class FrontApp(Flask):
    """
    Frontend flask app class
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.dslr = DSLRManager()
        self.control = Control(self)
        self.guider = GuiderHelper()

    def get_status(self):
        """Get app status"""
        if self.dslr.locked:
            return {"status": True, "locked": True}
        capturing = self.control.current_status in [
            self.control.STATUS_CAPTURING,
            self.control.STATUS_DITHERING,
        ]
        if capturing:
            camera_list = self.control.cached_camera_list
            camera_config = self.control.cached_camera_config
        else:
            camera_list = self.dslr.get_camera_list()
            camera_config = self.dslr.get_config()
        return {
            "status": True,
            "camera_list": camera_list,
            "camera_config": camera_config,
            "capturing": capturing,
            "camera_connected": self.dslr.camera is not None,
            "guider_connected": self.guider.guider is not None,
            "last_capture": self.control.last_capture,
            "image_data": self.control.last_image,
        }


# Initialize flask app
app = FrontApp(__name__)


# Main application page
@app.route("/", methods=["GET"])
def index():
    """Main page"""
    return render_template("html/index.html")


# Static content
@app.route("/static/<path:path>")
def send_js(path):
    return send_from_directory("static", path)


# Internal API calls
@app.route("/status/", methods=["GET"])
def status():
    """Return application status"""
    try:
        return jsonify(app.get_status())
    except Exception as e:
        return jsonify({"status": False, "error": "Failed getting status: %s" % e})


# Camera
@app.route("/camera/list/", methods=["GET"])
def get_camera_list():
    """Return camera list"""
    try:
        app.control.cached_camera_list = app.dslr.get_camera_list()
        return jsonify(
            {
                "status": True,
                "camera_list": app.control.cached_camera_list,
            }
        )
    except Exception as e:
        return jsonify({"status": False, "error": "Failed getting status: %s" % e})


@app.route("/camera/connect/", methods=["POST"])
def camera_connect():
    try:
        port = request.form["port"]
        app.dslr.connect_camera(port)
        return jsonify({"status": True})
    except Exception as e:
        return jsonify({"status": False, "error": "Failed to connect camera: %s" % e})


@app.route("/camera/disconnect/", methods=["POST"])
def camera_disconnect():
    try:
        app.dslr.disconnect_camera()
        return jsonify({"status": True})
    except Exception as e:
        return jsonify(
            {"status": False, "error": "Failed to disconnect camera: %s" % e}
        )


@app.route("/camera/config/", methods=["GET", "POST"])
def camera_config():
    if request.method == "POST":
        # Set camera configuration
        app.dslr.set_config(request.form)
    # Read configuration and return it
    conf = app.dslr.get_config()
    if conf is None:
        return jsonify({"status": False})
    app.control.cached_camera_config = conf
    return jsonify({"status": True, "config": conf})


@app.route("/camera/preview/", methods=["POST"])
def camera_preview():
    try:
        exposure = float(request.form["exposure"])
        image_data = app.dslr.capture_image_bulb(exposure)
        return jsonify(
            {
                "status": True,
                "image_data": image_data,
            }
        )
    except Exception as e:
        return jsonify(
            {"status": False, "error": "Failed getting camera preview: %s" % e}
        )


# Capture management
@app.route("/capture/start/", methods=["POST"])
def capture_start():
    try:
        exposure = float(request.form["exposure"])
        captures = int(request.form["captures"])
        dither = request.form["dither"]
        dither_n = int(request.form["dither_n"])
        dither_px = int(request.form["dither_px"])
        settle_px = int(request.form["settle_px"])
        settle_time = int(request.form["settle_time"])
        settle_timeout = int(request.form["settle_timeout"])
        # Send capture configuration to control thread
        app.control.capture_start(
            exposure,
            captures,
            dither,
            dither_n,
            dither_px,
            settle_px,
            settle_time,
            settle_timeout,
        )
        return jsonify({"status": True})
    except Exception as e:
        return jsonify(
            {"status": False, "error": "Failed starting capture process: %s" % e}
        )


@app.route("/capture/stop/", methods=["POST"])
def capture_stop():
    try:
        app.control.capture_stop()
        return jsonify({"status": True})
    except Exception as e:
        return jsonify(
            {"status": False, "error": "Failed stopping capture process: %s" % e}
        )


@app.route("/capture/status/", methods=["GET"])
def capture_status():
    try:
        capture_status = app.control.get_capture_status()
        return jsonify({"status": True, "capture_status": capture_status})
    except Exception as e:
        return jsonify(
            {"status": False, "error": "Failed getting capture status: %s" % e}
        )


@app.route("/capture/last_image/", methods=["GET"])
def capture_get_last_image():
    try:
        image_data = app.control.get_capture_image()
        return jsonify(
            {
                "status": True,
                "image_data": image_data,
            }
        )
    except Exception as e:
        return jsonify(
            {"status": False, "error": "Failed getting capture image: %s" % e}
        )


# Guider connection
@app.route("/guider/connect/", methods=["POST"])
def guiding_connect():
    """Connect to guiding software"""
    try:
        host = request.form["host"]
        app.guider.connect(host)
        return jsonify({"status": True})
    except Exception as e:
        return jsonify(
            {"status": False, "error": "Failed connecting to guider: %s" % e}
        )


@app.route("/guider/disconnect/", methods=["POST"])
def guiding_disconnect():
    """Disconnect from guiding software"""
    try:
        app.guider.disconnect()
        return jsonify({"status": True})
    except Exception as e:
        return jsonify(
            {"status": False, "error": "Failed disconnecting from guider: %s" % e}
        )
