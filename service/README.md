# OCRR_Engine Service

## Description
OCRR_Engine is a Windows service designed to run the `ocrr_engine.py` script. It monitors the `python.exe` process, and in case the `python.exe` process stops unexpectedly, it automatically restarts the `python.exe` process to resume the execution of the `ocrr_engine.py` script.
