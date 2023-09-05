import socketserver
from models.mikrotik import MikrotikRouter


class SyslogUDPHandler(socketserver.BaseRequestHandler):
    def handle(self):
        data = bytes.decode(self.request[0].strip())
        print("%s : " % self.client_address[0], str(data))
        router = MikrotikRouter.get(host=self.client_address[0])
        if router:
            router.add_log(str(data))


server = socketserver.UDPServer(('0.0.0.0', 514), SyslogUDPHandler)
server.serve_forever(poll_interval=0.5)
