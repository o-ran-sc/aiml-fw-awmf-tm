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

    @patch('trainingmgr.schemas.featuregroup_schema.FeatureGroupSchema.load', side_effect=DBException("feature group already exist"))
    def test_conflict_error(self, mock_load, client):
        response = client.post("/featureGroup", json={})
        assert response.status_code == 409
        expected = ProblemDetails(409, "Conflict", "feature group already exist").to_dict()
        assert response.get_json() == expected

    @patch('trainingmgr.schemas.featuregroup_schema.FeatureGroupSchema.load', side_effect=DBException("some DB error"))
    def test_db_exception(self, mock_load, client):
        response = client.post("/featureGroup", json={})
        assert response.status_code == 400
        expected = ProblemDetails(400, "Bad Request", "some DB error").to_dict()
        assert response.get_json() == expected

    @patch('trainingmgr.schemas.featuregroup_schema.FeatureGroupSchema.load', side_effect=Exception("unexpected fail"))
    def test_generic_exception(self, mock_load, client):
        response = client.post("/featureGroup", json={})
        assert response.status_code == 500
        expected = ProblemDetails(500, "Internal Server Error", "unexpected fail").to_dict()
        assert response.get_json() == expected
        
class TestGetFeatureGroup:

    @patch('trainingmgr.service.featuregroup_service.get_all_featuregroups', side_effect=Exception("DB fail"))
    def test_get_failure(self, mock_get, client):
        response = client.get("/featureGroup")
        assert response.status_code == 500
        expected = ProblemDetails(500, "Internal Server Error", "Failed to get featuregroups").to_dict()
        assert response.get_json() == expected