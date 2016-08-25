###Bluetooth with D-Bus API

###Install
`make install`

###Usage
 - Bluetooth:
	dict: key - "Name", value - "MAC-address"

	Methods of class Bluetooth:
	- `get_devices_to_pair()`, return dict
	- `scan()`, return dict
	- `get_devices("Paired" or "Connected")`, return dict
	- `make_discoverable`, return bool
	- `pair(address)`, return bool
	- `trust(address)`, return bool
	- `remove(address)`, return bool

	#####Example
	```
	from bluetool import Bluetooth

	bluetooth = Bluetooth()

	devices = bluetooth.scan()

	for key, value in devices.items():
	    print key, value
	```

 - BluetoothServer:
 	Use `run()` to create TCPserver and SPP, you should connect to TCPserver, 
 	after SPP will be available for connection. Use `quit()` to stop server. 
 
	#####Example
	```
	from bluetool import BluetoothServer

	port = 8100
	server = BluetoothServer(port)

	server.run()
	...
	server.quit()
	```
