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

import socket
import select
import multiprocessing
import dbus
import dbus.service
import dbus.mainloop.glib
try:
  from gi.repository import GObject
except ImportError:
  import gobject as GObject
from bluetool import Bluetooth

class SerialPort(object):

    profile_path = "/org/bluez/myprofile"

    def __init__(self, channel=1):
        dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
        self.bus = dbus.SystemBus()
        self.uuid = "1101"
        self.opts = {
            "Name": "Reach SPP",
            "Channel": dbus.UInt16(channel),
            "AutoConnect": False
        }
        self.manager = dbus.Interface(self.bus.get_object("org.bluez",
                "/org/bluez"), "org.bluez.ProfileManager1")

    def initialize(self):
        try:
            self.manager.RegisterProfile(self.profile_path, self.uuid, self.opts)
        except dbus.exceptions.DBusException as error:
            print error
            return False

        return True
    
    def deinitialize(self):
        try:    
            self.manager.UnregisterProfile(self.profile_path)
        except dbus.exceptions.DBusException:
            pass

class TCPConnectionError(Exception):
    pass

class TCPServerError(Exception):
    pass

class TCPServer(object):  

    def __init__(self, tcp_port, buffer_size=1024):
        self.server_socket = None
        self.client_socket = None
        self.address = ("localhost", tcp_port)
        self.buffer_size = buffer_size

    def initialize(self):
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind(self.address)
            self.server_socket.listen(5)
        except socket.error as error:
            print error
            return False

        return True

    def accept_connection(self):
        self.client_socket, client_info = self.server_socket.accept() 
        return client_info

    def kill_connection(self):
        self.client_socket.close()
        self.server_socket.close()

    def read(self):
        return self.client_socket.recv(self.buffer_size)

    def write(self, data):
        return self.client_socket.send(data)

class BluetoothServer(dbus.service.Object):

    def __init__(self, tcp_port=8043, channel=1,
            tcp_buffer_size=1024, blue_buffer_size=1024):
        self.spp = SerialPort(channel)
        dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
        dbus.service.Object.__init__(self, dbus.SystemBus(), self.spp.profile_path)
        self.tcp_port = tcp_port
        self.tcp_buffer_size = tcp_buffer_size
        self.blue_buffer_size = blue_buffer_size
        self.server_process = None
        self.mainloop = GObject.MainLoop()

    def run(self):
        if not self.spp.initialize():
            return
        self.mainloop.run()

    def run_in_background(self):
        if not self.spp.initialize():
            return False
        
        if self.server_process is None:
            self.server_process = multiprocessing.Process(target=self.mainloop.run)
            self.server_process.start()
        
        return True

    def quit(self):
        self.mainloop.quit()

        if self.server_process is not None:
            self.server_process.terminate()
            self.server_process.join()
            self.server_process = None
        
        self.spp.deinitialize()

    @dbus.service.method("org.bluez.Profile1",
                in_signature="oha{sv}", out_signature="")
    def NewConnection(self, path, fd, properties):
        address = str(path)
        address = address[len(address)-17:len(address)]
        address = address.replace("_", ":")

        print "Connected:", address

        try:
            tcp_server = TCPServer(self.tcp_port, self.tcp_buffer_size)
            if not tcp_server.initialize():
                raise TCPServerError("TCP server did not start")
            
            print "Waiting for TCPClient..."
            print "Connected:", tcp_server.accept_connection()

            blue_socket = socket.fromfd(fd.take(), socket.AF_UNIX, socket.SOCK_STREAM)
            blue_socket.setblocking(1)
            
            try:
                while True:
                    read, write, error = select.select([tcp_server.client_socket,
                            blue_socket], [], [])

                    for sock in read:
                        if sock == tcp_server.client_socket:
                            data = tcp_server.read()
                            if not data:
                                raise TCPConnectionError("External connection shutdown")
                            blue_socket.send(data)

                        if sock == blue_socket:
                            data = blue_socket.recv(self.blue_buffer_size)
                            if data:
                                tcp_server.write(data)
            except IOError as error:
                print error
            except TCPConnectionError as error:
                print error

            blue_socket.close()
            tcp_server.kill_connection()
        except TCPServerError as error:
            print error

        bluetooth = Bluetooth()
        bluetooth.disconnect(address)
