from quotexapi.http.qxbroker import authorize
from quotexapi.http.navigator import Browser

class Login(Browser):

    cookies = None
    ssid = None
    
    def __call__(self, username, password):
        self.ssid, self.cookies = authorize(username, password)
        return self.ssid, self.cookies