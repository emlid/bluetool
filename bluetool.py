#!/usr/bin/python

import os
import sys
import dbus
import dbus.mainloop.glib
try:
    from gi.repository import GObject
except ImportError:
    import gobject as GObject
import bluezutils

class Bluetooth(object):

    def __init__(self):
        os.system("rfkill unblock bluetooth")
        dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
        self.bus = dbus.SystemBus()

    def scan(self, timeout=5):
        try:
            adapter = bluezutils.find_adapter()
        except Exception as error:
            print error
        else:
            self.bus.add_signal_receiver(Bluetooth.interfaces_added,
                    dbus_interface = "org.freedesktop.DBus.ObjectManager",
                    signal_name = "InterfacesAdded")

            adapter.StartDiscovery()
            
            mainloop = GObject.MainLoop()
            mainloop.run()

    @staticmethod
    def interfaces_added(path, interfaces):#path!
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

    def pair(self, address):
        try:
            device = bluezutils.find_device(address)
        except Exception as error:
            print error
            return False
        else:
            device.Pair()
            return True


if __name__ == "__main__":

    bluetooth = Bluetooth()

    #bluetooth.scan()
    bluetooth.pair(sys.argv[1])

    sys.exit(0)
