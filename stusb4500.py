"""
`stusb4500`
================================================================================

CircuitPython driver for STUSB4500 USB Power Delivery board.


* Author(s): Jessica Stokes

Implementation Notes
--------------------

Based on SparkFun's Arduino library, <https://github.com/sparkfun/SparkFun_STUSB4500_Arduino_Library>. Further information and notes from the reference implementation, <https://github.com/usb-c/STUSB4500>. Python library and project structure inspired by <https://github.com/adafruit/Adafruit_CircuitPython_VEML7700> (and Adafruit's other such libraries).

**Hardware:**

* `SparkFun STUSB4500 <https://www.sparkfun.com/products/15801>`

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards:
  https://github.com/adafruit/circuitpython/releases

* Adafruit's Bus Device library: https://github.com/adafruit/Adafruit_CircuitPython_BusDevice
"""

from micropython import const
import adafruit_bus_device.i2c_device as i2cdevice

__version__ = "0.0.0-auto.0"
__repo__ = "https://github.com/ticky/CircuitPython_STUSB4500.git"

# NVM Flasher Registers
FTP_CUST_PASSWORD_REG = const(0x95) # Register address for the password
FTP_CUST_PASSWORD     =   const(0x47) # The default password value

FTP_CTRL_0     = const(0x96) # First control register, and its four parameters
FTP_CUST_PWR   =   const(0x80)
FTP_CUST_RST_N =   const(0x40)
FTP_CUST_REQ   =   const(0x10)
FTP_CUST_SECT  =   const(0x07)

FTP_CTRL_1           = const(0x97) # Second control register, and its two parameters
FTP_CUST_SER_MASK    =   const(0xF8)
FTP_CUST_OPCODE_MASK =   const(0x07)

RW_BUFFER = const(0x53) # Address of the read-write buffer for sharing data

# FTP_CUST_OPCODE field values
READ             = const(0x00) # Read memory array
WRITE_PL         = const(0x01) # Shift In Data on Program Load (PL) Register
WRITE_SER        = const(0x02) # Shift In Data on Sector Erase (SER) Register
READ_PL          = const(0x03) # Shift Out Data on Program Load (PL) Register
READ_SER         = const(0x04) # Shift Out Data on sector Erase (SER) Register
ERASE_SECTOR     = const(0x05) # Erase memory array
PROG_SECTOR      = const(0x06) # Program 256b word into EEPROM
SOFT_PROG_SECTOR = const(0x07) # Soft Program array

# FTP_CUST_SER field values
SECTOR_0 = const(0x01)
SECTOR_1 = const(0x02)
SECTOR_2 = const(0x04)
SECTOR_3 = const(0x08)
SECTOR_4 = const(0x10)

class STUSB4500:
    """Driver for the STUSB4500 USB Power Delivery board.

    :param busio.I2C i2c_bus: The I2C bus the STUSB4500 is connected to.

    """

    read_sectors = False
    sectors_data = bytearray(8 * 5)
    
    def __init__(self, i2c_bus, address=0x28):
        self.i2c_device = i2cdevice.I2CDevice(i2c_bus, address)
        
        if not self.read_sectors:
          self._read_parameters()

    def _read_parameters(self):
      """Read current parameters from the device"""
      self.read_sectors = True
      
      with self.i2c_device as device:
        # The device needs this one-byte "password" to enter read mode
        device.write(bytes([FTP_CUST_PASSWORD_REG, FTP_CUST_PASSWORD]))
        
        # Then we need to reset the controller
        device.write(bytes([FTP_CTRL_0, 0x00])) # NVM internal controller reset
        device.write(bytes([FTP_CTRL_0, (FTP_CUST_PWR | FTP_CUST_RST_N)])) # Set PWR and RST_N bits
        
        # Now that we're in read mode, we need to grab the data from the five NVM "sectors"
        for i in range(5):
          device.write(bytes([FTP_CTRL_0, (FTP_CUST_PWR | FTP_CUST_RST_N)])) # Set PWR and RST_N bits
          device.write(bytes([FTP_CTRL_1, (READ & FTP_CUST_OPCODE_MASK)])) # Set Read Sectors Opcode
          device.write(bytes([FTP_CTRL_0, (i & FTP_CUST_SECT) | FTP_CUST_PWR | FTP_CUST_RST_N | FTP_CUST_REQ])) # Load Read Sectors Opcode
          
          buffer = bytearray(1)
          while True:
            device.write_then_readinto(bytes([FTP_CTRL_0]), buffer)
            if not buffer[0] & FTP_CUST_REQ:
              break
          
          device.write_then_readinto(bytes([RW_BUFFER]), self.sectors_data, in_start=i * 8, in_end=i * 8 + 8)
      
      self._exit_test_mode()

    def _exit_test_mode(self):
      """Exit the "test"/"configuration" mode"""
      
      with self.i2c_device as device:
        device.write(bytes([FTP_CTRL_0, FTP_CUST_RST_N, 0x00])) # Clear Registers
        device.write(bytes([FTP_CUST_PASSWORD_REG, 0x00])) # Clear Password
