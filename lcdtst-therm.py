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

SIG_WAKEUP_FD_RLEN = 8  # length of data read from signal wakeup file descriptor

cleanup_objects = {
    'poller': None,
    'pipe_r': None,
    'pipe_w': None,
}

def disp_init():
    """Initialize display."""

    lcd = ws0010.WS0010(I2C_ADDRESS, I2C_BUS)
    lcd.emode_set(increment=True)
    lcd.dispctl_set(disp_on=True, curs_on=True, blink_on=True)
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

def cleanup():
    """Cleanup routine."""

    sys.stderr.write('INFO: Clean-up\n')
    signal.setitimer(signal.ITIMER_REAL, 0)
    if cleanup_objects['poller']:
        cleanup_objects['poller'].close()
    if cleanup_objects['pipe_r']:
        os.close(cleanup_objects['pipe_r'])
    if cleanup_objects['pipe_w']:
        os.close(cleanup_objects['pipe_w'])

def main():
    """Main program."""

    sensors = []
    itimer_next = {}

    # Initialize sensors
    for sensor in W1ThermSensor.get_available_sensors():
        sensors.append({'obj': sensor, 'read_success': 0, 'read_crc': 0, 'read_nan': 0, 'value': None})
    if len(sensors) == 0:
        sys.stderr.write('\nERROR: No sensors found\n')
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
    signal.signal(signal.SIGALRM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGHUP, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Calculate interval timer value and bounded variables
    itimer_value = gcd(gcd(SENSOR_READ_INTERVAL, SENSOR_DISP_INTERVAL), CLOCK_INTERVAL)
    t = time.time()
    itimer_next['sensor_read_interval'] = t + SENSOR_READ_INTERVAL
    itimer_next['sensor_disp_interval'] = t + SENSOR_DISP_INTERVAL
    itimer_next['clock_interval'] = t + CLOCK_INTERVAL

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

    # Main loop
    sys.stderr.write('INFO: Entering main loop\n')
    while True:
    
        # Wait for events and process its
        try:
            events = poller.poll()
        except InterruptedError:
            continue
        for fd, flags in events:
    
            # Signal received, extract signal numbers from wakeup fd
            if fd == pipe_r and flags & select.EPOLLIN:
                data = os.read(pipe_r, SIG_WAKEUP_FD_RLEN)
                signums = struct.unpack('{}B'.format(len(data)), data)

                # Process signals
                for signum in signums:
                    if signum == signal.SIGALRM:

                        # Display clock
                        if t >= itimer_next['clock_interval'] <= time.time():
                            disp_clock(lcd)
                            while itimer_next['clock_interval'] <= time.time():
                                itimer_next['clock_interval'] += CLOCK_INTERVAL

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
                        sys.stderr.write('\nINFO: SIGINT received\n')
                        cleanup()
                        sys.exit(0)
                    elif signum == signal.SIGTERM:
                        sys.stderr.write('\nINFO: SIGTERM received\n')
                        cleanup()
                        sys.exit(0)
                    elif signum == signal.SIGHUP:
                        sys.stderr.write('INFO: SIGHUP received\n')
                    else:
                        sys.stderr.write('WARNING: Unexpected signal received: {}\n'.format(signum))

            # Unexpected event
            else:
                sys.stderr.write('ERROR: Unexpected event on fd {}, flags {}\n'.format(fd, flags))

# Call main routine
main()

# This point should be never reached
# Cleanup and exit
cleanup()
sys.exit(0)
