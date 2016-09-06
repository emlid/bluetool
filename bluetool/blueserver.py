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

import socket
import select
import subprocess
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
        #subprocess.check_output("rfkill unblock bluetooth", shell=True)
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
            return False
        
        self.server_process = multiprocessing.Process(target=self.mainloop.run)
        self.server_process.start()
        
        return True

    def quit(self):
        if self.server_process is not None:
            self.mainloop.quit()
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

