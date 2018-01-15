#! /usr/bin/python3
#
# 1st line: date[DD.MM.YYYY] time[HH:MM]
# 2nd line: id[IIII] err[EE%] temp[+NN.N]

import sys
import ws0010
from w1thermsensor import W1ThermSensor


I2C_ADDRESS = 0x39
I2C_BUS = 0

W1_BUS_DIR = '/sys/bus/w1/'
W1_DEVS_DIR = W1_BUS_DIR + 'devices/'
W1_MASTER_DIR = W1_DEVS_DIR + 'w1_bus_master1/'
W1_SLAVES_FILE = W1_MASTER_DIR + 'w1_master_slaves'

W1_THERM_SENSOR_NAN = 85000

M_INTERVAL = 60
DISP_INTERVAL = 5

class MyTempSensor(W1ThermSensor):
    """
    My own class for 1-wire temperature sensors.
    Based on <https://github.com/timofurrer/w1thermsensor> project.
    """

    _read_success = 0
    _read_crc = 0
    _read_nan = 0
    _prev = None
    _nosense = False

    def get_temperature(self, unit=DEGREES_C):
        """
        Returns the temperature in the specified unit
        """

        try:
            tmp = W1ThermSensor.raw_sensor_value(self, unit)
        except SensorNotReadyError:
            self._read_crc += 1
        else:
            if int(tmp) == W1_THERM_SENSOR_NAN:
                self._read_nan += 1
            else:
                self._read_success += 1
                self._prev = tmp

        return self._prev

def disp_init():
    """Initialize display."""

    lcd = ws0010.WS0010(I2C_ADDRESS, I2C_BUS)
    lcd.emode_set(increment=True)
    lcd.dispctl_set(disp_on=True, curs_on=True, blink_on=True)
    return lcd

def read_temp():
    """Read all 1W temperature sensors."""


    for sensor in MyTempSensor.get_available_sensors():
