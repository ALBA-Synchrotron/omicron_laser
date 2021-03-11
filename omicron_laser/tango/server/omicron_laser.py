# -*- coding: utf-8 -*-
#
# This file is part of the Omicron Laser project
#
# Copyright (c) 2021 Alberto López Sánchez
# Distributed under the GNU General Public License v3. See LICENSE for more info.

"""Tango server class for Omicron_laser"""

import serial
from tango.server import Device, attribute, command, device_property

import omicron_laser.core


class Omicron_laser(Device):

    url = device_property(dtype=str)

    def init_device(self):
        super().init_device()
        self.connection = serial.serial_for_url(self.url)
        self.omicron_laser = omicron_laser.core.Omicron_laser(
            self.connection)


    

################################################################################

    @attribute(dtype=float, unit="bar", label="Pressure set point")
    def pressure_setpoint(self):
        # example processing the result
        setpoint = self.omicron_laser.get_pressure_setpoint()
        return setpoint / 1000

    @pressure_setpoint.setter
    def pressure_setpoint(self, value):
        # example returning the coroutine back to tango
        return self.omicron_laser.get_pressure_setpoint(value * 1000)

    @command
    def turn_on(self):
        # example returning the coroutine back to who calling function
        return self.omicron_laser.turn_on()


if __name__ == "__main__":
    import logging
    fmt = "%(asctime)s %(levelname)s %(name)s %(message)s"
    logging.basicConfig(level="DEBUG", format=fmt)
    Omicron_laser.run_server()
