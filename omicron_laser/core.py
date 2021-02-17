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
import logging
from enum import Enum


def bit_enabled(byte: bytes, pos: int) -> bool:
    return int(byte) & (0x01 << pos) != 0


class Status:

    def __init__(self, bytes) -> None:
        """
        This bit indicates whetherany preceded or pending error prevents the 
        devicefrom starting into normal operation. Only if this bit is unset 
        the laser/ledwill operate as expected. Please refer to the 
        “error handling” chapter for details.
        """
        self.error = bit_enabled(bytes[0], 0)

        """
        If the bit is set the laser/led is switched on and the working hours
        are counting. Note: there are some other dependencies that may prevent
        the laser/led from emitting light. Please refer to the “Best practices”
        chapter for details.
        """
        self.on = bit_enabled(bytes[0], 1)

        """
        This bit indicates if the device is actually preheating. This is a 
        temporary state. If the laser/led is already switched on, the 
        “Laser-ON”/“Led-ON” bit will be signaled beside the “preheating” bit 
        but the laser/led will not emit light during this situation. Immediately
        after the diode temperature has reached the valid range the laser/led 
        will start into operation.
        """
        self.preheating = bit_enabled(bytes[0], 2)

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
        self.attention_required = bit_enabled(bytes[0], 4)

        """
        This bit represents the state of the laser-enable/led-enable input pin 
        at the control-port.Note: if the laser-enable/led-enable input is not
        connected it will stay active and the bit is set.LedHUB: the bit is 
        set if “shutter” on the front panelis set to “open”
        """
        self.enabled_pin = bit_enabled(bytes[0], 6)

        """
        This bit represents the state of the key-switch input pin at the 
        control-port.
        """
        self.key_switch = bit_enabled(bytes[0], 7)

        """
        This bit relies to laserCDRH operation only. If the bit is set,a
        key-switch toggle is needed to release laser operation.
        """
        self.toggle_key = bit_enabled(bytes[1], 0)

        """
        If the bit is set,the laser/ledsystem is powered-up. This will happen
        automatically if the laser/led is in auto power-up mode (default state).
        """
        self.system_power = bit_enabled(bytes[1], 1)

        """
        This bit is set, if an external light sensor is connected to the device.
        (LedHUB controller only)
        """
        self.external_sensor_connected = bit_enabled(bytes[1], 5)

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


class LatchedFailure:

    def __init__(self, bytes) -> None:
        """
        This bit indicates that the laser system is in internal error state
        (safety lockout). This bit is signalized in the “Get Actual Status” 
        value (bit 0), too. 
        """
        self.error_state = bit_enabled(bytes[0], 0)

        """
        This error bit may be signaled in two situations:
        - a laser is configured as CDHR compliant but no CDRH-kit is connected 
          to the laser.
        - a laser is not configured as CDHR compliant (OEM) but a CDRH-kit is 
          connected.
        """
        self.CDRH = bit_enabled(bytes[0], 4)

        """
        A controller<->headcommunication error occurred.With PhoxX lasers this
        mostly indicates that the laserhead is not connected correctly to the
        controller or the cable is defect.Otherwise this indicates serious 
        electronic problems.
        """
        self.internal_comunication_error = bit_enabled(bytes[0], 5)

        """
        An internal error occurred(the K1 relay did not operate).This indicates 
        serious electronic problems
        """
        self.k1_relay_error = bit_enabled(bytes[0], 6)

        """
        (Possible with PhoxX lasers only) some diodes of PhoxX lasers need a
        specially signed “high power controller”.If you own high and low power 
        PhoxX lasers and do mix up the controllers this bit will indicate that
        the actual connected low power controller is not suitable to drive the 
        connected high power laser head.
        """
        self.high_power = bit_enabled(bytes[0], 7)

        """
        an under voltage or overvoltage occurred.(is still pending ifbit is set 
        in “Get Failure Byte” command)
        """
        self.under_over_voltage = bit_enabled(bytes[1], 0)

        """
        The external interlock loop was open.(it is still open if this bit is
        set in “Get Failure Byte” command)Note:if the “Auto Reset” function is 
        active this will also be signalized in the “Latched Failure”as long the
        interlock loop is still open, since the device will automatically reset
        itself after the interlock is closed again.
        """
        self.external_interlock = bit_enabled(bytes[1], 1)

        """
        The diode currentexceeded the maximum allowed value.
        """
        self.diode_current = bit_enabled(bytes[1], 2)

        """
        The ambient temperaturein the laser head exceededthe valid temperature 
        range. (still exceeds if bit is set in “Get Failure Byte” command)
        """
        self.ambient_temp = bit_enabled(bytes[1], 3)

        """
        The diode temperatureexceededthe valid temperature range.(still exceeds 
        if bit is set in “Get Failure Byte” command)
        """
        self.diode_temp = bit_enabled(bytes[1], 4)

        """
        The test error was triggered.This test error can be triggered by 
        sending “?TIS” (test interlock state).
        """
        self.test_error = bit_enabled(bytes[1], 5)

        """
        An internal error occurred. This indicates serious electronic problems.
        """
        self.internal_error = bit_enabled(bytes[1], 6)

        """
        The diode power exceeded the maximum allowed value.
        """
        self.diode_power = bit_enabled(bytes[1], 7)

    def __repr__(self) -> str:
        return """{{
            "error_state": {},
            "CDRH_error": {},
            "internal_communication_error": {},
            "k1_relay_error": {},
            "high_power": {},
            "under_over_voltage": {},
            "external_interlock": {},
            "diode_current": {},
            "ambient_temp": {},
            "diode_temp": {},
            "test_error": {},
            "internal_error": {},
            "diode_power": {}
        }}""".format(self.error_state, self.CDRH,
                     self.internal_comunication_error, self.k1_relay_error,
                     self.high_power, self.under_over_voltage,
                     self.external_interlock, self.diode_current,
                     self.ambient_temp, self.diode_temp, self.test_error,
                     self.internal_error, self.diode_power)


class OperationMode:
    def __init__(self, bytes) -> None:
        self.internal_clock_generator = bit_enabled(bytes[0], 2)
        self.bias_level_release = bit_enabled(bytes[0], 3)
        self.operating_level_release = bit_enabled(bytes[0], 4)
        self.digital_input_release = bit_enabled(bytes[0], 5)
        self.analog_input_release = bit_enabled(bytes[0], 7)

        self.APC_mode = bit_enabled(bytes[1], 0)
        self.digital_input_impedance = bit_enabled(bytes[1], 3)
        self.analog_input_impedance = bit_enabled(bytes[1], 4)
        self.usb_adhoc_mode = bit_enabled(bytes[1], 5)
        self.auto_startup = bit_enabled(bytes[1], 6)
        self.auto_powerup = bit_enabled(bytes[1], 7)

    def __repr__(self) -> str:
        return """{{ "hex": "{}", "bin": "{}", 
            "internal_clock_generator": {},
            bias_level_release {},
            "operating_level_release", {},
            "digital_input_release", {},
            "analog_input_release", {},
            "APC_mode", {},
            "digital_input_impedance", {},
            "analog_input_impedance", {},
            "usb_adhoc_mode", {},
            "auto_startup", {},
            "auto_powerup", {}
        }}""".format(hex(int(self)), bin(int(self)),
                     self.internal_clock_generator,
                     self.bias_level_release,
                     self.operating_level_release,
                     self.digital_input_release,
                     self.analog_input_release,
                     self.APC_mode,
                     self. digital_input_impedance,
                     self.analog_input_impedance,
                     self.usb_adhoc_mode,
                     self.auto_startup,
                     self.auto_powerup)

    def __int__(self) -> int:
        return self.internal_clock_generator << 2 | \
            self.bias_level_release << 3 | \
            self.operating_level_release << 4 | \
            self.digital_input_release << 5 | \
            self.analog_input_release << 7 | \
            self.APC_mode << 8 | \
            self.digital_input_impedance << 10 | \
            self.analog_input_impedance << 12 | \
            self.usb_adhoc_mode << 13 | \
            self.auto_startup << 14 | \
            self.auto_powerup << 15

    def __bytes__(self) -> bytes:
        return hex(self.__int__())[2:].encode("Latin1")


class CalibrationResult(Enum):
    SUCCESS = 0
    MAX_POWER_UNREACHABLE = 1
    KEY_SWITCH_OFF = 2
    LASER_ENABLE_INPUT_LOW = 3
    INTERLOCK_OCURRED = 4
    DIODE_TEMP_ERROR = 5
    CONTROLLER_HEAD_COMM_ERROR = 6
    BIAS_OUT_OF_RANGE = 7
    NO_BIAS_POINT = 8
    LESS_THAN_PREV_95 = 9
    LASER_SWITCHED_OFF = 10
    NO_CALIBRATION_SENSOR = 11
    NO_LIGHT_DETECTED = 12
    OVER_POWER_OCURRED = 13
    UNKNOWN_ERROR = 14


class Omicron_laser:
    """The central Omicron_laser"""

    def _ask(self, question: bytes) -> str:
        self._conn.write(b"?" + question + b"|\r")
        raw = self._conn.read_until(b'\r')
        return raw[:-1].decode("Latin1")[4:].split("|")

    def _ask_bytes(self, question: bytes) -> bytes:
        self._conn.write(b"?" + question + b"|\r")
        return self._conn.read_until(b'\r')[4:-1]

    def _set(self, what: bytes, value: bytes) -> str:
        self._conn.write(b"?" + what + value + b"|\r")
        return self._conn.read_until(b'\r')[:-1].decode("Latin1")[4:].split("|")

    def _process_adhoc(self):
        raw = self._conn.read_until(b'\r')
        while raw != b'':
            decoded = raw[:-1].decode("Latin1")
            command = decoded[:4]
            content = decoded[4:].split("|")
            if command.startswith("$TPP"):
                self.temporal_power = float(content[0])

            raw = self._conn.read_until(b'\r')

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
        self.status = Status(self._ask_bytes(b"GAS"))
        return self.status

    def get_failure_bytes(self) -> bytes:
        return self._ask_bytes(b"GFB")

    def get_latched_failure(self) -> LatchedFailure:
        self.latched_failure = LatchedFailure(self._ask_bytes(b"GLF"))
        return self.latched_failure

    def get_level_power(self):
        response = self._ask(b"GLP")[0]
        return int(response, 16)

    def set_level_power(self, value: int) -> bool:
        response = self._set(b"SLP", hex(value)[2:].encode("Latin1"))
        self._process_adhoc()
        return response == ">"

    def set_temporary_power(self, percentage: float):
        response = self._set(b"TPP", str(percentage).encode("Latin1"))
        self._process_adhoc()
        return response == ">"

    def get_temporary_power(self):
        return self._ask(b"TPP")[0]

    def get_operation_mode(self) -> OperationMode:
        self.operation_mode = OperationMode(self._ask_bytes(b"GOM"))
        return self.operation_mode

    def update_operation_mode(self):
        mode = bytes(self.operation_mode)
        print("Mode: ", mode)
        response = self._set(b"SOM", mode)[0]
        return response == '>'

    def set_auto_powerup(self, value: bool) -> bool:
        response = self._set(b"SAP", str(int(value)).encode("Latin1"))[0]
        return response == ">"

    def set_auto_startup(self, value: bool) -> bool:
        response = self._set(b"SAS", str(int(value)).encode("Latin1"))[0]
        return response == ">"

    def power_on(self) -> bool:
        response = self._ask(b"POn")[0]
        return response == ">"

    def power_off(self) -> bool:
        response = self._ask(b"POf")[0]
        return response == ">"

    def laser_on(self) -> bool:
        response = self._ask(b"LOn")[0]
        return response == ">"

    def laser_off(self) -> bool:
        response = self._ask(b"LOf")[0]
        return response == ">"

    def reset(self) -> bool:
        self._conn.write(b"?RsC\r")
        response = self._conn.read_until(b'\r')
        recv = response == b"!RsC\r"
        logging.info("Reset command received. Laser reponse: {}".format(recv))

        if recv:
            response = self._conn.read_until(b'\r')
            while response != b'\x00$RsC>\r':
                response += self._conn.read_until(b'\r')
                logging.info(
                    "Reset in course, Laser response: {}".format(response))
            return True

        return False

    def set_auto_reset(self, value) -> bool:
        """
        Auto reset will not work for class 4 lasers or if a laser system is in 
        CDRH mode.
        """
        response = self._set(b"ARs", str(int(value)).encode("Latin1"))[0]
        return response == ">"

    def calibrate_laser_diode(self) -> CalibrationResult:
        response = self._set(b"CLD", b'')[0]
        if response == ">":
            logging.info("Laser calibration initiated")
            response = self._conn.read_until(b'\r')
            logging.info("Laser GCI: {}".format(response))

            response = self._conn.read_until(b'\r')
            while b"$CLD" not in response:
                response += self._conn.read_until(b'\r')
                print(response)
                logging.info("Laser calibration in course.")

            return CalibrationResult(int(response[4:-1]))

        return CalibrationResult.UNKNOWN_ERROR


if __name__ == "__main__":
    from time import sleep
    logging.basicConfig(level=logging.INFO)

    s = serial.serial_for_url("COM4")
    s.baudrate = 500000
    s.timeout = 0.1

    s.write(b"?GFw\r")
    print("Response:", s.read_until(b'\r'))

    laser = Omicron_laser(s)

    print("Working hours: ", laser.get_working_hours())
    print("Diode power: ", laser.measure_diode_power())
    print("Temperature diode:", laser.measure_temperature_diode())
    print("Temperature ambient:", laser.measure_temperature_ambient())
    print("Status: ", laser.get_status())
    print("Failure byte: ", laser.get_failure_bytes())
    print("Latched Failure: ", laser.get_latched_failure())
    print("Level power: ", laser.get_level_power()/0xFFF)

    print("Set Level power to 0xFF0", laser.set_level_power(0xFF0))
    print("Level power: ", laser.get_level_power()/0xFFF)

    print("Temporary power: ", laser.get_temporary_power())
    print("Set temporal power", laser.set_temporary_power(0.56))
    print("Temporary power: ", laser.get_temporary_power())

    op_mode = laser.get_operation_mode()
    print("Laser operation mode:", op_mode)

    laser.operation_mode.usb_adhoc_mode = False
    response = laser.update_operation_mode()

    print("Laser set auto power-up:", laser.set_auto_powerup(True))
    print("Laser set auto start-up:", laser.set_auto_startup(True))

    print("Power on:", laser.power_on())
    print("Laser on:", laser.laser_on())

    print("Laser off:", laser.laser_off())
    print("Power off:", laser.power_off())

    print("Laser set auto reset:", laser.set_auto_reset(True))

    print("Laser calibration:", laser.calibrate_laser_diode().name)

    # laser.reset()
