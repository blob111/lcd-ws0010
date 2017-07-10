#! /usr/bin/python3

import i2cdev
from time import sleep

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
PMASK_LINES             = [0x00, 0x08]  # Parameter: two lines (1) or one line (0) display
PMASK_FT_ENJP           = 0x00  # Parameter: character font set:    english-japanese (0,0)
PMASK_FT_WE1            = 0x01  #                                   western europe I (0,1)
PMASK_FT_ENRU           = 0x02  #                                   english-russian (1,0)
PMASK_FT_WE2            = 0x03  #                                   western europe II (1,1)

IMASK_CGRAM_ADDR        = 0x40  # Instruction: Set CGRAM Address

IMASK_DDRAM_ADDR        = 0x80  # Instruction: Set DDRAM Address

# ===========================================================================
# Constants
# ===========================================================================

WAIT_BF         = .0001 # wait time between consequtive checking of BF
WAIT_SLOW       = .01  # wait time between instructions
MAX_LINES       = 2     # maximum lines number
DDRAM_ADDR      = [0x0, 0x40]   # DDRAM addresses per line

# ===========================================================================
# Translation table for russian letters
# ===========================================================================

TRANSLATE_RU = {
    'А': 0x41, 'Б': 0xA0, 'В': 0x42, 'Г': 0xA1, 'Д': 0xE0, 'Е': 0x45, 'Ж': 0xA3, 'З': 0xA4,
    'И': 0xA5, 'Й': 0xA6, 'К': 0x4B, 'Л': 0xA7, 'М': 0x4D, 'Н': 0x48, 'О': 0x4F, 'П': 0xA8,
    'Р': 0x50, 'С': 0x43, 'Т': 0x54, 'У': 0xA9, 'Ф': 0xAA, 'Х': 0x58, 'Ц': 0xE1, 'Ч': 0xAB,
    'Ш': 0xAC, 'Щ': 0xE2, 'Ъ': 0xAD, 'Ы': 0xAE, 'Ь': 0x62, 'Э': 0xAF, 'Ю': 0xB0, 'Я': 0xB1,
    'Ё': 0xA2, 'ё': 0xB5,
    'а': 0x61, 'б': 0xB2, 'в': 0xB3, 'г': 0xB4, 'д': 0xE3, 'е': 0x65, 'ж': 0xB6, 'з': 0xB7,
    'и': 0xB8, 'й': 0xB9, 'к': 0xBA, 'л': 0xBB, 'м': 0xBC, 'н': 0xBD, 'о': 0x6F, 'п': 0xBE,
    'р': 0x70, 'с': 0x63, 'т': 0xBF, 'у': 0x79, 'ф': 0xE4, 'х': 0x78, 'ц': 0xE5, 'ч': 0xC0,
    'ш': 0xC1, 'щ': 0xE6, 'ъ': 0xC2, 'ы': 0xC3, 'ь': 0xC4, 'э': 0xC5, 'ю': 0xC6, 'я': 0xC7 }

# ===========================================================================
# LCD Winstar WS0010 Class
# ===========================================================================

class LCD_WS0010:

    ## Constructor
    def __init__(self, address, bus, lines=2):
        self._address = address
        self._bus = bus
        self._device = i2cdev.i2cdev(address, bus)
        if lines > MAX_LINES:
            lines = MAX_LINES
        self._lines = lines
        self.initialize()

    def latch(self, b):
        """Latch command with EN input."""
        sleep(WAIT_SLOW)
        self._device.write8(b | PIN_EN)
        sleep(WAIT_SLOW)
        self._device.write8(b)

    def sendI(self, b):
        """Send instruction byte."""

        self.send4(b >> 4)
        self.send4(b)
        self.checkBF()

    def sendD(self, b):
        """Send data byte."""

        self.send4(b >> 4, True)
        self.send4(b, True)
        self.checkBF()

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
            bfac = (self._device.read8() & 0xF) << 4
            self._device.write8(PIN_RW)

            # Read low nibble of BFAC byte to t3
            self._device.write8(PIN_RW | PIN_EN)
            bfac |= self._device.read8() & 0xF
            self._device.write8(PIN_RW)

            # Check BF
            if bfac & RMASK_BF:
                sleep(WAIT_BF)
            else:
                break

        # Clear R/W bit
        self._device.write8(0)

        # Return AC
        return bfac

    def initialize(self):
        """Initialize controller for necessary mode (currently 4-bit mode only)."""

        # Synchronization sequence for 4-bit mode
        self.send4(0)
        self.send4(0)
        self.send4(0)
        self.send4(0)
        self.send4(0)
        sleep(WAIT_SLOW)

        # Function Set: 4bit mode, necessary lines number, en-ru font table
        self.send4(IMASK_FUNC >> 4)
        sleep(WAIT_SLOW)
        self.sendI(IMASK_FUNC | PMASK_LINES[self._lines - 1] | PMASK_FT_ENRU)
        sleep(WAIT_SLOW)

        # Display ON/OFF Control: turn on display, cursor and blinking
        self.sendI(IMASK_DISP_CTRL | PMASK_DISP_ON | PMASK_CURS_ON | PMASK_BLINK_ON)
        sleep(WAIT_SLOW)

        # Clear Display and Return Home
        self.sendI(IMASK_CLR_DISP)
        sleep(WAIT_SLOW)
        self.sendI(IMASK_RET_HOME)
        sleep(WAIT_SLOW)

        # Entry Mode Set: increment address, no shift
        self.sendI(IMASK_ENTRY_MODE | PMASK_INC)
        sleep(WAIT_SLOW)

    def puts(self, string, line, clear=True, rethome=True):
        """Output a 'string' to specified 'line' of screen.
        Clears screen if 'clear' is True. Return cursor to beginning if 'rethome' is True."""

        if clear:
            self.sendI(IMASK_CLR_DISP)
        if rethome:
            self.sendI(IMASK_RET_HOME)

        # Circle line number (take line_number modulo line_numbers) and get DDRAM address
        line = (line - 1) % 2 + 1
        addr = DDRAM_ADDR[line - 1]
        self.sendI(IMASK_DDRAM_ADDR | addr)
        sleep(WAIT_SLOW)

        # Output string
        for char in string:
            try:
                symbol = TRANSLATE_RU[char]
            except KeyError:
                symbol = ord(char) & 0xFF
            self.sendD(symbol)
            sleep(WAIT_SLOW)
