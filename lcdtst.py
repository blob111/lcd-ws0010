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

def ask_choice(choices, header):
    """Ask operator to pick up choice from list.
    Header is outputted before list as helper what to choice."""

    while True:
        print('\n{}'.format(header))
        for i, ent in enumerate(choices):
            print('{}) {}'.format(i + 1, ent))
        answer = input('Enter your choice (1 - {}): '.format(len(choices)))

        try:
            answer_int = int(answer)
        except ValueError:
            print('\nInvalid input: {}'.format(answer))
            continue
        else:
            break

        if answer_int not in range(1, len(choices) + 1):
            print('\nChoice {} out of range'.format(answer))
            continue
    return answer_int

def display_out(lcd):
    """Output string to specified line."""

    string = input('Enter string: ')
    line = ask_int('line number', 1, 2)
    sys.stdout.write('Sending string to line {} ...'.format(line))
    lcd.puts(string, line)
    sys.stdout.write(' done\n')

def move_cursor(lcd):
    """Move cursor."""

    choices = ['Left', 'Right']
    dir = ask_choice(choices, 'Where do you want to move cursor?')
    if dir == 1:
        f = lcd.move_cursor_left
    else: # dir is 2
        f = lcd.move_cursor_right
    sys.stdout.write('Moving cursor to the {} ...'.format(choices[dir - 1]))
    f()
    sys.stdout.write(' done\n')

def shift_display(lcd):
    """Shift display."""

    choices = ['Left', 'Right']
    dir = ask_choice(choices, 'Where do you want to shift display?')
    if dir == 1:
        f = lcd.shift_display_left
    else: # dir is 2
        f = lcd.shift_display_right
    sys.stdout.write('Shifting display to the {} ...'.format(choices[dir - 1]))
    f()
    sys.stdout.write(' done\n')

def clear_display(lcd):
    """Clear entire display."""

    sys.stdout.write('Requesting clear display ...')
    lcd.clear_display()
    sys.stdout.write(' done\n')

def ret_home(lcd):
    """Return home."""

    sys.stdout.write('Requesting return home ...')
    lcd.ret_home()
    sys.stdout.write(' done\n')

def display_ctl(lcd):
    """Display ON/OFF Control settings."""

    prop_list = ('Display', 'Cursor', 'Blinking')
    op_choices = ['Get', 'Set']
    op = ask_choice(op_choices, 'What kind of operation do you going to perform with Display ON/OFF Control settings?')
    if op == 1:
        # Get operation
        sys.stdout.write('Requesting Display ON/OFF Control settings ...')
        res = lcd.dispctl_get()
        sys.stdout.write(' done\n')
        sys.stdout.write('Got: ')
        str_a = []
        for pair in list(zip(prop_list, res)):
            str = pair[0] + ' is '
            if pair[1]:
                str += 'ON'
            else:
                str += 'OFF'
            str_a.append(str)
        print(', '.join(str_a))
    else:
        # Set operation
        bit_choices = ['ON', 'OFF', 'Not change']
        bit_actions = [True, False, None]
        args = []
        for prop in prop_list:
            prop_choice = ask_choice(bit_choices, 'Here is list of actions permissible for {} control bit:'.format(prop))
            args.append(bit_actions[prop_choice - 1])
        sys.stdout.write('Sending Display ON/OFF Control settings ...')
        res = lcd.dispctl_set(*args)
        sys.stdout.write(' done\n')

def emode(lcd):
    """Entry mode settings."""

    op_choices = ['Get', 'Set']
    op = ask_choice(op_choices, 'What kind of operation do you going to perform with Entry Mode settings?')
    if op == 1:
        # Get operation
        sys.stdout.write('Requesting Entry Mode settings ...')
        res = lcd.emode_get()
        sys.stdout.write(' done\n')
        sys.stdout.write('Got: ')
        str = 'I/D is set to '
        if res[0]:
            str += 'increment'
        else:
            str += 'decrement'
        str += ', Display Shift is '
        if res[1]:
            str += 'enabled'
        else:
            str += 'disabled'
        print(str)
    else:
        # Set operation
        bit_choices = ['ON', 'OFF', 'Not change']
        bit_actions = [True, False, None]
        args = []
        for prop in ('I/D', 'Display Shift'):
            prop_choice = ask_choice(bit_choices, 'Here is list of actions permissible for {} control bit:'.format(prop))
            args.append(bit_actions[prop_choice - 1])
        sys.stdout.write('Sending Entry Mode settings ...')
        res = lcd.emode_set(*args)
        sys.stdout.write(' done\n')

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

top_choices = [
    ('Output to display', display_out),
    ('Move cursor', move_cursor),
    ('Shift display', shift_display),
    ('Clear display', clear_display),
    ('Return Home', ret_home),
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
    top_choices_list = list(map(lambda x: x[0], top_choices))
    k = ask_choice(top_choices_list, 'Main loop')
    print('\nYour choice: {}) {}\n'.format(k, top_choices_list[k - 1]))
    top_choices[k - 1][1](lcd)
