from flask import jsonify

class ProblemDetails:
    """
    A structured class for generating error responses in OpenAPI Problem Details format.
    """
    def __init__(self, status: int, title: str, detail: str):
        """
        Initialize a ProblemDetails instance.
        :param status: HTTP status code (e.g., 400, 404, 500)
        :param title: Short description of the error
        :param detail: Detailed error message
        """
        self.status = status
        self.title = title
        self.detail = detail
    def to_dict(self):
        """
        Convert the ProblemDetails object into a dictionary.
        """
        return {
            "title": self.title,
            "status": self.status,
            "detail": self.detail
        }
    def to_json(self):
        """
        Convert the ProblemDetails object into a Flask JSON response.
        """
        return jsonify(self.to_dict()), self.status, {"Content-Type": "application/problem+json"}
