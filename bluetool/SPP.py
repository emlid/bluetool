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

profile_path = "/org/bluez/myprofile"
dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
bus = dbus.SystemBus()

class SerialPort(object):

    def __init__(self, channel=1):
        subprocess.check_output("rfkill unblock bluetooth", shell = True)
        
        self.mainloop = GObject.MainLoop()
        self.uuid = "1101" #serial port
        self.opts = {
            "Name": "Reach SPP",
            "Channel": dbus.UInt16(channel),
            "AutoConnect": False
        }

        self.spp_process = None

    def init(self):
        try:
            manager = dbus.Interface(bus.get_object("org.bluez",
                    "/org/bluez"), "org.bluez.ProfileManager1")
            manager.RegisterProfile(profile_path, self.uuid, self.opts)
        except dbus.exceptions.DBusException as error:
            print error
            return False

        return True

    def run(self):
        self.spp_process = multiprocessing.Process(target = self.mainloop.run)
        self.spp_process.start()

    def quit(self):
        if self.spp_process is not None:
            self.spp_process.terminate()
            self.spp_process.join()
            self.spp_process = None

class TCPConnectionError(Exception):
    pass

class TCPServer():
    """A wrapper around TCP server."""

    def __init__(self, tcp_port, buffer_size=1024):
        self.server_socket = None
        self.client_socket = None
        self.address = ("localhost", tcp_port)
        self.buffer_size = buffer_size

    def initialize(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind(self.address)
        self.server_socket.listen(5)

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

class BlueServer(dbus.service.Object):

    event = multiprocessing.Event()

    def __init__(self, tcp_port=8043, channel=1):
        self.spp = SerialPort(channel)
        dbus.service.Object.__init__(self, bus, profile_path)
        self.spp.init()
        self.tcp_server = TCPServer(tcp_port)

    def start(self):
        #self.spp.run()
        self.tcp_server.initialize()
        print "Waiting for TCPClient..."
        print "Connected:", self.tcp_server.accept_connection()

    def stop(self):
        self.spp.quit()

    @dbus.service.method("org.bluez.Profile1",
                in_signature="oha{sv}", out_signature="")
    def NewConnection(self, path, fd, properties):
        print "Connected:", path
        fd = fd.take()
        server_sock = socket.fromfd(fd, socket.AF_UNIX, socket.SOCK_STREAM)
        server_sock.setblocking(1)
        
        try:
            while True:                
                out = self.tcp_server.read()    

                server_sock.send(out)
                break
        except IOError:
            pass

        server_sock.close()
        print("all done")

