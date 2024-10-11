# ==================================================================================
#
#       Copyright (c) 2024 Samsung Electronics Co., Ltd. All Rights Reserved.
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#          http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
# ==================================================================================
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

