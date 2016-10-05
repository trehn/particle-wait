# particle-wait

Script that terminates when an event is received from [Particle.io](http://particle.io).

You can use this to queue up shell commands and execute them at the push of a Particle-connected button.

Usage:

```
ACCESS_TOKEN="yourtoken" particle-wait -d yourdeviceid && poweroff
```

Installation:

```
pip install particle-wait
```
