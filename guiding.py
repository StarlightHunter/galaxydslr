"""
PHD2 guider helper
"""

from thirdparty.phd2guider import Guider as PHD2Guider


class GuiderHelper:

    guider = None

    def connect(self, hostname="localhost"):
        if self.guider is None:
            self.guider = PHD2Guider(hostname)
            self.guider.Connect()

    def disconnect(self):
        if self.guider is not None:
            self.guider.Disconnect()
            self.guider = None

    def start_dither(self, dither_px, settle_px, settle_time, settle_timeout):
        if self.guider is not None:
            self.guider.Dither(dither_px, settle_px, settle_time, settle_timeout)
        else:
            raise Exception("The guider is not connected")

    def check_settled(self):
        settling = self.guider.CheckSettling()
        if settling.Done:
            if settling.Error:
                raise Exception(settling.Error)
            return True, settling
        return False, settling
