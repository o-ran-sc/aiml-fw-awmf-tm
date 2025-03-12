import json
import pytest
from flask import Flask
from trainingmgr.schemas.problemdetail_schema import ProblemDetails

@pytest.fixture
def test_app():
    """
    Creates a Flask test app context for testing ProblemDetails JSON response.
    """
    app = Flask(__name__)
    app.config['TESTING'] = True
    return app.test_client()
def test_problem_details_initialization():
    """
    Test that ProblemDetails initializes correctly with provided values.
    """
    problem = ProblemDetails(400, "Bad Request", "Invalid input data")
    assert problem.status == 400
    assert problem.title == "Bad Request"
    assert problem.detail == "Invalid input data"

def test_problem_details_to_dict():
    """
    Test that ProblemDetails generates the correct dictionary representation.
    """
    problem = ProblemDetails(404, "Not Found", "The requested resource does not exist.")
    expected_dict = {
        "title": "Not Found",
        "status": 404,
        "detail": "The requested resource does not exist."
    }
    assert problem.to_dict() == expected_dict

def test_problem_details_to_json(test_app):
    """
    Test that ProblemDetails generates the correct Flask JSON response.
    """
    problem = ProblemDetails(500, "Internal Server Error", "Something went wrong")
    with Flask(__name__).test_request_context():
        response, status, headers = problem.to_json()
    assert status == 500
    assert headers["Content-Type"] == "application/problem+json"
    # Convert response data to JSON and compare
    response_data = json.loads(response.get_data(as_text=True))
    expected_json = {
        "title": "Internal Server Error",
        "status": 500,
        "detail": "Something went wrong"
    }
    assert response_data == expected_json

