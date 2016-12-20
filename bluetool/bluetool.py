from __future__ import print_function
from __future__ import absolute_import
# Bluetool code is placed under the GPL license.
# Written by Aleksandr Aleksandrov (aleksandr.aleksandrov@emlid.com)
# Copyright (c) 2016, Emlid Limited
# All rights reserved.

# If you are interested in using Bluetool code as a part of a
# closed source project, please contact Emlid Limited (info@emlid.com).

# This file is part of Bluetool.

# Bluetool is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# Bluetool is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with Bluetool.  If not, see <http://www.gnu.org/licenses/>.

from builtins import object
import dbus
import dbus.mainloop.glib
import threading
from . import bluezutils


class Bluetooth(object):

    def __init__(self):
        dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
        self.__bus = dbus.SystemBus()
        self.scan_thread = None

    def start_scanning(self, timeout=10):
        if self.scan_thread is None:
            self.scan_thread = threading.Thread(target=self.scan, args=(timeout,))
            self.scan_thread.start()

    def scan(self, timeout=10):
        try:
            adapter = bluezutils.find_adapter()
        except bluezutils.BluezUtilError as error:
            print(error)
        else:
            try:
                adapter.StartDiscovery()

                import time
                time.sleep(timeout)

                adapter.StopDiscovery()
            except dbus.exceptions.DBusException as error:
                print(error)

        self.scan_thread = None

    def get_devices_to_pair(self):
        devices = self.get_available_devices()

        for key in self.get_paired_devices():
            devices.remove(key)

        return devices

    def get_available_devices(self):
        return self.__get_devices("Available")

    def get_paired_devices(self):
        return self.__get_devices("Paired")

    def get_connected_devices(self):
        return self.__get_devices("Connected")

    def __get_devices(self, condition):
        devices = []

        conditions = ["Available", "Paired", "Connected"]

        if condition not in conditions:
            print("__get_devices: unknown condition - {}".format(condition))
            return devices

        try:
            man = dbus.Interface(
                self.__bus.get_object("org.bluez", "/"),
                "org.freedesktop.DBus.ObjectManager"
            )
            objects = man.GetManagedObjects()

            for path, interfaces in objects.items():
                if "org.bluez.Device1" in interfaces:
                    dev = interfaces["org.bluez.Device1"]

                    if condition == "Available":
                        if "Address" not in dev:
                            continue
                        if "Name" not in dev:
                            dev["Name"] = "<unknown>"

                        device = {
                            "mac_address": dev["Address"].encode("utf-8"),
                            "name": dev["Name"].encode("utf-8")
                        }

                        devices.append(device)
                    else:
                        props = dbus.Interface(
                            self.__bus.get_object("org.bluez", path),
                            "org.freedesktop.DBus.Properties"
                        )

                        if props.Get("org.bluez.Device1", condition):
                            if "Address" not in dev:
                                continue
                            if "Name" not in dev:
                                dev["Name"] = "<unknown>"

                            device = {
                                "mac_address": dev["Address"].encode("utf-8"),
                                "name": dev["Name"].encode("utf-8")
                            }

                            devices.append(device)

        except dbus.exceptions.DBusException as error:
            print(error)

        return devices

    def make_discoverable(self):
        try:
            adapter = bluezutils.find_adapter()
        except bluezutils.BluezUtilError as error:
            print(error)
            return False
        else:
            try:
                props = dbus.Interface(
                    self.__bus.get_object("org.bluez", adapter.object_path),
                    "org.freedesktop.DBus.Properties"
                )

                if not props.Get("org.bluez.Adapter1", "Discoverable"):
                    props.Set("org.bluez.Adapter1", "Discoverable", dbus.Boolean(1))
            except dbus.exceptions.DBusException as error:
                print(error)
                return False

        return True

    def start_pairing(self, address, callback=None, args=None):
        pair_thread = threading.Thread(
            target=self.send_report,
            args=(address, callback, args)
        )
        pair_thread.start()

    def send_report(self, address, callback=None, args=None):
        result = False

        if self.pair(address) and self.trust(address):
            result = True

        if callback is not None:
            callback(result, *args)

    def pair(self, address):
        try:
            device = bluezutils.find_device(address)
        except bluezutils.BluezUtilError as error:
            print(error)
            return False
        else:
            try:
                props = dbus.Interface(
                    self.__bus.get_object("org.bluez", device.object_path),
                    "org.freedesktop.DBus.Properties"
                )

                if not props.Get("org.bluez.Device1", "Paired"):
                    device.Pair()
            except dbus.exceptions.DBusException as error:
                print(error)
                return False

        return True

    def connect(self, address):
        try:
            device = bluezutils.find_device(address)
        except bluezutils.BluezUtilError as error:
            print(error)
            return False
        else:
            try:
                props = dbus.Interface(
                    self.__bus.get_object("org.bluez", device.object_path),
                    "org.freedesktop.DBus.Properties"
                )

                if not props.Get("org.bluez.Device1", "Connected"):
                    device.Connect()
            except dbus.exceptions.DBusException as error:
                print(error)
                return False

        return True

    def disconnect(self, address):
        try:
            device = bluezutils.find_device(address)
        except bluezutils.BluezUtilError as error:
            print(error)
            return False
        else:
            try:
                props = dbus.Interface(
                    self.__bus.get_object("org.bluez", device.object_path),
                    "org.freedesktop.DBus.Properties"
                )

                if props.Get("org.bluez.Device1", "Connected"):
                    device.Disconnect()
            except dbus.exceptions.DBusException as error:
                print(error)
                return False

        return True

    def trust(self, address):
        try:
            device = bluezutils.find_device(address)
        except bluezutils.BluezUtilError as error:
            print(error)
            return False
        else:
            try:
                props = dbus.Interface(
                    self.__bus.get_object("org.bluez", device.object_path),
                    "org.freedesktop.DBus.Properties"
                )

                if not props.Get("org.bluez.Device1", "Trusted"):
                    props.Set("org.bluez.Device1", "Trusted", dbus.Boolean(1))
            except dbus.exceptions.DBusException as error:
                print(error)
                return False

        return True

    def remove(self, address):
        try:
            adapter = bluezutils.find_adapter()
            dev = bluezutils.find_device(address)
        except bluezutils.BluezUtilError as error:
            print(error)
            return False
        else:
            try:
                adapter.RemoveDevice(dev.object_path)
            except dbus.exceptions.DBusException as error:
                print(error)
                return False

        return True
