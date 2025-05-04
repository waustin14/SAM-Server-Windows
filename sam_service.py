"""
Windows Service wrapper for SAM Flask micro‑service.

• Installs with:  python sam_service.py install
• Removes  with:  python sam_service.py remove
• Starts   with:  python sam_service.py start
"""

import os, sys, servicemanager, win32event, win32service
import win32serviceutil
from multiprocessing import Process

SERVICE_NAME = "SAMService"
DISPLAY_NAME = "SAM Segment‑Anything Service"
BASE_DIR      = os.path.abspath(os.path.dirname(__file__))

# --------------------------------------------------------------------------- #
# 1) target workload — your existing Flask server in a child process
# --------------------------------------------------------------------------- #
def run_flask():
    from sam_server import app          # <-- your existing Flask instance
    app.run(host="127.0.0.1", port=5001)

# --------------------------------------------------------------------------- #
# 2) Service framework
# --------------------------------------------------------------------------- #
class SAMService(win32serviceutil.ServiceFramework):
    _svc_name_        = SERVICE_NAME
    _svc_display_name_= DISPLAY_NAME
    _svc_description_ = "Background micro‑service exposing Meta SAM masks on port 5001."

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.stop_event = win32event.CreateEvent(None, 0, 0, None)
        self.worker     = None

    def SvcDoRun(self):
        servicemanager.LogInfoMsg("SAMService starting…")
        self.worker = Process(target=run_flask, daemon=True)
        self.worker.start()

        # Wait until stop signal
        win32event.WaitForSingleObject(self.stop_event, win32event.INFINITE)
        servicemanager.LogInfoMsg("SAMService stopped.")

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.stop_event)
        if self.worker and self.worker.is_alive():
            self.worker.terminate()

# --------------------------------------------------------------------------- #
if __name__ == '__main__':
    # Allow normal CLI usage: install / start / stop …
    win32serviceutil.HandleCommandLine(SAMService)