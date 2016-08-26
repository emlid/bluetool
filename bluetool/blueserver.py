import socket
import subprocess
import multiprocessing
import dbus
import dbus.service
import dbus.mainloop.glib
try:
  from gi.repository import GObject
except ImportError:
  import gobject as GObject

class SerialPort(object):

    profile_path = "/org/bluez/myprofile"

    def __init__(self, channel=1):
        subprocess.check_output("rfkill unblock bluetooth", shell=True)
        dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
        self.bus = dbus.SystemBus()
        self.uuid = "1101"
        self.opts = {
            "Name": "Reach SPP",
            "Channel": dbus.UInt16(channel),
            "AutoConnect": False
        }

    def initialize(self):
        try:
            manager = dbus.Interface(self.bus.get_object("org.bluez",
                    "/org/bluez"), "org.bluez.ProfileManager1")
            manager.RegisterProfile(self.profile_path, self.uuid, self.opts)
        except dbus.exceptions.DBusException as error:
            print error
            return False

        return True

class TCPConnectionError(Exception):
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

    def __init__(self, tcp_port=8043, channel=1):
        self.spp = SerialPort(channel)
        dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
        dbus.service.Object.__init__(self, dbus.SystemBus(), self.spp.profile_path)
        self.tcp_server = TCPServer(tcp_port)
        self.server_process = None
        self.mainloop = GObject.MainLoop()

    def run(self):
        if not self.spp.initialize():
            return False
        
        if not self.tcp_server.initialize():
            return False
        print "Waiting for TCPClient..."
        print "Connected:", self.tcp_server.accept_connection()
        
        self.server_process = multiprocessing.Process(target=self.mainloop.run)
        self.server_process.start()
        
        return True

    def quit(self):
        self.tcp_server.kill_connection()
        
        if self.server_process is not None:
            self.mainloop.quit()
            self.server_process.terminate()
            self.server_process.join()
            self.server_process = None

    @dbus.service.method("org.bluez.Profile1",
                in_signature="oha{sv}", out_signature="")
    def NewConnection(self, path, fd, properties):
        print "Connected:", path
        
        server_sock = socket.fromfd(fd.take(), socket.AF_UNIX, socket.SOCK_STREAM)
        server_sock.setblocking(1)
        
        try:
            while True:                
                data = self.tcp_server.read()    
                if not data:
                    raise TCPConnectionError("External connection shutdown")
                server_sock.send(data)
        except IOError as error:
            print "Abort connection:", error
            server_sock.close()
        except TCPConnectionError as error:
            self.tcp_server.kill_connection()
            self.tcp_server.initialize()
            server_sock.close()
            print "Waiting for TCPClient..."
            print "Connected:", self.tcp_server.accept_connection()
        else:
            server_sock.close()


