#! /usr/bin/python3
#
# 1st line: date[DD.MM.YYYY] time[HH:MM]
# 2nd line: id[IIII] err[EE%] temp[+NN.N]

import sys
import ws0010

I2C_ADDRESS = 0x39
I2C_BUS = 0

W1_BUS_DIR = '/sys/bus/w1/'
W1_DEVS_DIR = W1_BUS_DIR + 'devices/'
W1_MASTER_DIR = W1_DEVS_DIR + 'w1_bus_master1/'
W1_SLAVES_FILE = W1_MASTER_DIR + 'w1_master_slaves'

M_INTERVAL = 60
DISP_INTERVAL = 5

def disp_init():
    """Initialize display."""
    
    lcd = ws0010.WS0010(I2C_ADDRESS, I2C_BUS)
    lcd.emode_set(increment=True)
    lcd.dispctl_set(disp_on=True, curs_on=True, blink_on=True)
    return lcd

def read_temp():
    """Read all 1W temperature sensors."""
    
    
