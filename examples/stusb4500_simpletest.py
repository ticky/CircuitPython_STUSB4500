# SPDX-FileCopyrightText: Copyright (c) 2020 Jessica Stokes
#
# SPDX-License-Identifier: MIT
import board
import busio
import stusb4500

i2c = busio.I2C(board.SCL, board.SDA)
pd_board = stusb4500.STUSB4500(i2c)

print("Current PD Configuration:")
print("PDO Number: {}".format(pd_board.pdo_number))

for i in range(1, 4):
    print(
        "PDO{}: {}V (+{}%/-{}%), {}A".format(
            i,
            pd_board.get_voltage(i),
            pd_board.get_upper_voltage_limit(i),
            pd_board.get_lower_voltage_limit(i),
            pd_board.get_current(i)
        )
    )

print("Flex Current: {}".format(pd_board.flex_current))
print("External Power: {}".format(pd_board.external_power))
print("USB Communication Capable: {}".format(pd_board.usb_comm_capable))
print("Configuration OK GPIO: {}".format(pd_board.config_ok_gpio))
print("GPIO Control: {}".format(pd_board.gpio_ctrl))
print("Enable Power Only Above 5V: {}".format(pd_board.power_above_5v_only))
print("Request Source Current: {}".format(pd_board.req_src_current))
print("Factory Default: {}".format(pd_board.is_factory_defaults))
