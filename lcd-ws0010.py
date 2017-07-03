#! /usr/bin/python3

import i2cdev.py

# ===========================================================================
# LCD Winstar WS0010 Class
# ===========================================================================

class LCD_WS0010:
    
    ## Constructor
    def __init__(self, address, bus):
        self._device = i2cdev.i2cdev(address, bus)
        
        self.initialize()
        
    def initialize(self):
        """Initialize controller for necessary mode (currently 4-bit mode only)."""
        
    def strobe(self):
        """Latch command with EN input."""
        
