#! /usr/bin/python3
#
# 1st line: date[DD.MM.YYYY] time[HH:MM]
# 2nd line: id[IIII] err[EE%] temp[+NN.N]

import sys
import select
import signal
import fcntl
from math import gcd
import ws0010
from w1thermsensor import W1ThermSensor


I2C_ADDRESS = 0x39
I2C_BUS = 0

W1_BUS_DIR = '/sys/bus/w1/'
W1_DEVS_DIR = W1_BUS_DIR + 'devices/'
W1_MASTER_DIR = W1_DEVS_DIR + 'w1_bus_master1/'
W1_SLAVES_FILE = W1_MASTER_DIR + 'w1_master_slaves'
W1_THERM_SCALE_FACTOR = lambda x: x * 0.001
W1_THERM_SENSOR_NAN = 85000

SENSOR_READ_INTERVAL = 60
SENSOR_DISP_INTERVAL = 10
CLOCK_INTERVAL = 5

def disp_init():
    """Initialize display."""

    lcd = ws0010.WS0010(I2C_ADDRESS, I2C_BUS)
    lcd.emode_set(increment=True)
    lcd.dispctl_set(disp_on=True, curs_on=True, blink_on=True)
    return lcd

def read_sensor(sensor):
    """Save sensor's value."""

    val = int(sensor['obj'].raw_sensor_value)
    if val == W1_THERM_SENSOR_NAN:
        sensor['read_nan'] += 1
    else:
        sensor['obj'].value = W1_THERM_SCALE_FACTOR(val)
        sensor['read_success'] += 1

def main():
    """Main program."""

    sensors = []
    itimer_factor = {}
    itimer_current = {}

    # Initialize sensors
    for sensor in W1ThermSensor.get_available_sensors():
        sensors.add({obj=sensor, read_success=0, read_crc=0, read_nan=0, value=None})
    if len(sensors) == 0:
        sys.stderr.write('\nNo sensors found\n')
        exit(0)

    # Calculate interval timer value and bounded variables
    itimer_value = gcd(gcd(SENSOR_READ_INTERVAL, SENSOR_DISP_INTERVAL), CLOCK_INTERVAL)
    itimer_factor['sensor_read_interval'] = int(SENSOR_READ_INTERVAL / itimer_value)
    itimer_current['sensor_read_interval'] = itimer_factor['sensor_read_interval']
    itimer_factor['sensor_disp_interval'] = int(SENSOR_DISP_INTERVAL / itimer_value)
    itimer_current['sensor_disp_interval'] = itimer_factor['sensor_disp_interval']
    itimer_factor['clock_interval'] = int(CLOCK_INTERVAL / itimer_value)
    itimer_current['clock_interval'] = itimer_factor['clock_interval']

    # Initialize signal file descriptor
    # We must set write end of pipe to non blocking mode
    # Also we don't want to block while read signal numbers from read end
    pipe_r, pipe_w = os.pipe()
    flags = fcntl.fcntl(pipe_w, fcntl.F_GETFL, 0)
    fcntl.fcntl(pipe_w, fcntl.F_SETFL, flags | os.O_NONBLOCK)
    signal.set_wakeup_fd(pipe_w)
    flags = fcntl.fcntl(pipe_r, fcntl.F_GETFL, 0)
    fcntl.fcntl(pipe_r, fcntl.F_SETFL, flags | os.O_NONBLOCK)

