import subprocess
import dbus
import dbus.mainloop.glib
try:
    from gi.repository import GObject
except ImportError:
    import gobject as GObject
import bluezutils

class BluetoothError(Exception):
    pass

class Bluetooth(object):
    
    def __init__(self):
        subprocess.check_output("rfkill unblock bluetooth", shell=True)
        dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
        self.__bus = dbus.SystemBus()

    def get_devices_to_pair(self, timeout=10):
        devices = self.scan(timeout)

        try:
            for key in self.get_devices("Paired").keys():
                devices.pop(key)
        except BluetoothError as error:
            print error
            return {}

        return devices

    def scan(self, timeout=10):
        devices = {}

        try:
            adapter = bluezutils.find_adapter()
        except Exception as error:
            print error
        else:
            try:
                adapter.StartDiscovery()
                
                mainloop = GObject.MainLoop()
                
                GObject.timeout_add(timeout*1000, mainloop.quit)

                mainloop.run()

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

    def get_devices(self, condition):
        conditions = ["Paired", "Connected"]

        if condition not in conditions:
            raise BluetoothError("get_devices: unknown condition - {}".\
                    format(condition))
        
        devices = {}

        try:
            man = dbus.Interface(self.__bus.get_object("org.bluez", "/"),
                    "org.freedesktop.DBus.ObjectManager")
            objects = man.GetManagedObjects()
            
            for path, interfaces in objects.iteritems():
                if "org.bluez.Device1" in interfaces:
                    dev = interfaces["org.bluez.Device1"]

                    props = dbus.Interface(self.__bus.get_object("org.bluez",
                            path),
                        "org.freedesktop.DBus.Properties")

                    if props.Get("org.bluez.Device1", condition):
                        if "Address" not in dev:
                            continue
                        if "Name" not in dev:
                            dev["Name"] = "<unknown>"

                        devices[str(dev["Name"])] = str(dev["Address"])

        except dbus.exceptions.DBusException as error:
            print error
      
        return devices

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

