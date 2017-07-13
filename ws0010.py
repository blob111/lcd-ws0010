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

IMASK_DISP_CTL          = 0x08  # Instruction: Display ON/OFF Control
PMASK_DISP_ON           = 0x04  # Parameter: D, display on (1) or off (0)
PMASK_CURS_ON           = 0x02  # Parameter: C, cursor on (1) or off (0)
PMASK_BLINK_ON          = 0x01  # Parameter: B, blinking on (1) or off (0)

IMASK_CURS_DISP_SHIFT   = 0x10  # Instruction: Cursor/Display Shift
PMASK_DISP_SHIFT        = 0x08  # Parameter: display shift (1) or cursor move (0)
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

IMASK_CGRAM_ADDR        = 0x40  # Instruction: Set CGRAM (Character Generator RAM) Address

IMASK_DDRAM_ADDR        = 0x80  # Instruction: Set DDRAM (Display Data RAM) Address

# ===========================================================================
# Constants
# ===========================================================================

WAIT_BF         = .001  # wait time between consequtive checking of BF
WAIT_SLOW       = .0001 # wait time between instructions
MAX_LINES       = 2     # maximum lines number
DDRAM_ADDR      = [0x0, 0x40]   # initial DDRAM addresses per line
DDRAM_SIZE      = 128   # DDRAM size in bytes

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

UNTRANSLATE_RU = {v: k for k, v in TRANSLATE_RU.items()}

# ===========================================================================
# LCD Winstar WS0010 Class
# ===========================================================================

class WS0010:

    ## Constructor
    def __init__(self, address, bus, lines=2):
        self._address = address # I2C address of PCF8754
        self._bus = bus         # I2C bus number
        self._device = i2cdev.i2cdev(address, bus)
        if lines > MAX_LINES:
            lines = MAX_LINES
        self._lines = lines     # lines of screen
        self._disp_on = False
        self._curs_on = False
        self._blink_on = False
        self._increment = False
        self._display_shift = False
        self.initialize()

    @staticmethod
    def _prop_setter(prop, param):
        """Helper function. Returns property value based on property value itself and parameter."""
        if param in (True, False):
            return param
        else:
            return prop

    def _set_disp_on(self, p):
        """Set 'disp_on' property."""
        self._disp_on = self._prop_setter(self._disp_on, p)

    def _set_curs_on(self, p):
        """Set 'disp_on' property."""
        self._curs_on = self._prop_setter(self._curs_on, p)

    def _set_blink_on(self, p):
        """Set 'blink_on' property."""
        self._blink_on = self._prop_setter(self._blink_on, p)

    def _set_increment(self, p):
        """Set 'increment' property."""
        self._increment = self._prop_setter(self._increment, p)

    def _set_display_shift(self, p):
        """Set 'display_shift' property."""
        self._display_shift = self._prop_setter(self._display_shift, p)

    def _dispctl_make_instr(self):
        """Make Display ON/OFF Control instruction byte according to property values."""
        instr = IMASK_DISP_CTL
        for (p, m) in (self._disp_on, PMASK_DISP_ON), (self._curs_on, PMASK_CURS_ON), (self._blink_on, PMASK_BLINK_ON):
            if p:
                instr |= m
        return instr

    def _emode_make_instr(self):
        """Make Entry Mode instruction byte according to property values."""
        instr = IMASK_ENTRY_MODE
        for (p, m) in (self._increment, PMASK_INC), (self._display_shift, PMASK_DISP_SHIFT_EN):
            if p:
                instr |= m
        return instr

    def latch(self, b):
        """Latch command with EN input."""
        self._device.write8(b | PIN_EN)
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

        # Set R/W pin
        self._device.write8(PIN_RW)

        while True:

            # Read high nibble of BFAC byte
            self._device.write8(PIN_RW | PIN_EN)
            bfac = (self._device.read8() & 0xF) << 4
            self._device.write8(PIN_RW)

            # Read low nibble of BFAC byte
            self._device.write8(PIN_RW | PIN_EN)
            bfac |= self._device.read8() & 0xF
            self._device.write8(PIN_RW)

            # Check BF
            if bfac & RMASK_BF:
                sleep(WAIT_BF)
            else:
                break

        # Clear R/W pin
        self._device.write8(0)

        # Return AC
        return bfac

    def dispctl_set(self, disp_on=None, curs_on=None, blink_on=None):
        """Set Display ON/OFF Control properties for display, cursor and blinking.
        Write the properties to LCD controller.
        Parameter values:
        True - property turned ON;
        False - property turned OFF;
        any other value - property not changed."""

        self._set_disp_on(disp_on)
        self._set_curs_on(curs_on)
        self._set_blink_on(blink_on)
        instr = self._dispctl_make_instr()
        self.sendI(instr)

    def dispctl_get(self):
        """Return Display ON/OFF Control properties for display, cursor and blinking.
        Returned properties grouped in tuple (disp_on, curs_on, blink_on).
        Returned values:
        True - property turned ON;
        False - property turned OFF."""

        res = (self._disp_on, self._curs_on, self._blink_on)
        return res

    def emode_set(self, increment=None, display_shift=None):
        """Set Entry Mode properties for increment/decrement and display shift.
        Write the properties to LCD controller.
        Parameter values:
        True - property turned ON;
        False - property turned OFF;
        any other value - property not changed."""

        self._set_increment(increment)
        self._set_display_shift(display_shift)
        instr = self._emode_make_instr()
        self.sendI(instr)

    def emode_get(self):
        """Return Display ON/OFF Control properties for display, cursor and blinking.
        Returned properties grouped in tuple (disp_on, curs_on, blink_on).
        Returned values:
        True - property turned ON;
        False - property turned OFF."""

        res = (self._disp_on, self._curs_on, self._blink_on)
        return res

    def initialize(self):
        """Initialize controller for necessary mode (currently 4-bit mode only)."""

        # Synchronization sequence for 4-bit mode
        self.send4(0)
        self.send4(0)
        self.send4(0)
        self.send4(0)
        self.send4(0)

        # Function Set: 4bit mode, necessary lines number, en-ru font table
        self.send4(IMASK_FUNC >> 4)
        self.sendI(IMASK_FUNC | PMASK_LINES[self._lines - 1] | PMASK_FT_ENRU)

        # Clear Display and Return Home
        self.sendI(IMASK_CLR_DISP)
        self.sendI(IMASK_RET_HOME)

    def poweroff(self):
        """Turn off power."""

        self.sendI(IMASK_GCMODE_PWR)

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

        # Output string
        for char in string:
            try:
                symbol = TRANSLATE_RU[char]
            except KeyError:
                symbol = ord(char) & 0xFF
            self.sendD(symbol)

    def read_ddram(self, ac=0, size=1):
        """Read 'size' bytes of data from 'ac' position."""

        if ac < 0:
            ac = 0
        if ac > DDRAM_SIZE:
            ac = DDRAM_SIZE - 1
        if size < 1:
            size = 1
        if size > DDRAM_SIZE:
            size = DDRAM_SIZE

        # Save current address and set it to 'ac'
        saved_ac = self.checkBF()
        self.sendI(IMASK_DDRAM_ADDR | ac)

        # Set RS and R/W pins
        ctl = PIN_RS | PIN_RW
        ctl_en = ctl | PIN_EN
        self._device.write8(PIN_RW) ### !!!
        self._device.write8(ctl)

        # Read DDRAM
        str = ''
        while size:

            # Read high nibble of DDRAM location
            self._device.write8(ctl) ### !!!
            self._device.write8(ctl_en)
            #sleep(WAIT_SLOW) ### !!!
            symbol = (self._device.read8() & 0xF) << 4
            self._device.write8(ctl) ### !!!
            self._device.write8(0) ### !!!
            xh = self._device.read8() ### !!!
            sleep(WAIT_SLOW) ### !!!
            xh_slow = self._device.read8() ### !!!

            # Read low nibble of DDRAM location
            self._device.write8(ctl) ### !!!
            self._device.write8(ctl_en)
            #sleep(WAIT_SLOW) ### !!!
            symbol |= self._device.read8() & 0xF
            self._device.write8(ctl) ### !!!
            self._device.write8(0) ### !!!
            xl = self._device.read8() ### !!!
            sleep(WAIT_SLOW) ### !!!
            xl_slow = self._device.read8() ### !!!

            # Convert symbol to character
            try:
                char = UNTRANSLATE_RU[symbol]
            except KeyError:
                char = chr(symbol)
            str += char

            # Decrement size
            size -= 1

        # Clear RS and R/W pins
        self._device.write8(0)

        # Restore saved address counter
        self.sendI(IMASK_DDRAM_ADDR | saved_ac)

        return str

    def shift_cursor_right(self):
        """Move cursor right. Address counter incremented."""
        self.sendI(IMASK_CURS_DISP_SHIFT | PMASK_SHIFT_MOVE_RIGHT)

    def shift_cursor_left(self):
        """Move cursor left. Address counter decremented."""
        self.sendI(IMASK_CURS_DISP_SHIFT)

    def shift_display_right(self):
        """Shift display right."""
        self.sendI(IMASK_CURS_DISP_SHIFT | PMASK_DISP_SHIFT | PMASK_SHIFT_MOVE_RIGHT)

    def shift_cursor_left(self):
        """Shift display left."""
        self.sendI(IMASK_CURS_DISP_SHIFT | PMASK_DISP_SHIFT)
