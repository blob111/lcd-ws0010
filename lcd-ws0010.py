#! /usr/bin/python3

import i2cdev.py
import time

# ===========================================================================
# Control pins numbering
# ===========================================================================

PIN_RS      = 0x10
PIN_RW      = 0x20
PIN_EN      = 0x40

# ===========================================================================
# Masks
# ===========================================================================

MASK_BF     = 0x80
MASK_AC     = 0x7F

# ===========================================================================
# Constants
# ===========================================================================

WAIT_BF     = .001

# ===========================================================================
# LCD Winstar WS0010 Class
# ===========================================================================

class LCD_WS0010:
    
    ## Constructor
    def __init__(self, address, bus):
        self._address = address
        self._bus = bus
        self._device = i2cdev.i2cdev(address, bus)
        
        self.initialize()
        
    def initialize(self):
        """Initialize controller for necessary mode (currently 4-bit mode only)."""
        
    def kick(self, b):
        """Latch command with EN input."""
        b |= PIN_EN
        self._device.write8(b)
        b &= ~PIN_EN & 0xff
        self._device.write8(b)
        
    def cmd(self, c):
        """Send instruction to LCD."""
        
        # Write high nibble of command byte
        t = c & 0xFF
        t >>= 4
        self._device.write8(t)
        self.kick(t)
        
        # Write low nibble of command byte
        t = c & 0xF
        self._device.write8(t)
        self.kick(t)
        
    def readBFAC(self):
        """Read BF (Busy Flag) and AC (Address Counter)."""
        
        # Read high nibble of BFAC byte
        t1 = 0
        t1 |= PIN_RW
        self._device.write8(t1)
        t1 |= PIN_EN
        self._device.write8(t1)
        t2 = self._device.read8()
        t1 &= ~PIN_EN & 0xff
        self._device.write8(t1)
        
        # Read low nibble of BFAC byte
        t1 |= PIN_EN
        self._device.write8(t1)
        t3 = self._device.read8()
        t1 &= ~PIN_EN & 0xff
        self._device.write8(t1)
        
        # Clear R/W bit
        t1 &= ~PIN_RW & 0xff
        self._device.write8(t1)
        
        # Return result
        t2 <<= 4
        t2 |= t3 & 0xF
        return t2
        
    def checkBF(self):
        """Check BF (Busy Flag)."""
        
        while True:
            bf = self.readBFAC()
            if bf & MASK_BF:
                time.sleep(WAIT_BF)
            else:
                break
                
