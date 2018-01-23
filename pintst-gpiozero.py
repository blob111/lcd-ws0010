#! /usr/bin/python3

from time import time, localtime, gmtime, strftime
from math import modf
import queue
from gpiozero import Button

GPIO_PIN = 23
GPIO_DEBOUNCE = 0.2
GPIO_HOLDTIME = 1
TS_FORMAT = '%H:%M:%S'
DEVT_FORMAT = '%S'
PIN_EVENT_PRESSED = 1
PIN_EVENT_RELEASED = 2
PIN_EVENT_HELD = 3

event_text = {
    PIN_EVENT_PRESSED: 'pressed',
    PIN_EVENT_RELEASED: 'released',
    PIN_EVENT_HELD: 'held'
}

def time_conv(t, format=TS_FORMAT, local=True):
    if t:
        ts = round(t, 3)
        if local:
            cf = localtime
        else:
            cf = gmtime
        ts_string = strftime(format, cf(ts))
        ts_fraction = int(modf(ts)[0] * 1000)
        return '{}.{:03d}'.format(ts_string, ts_fraction)
    else:
        return 'None'

def gpio_handler_pressed(device):
    global q
    q.put((device, PIN_EVENT_PRESSED, time()))
    return

def gpio_handler_released(device):
    global q
    q.put((device, PIN_EVENT_RELEASED, time()))
    return

def gpio_handler_held(device):
    global q
    q.put((device, PIN_EVENT_HELD, time()))
    return

q = queue.Queue()
btn = Button(GPIO_PIN, pull_up=True, bounce_time=GPIO_DEBOUNCE, hold_time=GPIO_HOLDTIME, hold_repeat=True)
btn.when_pressed = gpio_handler_pressed
btn.when_released = gpio_handler_released
btn.when_held = gpio_handler_held

while True:
    (device, pin_event, t) = q.get()
    pin = device.pin.number
    print('{}: Pin {} {}: active={}, pressed={}, held={}, active_time={}, held_time={}'.format(time_conv(t), pin,
        event_text[pin_event], device.is_active, device.is_pressed, device.is_held,
        time_conv(device.active_time, format=DEVT_FORMAT, local=False),
        time_conv(device.held_time, format=DEVT_FORMAT, local=False)))
    q.task_done()

