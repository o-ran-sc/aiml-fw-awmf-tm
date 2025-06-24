# ==================================================================================
#
#      Copyright (c) 2024 Samsung Electronics Co., Ltd. All Rights Reserved.
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
from trainingmgr.schemas.problemdetail_schema import ProblemDetails
from trainingmgr.common.trainingConfig_parser import getField

#mock ModelMetricsSdk before importing
mock_modelmetrics_sdk = MagicMock()
sys.modules["trainingmgr.handler.async_handler"] = MagicMock(ModelMetricsSdk=mock_modelmetrics_sdk)
from trainingmgr.controller.trainingjob_controller import training_job_controller
from trainingmgr import trainingmgr_main

trainingmgr_main.LOGGER = pytest.logger
trainingmgr_main.LOCK = Lock()
trainingmgr_main.DATAEXTRACTION_JOBS_CACHE = {}


# =======================
# Test: Create Training Job
# =======================
class TestCreateTrainingJob:
    def setup_method(self):
        app = Flask(__name__)
        app.register_blueprint(training_job_controller)
        self.client = app.test_client()

    def test_create_trainingjob_missing_training_config(self):
        trainingmgr_main.LOGGER.debug("******* test_create_trainingjob_missing_training_config *******")
        expected_data = {
            "title": "Bad Request",
            "status": 400,
            "detail": "The 'training_config' field is missing."
        }
        trainingjob_req = {
            "modelId": {
                "modelname": "modeltest",
                "modelversion": "1"
            }
        }
        response = self.client.post("/training-jobs", data=json.dumps(trainingjob_req),
                                    content_type="application/json")
        assert response.status_code == 400
        assert response.json == expected_data

    def test_create_trainingjob_invalid_training_config(self):
        trainingmgr_main.LOGGER.debug("******* test_create_trainingjob_invalid_training_config *******")
        expected_data = {
            "title": "Bad Request",
            "status": 400,
            "detail": "The provided 'training_config' is not valid."
        }
        trainingjob_req = {
            "modelId": {
                "modelname": "modeltest",
                "modelversion": "1"
            },
            "training_config": {
                "description": "training job for testing"
            }
        }
        response = self.client.post("/training-jobs", data=json.dumps(trainingjob_req),
                                    content_type="application/json")
        assert response.status_code == 400
        assert response.json == expected_data

    @patch('trainingmgr.controller.trainingjob_controller.get_modelinfo_by_modelId_service', return_value=None)
    def test_create_trainingjob_model_not_registered(self, mock1):
        trainingmgr_main.LOGGER.debug("******* test_create_trainingjob_model_not_registered *******")
        expected_data = {
            "title": "Bad Request",
            "status": 400,
            "detail": "Model 'test_model' version '1' is not registered at MME. Please register at MME first."
        }
        trainingjob_req = {
            "modelId": {
                "modelname": "test_model",
                "modelversion": "1"
            },
            "model_location": "",
            "training_config": {
                "description": "trainingjob for testing",
                "dataPipeline": {
                    "feature_group_name": "testing_influxdb_03",
                    "query_filter": "",
                    "arguments": {"epochs": 10}
                },
                "trainingPipeline": {
                    "training_pipeline_name": "qoe_Pipeline",
                    "training_pipeline_version": "qoe_Pipeline",
                    "retraining_pipeline_name": "qoe_Pipeline_retrain",
                    "retraining_pipeline_version": "qoe_Pipeline_retrain"
                }
            }
        }
        response = self.client.post("/training-jobs", data=json.dumps(trainingjob_req),
                                    content_type="application/json")
        assert response.status_code == 400
        assert response.json == expected_data
    registered_model_list = [{"modelLocation": "s3://different-location"}]

    @patch('trainingmgr.controller.trainingjob_controller.get_modelinfo_by_modelId_service', return_value=registered_model_list)
    def test_create_trainingjob_model_location_mismatch(self, mock1):
        expected_data = {
            "title": "Bad Request",
            "status": 400,
            "detail": "Model 'test_model' version '1' does not match the registered model location."
        }
        trainingjob_req = {
            "modelId": {
                "modelname": "test_model",
                "modelversion": "1"
            },
            "model_location": "",
            "training_config": {
                "description": "trainingjob for testing",
                "dataPipeline": {
                    "feature_group_name": "testing_influxdb_03",
                    "query_filter": "",
                    "arguments": {"epochs": 10}
                },
                "trainingPipeline": {
                    "training_pipeline_name": "qoe_Pipeline",
                    "training_pipeline_version": "qoe_Pipeline",
                    "retraining_pipeline_name": "qoe_Pipeline_retrain",
                    "retraining_pipeline_version": "qoe_Pipeline_retrain"
                }
            }
        }
        response = self.client.post("/training-jobs", data=json.dumps(trainingjob_req),
                                    content_type="application/json")
        assert response.status_code == 400
        assert response.json == expected_data
# =======================
# Test: Delete Training Job
# =======================
class TestDeleteTrainingJob:
    def setup_method(self):
        app = Flask(__name__)
        app.register_blueprint(training_job_controller)
        self.client = app.test_client()
    @patch('trainingmgr.controller.trainingjob_controller.delete_training_job', return_value=True)
    def test_delete_trainingjob_success(self, mock1):
        response = self.client.delete("/training-jobs/123")
        assert response.status_code == 204
        assert response.data == b''
    @patch('trainingmgr.controller.trainingjob_controller.delete_training_job', return_value=False)
    def test_delete_trainingjob_not_found(self, mock1):
        expected_data = {
            "title": "Not Found",
            "status": 404,
            "detail": "Training job with ID 123 does not exist."
        }
        response = self.client.delete("/training-jobs/123")
        assert response.status_code == 404
        assert response.json == expected_data

# =======================
# Test: Get Training Jobs (All / Filtered / Latest)
# =======================
class TestGetFilteredTrainingJobs:
    def setup_method(self):
        app = Flask(__name__)
        app.register_blueprint(training_job_controller)
        self.client = app.test_client()
    @patch('trainingmgr.controller.trainingjob_controller.get_trainining_jobs')
    @patch('trainingmgr.controller.trainingjob_controller.trainingjobs_schema.dump')
    def test_success_all_jobs(self, mock_dump, mock_get):
        mock_get.return_value = [
            MagicMock(id=1, modelId=MagicMock(modelname='abc', modelversion='1')),
            MagicMock(id=2, modelId=MagicMock(modelname='xyz', modelversion='2'))
        ]
        mock_dump.return_value = [
            {"id": 1, "modelId": {"modelname": "abc", "modelversion": "1"}},
            {"id": 2, "modelId": {"modelname": "xyz", "modelversion": "2"}}
        ]
        response = self.client.get("/training-jobs")
        assert response.status_code == 200
        assert len(response.json) == 2

    @patch('trainingmgr.controller.trainingjob_controller.get_trainining_jobs')
    @patch('trainingmgr.controller.trainingjob_controller.trainingjobs_schema.dump')
    def test_success_with_filters(self, mock_dump, mock_get):
        mock_get.return_value = [
            MagicMock(id=1, modelId=MagicMock(modelname='abc', modelversion='1')),
            MagicMock(id=2, modelId=MagicMock(modelname='abc', modelversion='1')),
            MagicMock(id=3, modelId=MagicMock(modelname='xyz', modelversion='2'))
        ]
        mock_dump.return_value = [
            {"id": 1, "modelId": {"modelname": "abc", "modelversion": "1"}},
            {"id": 2, "modelId": {"modelname": "abc", "modelversion": "1"}}
        ]
        response = self.client.get("/training-jobs?model_name=abc&model_version=1")
        assert response.status_code == 200
        assert all(job["modelId"]["modelname"] == "abc" and job["modelId"]["modelversion"] == "1" for job in response.json)

    @patch('trainingmgr.controller.trainingjob_controller.get_trainining_jobs')
    @patch('trainingmgr.controller.trainingjob_controller.trainingjobs_schema.dump')
    def test_success_latest(self, mock_dump, mock_get):
        job1 = MagicMock(id=1, modelId=MagicMock(modelname='abc', modelversion='1'))
        job2 = MagicMock(id=3, modelId=MagicMock(modelname='abc', modelversion='1'))
        job3 = MagicMock(id=2, modelId=MagicMock(modelname='abc', modelversion='1'))
        mock_get.return_value = [job1, job2, job3]
        mock_dump.return_value = [{"id": 3, "modelId": {"modelname": "abc", "modelversion": "1"}}]
        response = self.client.get("/training-jobs?model_name=abc&model_version=1&latest=true")
        assert response.status_code == 200
        assert response.json[0]['id'] == 3
    @patch('trainingmgr.controller.trainingjob_controller.get_trainining_jobs', side_effect=Exception("Generic error"))
    def test_internal_error(self, mock_get):
        response = self.client.get("/training-jobs?model_name=abc&model_version=1")
        assert response.status_code == 500
        assert response.json["title"] == "Internal Server Error"

# =======================
# Test: Get Training Job by ID
# =======================
class TestGetTrainingJob:
    def setup_method(self):
        app = Flask(__name__)
        app.register_blueprint(training_job_controller)
        self.client = app.test_client()
    @patch('trainingmgr.controller.trainingjob_controller.get_training_job', return_value={"id": 1, "name": "Test Job"})
    @patch('trainingmgr.controller.trainingjob_controller.trainingjob_schema.dump', return_value={"id": 1, "name": "Test Job"})
    def test_get_trainingjob_success(self, mock_schema_dump, mock_get_training_job):
        response = self.client.get('/training-jobs/1')
        assert response.status_code == 200
        assert response.json == {"id": 1, "name": "Test Job"}
    @patch('trainingmgr.controller.trainingjob_controller.get_training_job')
    def test_get_trainingjob_generic_exception(self, mock_get_training_job):
        mock_get_training_job.side_effect = Exception('Unexpected error')
        expected_data = {
            "title": "Internal Server Error",
            "status": 500,
            "detail": "Unexpected error"
        }
        response = self.client.get('/training-jobs/1')
        assert response.status_code == 500
        assert response.json == expected_data
