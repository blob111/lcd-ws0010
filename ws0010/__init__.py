"""
    This module provides an interface to WS0010 based LCD
    via PCF8574 8-Bit I/O expander for I2C bus.
"""

from .ws0010 import WS0010

__version__ = "1.0.0"
__author__  = "Sergey Nikiforov"
__email__   = "yooozh@gmail.com"
__all__     = [
    'getAC',
    'dispctl_set',
    'dispctl_get',
    'emode_set',
    'emode_get',
    'gcmpwr_set',
    'gcmpwr_get',
    'clear_display',
    'ret_home',
    'initialize',
    'poweroff',
    'puts',
    'putline',
    'set_ddram_addr',
    'read_ddram',
    'move_cursor',
    'shift_display'
]

