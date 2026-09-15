import os

PLC_WRITE_ENABLED = os.getenv("PLC_WRITE_ENABLED", "false").lower() == "true"
PLC_MODE = os.getenv("PLC_MODE", "SIMULATOR").upper()
PLC_ENDPOINT = os.getenv("PLC_ENDPOINT", "opc.tcp://plc:4840")
PLC_STOP_TAG = os.getenv("PLC_STOP_TAG", "Conveyor.CV01.StopRequest")
