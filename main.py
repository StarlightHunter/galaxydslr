"""Main script of GalaxyDSLR application"""

import threading

from flaskapp import app

# Application execution
if __name__ == "__main__":
    control_thread = threading.Thread(target=app.control.run)
    control_thread.start()
    app.run(host="0.0.0.0", port=5000)
