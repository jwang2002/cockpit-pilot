# Serve two test cameras, each on their own process.
from microscope.device_server import device
from microscope.simulators import SimulatedCamera

DEVICES = [
    device(SimulatedCamera, host="127.0.0.1", port=8000),
    device(SimulatedCamera, host="127.0.0.1", port=8001)
]