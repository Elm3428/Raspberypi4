import logging
from pymodbus.server import StartTcpServer
from pymodbus.device import ModbusDeviceIdentification
from pymodbus.datastore import ModbusSequentialDataBlock, ModbusSlaveContext, ModbusServerContext

# Setup logging
logging.basicConfig()
log = logging.getLogger()
log.setLevel(logging.INFO)

def run_server():
    # Define 5 holding registers simulating motor temperatures
    # 450 = 45.0 °C
    # Initialize data store
    # zero_mode=False means block addresses are 1-based. Wire address 0 maps to block address 1.
    store = ModbusSlaveContext(
        di=ModbusSequentialDataBlock(1, [0]*100),
        co=ModbusSequentialDataBlock(1, [0]*100),
        hr=ModbusSequentialDataBlock(1, [450, 465, 420, 501, 395]),
        ir=ModbusSequentialDataBlock(1, [0]*100),
        zero_mode=False
    )

    context = ModbusServerContext(slaves={1: store}, single=False)

    # Server Identity
    identity = ModbusDeviceIdentification()
    identity.VendorName = 'Python Modbus Simulator'
    identity.ProductCode = 'PM'
    identity.VendorUrl = 'http://github.com/riptideio/pymodbus/'
    identity.ProductName = 'Python Modbus Server'
    identity.ModelName = 'Python Modbus Server'
    identity.MajorMinorRevision = '1.0.0'

    log.info("Starting Modbus TCP server on localhost:5020")
    
    # Start the server on port 5020
    StartTcpServer(
        context=context,
        identity=identity,
        address=("127.0.0.1", 5020)
    )

if __name__ == "__main__":
    run_server()
