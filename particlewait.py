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
    "-d",
    "--device",
    default=None,
    dest='device',
    help="capture events only from this device ID",
)
argparser.add_argument(
    "-e",
    "--event",
    default=None,
    dest='event',
    help="wait for an event with this prefix (defaults to any event)",
)
triggered = Event()
quit = Event()


def setup(stdscr):
    # curses
    curses.use_default_colors()
    curses.init_pair(1, curses.COLOR_RED, -1)
    curses.init_pair(2, curses.COLOR_RED, curses.COLOR_RED)
    curses.init_pair(3, curses.COLOR_GREEN, -1)
    curses.init_pair(4, -1, curses.COLOR_RED)
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


def connection_thread_body(device, event):
    if device and event:
        url = "https://api.particle.io/v1/devices/{}/events/{}".format(device, event)
    elif device:
        url = "https://api.particle.io/v1/devices/{}/events".format(device)
    elif event:
        url = "https://api.particle.io/v1/events/{}".format(event)
    else:
        url = "https://api.particle.io/v1/events"

    with closing(get(
        url,
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
                if not triggered.is_set():
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
    while not quit.is_set():
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
                stdscr.erase()
                for x in range(int(progress * float(width))):
                    for y in range(height):
                        stdscr.addstr(y, x, "X", curses.color_pair(2))
                stdscr.refresh()
                sleep(0.03)
            stdscr.erase()
            stdscr.refresh()


def main():
    curses.wrapper(wait, argparser.parse_args(argv[1:]))


if __name__ == '__main__':
    main()
