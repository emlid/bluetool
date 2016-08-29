###Bluetooth with D-Bus API

###Install
`make install`

###Usage
 - Bluetooth:
	
	dict: key - "Name", value - "MAC-address"

	Methods of class Bluetooth:
	- `get_devices_to_pair(timeout)`, return dict
	- `scan(timeout)`, return dict
	- `get_devices("Paired" or "Connected")`, return dict
	- `make_discoverable()`, return bool
	- `pair(address)`, return bool
	- `connect(address)`, return bool
	- `disconnect(address)`, return bool
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
