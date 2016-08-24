import socket
import subprocess
import dbus
import dbus.service
import dbus.mainloop.glib
try:
  from gi.repository import GObject
except ImportError:
  import gobject as GObject

class SerialPort(dbus.service.Object):

    def __init__(self, channel=1):
        subprocess.check_output("rfkill unblock bluetooth", shell = True)
        
        dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
        self.__bus = dbus.SystemBus()
        self.mainloop = GObject.MainLoop()
        self.path="/org/bluez/myprofile"
        self.uuid = "1101" #serial port
        self.opts = {
            "Name": "Reach SPP",
            "Channel": dbus.UInt16(channel),
            "AutoConnect": False
        }

        dbus.service.Object.__init__(self, self.__bus, self.path)

    def init(self):
        try:
            manager = dbus.Interface(self.__bus.get_object("org.bluez",
                    "/org/bluez"), "org.bluez.ProfileManager1")
            manager.RegisterProfile(self.path, self.uuid, self.opts)
        except dbus.exceptions.DBusException as error:
            print error
            return False

        return True

    def run(self):
        self.mainloop.run()

    @dbus.service.method("org.bluez.Profile1",
                in_signature="oha{sv}", out_signature="")
    def NewConnection(self, path, fd, properties):
        self.fd = fd.take()
        print("NewConnection(%s, %d)" % (path, self.fd))

        server_sock = socket.fromfd(self.fd, socket.AF_UNIX, socket.SOCK_STREAM)
        server_sock.setblocking(1)
        server_sock.send("This is Edison SPP loopback test\nAll data will be loopback\nPlease start:\n")

        try:
            while True:
                data = server_sock.recv(1024)
                print("received: %s" % data)
                server_sock.send("looping back: %s\n" % data)
        except IOError:
            pass

        server_sock.close()
        print("all done")

