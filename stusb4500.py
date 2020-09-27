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
    
    sectors_data = bytearray(8 * 5)
    
    def __init__(self, i2c_bus, address=0x28):
        self.i2c_device = i2cdevice.I2CDevice(i2c_bus, address)
        self._read_parameters()
    
    def _read_parameters(self):
      """Read current parameters from the device"""
      
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
            device.write_then_readinto(bytes([FTP_CTRL_0]), buffer) # Wait for execution
            
            # This feels like a smelly way to do a "do...while" but
            # if there's a better way in Python I am all ears!
            if not buffer[0] & FTP_CUST_REQ: # The FTP_CUST_REQ is cleared by NVM controller when the operation is finished
              break
          
          device.write_then_readinto(bytes([RW_BUFFER]), self.sectors_data, in_start=i * 8, in_end=i * 8 + 8)
      
      self._exit_test_mode()
    
    def _exit_test_mode(self):
      """Exit the "test"/"configuration" mode"""
      
      with self.i2c_device as device:
        device.write(bytes([FTP_CTRL_0, FTP_CUST_RST_N, 0x00])) # Clear Registers
        device.write(bytes([FTP_CUST_PASSWORD_REG, 0x00])) # Clear Password
    
    # Note: All the "gets" that take a PDO number are just methods,
    # because there didn't seem to be a nice way to make them properties
    
    def get_voltage(self, pdo=None):
      """Returns the voltage requested for the PDO number"""
      
      if pdo == 1:
        return 5
      
      elif pdo == 2:
        return self.sectors_data[4 * 8 + 1] * 0.2
      
      else: # PDO 3
        return (((self.sectors_data[4 * 8 + 3] & 0x03) << 8) + self.sectors_data[4 * 8 + 2]) * 0.05
    
    def get_current(self, pdo=None):
      """Returns the current requested for the PDO number"""
      
      if pdo == 1:
        digital_value = (self.sectors_data[3 * 8 + 2] & 0xF0) >> 4
      
      elif pdo == 2:
        digital_value = self.sectors_data[3 * 8 + 4] & 0x0F
      
      else: # PDO 3
        digital_value = (self.sectors_data[3 * 8 + 5] & 0xF0) >> 4
      
      if digital_value == 0:
        return digital_value
      
      elif digital_value < 11:
        return digital_value * 0.25 + 0.25
      
      else:
        return digital_value * 0.50 - 2.50
    
    def get_lower_voltage_limit(self, pdo=None):
      """Returns the under voltage lockout parameter for the PDO number"""
      
      if pdo == 1:
        return 5
      
      elif pdo == 2:
        return (self.sectors_data[3 * 8 + 4] >> 4) + 5
      
      else: # PDO 3
        return (self.sectors_data[3 * 8 + 6] & 0x0F) + 5
    
    def get_upper_voltage_limit(self, pdo=None):
      """Returns the over voltage lockout parameter for the PDO number"""
      
      if pdo == 1:
        return (self.sectors_data[3 * 8 + 3] >> 4) + 5
      
      elif pdo == 2:
        return (self.sectors_data[3 * 8 + 5] & 0x0F) + 5
      
      else: # PDO 3
        return (self.sectors_data[3 * 8 + 6] >> 4) + 5
    
    @property
    def flex_current(self):
      """A float value to set the current common to all PDOs. This value is only used in the power negotiation if the current value for that PDO is set to 0."""
      
      return ((self.sectors_data[4 * 8 + 4] & 0x0F) << 6) + ((self.sectors_data[4 * 8 + 3] & 0xFC) >> 2) / 100
    
    @property
    def pdo_number(self):
      """The value saved in memory for the highest priority PDO number"""
      
      return (self.sectors_data[3 * 8 + 2] & 0x06) >> 1
    
    @property
    def external_power(self):
      """The value for the SNK_UNCONS_POWER parameter. SNK_UNCONS_POWER is the unconstrained power bit setting in capabilities message sent by the sink. True means an external source of power is available and is sufficient to adequately power the system while charging external devices"""
      
      return (self.sectors_data[3 * 8 + 2] & 0x08) >> 3 == 1
    
    @property
    def usb_comm_capable(self):
      """USB_COMM_CAPABLE refers to USB2.0 or 3.x data communication capability by the sink system. True means that the sink does support data communication."""
      
      return self.sectors_data[3 * 8 + 2] & 0x01 == 1
    
    @property
    def config_ok_gpio(self):
      """Controls the behaviour of the VBUS_EN_SNK, POWER_OK2, and POWER_OK3 pins"""
      
      return (self.sectors_data[4 * 8 + 4] & 0x60) >> 5
    
    @property
    def gpio_ctrl(self):
      """Controls the behaviour setting for the GPIO pin"""
      
      return (self.sectors_data[1 * 8 + 0] & 0x30) >> 4
    
    @property
    def power_above_5v_only(self):
      """Controls whether the output will be enabled only when the source is attached and VBUS voltage is negotiated to PDO2 or PDO3"""
      
      return (self.sectors_data[4 * 8 + 6] & 0x08) >> 3 == 1
    
    @property
    def req_src_current(self):
      """False requests the sink current as operating current in the RDO message. True requests the source current as operating current in the RDO message."""
      
      return (self.sectors_data[4 * 8 +  6] & 0x10) >> 4 == 1
