from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
from SocketServer import ThreadingMixIn
import threading
import time
import urlparse

secret = 1

class Handler(BaseHTTPRequestHandler):
    
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        message =  threading.currentThread().getName()
        
        qs = {}
        path = self.path
        if '?' in path:
            path, tmp = path.split('?', 1)
            qs = urlparse.parse_qs(tmp)
        print path, qs
        
        if 'secret' in qs.keys() :
            global secret
            print('new secret: ' + str(qs['secret'][0]))
            secret = int(qs['secret'][0])
        
        self.wfile.write(message)
        self.wfile.write('\n')
        return

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Handle requests in a separate thread."""

class WebserverBackground(threading.Thread):   
   def run(self):
      server = ThreadedHTTPServer(('localhost', 8080), Handler)
      server.serve_forever()

if __name__ == '__main__':
    thread = WebserverBackground()
    thread.daemon = True
    thread.start()
    
    while True :
        print("time passes... secret is: " + str(secret))
        time.sleep(5)