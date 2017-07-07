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

RMASK_BF                = 0x80  # Busy Flag

IMASK_CLR_DISP          = 0x01  # Instruction: Clear Display

IMASK_RET_HOME          = 0x02  # Instruction: Return Home

IMASK_ENTRY_MODE        = 0x04  # Instruction: Entry Mode
PMASK_INC               = 0x02  # Parameter: I/D, address increment (1) or decrement (0)
PMASK_DISP_SHIFT_EN     = 0x01  # Parameter: S, display shift enable (1) or disable (0)

IMASK_DISP_CTRL         = 0x08  # Instruction: Display ON/OFF Control
PMASK_DISP_ON           = 0x04  # Parameter: D, display on (1) or off (0)
PMASK_CURS_ON           = 0x02  # Parameter: C, cursor on (1) or off (0)
PMASK_BLINK_ON          = 0x01  # Parameter: B, blinking on (1) or off (0)

IMASK_CURS_DISP_SHIFT   = 0x10  # Instruction: Cursor/Display Shift
PMASK_DISP_SHIFT_ON     = 0x08  # Parameter: display shift (1) or cursor move (0)
PMASK_SHIFT_MOVE_RIGHT  = 0x04  # Parameter: shift/move right (1) or left (0)

IMASK_GCMODE_PWR        = 0x13  # Instruction: Graphics/Character Mode and Power ON/OFF Control
IMASK_GRAPHICS_MODE     = 0x08  # Parameter: graphics (1) or character (0) mode
IMASK_PWR_ON            = 0x04  # Parameter: internal power on (1) or off (0)

IMASK_FUNC              = 0x20  # Instruction: Function Set
PMASK_8BIT_MODE         = 0x10  # Parameter: data length operation 8bit (1) or 4bit (0)
PMASK_2LINES            = 0x08  # Parameter: two lines (1) or one line (0) display
PMASK_FT_ENJP           = 0x00  # Parameter: character font set:    english-japanese (0,0)
PMASK_FT_WE1            = 0x01  #                                   western europe I (0,1)
PMASK_FT_ENRU           = 0x02  #                                   english-russian (1,0)
PMASK_FT_WE2            = 0x03  #                                   western europe II (1,1)

IMASK_CGRAM_ADDR        = 0x40  # Instruction: Set CGRAM Address

IMASK_DGRAM_ADDR        = 0x80  # Instruction: Set DGRAM Address

# ===========================================================================
# Constants
# ===========================================================================

WAIT_BF     = .0001

# ===========================================================================
# LCD Winstar WS0010 Class
# ===========================================================================

class LCD_WS0010:

    ## Constructor
    def __init__(self, address, bus):
        self._address = address
        self._bus = bus
        self._device = i2cdev.i2cdev(address, bus)

        self.init()

    def latch(self, b):
        """Latch command with EN input."""
        self._device.write8(b | PIN_EN)
        self._device.write8(b)

    def sendI(self, b):
        """Send instruction byte."""

        self.send4(b >> 4)
        self.send4(b)

    def sendD(self, b):
        """Send data byte."""

        self.send4(b >> 4, True)
        self.send4(b, True)

    def send4(self, b, rs=False):
        """Send low nibble of byte.
        Parameter 'rs' selects what 'b' contains: instruction (False) or data (True)"""

        b &= 0xF
        if rs:
            b |= PIN_RS
        self._device.write8(b)
        self.latch(b)

    def checkBF(self):
        """Check BF (Busy Flag) and wait for BF will cleared.
        Return AC (Address Counter)."""

        while True:

            # Read high nibble of BFAC byte
            self._device.write8(PIN_RW | PIN_EN)
            bfac = self._device.read8() << 4
            self._device.write8(PIN_RW)

            # Read low nibble of BFAC byte to t3
            self._device.write8(PIN_RW | PIN_EN)
            bfac |= self._device.read8() & 0xF
            self._device.write8(PIN_RW)

            # Check BF
            if bfac & RMASK_BF:
                time.sleep(WAIT_BF)
            else:
                break

        # Clear R/W bit
        self._device.write8(0)

        # Return AC
        return bfac

    def init(self):
        """Initialize controller for necessary mode (currently 4-bit mode only)."""

        # Synchronization sequence for 4-bit mode
        self.send4(0)
        self.send4(0)
        self.send4(0)
        self.send4(0)
        self.send4(0)

        # Function set
        self.send4(IMASK_FUNC >> 4)
        self.sendI(IMASK_FUNC | PMASK_2LINES | PMASK_FT_ENRU)
        self.checkBF()
