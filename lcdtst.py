#! /usr/bin/python3

import sys
import ws0010

I2C_ADDRESS = 0x39
I2C_BUS = 0

def ask_int(name, v_min, v_max):
    """Ask operator to enter integer (name) and return it.
    Entered value checked for permitted range between v_min and v_max inclusive."""
    
    name = name.lower()
    cname = name.capitalize()
    while True:
        v = input('Enter {} ({} - {}): '.format(name, v_min, v_max))
        try:
            v_int = int(v)
        except ValueError:
            print('Invalid {} {}'.format(name, v))
            continue
        else:
            if v_int in range(v_min, v_max + 1):
                break
            else:
                print('{} {} out of range'.format(cname, v))
                continue
    return v_int

def display_out(lcd):
    """Output string to specified line."""

    string = input('Enter string: ')
    line = ask_int('line number', 1, 2)
    sys.stdout.write('Sending string to line {} ...'.format(line))
    lcd.puts(string, line)
    sys.stdout.write(' done\n')

def move_cursor(lcd):
    """Move cursor."""
    
    pass

def shift_display(lcd):
    """Shift display."""
    
    pass

def display_ctl(lcd):
    """Display ON/OFF Control settings."""
    
    pass

def emode(lcd):
    """Entry mode settings."""
    
    pass

def read_ddram(lcd):
    """Read DDRAM contents and print it."""
    
    ac = ask_int('address counter', 0, 127)
    size = ask_int('size', 1, 128)
    sys.stdout.write('Reading {} bytes starting at {} ...'.format(size, ac))
    ddram = lcd.read_ddram(ac, size)
    sys.stdout.write(' done\n')
    print('Got: ')
    print(repr(ddram))

def reinit(lcd):
    """Reinitialize LCD."""
    
    sys.stdout.write('Reinitializing LCD ...')
    lcd.initialize()
    lcd.emode_set(increment=True)
    lcd.dispctl_set(disp_on=True, curs_on=True, blink_on=True)
    sys.stdout.write(' done\n')

def quit_prog(lcd):
    """Quit program."""
    
    print('Request to quit program. Good bye!')
    sys.exit(0)

choices = [
    ('Output to display', display_out),
    ('Move cursor', move_cursor),
    ('Shift display', shift_display),
    ('Display ON/OFF Control', display_ctl),
    ('Entry Mode', emode),
    ('Read DDRAM', read_ddram),
    ('Reinitialize display', reinit),
    ('Quit', quit_prog)
]

print('\nWinstar Display test program.')

sys.stdout.write('Initializing LCD ...')
lcd = ws0010.WS0010(I2C_ADDRESS, I2C_BUS)
lcd.emode_set(increment=True)
lcd.dispctl_set(disp_on=True, curs_on=True, blink_on=True)
sys.stdout.write(' done\n')

while True:
    print('\nMain loop.')
    for i, ent in enumerate(choices):
        print('{}) {}'.format(i + 1, ent[0]))
    answer = input('Enter your choice (1 - {}): '.format(len(choices)))

    try:
        answer_int = int(answer)
    except ValueError:
        print('\nInvalid input: {}'.format(answer))
        continue

    if answer_int not in range(1, len(choices) + 1):
        print('\nInvalid input: {}'.format(answer))
        continue

    print('\nYour choice: {}) {}\n'.format(answer, choices[answer_int - 1][0]))
    choices[answer_int - 1][1](lcd)
