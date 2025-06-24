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