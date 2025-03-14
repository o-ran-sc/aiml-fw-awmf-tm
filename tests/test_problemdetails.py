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

