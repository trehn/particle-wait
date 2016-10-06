#!/usr/bin/env python
from __future__ import unicode_literals

from argparse import ArgumentParser
from contextlib import closing
from datetime import datetime
import curses
from os import environ
from sys import argv, exit
from threading import Event, Thread
from time import sleep

from requests import get


argparser = ArgumentParser(
    prog="particle-wait",
    description="waits for events from particle.io",
)
argparser.add_argument(
    "-c",
    "--cancel",
    default=False,
    dest='cancel',
    metavar="N",
    help="cancel if any event is received within N seconds after the first event",
    type=int,
)
argparser.add_argument(
    "-e",
    "--event",
    default=None,
    dest='event',
    help="wait for an event with this name (defaults to any event)",
    metavar="NAME",
)
argparser.add_argument(
    "-t",
    "--title-wait",
    default="WAITING FOR EVENT...",
    dest='title_wait',
    help="text to show while waiting for initial event",
    metavar="TEXT",
)
argparser.add_argument(
    "-T",
    "--title-cancel",
    default="WAITING FOR EVENT...",
    dest='title_cancel',
    help="text to show while waiting for canceling event",
    metavar="TEXT",
)
argparser.add_argument(
    'device',
    help="capture events from this device ID",
    metavar="DEVICE_ID",
    type=str,
)
triggered = Event()
quit = Event()


def setup(stdscr):
    # curses
    curses.use_default_colors()
    curses.init_pair(1, curses.COLOR_RED, -1)
    curses.init_pair(2, curses.COLOR_RED, curses.COLOR_RED)
    curses.init_pair(3, curses.COLOR_GREEN, curses.COLOR_GREEN)
    curses.init_pair(4, curses.COLOR_GREEN, -1)
    try:
        curses.curs_set(False)
    except curses.error:
        # fails on some terminals
        pass
    stdscr.timeout(0)


def graceful_ctrlc(func):
    """
    Makes the decorated function exit with code 1 on CTRL+C.
    """
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except KeyboardInterrupt:
            exit(1)
    return wrapper


def pad_to_size(text, x):
    pad_left = int((float(x) - float(len(text))) / 2)
    pad_right = x - (pad_left + len(text))
    return " " * pad_left + text + " " * pad_right


def draw_progress(stdscr, progress, title):
    stdscr.erase()
    height, width = stdscr.getmaxyx()
    title_lines = len(title.splitlines())
    pad_x = int(0.1 * float(width))
    pad_y = int((float(height) - 4.0 - float(title_lines)) / 2.0)
    for i, line in enumerate(title.splitlines()):
        stdscr.insstr(pad_y + i, 0, pad_to_size(line, width), curses.color_pair(1))
    bar_length = width - (2 * pad_x)
    pad_y += title_lines
    stdscr.insstr(pad_y + 1, 0, pad_to_size("╭" + bar_length * "─" + "╮", width))
    stdscr.insstr(pad_y + 2, 0, pad_to_size("│" + bar_length * " " + "│", width))
    stdscr.insstr(pad_y + 3, 0, pad_to_size("╰" + bar_length * "─" + "╯", width))
    stdscr.addstr(
        pad_y + 2,
        pad_x + int(bar_length / 2.0) + int(progress * -0.5 * bar_length),
        int(progress * bar_length) * " ",
        curses.color_pair(2),
    )
    stdscr.refresh()


def draw_wait(stdscr, position, change, title):
    stdscr.erase()
    height, width = stdscr.getmaxyx()
    title_lines = len(title.splitlines())
    pad_x = int(0.1 * float(width))
    pad_y = int((float(height) - 4.0 - float(title_lines)) / 2.0)
    for i, line in enumerate(title.splitlines()):
        stdscr.insstr(pad_y + i, 0, pad_to_size(line, width), curses.color_pair(4))
    bar_length = width - (2 * pad_x)
    pad_y += title_lines
    stdscr.insstr(pad_y + 1, 0, pad_to_size("╭" + bar_length * "─" + "╮", width))
    stdscr.insstr(pad_y + 2, 0, pad_to_size("│" + bar_length * " " + "│", width))
    stdscr.insstr(pad_y + 3, 0, pad_to_size("╰" + bar_length * "─" + "╯", width))
    stdscr.addstr(pad_y + 2, pad_x + position, 2 * " ", curses.color_pair(3))
    position += change
    if position == bar_length - 2 or position == 0:
        change = -1 * change
    stdscr.refresh()
    return (position, change)


def connection_thread_body(device, event):
    with closing(get(
        "https://api.particle.io/v1/devices/{}/events".format(device),
        headers={
            "Authorization": "Bearer {}".format(environ["ACCESS_TOKEN"]),
        },
        stream=True,
    )) as response:
        response.raise_for_status()
        for line in response.iter_lines():
            if quit.is_set():
                return
            line = line.decode('utf-8')
            if line.startswith("event: "):
                if not triggered.is_set() and (not event or line[7:] == event):
                    triggered.set()
                else:
                    triggered.clear()


@graceful_ctrlc
def wait(stdscr, args):
    setup(stdscr)
    connection_thread = Thread(
        args=(args.device, args.event),
        target=connection_thread_body,
    )
    connection_thread.daemon = True
    connection_thread.start()
    position = 0
    change = +1
    while not quit.is_set():
        position, change = draw_wait(stdscr, position, change, args.title_wait)
        if triggered.wait(0.01):
            trigger_time = datetime.utcnow()
            if not args.cancel:
                quit.set()
                return
            while triggered.is_set():
                elapsed = datetime.utcnow() - trigger_time
                progress = elapsed.total_seconds() / float(args.cancel)
                if progress >= 1.0:
                    quit.set()
                    return
                height, width = stdscr.getmaxyx()
                draw_progress(stdscr, progress, args.title_cancel)
                sleep(0.03)
            stdscr.erase()
            stdscr.refresh()


def main():
    curses.wrapper(wait, argparser.parse_args(argv[1:]))


if __name__ == '__main__':
    main()
