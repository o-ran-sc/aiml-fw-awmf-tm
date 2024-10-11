import time
from werkzeug.wrappers import Request, Response

class LoggingMiddleware:
    def __init__(self, app):
        self.app = app
    
    def __call__(self, environ, start_response):
        request = Request(environ)

        request_start_time = time.time()
        response = self.app(environ, start_response)
        request_end_time = time.time()
        request_time_taken = request_end_time - request_start_time

        print(f"=(TM)=> Request: {request.method} {request.url} - Time Taken: {request_time_taken:.4f} seconds")
        return response

