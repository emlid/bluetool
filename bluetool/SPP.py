import socket
import dbus
import dbus.service
import dbus.mainloop.glib
try:
  from gi.repository import GObject
except ImportError:
  import gobject as GObject

class Profile(dbus.service.Object):

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


if __name__ == '__main__':

    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)

    bus = dbus.SystemBus()

    manager = dbus.Interface(bus.get_object("org.bluez",
				"/org/bluez"), "org.bluez.ProfileManager1")

    uuid = "1101"
    path = "/org/bluez/myprofile"

    profile = Profile(bus, path)

    mainloop = GObject.MainLoop()

    opts = {
        "Name": "Reach SPP",
        "Channel": dbus.UInt16(1),
        "AutoConnect": False
    }

    manager.RegisterProfile(path, uuid, opts)

    try:
        mainloop.run()
    except KeyboardInterrupt:
        pass
    
    mainloop.quit()

    manager.UnregisterProfile(path)



