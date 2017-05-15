import signal
from bluetool.agent import Client, AgentSvr


class MyClient(Client):

    def request_pin_code(self, dev_info):
        print(dev_info)
        return raw_input("Input pin code:")

    def request_passkey(self, dev_info):
        print(dev_info)
        return raw_input("Input passkey:")

    def request_confirmation(self, dev_info, *args):
        print(dev_info, args)
        return raw_input("Input 'yes' to accept request:") == "yes"

    def request_authorization(self, dev_info):
        print(dev_info)
        return raw_input("Input 'yes' to accept request:") == "yes"


def handler(signum, frame):
    svr.shutdown()


svr = AgentSvr(client_class=MyClient)

signal.signal(signal.SIGINT, handler)
signal.signal(signal.SIGTERM, handler)

svr.run()
