#! /usr/bin/python3

import ws0010

I2C_ADDRESS = 0x39
I2C_BUS = 0

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

# Insert initialization code from old program here

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

    if answer_int not in range(1, len(choices) - 1):
        print('\nInvalid input: {}'.format(answer))
        continue

    print('\nYour choice: {}) {}\n'.format(answer, choices[answer_int][0]))
    choices[answer_int][1](lcd)

def display_out(lcd):
    """Output string to specified line."""

    string = input('Enter string: ')
    line = input('Enter line number (1 or 2): ')
    try:
        line_int = int(line)
    except ValueError:
        print('Invalid line number {}'.format(line))
