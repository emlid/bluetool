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
        devices = {}

        try:
            adapter = bluezutils.find_adapter()
        except Exception as error:
            print error
        else:
            try:
                adapter.StartDiscovery()
                
                Bluetooth.__mainloop = GObject.MainLoop()
                
                GObject.timeout_add(timeout * 1000, Bluetooth.interrupt_mainloop)

                Bluetooth.__mainloop.run()

                man = dbus.Interface(self.__bus.get_object("org.bluez", "/"),
                        "org.freedesktop.DBus.ObjectManager")
                objects = man.GetManagedObjects()
                
                for path, interfaces in objects.iteritems():
                    if "org.bluez.Device1" in interfaces:
                        dev = interfaces["org.bluez.Device1"]

                        if "Address" not in dev:
                            continue
                        if "Name" not in dev:
                            dev["Name"] = "<unknown>"
                        
                        devices[str(dev["Name"])] = str(dev["Address"])
                
            except dbus.exceptions.DBusException as error:
                print error

        return devices

    @staticmethod
    def interrupt_mainloop():
        if Bluetooth.__mainloop is not None: 
            Bluetooth.__mainloop.quit()

    def make_discoverable(self):
        try:
            adapter = bluezutils.find_adapter()
        except Exception as error:
            print error
            return False
        else:
            try:
                props = dbus.Interface(self.__bus.get_object("org.bluez",
                            adapter.object_path),
                        "org.freedesktop.DBus.Properties")

                if not props.Get("org.bluez.Adapter1", "Discoverable"):
                    props.Set("org.bluez.Adapter1", "Discoverable", dbus.Boolean(1))
            except dbus.exceptions.DBusException as error:
                print error
                return False

        return True

    def pair(self, address):
        try:
            device = bluezutils.find_device(address)
        except Exception as error:
            print error
            return False
        else:
            try:
                props = dbus.Interface(self.__bus.get_object("org.bluez",
                            device.object_path),
                        "org.freedesktop.DBus.Properties")

                if not props.Get("org.bluez.Device1", "Paired"):
                    device.Pair()
            except dbus.exceptions.DBusException as error:
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
                props = dbus.Interface(self.__bus.get_object("org.bluez",
                            device.object_path),
                        "org.freedesktop.DBus.Properties")

                if not props.Get("org.bluez.Device1", "Trusted"):
                    props.Set("org.bluez.Device1", "Trusted", dbus.Boolean(1))
            except dbus.exceptions.DBusException as error:
                print error
                return False
        
        return True

    def remove(self, address):
        try:
            adapter = bluezutils.find_adapter()
            dev = bluezutils.find_device(address)
        except Exception as error:
            print error
            return False
        else:
            try:
                adapter.RemoveDevice(dev.object_path)
            except dbus.exceptions.DBusException as error:
                print error
                return False

        return True


if __name__ == "__main__":

    bluetooth = Bluetooth()

    print bluetooth.make_discoverable()

    devices = bluetooth.scan()

    for name, address in devices.items():
        print name, address

    name = "HTC_"

    #if bluetooth.pair(devices[name]):
    #    if bluetooth.trust(devices[name]):
    #        print name, "is ready"

    print bluetooth.remove(devices[name])

    sys.exit(0)
