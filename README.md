# Omicron Laser


[![Omicron Laser](https://img.shields.io/pypi/v/omicron_laser.svg)](https://pypi.python.org/pypi/omicron_laser)



Omicron Laser with optional tango server and simulator


Apart from the core library, an optional [simulator](https://pypi.org/project/sinstruments) is also provided.



Apart from the core library, an optional [tango](https://tango-controls.org/) device server is also provided.


## Installation

From within your favorite python environment type:

`$ pip install omicron_laser`

## Library

The core of the omicron_laser library consists of Omicron_laser object.
To create a Omicron_laser object you need to pass a communication object.

The communication object can be any object that supports a simple API
consisting of two methods (either the sync or async version is supported):

* `write_readline(buff: bytes) -> bytes` *or*

  `async write_readline(buff: bytes) -> bytes`

* `write(buff: bytes) -> None` *or*

  `async write(buff: bytes) -> None`

A library that supports this API is [sockio](https://pypi.org/project/sockio/)
(Omicron Laser comes pre-installed so you don't have to worry
about installing it).

This library includes both async and sync versions of the TCP object. It also
supports a set of features like re-connection and timeout handling.

Here is how to connect to a Omicron_laser controller:

```python
import asyncio

from sockio.aio import TCP
from omicron_laser import Omicron_laser


async def main():
    tcp = TCP("192.168.1.123", 5000)  # use host name or IP
    omicron_laser_dev = Omicron_laser(tcp)

    idn = await omicron_laser_dev.idn()
    print("Connected to {} ({})".format(idn))


asyncio.run(main())
```


### Simulator

A Omicron_laser simulator is provided.

Before using it, make sure everything is installed with:

`$ pip install omicron_laser[simulator]`

The [sinstruments](https://pypi.org/project/sinstruments/) engine is used.

To start a simulator you need to write a YAML config file where you define
how many devices you want to simulate and which properties they hold.

The following example exports a hardware device with a minimal configuration
using default values:

```yaml
# config.yml

devices:
- class: Omicron_laser
  package: omicron_laser.simulator
  transports:
  - type: tcp
    url: :5000
```

To start the simulator type:

```terminal
$ sinstruments-server -c ./config.yml --log-level=DEBUG
2020-05-14 16:02:35,004 INFO  simulator: Bootstraping server
2020-05-14 16:02:35,004 INFO  simulator: no backdoor declared
2020-05-14 16:02:35,004 INFO  simulator: Creating device Omicron_laser ('Omicron_laser')
2020-05-14 16:02:35,080 INFO  simulator.Omicron_laser[('', 5000)]: listening on ('', 5000) (newline='\n') (baudrate=None)
```

(To see the full list of options type `sinstruments-server --help`)





### Tango server

A [tango](https://tango-controls.org/) device server is also provided.

Make sure everything is installed with:

`$ pip install omicron_laser[tango]`

Register a Omicron_laser tango server in the tango database:
```
$ tangoctl server add -s Omicron_laser/test -d Omicron_laser test/omicron_laser/1
$ tangoctl device property write -d test/omicron_laser/1 -p address -v "tcp://192.168.123:5000"
```

(the above example uses [tangoctl](https://pypi.org/project/tangoctl/). You would need
to install it with `pip install tangoctl` before using it. You are free to use any other
tango tool like [fandango](https://pypi.org/project/fandango/) or Jive)

Launch the server with:

```terminal
$ Omicron_laser test
```


## Credits

### Development Lead

* Alberto López Sánchez <controls@cells.es>

### Contributors

None yet. Why not be the first?
