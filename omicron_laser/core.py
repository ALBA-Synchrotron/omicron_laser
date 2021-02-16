# -*- coding: utf-8 -*-
#
# This file is part of the Omicron Laser project
#
# Copyright (c) 2021 Alberto López Sánchez
# Distributed under the GNU General Public License v3. See LICENSE for more info.

"""
Core Omicron_laser module.

It can receive an asynchronous connection object. Example::

    from connio import connection_for_url
    from omicron_laser.core import Omicron_laser

    async def main():
        tcp = connection_for_url("tcp://omicron_laser.acme.org:5000")
        omicron_laser = Omicron_laser(tcp)

        idn = await omicron_laser.get_idn()
        print(idn)

    asyncio.run(main())
"""
from serial import Serial
import serial


class Status:

    @staticmethod
    def __bit_enabled(byte: bytes, pos: int) -> bool:
        return int(byte) & (0x01 << pos) != 0

    def __init__(self, bytes) -> None:
        """
        This bit indicates whetherany preceded or pending error prevents the
        devicefrom starting into normal operation. Only if this bit is unset
        the laser/ledwill operate as expected. Please refer to the
        “error handling” chapter for details.
        """
        self.error = self.__bit_enabled(bytes[0], 0)

        """
        If the bit is set the laser/led is switched on and the working hours
        are counting. Note: there are some other dependencies that may prevent
        the laser/led from emitting light. Please refer to the “Best practices”
        chapter for details.
        """
        self.on = self.__bit_enabled(bytes[0], 1)

        """
        This bit indicates if the device is actually preheating. This is a
        temporary state. If the laser/led is already switched on, the
        “Laser-ON”/“Led-ON” bit will be signaled beside the “preheating” bit
        but the laser/led will not emit light during this situation. Immediately
        after the diode temperature has reached the valid range the laser/led
        will start into operation.
        """
        self.preheating = self.__bit_enabled(bytes[0], 2)

        """
        This bit is signalized if a situation occurred that needs special
        attention.LedHUBcontroller:one or more channels are in interlock state.
        In this situation the functionality of the LedHUB is restricted, but it
        still may be operated with the remaining wavelengths. QuixX:The bit is
        set if the laser is in pulse mode and triggered by the external digital
        input, but the externally applied frequency is far from the given set
        point. (see QuixX manual for details).
        For all other devices this bit is reserved
        """
        self.attention_required = self.__bit_enabled(bytes[0], 4)

        """
        This bit represents the state of the laser-enable/led-enable input pin
        at the control-port.Note: if the laser-enable/led-enable input is not
        connected it will stay active and the bit is set.LedHUB: the bit is
        set if “shutter” on the front panelis set to “open”
        """
        self.enabled_pin = self.__bit_enabled(bytes[0], 6)

        """
        This bit represents the state of the key-switch input pin at the
        control-port.
        """
        self.key_switch = self.__bit_enabled(bytes[0], 7)

        """
        This bit relies to laserCDRH operation only. If the bit is set,a
        key-switch toggle is needed to release laser operation.
        """
        self.toggle_key = self.__bit_enabled(bytes[1], 0)

        """
        If the bit is set,the laser/ledsystem is powered-up. This will happen
        automatically if the laser/led is in auto power-up mode (default state).
        """
        self.system_power = self.__bit_enabled(bytes[1], 1)

        """
        This bit is set, if an external light sensor is connected to the device.
        (LedHUB controller only)
        """
        self.external_sensor_connected = self.__bit_enabled(bytes[1], 5)

    def __repr__(self) -> str:
        return """{{
            "error": {},
            "on": {},
            "preheating": {},
            "attention_required": {},
            "enabled_pin": {},
            "key_switch": {},
            "toggle_key": {},
            "system_power": {},
            "external_sensor_connected": {}
        }}""".format(self.error, self.on, self.preheating,
                     self.attention_required, self.enabled_pin, self.key_switch,
                     self.toggle_key, self.system_power,
                     self.external_sensor_connected)


class Omicron_laser:
    """The central Omicron_laser"""

    def _ask(self, question: bytes) -> str:
        self._conn.write(b"?" + question + b"|\r")
        return self._conn.read_until(b'\r')[:-1].decode("Latin1")[4:].split("|")

    def _ask_bytes(self, question: bytes) -> bytes:
        self._conn.write(b"?" + question + b"|\r")
        return self._conn.read_until(b'\r')[4:-1]

    def __init__(self, conn: Serial):
        self._conn = conn

        firmware = self._ask(b"GFw")
        self.model_code = firmware[0]
        self.device_id = firmware[1]
        self.firmware_version = firmware[2]

        self.serial_number = self._ask(b"GSN")[0]

        specs = self._ask(b"GSI")
        self.wavelength = specs[0]
        self.power = specs[1]

        self.max_power = self._ask(b"GMP")

    def get_working_hours(self):
        return self._ask(b"GWH")[0]

    def measure_diode_power(self) -> float:
        return float(self._ask(b"MDP")[0])

    def measure_temperature_diode(self) -> float:
        return float(self._ask(b"MTD")[0])

    def measure_temperature_ambient(self) -> float:
        return float(self._ask(b"MTA")[0])

    def get_status(self) -> Status:
        self.status = Status(self._ask_bytes(b"MTA"))
        return self.status

    def get_failure_bytes(self) -> bytes:
        return self._ask_bytes(b"GFB")


if __name__ == "__main__":
    s = serial.serial_for_url("COM4")
    s.baudrate = 500000

    s.write(b"?GFw\r")
    print("Response:", s.read_until(b'\r'))

    laser = Omicron_laser(s)

    print("Working hours: ", laser.get_working_hours())
    print("Diode power: ", laser.measure_diode_power())
    print("Temperature diode:", laser.measure_temperature_diode())
    print("Temperature ambient:", laser.measure_temperature_ambient())
    print("Status: ", laser.get_status())
    print("Failure byte: ", laser.get_failure_bytes())
