# SPDX-FileCopyrightText: Copyright (c) 2020 Jessica Stokes
#
# SPDX-License-Identifier: MIT
"""
`stusb4500` - CircuitPython driver for STUSB4500 USB Power Delivery board
=========================================================================
"""

from micropython import const
import adafruit_bus_device.i2c_device as i2cdevice

__version__ = "0.0.0-auto.0"
__repo__ = "https://github.com/ticky/CircuitPython_STUSB4500.git"

DEFAULT_NVM = bytes([
  0x00, 0x00, 0xB0, 0xAA, 0x00, 0x45, 0x00, 0x00,
  0x10, 0x40, 0x9C, 0x1C, 0xFF, 0x01, 0x3C, 0xDF,
  0x02, 0x40, 0x0F, 0x00, 0x32, 0x00, 0xFC, 0xF1,
  0x00, 0x19, 0x56, 0xAF, 0xF5, 0x35, 0x5F, 0x00,
  0x00, 0x4B, 0x90, 0x21, 0x43, 0x00, 0x40, 0xFB
])

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
    """
    Represents a STUSB4500 I2C device and manages its communication, locking
    and configuration.

    Properties and ``set_*`` methods do not directly write to the device,
    instead the device's configuration is read when this class is initialised
    (or by explicitly calling :py:meth:`read_parameters` if changes should be
    abandoned), and parameters are read and written to that buffer.

    To change settings on the device, you must set the desired configuration
    using the supplied methods and properties, and once satisfied may call the
    :py:meth:`write_parameters` method to commit the parameters to the device's
    non-volatile memory.

    :param busio.I2C i2c_bus: The I2C bus the STUSB4500 is connected to.
    :param int address: The I2C device address. If omitted, the default of
        ``0x28`` is used.

    """

    sectors_data = bytearray(8 * 5)

    def __init__(self, i2c_bus, address=0x28):
        self.i2c_device = i2cdevice.I2CDevice(i2c_bus, address)
        self.read_parameters()

    def read_parameters(self):
        """
        Read all the current NVM parameters from the device.

        The :class:`STUSB4500` object will automatically read the current NVM
        parameters when initialised, however, you may use this function to
        fetch the currently stored parameters if otherwise needed, for example,
        to reset any pending changes which have not yet been written to the
        device.
        """

        self.__enter_read_mode()

        # Now that we're in read mode, we need to grab the data from the five NVM "sectors"
        for i in range(5):
            with self.i2c_device as device:
                device.write(bytes([
                  FTP_CTRL_0, (FTP_CUST_PWR | FTP_CUST_RST_N) # Set PWR and RST_N bits
                ]))
                device.write(bytes([
                  FTP_CTRL_1, (READ & FTP_CUST_OPCODE_MASK) # Set Read Sectors Opcode
                ]))
                device.write(bytes([
                  FTP_CTRL_0, # Load Read Sectors Opcode
                  (i & FTP_CUST_SECT) | FTP_CUST_PWR | FTP_CUST_RST_N | FTP_CUST_REQ
                ]))

            self.__await_ftp_cust_req() # Wait for execution

            with self.i2c_device as device:
                device.write_then_readinto(
                  bytes([RW_BUFFER]),
                  self.sectors_data,
                  in_start=i * 8,
                  in_end=i * 8 + 8
                )

        self.__exit_test_mode()

    def write_parameters(self):
        """
        Writes all current parameters to the device.
        """
        self.__write_parameters(self.sectors_data)

    def write_parameter_defaults(self):
        """
        Writes the factory-default parameters to the device.
        """
        self.__write_parameters(DEFAULT_NVM)

    def __write_parameters(self, data):
        """
        Writes all parameters from the provided object to the device.

        :param bytes data: The NVM parameter bytes to write.
            Must be exactly 40 bytes long.
        """

        # BEGIN Entering Write Mode

        self.__enter_password()

        with self.i2c_device as device:
            # This register must be NULL for Partial Erase feature
            device.write(bytes([RW_BUFFER, 0x00]))

        self.__nvm_power_up()

        with self.i2c_device as device:
            # Note: we always write all the sectors, without regard for where
            # changes may in fact have occurred, if at all.
            # If this weren't aimed at use in a memory-constrained environment,
            # one could almost certainly optimise this further.
            erase_sectors = SECTOR_0 | SECTOR_1 | SECTOR_2 | SECTOR_3 | SECTOR_4

            # Load 0xF1 to erase all sectors of FTP and Write SER Opcode
            device.write(bytes([
              FTP_CTRL_1, # Set Write SER Opcode
              (((erase_sectors << 3) & FTP_CUST_SER_MASK)
              | (WRITE_SER & FTP_CUST_OPCODE_MASK))
            ]))

            device.write(bytes([
              FTP_CTRL_0, # Load Write SER Opcode
              FTP_CUST_PWR | FTP_CUST_RST_N | FTP_CUST_REQ
            ]))

        self.__await_ftp_cust_req() # Wait for execution

        with self.i2c_device as device:
            device.write(bytes([
              FTP_CTRL_1, # Set Soft Prog Opcode
              SOFT_PROG_SECTOR & FTP_CUST_OPCODE_MASK
            ]))

            device.write(bytes([
              FTP_CTRL_0, # Load Soft Prog Opcode
              FTP_CUST_PWR | FTP_CUST_RST_N | FTP_CUST_REQ
            ]))

        self.__await_ftp_cust_req() # Wait for execution

        with self.i2c_device as device:
            device.write(bytes([
              FTP_CTRL_1, # Set Erase Sectors Opcode
              ERASE_SECTOR & FTP_CUST_OPCODE_MASK
            ]))

            device.write(bytes([
              FTP_CTRL_0, # Load Erase Sectors Opcode
              FTP_CUST_PWR | FTP_CUST_RST_N | FTP_CUST_REQ
            ]))

        self.__await_ftp_cust_req() # Wait for execution

        # END Entering Write Mode

        # Now that we're in write mode, we need to send the data to the five NVM "sectors"
        for i in range(5):
            with self.i2c_device as device:
                # Write the 64-bit data to be written in the sector
                device.write(bytes([RW_BUFFER]) + data[i * 8:i * 8 + 8])

                device.write(bytes([
                  FTP_CTRL_0, (FTP_CUST_PWR | FTP_CUST_RST_N) # Set PWR and RST_N bits
                ]))

                # NVM Program Load Register to write with the 64-bit data to be written in sector
                device.write(bytes([
                  FTP_CTRL_1, (WRITE_PL & FTP_CUST_OPCODE_MASK) # Set Write to PL Opcode
                ]))

                device.write(bytes([
                  FTP_CTRL_0, # Load Write to PL Sectors Opcode
                  FTP_CUST_PWR | FTP_CUST_RST_N | FTP_CUST_REQ
                ]))

            self.__await_ftp_cust_req() # Wait for execution

            with self.i2c_device as device:
                # NVM "Word Program" operation to write the
                # Program Load Register in the sector to be written
                device.write(bytes([
                  FTP_CTRL_1, (PROG_SECTOR & FTP_CUST_OPCODE_MASK) # Set Prog Sectors Opcode
                ]))

                device.write(bytes([
                  FTP_CTRL_0, # Load Prog Sectors Opcode
                  (i & FTP_CUST_SECT) | FTP_CUST_PWR | FTP_CUST_RST_N | FTP_CUST_REQ
                ]))

            self.__await_ftp_cust_req() # Wait for execution

        self.__exit_test_mode()

    def __await_ftp_cust_req(self):
        """
        Waits for the ``FTP_CTRL_0`` register to have ``FTP_CUST_REQ`` cleared,
        indicating a requested operation has finished.

        Must be called outside an :class:`busio.I2C` lock, or it will freeze.
        """

        buffer = bytearray(1)

        with self.i2c_device as device:
            # This feels like a smelly way to do a "do...while" but
            # if there's a better way in Python I am all ears!
            while True: # Wait for execution
                device.write_then_readinto(bytes([FTP_CTRL_0]), buffer)

                # The FTP_CUST_REQ is cleared by NVM controller when the operation is finished
                if not buffer[0] & FTP_CUST_REQ:
                    break

    def __enter_read_mode(self):
        """
        Enters the "read" mode for reading configuration.
        Must be exited using :py:meth:`__exit_test_mode`.
        """

        self.__enter_password()
        self.__nvm_power_up()

    def __enter_password(self):
        """
        Enters the default password byte to the password register.
        """

        with self.i2c_device as device:
            # The device needs this one-byte "password"
            device.write(bytes([FTP_CUST_PASSWORD_REG, FTP_CUST_PASSWORD]))

    def __nvm_power_up(self):
        """
        NVM Power-up Sequence: After STUSB start-up sequence,
        the NVM is powered off.
        """

        with self.i2c_device as device:
            device.write(bytes([FTP_CTRL_0, 0x00])) # NVM internal controller reset
            device.write(bytes([
                FTP_CTRL_0, (FTP_CUST_PWR | FTP_CUST_RST_N) # Set PWR and RST_N bits
            ]))

    def __exit_test_mode(self):
        """
        Exit the "test"/"configuration" mode
        """

        with self.i2c_device as device:
            device.write(bytes([FTP_CTRL_0, FTP_CUST_RST_N, 0x00])) # Clear Registers
            device.write(bytes([FTP_CUST_PASSWORD_REG, 0x00])) # Clear Password

    @property
    def is_factory_defaults(self):
        """
        Check whether the current configuration is the same as the factory
        defaults.

        :rtype: bool
        """

        return self.sectors_data == DEFAULT_NVM

    # BEGIN Individual setting read/write methods and properties

    # Note: All the "gets" that take a PDO number are just methods,
    # because there didn't seem to be a nice way to make them properties

    def get_voltage(self, pdo=None):
        """
        Returns the voltage requested for the PDO number

        :param int pdo: PDO number (either ``1``, ``2``, or ``3``) to retrieve
            the parameter for.
            If omitted, or another value is passed, defaults to ``3``.

        :return: The voltage requested for the PDO, in volts.
        :rtype: decimal
        """

        if pdo == 1:
            return 5

        if pdo == 2:
            return self.sectors_data[4 * 8 + 1] * 0.2

        # PDO 3
        return (((self.sectors_data[4 * 8 + 3] & 0x03) << 8) + self.sectors_data[4 * 8 + 2]) * 0.05

    def set_voltage(self, voltage, pdo=None):
        """
        Sets the desired voltage for the PDO number

        :param decimal voltage: The voltage to request for the PDO, in volts.
            Must be between 5.0V and 20.0V.
        :param int pdo: PDO number (either ``2``, or ``3``) to retrieve
            the parameter for.
            If omitted, or another value is passed, defaults to ``3``.
            PDO1 is always set to 5.0V.
        """

        # Restrict voltage values to 5~20V
        if voltage < 5:
            voltage = 5

        elif voltage > 20:
            voltage = 20

        if pdo == 2:
            self.sectors_data[4 * 8 + 1] = int(voltage / 0.2)

        else:
            # Set voltage, converted to 10 bits
            voltage = int(voltage / 0.05)
            self.sectors_data[4 * 8 + 2] = 0xFF & voltage # load bits 0:7
            self.sectors_data[4 * 8 + 3] &= 0xFC # clear bits 0:1
            self.sectors_data[4 * 8 + 3] |= voltage >> 8 # load bits 8:9

    def get_current(self, pdo=None):
        """
        Returns the current requested for the PDO number

        :param int pdo: PDO number (either ``1``, ``2``, or ``3``) to retrieve
            the parameter for.
            If omitted, or another value is passed, defaults to ``3``.

        :return: The current requested for the PDO, in amps.
        :rtype: decimal
        """

        if pdo == 1:
            digital_value = (self.sectors_data[3 * 8 + 2] & 0xF0) >> 4

        elif pdo == 2:
            digital_value = self.sectors_data[3 * 8 + 4] & 0x0F

        else: # PDO 3
            digital_value = (self.sectors_data[3 * 8 + 5] & 0xF0) >> 4

        if digital_value == 0:
            return digital_value

        if digital_value < 11:
            return digital_value * 0.25 + 0.25

        return digital_value * 0.50 - 2.50

    def set_current(self, current, pdo=None):
        """
        Sets the desired current for the PDO number

        Current is stored as a 4-bit value, and has different precision
        depending on the magnitude. Values between 0.5 and 3.0A are set in
        0.25A steps, while values between 3.0 and 5.0A are in 0.5A steps.

        Input values are automatically rounded to the nearest possible value.

        :param decimal current: The current to request for the PDO, in amps.
            Must be between 0.0A and 5.0A.
        :param int pdo: PDO number (either ``1``, ``2``, or ``3``) to retrieve
            the parameter for.
            If omitted, or another value is passed, defaults to ``3``.
        """

        # Convert current to 4-bit value
        if current < 0.5:
            current = 0

        elif current <= 3:
            current = int((4 * current) - 1)

        else:
            if current > 5:
                current = 5

            current = int((2 * current) + 5)

        if pdo == 1:
            self.sectors_data[3 * 8 + 2] &= 0x0F # clear bits 4:7
            self.sectors_data[3 * 8 + 2] |= current << 4

        elif pdo == 2:
            self.sectors_data[3 * 8 + 4] &= 0xF0 # clear bits 0:3
            self.sectors_data[3 * 8 + 4] |= current

        else:
            self.sectors_data[3 * 8 + 5] &= 0x0F # clear bits 4:7
            self.sectors_data[3 * 8 + 5] |= current << 4

    def get_lower_voltage_limit(self, pdo=None):
        """
        Returns the under voltage lockout parameter for the PDO number

        :param int pdo: PDO number (either ``1``, ``2``, or ``3``) to retrieve
            the parameter for.
            If omitted, or another value is passed, defaults to ``3``.

        :return: The under voltage limit requested for the PDO, in percent.
        :rtype: decimal
        """

        if pdo == 1:
            return 5

        if pdo == 2:
            return (self.sectors_data[3 * 8 + 4] >> 4) + 5

        # PDO 3
        return (self.sectors_data[3 * 8 + 6] & 0x0F) + 5

    def get_upper_voltage_limit(self, pdo=None):
        """
        Returns the over voltage lockout parameter for the PDO number

        :param int pdo: PDO number (either ``1``, ``2``, or ``3``) to retrieve
            the parameter for.
            If omitted, or another value is passed, defaults to ``3``.

        :return: The over voltage limit requested for the PDO, in percent.
        :rtype: decimal
        """

        if pdo == 1:
            return (self.sectors_data[3 * 8 + 3] >> 4) + 5

        if pdo == 2:
            return (self.sectors_data[3 * 8 + 5] & 0x0F) + 5

        # PDO 3
        return (self.sectors_data[3 * 8 + 6] >> 4) + 5

    @property
    def flex_current(self):
        """
        A float value to set the current common to all PDOs.
        This value is only used in the power negotiation if the current value
        for that PDO is set to ``0``.

        :rtype: float
        """

        return (
            ((self.sectors_data[4 * 8 + 4] & 0x0F) << 6)
            + ((self.sectors_data[4 * 8 + 3] & 0xFC) >> 2)
        ) / 100

    @property
    def pdo_number(self):
        """
        The value saved in memory for the highest priority PDO number

        :rtype: int
        """

        return (self.sectors_data[3 * 8 + 2] & 0x06) >> 1

    @property
    def external_power(self):
        """
        The value for the ``SNK_UNCONS_POWER`` parameter.

        ``SNK_UNCONS_POWER`` is the unconstrained power bit setting in
        the capabilities message sent by the sink. ``True`` means an
        external source of power is available and is sufficient to
        adequately power the system while charging external devices.

        :rtype: bool
        """

        return (self.sectors_data[3 * 8 + 2] & 0x08) >> 3 == 1

    @property
    def usb_comm_capable(self):
        """
        ``USB_COMM_CAPABLE`` refers to USB2.0 or 3.x data communication
        capability by the sink system. ``True`` means that the sink supports
        data communication.

        :rtype: bool
        """

        return self.sectors_data[3 * 8 + 2] & 0x01 == 1

    @property
    def config_ok_gpio(self):
        """
        Controls the behaviour of the ``VBUS_EN_SNK``, ``POWER_OK2``,
        and ``POWER_OK3`` pins

        :rtype: int
        """

        return (self.sectors_data[4 * 8 + 4] & 0x60) >> 5

    @property
    def gpio_ctrl(self):
        """
        Controls the behaviour setting for the GPIO pin

        :rtype: int
        """

        return (self.sectors_data[1 * 8 + 0] & 0x30) >> 4

    @property
    def power_above_5v_only(self):
        """
        Controls whether the output will be enabled only when the source is
        attached and VBUS voltage is negotiated to PDO2 or PDO3

        :rtype: bool
        """

        return (self.sectors_data[4 * 8 + 6] & 0x08) >> 3 == 1

    @property
    def req_src_current(self):
        """
        ``False`` requests the sink current as operating current in the RDO
        message. ``True`` requests the source current as operating current in
        the RDO message.

        :rtype: bool
        """

        return (self.sectors_data[4 * 8 +  6] & 0x10) >> 4 == 1
