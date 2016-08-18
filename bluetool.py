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

    __mainloop = None
    
    def __init__(self):
        os.system("rfkill unblock bluetooth")
        dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
        self.__bus = dbus.SystemBus()

    def scan(self, timeout=10):
        try:
            adapter = bluezutils.find_adapter()
        except Exception as error:
            print error
        else:
            adapter.StartDiscovery()
            
            Bluetooth.__mainloop = GObject.MainLoop()
            
            GObject.timeout_add(timeout * 1000, Bluetooth.timeout)

            Bluetooth.__mainloop.run()

            bluez = dbus.Interface(self.__bus.get_object("org.bluez", "/"),
                                    "org.freedesktop.DBus.ObjectManager")
            objects = bluez.GetManagedObjects()
            devices = []
            
            for path, interfaces in objects.iteritems():
                if "org.bluez.Device1" in interfaces:
                    dev = interfaces["org.bluez.Device1"]

                    if "Address" not in dev:
                        continue
                    if "Name" not in dev:
                        dev["Name"] = "<unknown>"
                    
                    devices.append((str(dev["Name"]), str(dev["Address"])))
            
            return devices

    @staticmethod
    def timeout():
        Bluetooth.__mainloop.quit()

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

    devices = bluetooth.scan(10)

    for dev in devices:
        print dev

    sys.exit(0)
