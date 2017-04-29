import signal
from bluetool import BluetoothServer


def handler(signum, frame):
    server.shutdown()


tcp_port = 8100
server = BluetoothServer(tcp_port)

signal.signal(signal.SIGINT, handler)
signal.signal(signal.SIGTERM, handler)

server.run()
