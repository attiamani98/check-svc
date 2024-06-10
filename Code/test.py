import os 
import re 
import platform 
from http.server import BaseHTTPRequestHandler, HTTPServer
from prometheus_client import start_http_server, Counter, REGISTRY

# Define the counter outside the handler so it can be used globally
request_counter = Counter('http_requests', 'HTTP request', ["status_code", "instance"])

class HTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type','text/html')
            self.end_headers()
            self.wfile.write(bytes("<b> Hello World !</b>", "utf-8"))
            request_counter.labels(status_code='200', instance=platform.node()).inc()
        else:
            self.send_error(404)
            request_counter.labels(status_code='404', instance=platform.node()).inc()

if __name__ == '__main__':
    # Start Prometheus client HTTP server to expose the metrics endpoint
    start_http_server(9000)
    
    # Start the web server
    webServer = HTTPServer(("localhost", 8080), HTTPRequestHandler)
    print("Server started at http://localhost:8080")
    
    try:
        webServer.serve_forever()
    except KeyboardInterrupt:
        pass
    
    webServer.server_close()
    print("Server stopped.")
