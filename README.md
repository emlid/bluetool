###Bluetool

Bluetooth with D-Bus API. Dependence: python-dbus.

###Install
`make install`

###Usage
 - Bluetooth:
	
	list: [ {"name": Name, "mac_address": MAC-address}, ... ]

	Methods of class Bluetooth:
	- `start_scanning(timeout)`: `scan` inside thread
	- `scan(timeout)`
	- `get_devices_to_pair()`, return list
	- `get_available_devices()`, return list
	- `get_paired_devices()`, return list
	- `get_connected_devices()`, return list
	- `make_discoverable()`, return bool
	- `start_pairing(address)`: `pair` inside thread
	- `pair(address)`, return bool
	- `connect(address)`, return bool
	- `disconnect(address)`, return bool
	- `trust(address)`, return bool
	- `remove(address)`, return bool

	#####Example
	```
	from bluetool import Bluetooth

	bluetooth = Bluetooth()

	bluetooth.scan()

	devices = bluetooth.get_available_devices()

	print devices
	```

 - BluetoothServer:
 	
	- Step1: Use `run()` to create SPP. 
	- Step2: Connect the bluetooth device.
	- Step3: TCPServer is available for connection.
	
	BluetoothServer will disconnect your device if you lose TCPconnection. Use `quit()` to stop server. 
 
	#####Example
	```
	from bluetool import BluetoothServer

	port = 8100
	server = BluetoothServer(port)

	server.run()
	...
	server.quit()
	```
