import pytest
from flask import Flask
from unittest.mock import patch
from requests.models import Response
from threading import Lock
import os
import sys
import datetime
from io import BytesIO
from flask_api import status
from dotenv import load_dotenv
load_dotenv('tests/test.env')
from trainingmgr.constants.states import States
from threading import Lock
from trainingmgr.controller.featuregroup_controller import featuregroup_controller
from trainingmgr.common.exceptions_utls import DBException, TMException
from trainingmgr.common.trainingmgr_config import TrainingMgrConfig
from marshmallow import ValidationError
from trainingmgr.schemas.problemdetail_schema import ProblemDetails
from types import SimpleNamespace
from trainingmgr import trainingmgr_main
from trainingmgr.common.tmgr_logger import TMLogger

trainingmgr_main.LOGGER = pytest.logger

@pytest.fixture
def client():
    app = Flask(__name__)
    app.register_blueprint(featuregroup_controller)
    app.config['TESTING'] = True
    return app.test_client()

class TestCreateFeatureGroup:

    @patch('trainingmgr.schemas.featuregroup_schema.FeatureGroupSchema.load')
    def test_invalid_featuregroup_name(self, mock_load, client):
        mock_load.return_value = type("FeatureGroup", (), {"featuregroup_name": "xy", "enable_dme": False})
        response = client.post("/featureGroup", json={})
        assert response.status_code == 400
        expected = ProblemDetails(400, "Bad Request", "Failed to create the feature group since feature group not valid").to_dict()
        assert response.get_json() == expected

    @patch('trainingmgr.schemas.featuregroup_schema.FeatureGroupSchema.load', side_effect=ValidationError("Invalid format"))
    def test_validation_error(self, mock_load, client):
        response = client.post("/featureGroup", json={})
        assert response.status_code == 400
        expected = ProblemDetails(400, "Validation Error", "Invalid format").to_dict()
        assert response.get_json() == expected
