####################################################################
#   Copyright (c) 2016, Aleksandr Aleksandrov.
#   All rights reserved.
#
#   Redistribution and use in source and binary forms, with or
#   without modification, are permitted provided that
#   the following conditions are met:
#       * Redistributions of source code must retain the above
#         copyright notice, this list of conditions and
#         the following disclaimer.
#       * Redistributions in binary form must reproduce the above
#         copyright notice, this list of conditions and
#         the following disclaimer in the documentation and/or
#         other materials provided with the distribution.
#       * Neither the name Emlid nor the names of its
#         contributors may be used to endorse or promote products
#         derived from this software without specific prior
#         written permission.
#
#   THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND
#   CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES,
#   INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF
#   MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
#   DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR
#   CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
#   SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
#   BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
#   LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
#   CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,
#   STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
#   ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE,
#   EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
####################################################################

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
                
                adapter.StopDiscovery()

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

    def connect(self, address):
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

                if not props.Get("org.bluez.Device1", "Connected"):
                    device.Connect()
            except dbus.exceptions.DBusException as error:
                print error
                return False
        
        return True

    def disconnect(self, address):
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

                if props.Get("org.bluez.Device1", "Connected"):
                    device.Disconnect()
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

