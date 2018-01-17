#! /usr/bin/python3
#
# 1st line: date[DD.MM.YYYY] time[HH:MM]
# 2nd line: id[IIII] err[EE%] temp[+NN.N]

import os
import sys
import select
import signal
import fcntl
import time
import struct
from fractions import gcd
from w1thermsensor import W1ThermSensor
from debug import Debug
from ws0010 import WS0010

DEBUG_LVL = 1   # Debug level (0 - no debug)

LCD_I2C_ADDRESS = 0x39  # LCD address on I2C bus
LCD_I2C_BUS = 0         # I2C bus number

W1_BUS_DIR = '/sys/bus/w1/'                         # base directory of 1-wire bus in device tree
W1_DEVS_DIR = W1_BUS_DIR + 'devices/'               # devices directory
W1_MASTER_DIR = W1_DEVS_DIR + 'w1_bus_master1/'     # directory of 1-wire bus master
W1_SLAVES_FILE = W1_MASTER_DIR + 'w1_master_slaves' # the file contains number of detected slave devices on 1-wire bus
W1_THERM_SCALE_FACTOR = lambda x: x * 0.001         # scale function to convert raw sensor value in Celsius
W1_THERM_SENSOR_NAN = 85000                         # this sensor value means faulty reading

SENSOR_READ_INTERVAL = 60   # interval between sensor reads, in seconds
SENSOR_DISP_INTERVAL = 10   # interval between display of sensors
CLOCK_DISP_INTERVAL = 5          # interval between display of clock

SIG_WAKEUP_FD_RLEN = 8  # length of data read from signal wakeup file descriptor

cleanup_objects = {
    'debug': None,
    'pipe_r': None,
    'pipe_w': None,
    'sigalrm': None,
    'sigint': None,
    'sighup': None,
    'sigterm': None,
    'poller': None,
    'itimer': False
}

def cleanup():
    """Cleanup routine."""

    sys.stderr.write('INFO: Clean-up\n')
    if cleanup_objects['itimer']:
        signal.setitimer(signal.ITIMER_REAL, 0)
        cleanup_objects['itimer'] = False
    if cleanup_objects['poller']:
        cleanup_objects['poller'].close()
        cleanup_objects['poller'] = None
    if cleanup_objects['sigalrm']:
        signal.signal(signal.SIGALRM, cleanup_objects['sigalrm'])
        cleanup_objects['sigalrm'] = None
    if cleanup_objects['sigint']:
        signal.signal(signal.SIGINT, cleanup_objects['sigint'])
        cleanup_objects['sigint'] = None
    if cleanup_objects['sighup']:
        signal.signal(signal.SIGHUP, cleanup_objects['sighup'])
        cleanup_objects['sighup'] = None
    if cleanup_objects['sigterm']:
        signal.signal(signal.SIGTERM, cleanup_objects['sigterm'])
        cleanup_objects['sigterm'] = None
    if cleanup_objects['pipe_r']:
        os.close(cleanup_objects['pipe_r'])
        cleanup_objects['pipe_r'] = None
    if cleanup_objects['pipe_w']:
        os.close(cleanup_objects['pipe_w'])
        cleanup_objects['pipe_w'] = None
    if cleanup_objects['debug']:
        cleanup_objects['debug'].close()
        cleanup_objects['debug'] = None

def disp_init():
    """Initialize display."""

    lcd = WS0010(LCD_I2C_ADDRESS, LCD_I2C_BUS)
    lcd.emode_set(increment=True)
    lcd.dispctl_set(disp_on=True, curs_on=True, blink_on=True)
    lcd.gcmpwr_set(intpwr=False)
    return lcd

def disp_clock(lcd):
    """Display clock."""

    return

def disp_sensor(lcd, sensor):
    """Display sensor value."""

    return

def read_sensor(sensor):
    """Save sensor's value."""

    val = int(sensor['obj'].raw_sensor_value)
    if val == W1_THERM_SENSOR_NAN:
        sensor['read_nan'] += 1
    else:
        sensor['obj'].value = W1_THERM_SCALE_FACTOR(val)
        sensor['read_success'] += 1

def signal_handler(signal, frame):
    """Signal handler."""

    return

def main():
    """Main program."""

    sensors = []
    itimer_next = {}

    # Initialize debugging
    dbg = Debug(level=DEBUG_LVL)
    cleanup_objects['debug'] = dbg

    # Initialize sensors
    for sensor in W1ThermSensor.get_available_sensors():
        sensors.append({'obj': sensor, 'read_success': 0, 'read_crc': 0, 'read_nan': 0, 'value': None})
    if len(sensors) == 0:
        sys.stderr.write('\nERROR: No sensors found\n')
        cleanup()
        exit(0)
    else:
        sys.stderr.write('\nINFO: Found {} sensors\n'.format(len(sensors)))
        active_sensor_idx = 0

    # Initialize LCD
    lcd = disp_init()

    # Initialize signal file descriptor
    # We must set write end of pipe to non blocking mode
    # Also we don't want to block while read signal numbers from read end
    pipe_r, pipe_w = os.pipe()
    cleanup_objects['pipe_r'] = pipe_r
    cleanup_objects['pipe_w'] = pipe_w
    flags = fcntl.fcntl(pipe_w, fcntl.F_GETFL, 0)
    fcntl.fcntl(pipe_w, fcntl.F_SETFL, flags | os.O_NONBLOCK)
    signal.set_wakeup_fd(pipe_w)
    flags = fcntl.fcntl(pipe_r, fcntl.F_GETFL, 0)
    fcntl.fcntl(pipe_r, fcntl.F_SETFL, flags | os.O_NONBLOCK)

    # Redefine signal handlers
    cleanup_objects['sigalrm'] = signal.signal(signal.SIGALRM, signal_handler)
    cleanup_objects['sigint'] = signal.signal(signal.SIGINT, signal_handler)
    cleanup_objects['sighup'] = signal.signal(signal.SIGHUP, signal_handler)
    cleanup_objects['sigterm'] = signal.signal(signal.SIGTERM, signal_handler)

    # Calculate interval timer value and bounded variables
    itimer_value = gcd(gcd(SENSOR_READ_INTERVAL, SENSOR_DISP_INTERVAL), CLOCK_DISP_INTERVAL)
    dbg.dbg('Calculated itimer value is {} seconds'.format(itimer_value))
    t = time.time()
    dbg.dbg('  Base time is {}'.format(t))
    itimer_next['sensor_read_interval'] = t + SENSOR_READ_INTERVAL
    dbg.dbg('  Wake up time for SENSOR_READ set to {}'.format(itimer_next['sensor_read_interval']))
    itimer_next['sensor_disp_interval'] = t + SENSOR_DISP_INTERVAL
    dbg.dbg('  Wake up time for SENSOR_DISP set to {}'.format(itimer_next['sensor_disp_interval']))
    itimer_next['clock_disp_interval'] = t + CLOCK_DISP_INTERVAL
    dbg.dbg('  Wake up time for CLOCK_DISP set to {}'.format(itimer_next['clock_disp_interval']))

    # Create poller and register file descriptors
    poller = select.epoll()
    cleanup_objects['poller'] = poller
    poller.register(pipe_r, select.EPOLLIN)

    # Set interval timer
    # Initial value of timer bounded to measurement itimer_value
    t = time.time()
    t_rest = itimer_value - t % itimer_value
    if t_rest < 0:
        t_rest += itimer_value
    signal.setitimer(signal.ITIMER_REAL, t_rest, itimer_value)
    cleanup_objects['itimer'] = True
    dbg.dbg('ITIMER_REAL will fire at {} and each {} seconds'.format(t + t_rest, itimer_value))

    # Main loop
    sys.stderr.write('INFO: Entering main loop\n')
    while True:

        # Wait for events and process its
        try:
            events = poller.poll()
        except InterruptedError:
            continue
        for fd, flags in events:
            dbg.dbg('Start processing event, fd={}, flags={}'.format(fd, flags))

            # Signal received, extract signal numbers from wakeup fd
            if fd == pipe_r and flags & select.EPOLLIN:
                dbg.dbg('Signal received from wakeup fd, unpacking signal numbers')
                data = os.read(pipe_r, SIG_WAKEUP_FD_RLEN)
                signums = struct.unpack('{}B'.format(len(data)), data)
                dbg.dbg('Signal numbers unpacked: {}'.format(signums))

                # Process signals
                for signum in signums:
                    if signum == signal.SIGALRM:
                        dbg.dbg('Got SIGALRM, dispatch itimer based tasks')

                        # Display clock
                        if t >= itimer_next['clock_disp_interval'] <= time.time():
                            disp_clock(lcd)
                            while itimer_next['clock_disp_interval'] <= time.time():
                                itimer_next['clock_disp_interval'] += CLOCK_DISP_INTERVAL

                        # Display sensor
                        if t >= itimer_next['sensor_disp_interval']:
                            disp_sensor(lcd, sensors[active_sensor_idx])
                            active_sensor_idx += 1
                            if active_sensor_idx >= len(sensors):
                                active_sensor_idx = 0
                            while itimer_next['sensor_disp_interval'] <= time.time():
                                itimer_next['sensor_disp_interval'] += SENSOR_DISP_INTERVAL

                        # Read sensors
                        if t >= itimer_next['sensor_read_interval']:
                            for sensor in sensors:
                                read_sensor(sensor)
                            while itimer_next['sensor_read_interval'] <= time.time():
                                itimer_next['sensor_read_interval'] += SENSOR_READ_INTERVAL

                    elif signum == signal.SIGINT:
                        dbg.dbg('Got SIGINT, terminating')
                        sys.stderr.write('\nINFO: SIGINT received\n')
                        cleanup()
                        sys.exit(0)
                    elif signum == signal.SIGTERM:
                        dbg.dbg('Got SIGTERM, terminating')
                        sys.stderr.write('\nINFO: SIGTERM received\n')
                        cleanup()
                        sys.exit(0)
                    elif signum == signal.SIGHUP:
                        dbg.dbg('Got SIGHUP, ignoring')
                        sys.stderr.write('INFO: SIGHUP received\n')
                    else:
                        dbg.dbg('Got uncaught signal {}, ignoring'.format(signum))
                        sys.stderr.write('WARNING: Unexpected signal received: {}\n'.format(signum))

            # Unexpected event
            else:
                dbg.dbg('Unexpected event on fd {}, flags {}'.format(fd, flags))
                sys.stderr.write('ERROR: Unexpected event on fd {}, flags {}\n'.format(fd, flags))

# Call main routine
main()

# This point should be never reached
# Cleanup and exit
cleanup()
sys.exit(0)
