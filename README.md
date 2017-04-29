### Bluetool

A simple Python API for Bluetooth D-Bus calls. Allows easy pairing, connecting and scanning.
Also provides a TCP-to-RFCOMM socket bridge for data transfer.

#### Dependencies

- `python-dbus`
- `tcpbridge`

The package was tested with **Python 2.7**

#### Installation

`pip install bluetool`

or clone and run `make install`

#### Usage

- Bluetooth:
	
	list: `[{"name": Name, "mac_address": MAC-address}, ... ]`

	Methods of class Bluetooth:
	- `start_scanning(timeout)`: `scan` in background
	- `scan(timeout)`
	- `get_devices_to_pair()`, returns list
	- `get_available_devices()`, returns list
	- `get_paired_devices()`, returns list
	- `get_connected_devices()`, returns list
	- `make_discoverable()`, returns bool
	- `start_pairing(address)`: `pair` in background
	- `pair(address)`, returns bool
	- `connect(address)`, returns bool
	- `disconnect(address)`, returns bool
	- `trust(address)`, returns bool
	- `remove(address)`, returns bool

- BluetoothServer:
 	
	- Step1: Use `run()` to create SPP
	- Step2: Connect the bluetooth device
	- Step3: TCPServer is available for connection
	
	Use `shutdown()` to shutdown server.

##### Examples

- Scanning
```python
from bluetool import Bluetooth


bluetooth = Bluetooth()
bluetooth.scan()
devices = bluetooth.get_available_devices()
print(devices)
```
- Using the RFCOMM-TCP Bridge
```python
import signal
from bluetool import BluetoothServer


def handler(signum, frame):
    server.shutdown()


tcp_port = 8100
server = BluetoothServer(tcp_port)

signal.signal(signal.SIGINT, handler)
signal.signal(signal.SIGTERM, handler)

server.run()
```

### About the project

This package was written by [Aleksandr Aleksandrov](https://github.com/AD-Aleksandrov) working at [Emlid](https://emlid.com/).

The bluetool was originally written for the [Emlid Reach RTK receiver](https://emlid.com/reach/), but we decided to open source it, as there is no easy Python API for BT pairing/connecting. Feel free to add issues and submit pull requests.
