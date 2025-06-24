# ==================================================================================
#
#      Copyright (c) 2025 Samsung Electronics Co., Ltd. All Rights Reserved.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#
# ==================================================================================
import pytest
from flask import Flask
import json
import requests
from unittest import mock
from unittest.mock import patch, MagicMock
import pytest
from requests.models import Response
from threading import Lock
import os
import sys
import datetime
from flask_api import status
from dotenv import load_dotenv
load_dotenv('tests/test.env')
from trainingmgr.constants.states import States
from threading import Lock
from trainingmgr.common.tmgr_logger import TMLogger
from trainingmgr.common.trainingmgr_config import TrainingMgrConfig
from trainingmgr.common.exceptions_utls import DBException, TMException
from trainingmgr.models import TrainingJob
from trainingmgr.models import FeatureGroup
from trainingmgr.common.trainingConfig_parser import getField
from io import BytesIO
from trainingmgr.schemas.problemdetail_schema import ProblemDetails

#mock ModelMetricsSdk before importing
mock_modelmetrics_sdk = MagicMock()
sys.modules["trainingmgr.handler.async_handler"] = MagicMock(ModelMetricsSdk=mock_modelmetrics_sdk)
from trainingmgr.controller.pipeline_controller import pipeline_controller
from trainingmgr.service.pipeline_service import get_single_pipeline
from trainingmgr.common.exceptions_utls import TMException

from trainingmgr import trainingmgr_main

trainingmgr_main.LOGGER = pytest.logger
trainingmgr_main.LOCK = Lock()
trainingmgr_main.DATAEXTRACTION_JOBS_CACHE = {}

@pytest.fixture
def app():
    app = Flask(__name__)
    app.register_blueprint(pipeline_controller)  # Register the controller blueprint
    app.config["TESTING"] = True
    return app

@pytest.fixture
def client(app):
    return app.test_client()


class TestGetPipelineInfoByName:
    @patch("trainingmgr.controller.pipeline_controller.get_single_pipeline")
    def test_success(self, mock_get_single_pipeline, client):
        mock_get_single_pipeline.return_value = {"name": "test_pipeline", "version": "1.0"}
        response = client.get("/pipelines/test_pipeline")

        assert response.status_code == 200
        assert response.get_json() == {"pipeline_info": {"name": "test_pipeline", "version": "1.0"}}

    @patch("trainingmgr.controller.pipeline_controller.get_single_pipeline", return_value=None)
    def test_pipeline_not_found(self, mock_get_single_pipeline, client):
        response = client.get("/pipelines/unknown_pipeline")
        assert response.status_code == 404
        expected = ProblemDetails(404, "Not Found", "Pipeline 'unknown_pipeline' not found.").to_dict()
        assert response.get_json() == expected
    
    @patch("trainingmgr.controller.pipeline_controller.get_single_pipeline")
    def test_tm_exception(self, mock_get_single_pipeline, client):
        mock_get_single_pipeline.side_effect = TMException("Pipeline error")
        response = client.get("/pipelines/test_pipeline")
        assert response.status_code == 404
        expected = ProblemDetails(404, "Not Found", "Pipeline error").to_dict()
        assert response.get_json() == expected   
    
    @patch("trainingmgr.controller.pipeline_controller.get_single_pipeline")
    def test_unexpected_exception(self, mock_get_single_pipeline, client):
        mock_get_single_pipeline.side_effect = Exception("Unexpected error")
        response = client.get("/pipelines/test_pipeline")
        assert response.status_code == 500
        expected = ProblemDetails(500, "Internal Server Error", "Error communicating with KFAdapter : Unexpected error").to_dict()
        assert response.get_json() == expected

    @patch("trainingmgr.controller.pipeline_controller.get_single_pipeline", return_value={"name": "demo_pipeline", "version": "v1"})
    def test_pipeline_info_structure(self, mock_get_pipeline_info, client):
        response = client.get("/pipelines/demo_pipeline")
        assert response.status_code == 200
        assert "pipeline_info" in response.get_json()
        assert response.get_json()["pipeline_info"]["name"] == "demo_pipeline"

    @patch("trainingmgr.controller.pipeline_controller.get_single_pipeline")
    def test_large_pipeline_info(self, mock_get_pipeline_info, client):
        mock_data = {
            "name": "demo_pipeline",
            "description": "x" * 5000,
            "metadata": {"step": i for i in range(100)}
        }
        mock_get_pipeline_info.return_value = mock_data
        response = client.get("/pipelines/demo_pipeline")
        assert response.status_code == 200
        assert response.get_json()["pipeline_info"]["name"] == "demo_pipeline"