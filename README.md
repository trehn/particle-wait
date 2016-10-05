# particle-wait

Script that terminates when an event is received from [Particle.io](http://particle.io). You can use this to queue up shell commands and execute them at the push of a Particle-connected button.

## Example

```
ACCESS_TOKEN="yourtoken" particle-wait -d yourdeviceid && poweroff
```

## Installation

```
pip install particle-wait
```

## Options

```
usage: particle-wait [-h] [-c N] [-e NAME] DEVICE_ID

waits for events from particle.io

positional arguments:
  DEVICE_ID             capture events only from this device ID

optional arguments:
  -h, --help            show this help message and exit
  -c N, --cancel N      cancel if any event is received within N seconds after
                        the first event
  -e NAME, --event NAME
                        wait for an event with this name (defaults to any
                        event)
```
