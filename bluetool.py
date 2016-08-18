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
            try:
                adapter.StartDiscovery()
                
                Bluetooth.__mainloop = GObject.MainLoop()
                
                GObject.timeout_add(timeout * 1000, Bluetooth.timeout)

                Bluetooth.__mainloop.run()

                man = dbus.Interface(self.__bus.get_object("org.bluez", "/"),
                                        "org.freedesktop.DBus.ObjectManager")
                objects = man.GetManagedObjects()
                devices = []
                
                for path, interfaces in objects.iteritems():
                    if "org.bluez.Device1" in interfaces:
                        dev = interfaces["org.bluez.Device1"]

                        if "Address" not in dev:
                            continue
                        if "Name" not in dev:
                            dev["Name"] = "<unknown>"
                        
                        devices.append((str(dev["Name"]), str(dev["Address"])))
                
            except dbus.exceptions.DBusException as error:
                print error

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
            try:
                device.Pair()
            except dbus.exceptions.DBusException as error:
                if "AlreadyExists" in error:
                    return True
                print error
                return False
        
        return True

    def trust(self, address):
        try:
            device = bluezutils.find_device(address)
        except Exception as error:
            print error
            return False
        else:
            try:
                props = dbus.Interface(self.__bus.get_object("org.bluez", device.object_path),
                        "org.freedesktop.DBus.Properties")
  
                props.Set("org.bluez.Device1", "Trusted", dbus.Boolean(1))
            except dbus.exceptions.DBusException as error:
                print error
                return False
        
        return True


if __name__ == "__main__":

    bluetooth = Bluetooth()

    devices = bluetooth.scan(10)

    for dev in devices:
        print dev

    bluetooth.pair("DC:9B:9C:CB:DB:49")
    bluetooth.trust("DC:9B:9C:CB:DB:49")

    sys.exit(0)
