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
# from flask_api import status
from http import HTTPStatus as status
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

    @patch("trainingmgr.controller.pipeline_controller.get_single_pipeline", return_value = None)
    def test_pipeline_not_found(self, mock_get_single_pipeline, client):
        response = client.get("/pipelines/unknown_pipeline")

        assert response.status_code == 404
        assert response.get_json() == {"error": "Pipeline 'unknown_pipeline' not found"}

    @patch("trainingmgr.controller.pipeline_controller.get_single_pipeline")
    def test_tm_exception(self, mock_get_single_pipeline, client):
        mock_get_single_pipeline.side_effect = TMException("Pipeline error")

        response = client.get("/pipelines/test_pipeline")
        assert response.status_code == 404
        assert response.get_json() == {"error": "Pipeline error"}

    @patch("trainingmgr.controller.pipeline_controller.get_single_pipeline")
    def test_unexpected_exception(self, mock_get_single_pipeline, client):
        mock_get_single_pipeline.side_effect = Exception("Unexpected error")
        response = client.get("/pipelines/test_pipeline")

        assert response.status_code == 500
        assert response.get_json() == {"error": "An unexpected error occurred"}

# ---------------------------
# Test: get_versions_for_pipeline
# ---------------------------
class TestGetVersionsForPipeline:
    @patch("trainingmgr.controller.pipeline_controller.get_all_pipeline_versions")
    def test_success(self, mock_versions, client):
        mock_versions.return_value = ["v1", "v2"]
        resp = client.get("/pipelines/test/versions")
        assert resp.status_code == 200
        assert resp.get_json() == ["v1", "v2"]

    @patch("trainingmgr.controller.pipeline_controller.get_all_pipeline_versions", return_value=None)
    def test_not_found(self, mock_versions, client):
        resp = client.get("/pipelines/unknown/versions")
        assert resp.status_code == 404


# ---------------------------
# Test: get_pipelines
# ---------------------------
class TestGetPipelines:
    @patch("trainingmgr.controller.pipeline_controller.get_all_pipelines")
    def test_success(self, mock_pipelines, client):
        mock_pipelines.return_value = ["pipeline1", "pipeline2"]
        resp = client.get("/pipelines")
        assert resp.status_code == 200
        assert resp.get_json() == ["pipeline1", "pipeline2"]


# ---------------------------
# Test: upload_pipeline
# ---------------------------
class TestUploadPipeline:
    @patch("trainingmgr.controller.pipeline_controller.upload_pipeline_service")
    def test_success(self, mock_upload, client):
        data = {"file": (BytesIO(b"fake content"), "test.py")}
        resp = client.post("/pipelines/test/upload", data=data, content_type="multipart/form-data")
        assert resp.status_code == 200
        assert "Pipeline uploaded test Sucessfully!" in resp.get_json()["result"]

    def test_invalid_name(self, client):
        resp = client.post("/pipelines/invalid!name/upload", data={})
        assert resp.status_code == 500
        assert "not correct" in resp.get_json()["result"]

    def test_no_file(self, client):
        resp = client.post("/pipelines/test/upload", data={}, content_type="multipart/form-data")
        assert resp.status_code == 500
        assert "File not found" in resp.get_json()["result"]

    def test_empty_filename(self, client):
        data = {"file": (BytesIO(b""), "")}
        resp = client.post("/pipelines/test/upload", data=data, content_type="multipart/form-data")
        assert resp.status_code == 500
        assert "Filename is not found" in resp.get_json()["result"]

    @patch("trainingmgr.controller.pipeline_controller.upload_pipeline_service")
    def test_tm_exception(self, mock_upload, client):
        mock_upload.side_effect = TMException("Upload failed")
        data = {"file": (BytesIO(b"fake content"), "test.py")}
        resp = client.post("/pipelines/test/upload", data=data, content_type="multipart/form-data")
        assert resp.status_code == 500
        assert "Upload failed" in resp.get_json()["result"]


# ---------------------------
# Test: get_all_experiment_names
# ---------------------------
class TestGetAllExperimentNames:
    @patch("trainingmgr.controller.pipeline_controller.list_experiments_service")
    def test_success(self, mock_experiments, client):
        mock_experiments.return_value = ["exp1", "exp2"]
        resp = client.get("/pipelines/experiments")
        assert resp.status_code == 200
        assert resp.get_json() == ["exp1", "exp2"]

    @patch("trainingmgr.controller.pipeline_controller.list_experiments_service")
    def test_exception(self, mock_experiments, client):
        mock_experiments.side_effect = Exception("DB error")
        resp = client.get("/pipelines/experiments")
        assert resp.status_code == 500
        assert "DB error" in resp.get_json()["Exception"]