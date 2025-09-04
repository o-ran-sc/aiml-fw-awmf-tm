# ==================================================================================
#
#       Copyright (c) 2025 Minje Kim <alswp006@gmail.com> All Rights Reserved.
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
from flask import Blueprint, request, jsonify

agent_controller = Blueprint("agent_controller", __name__)

@agent_controller.route("/modelInfo", methods=["GET"])
def model_info():
    return jsonify({
        "llm": {
            "model": ""
        }
    }), 200

@agent_controller.route("/generate-content", methods=["POST"])
def generate_content():
    body = request.get_json(silent=True) or {}
    text = body.get("text")
    if not isinstance(text, str) or not text.strip():
        return jsonify({
            "title": "Bad Request",
            "status": 400,
            "detail": "The 'text' field is required and must be a non-empty string."
        }), 400
    dry_run = bool(body.get("dry_run", True))
    return jsonify({
        "action": "noop",
        "request": {"text": text, "dry_run": dry_run},
        "response": {"note": "Received successfully"},
        "status": "ok",
        "error_message": None
    }), 200