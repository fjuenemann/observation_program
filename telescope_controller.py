import http.client

class TelescopeController(object):
    
    def __init__(self, address, port):
        
        self.ip = address
        self.port = port

    def connection(self):
        return http.client.HTTPConnection(self.ip, self.port)
    
    def get_response(self):
        conn = connection(self)
        response = conn.getresponse()
        print(response.status, response.reason)
        time.sleep(1.)
        return response.read()
    
    def initiate(self):
        conn = self.connection()
        get_cmd_authority = "{\"path\":\"acu.command_arbiter.authority\",\"params\":{\"action\":\"1\"}}"
        conn.request("PUT", "/devices/command", get_cmd_authority)
