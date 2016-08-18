#!/usr/bin/python

import sys
import dbus
import dbus.mainloop.glib
try:
    from gi.repository import GObject
except ImportError:
    import gobject as GObject
import bluezutils

def interfaces_added(path, interfaces):
    properties = interfaces["org.bluez.Device1"]
    if not properties:
	return

    if "Address" in properties:
	address = properties["Address"]
    else:
	address = "<unknown>"

    if "Name" in properties:
	name = properties["Name"]
    else:
	name = "<unknown>"

    print(address, name)

if __name__ == "__main__":

    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
    bus = dbus.SystemBus()

    if (sys.argv[1] == "scan"):
	adapter = bluezutils.find_adapter()

	bus.add_signal_receiver(interfaces_added,
    	        dbus_interface = "org.freedesktop.DBus.ObjectManager",
		signal_name = "InterfacesAdded")

	adapter.StartDiscovery()
		
	mainloop = GObject.MainLoop()
	mainloop.run()

        sys.exit(0)

    if (sys.argv[1] == "pair"):
	if (len(sys.argv) < 3):
	    print("Need address parameter")
	else:
	    device = bluezutils.find_device(sys.argv[2])
	    device.Pair()

        sys.exit(0)

    print("Unknown command")
    sys.exit(1)

