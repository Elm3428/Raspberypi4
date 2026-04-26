from pymodbus.client import ModbusTcpClient

def run_client():
    # Connect to the local Modbus TCP server on port 5020
    client = ModbusTcpClient('127.0.0.1', port=5020)
    
    # Attempt to connect
    if client.connect():
        print("Successfully connected to Modbus TCP Server")
        try:
            # Read 5 holding registers starting from address 0
            # Note: Depending on pymodbus version, 'slave' parameter might be required (default is often 1 or 0).
            response = client.read_holding_registers(address=0, count=5, slave=1)
            
            if not response.isError():
                registers = response.registers
                print("-" * 30)
                print("Motor Temperature Readings:")
                print("-" * 30)
                for i, reg in enumerate(registers):
                    # Convert the stored integer (e.g., 450) back to float (45.0)
                    temp_celsius = reg / 10.0
                    print(f"Motor {i+1}: {temp_celsius:.1f} °C")
                print("-" * 30)
            else:
                print(f"Failed to read registers. Error: {response}")
                
        except Exception as e:
            print(f"An error occurred during communication: {e}")
        finally:
            client.close()
            print("Connection closed.")
    else:
        print("Failed to connect to the Modbus TCP Server. Is it running?")

if __name__ == "__main__":
    run_client()
