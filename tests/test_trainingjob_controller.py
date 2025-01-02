# ==================================================================================
#
#      Copyright (c) 2022 Samsung Electronics Co., Ltd. All Rights Reserved.
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
from trainingmgr import trainingmgr_main

#mock ModelMetricsSdk before importing
mock_modelmetrics_sdk = MagicMock()
sys.modules["trainingmgr.handler.async_handler"] = MagicMock(ModelMetricsSdk=mock_modelmetrics_sdk)
from trainingmgr.controller.trainingjob_controller import training_job_controller

trainingmgr_main.LOGGER = pytest.logger
trainingmgr_main.LOCK = Lock()
trainingmgr_main.DATAEXTRACTION_JOBS_CACHE = {}
class Test_CreateTrainingJob:
    def setup_method(self):
        self.client = trainingmgr_main.APP.test_client(self)
        self.logger = trainingmgr_main.LOGGER

    mocked_TRAININGMGR_CONFIG_OBJ = mock.Mock(name="TRAININGMGR_CONFIG_OBJ")
    attrs_TRAININGMGR_CONFIG_OBJ = {'kf_adapter_ip.return_value': '123', 'kf_adapter_port.return_value': '100'}
    mocked_TRAININGMGR_CONFIG_OBJ.configure_mock(**attrs_TRAININGMGR_CONFIG_OBJ)

    @patch('trainingmgr.trainingmgr_main.TRAININGMGR_CONFIG_OBJ', return_value=mocked_TRAININGMGR_CONFIG_OBJ)
    def test_create_trainingjob_missing_training_config(self, mock1):
        trainingmgr_main.LOGGER.debug("******* test_CreateTrainingJob POST *******")
        expected_data = {'Exception': 'The training_config is missing'}
        trainingjob_req = {
            "modelId": {"modelname": "test_model", "modelversion": "1.0"},
            "model_location": "s3://model-location"
        }

        response = self.client.post("/ai-ml-model-training/v1/training-jobs", data=json.dumps(trainingjob_req),
                                    content_type="application/json")

        trainingmgr_main.LOGGER.debug(response.data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert expected_data == response.json

    @patch('trainingmgr.trainingmgr_main.TRAININGMGR_CONFIG_OBJ', return_value=mocked_TRAININGMGR_CONFIG_OBJ)
    def test_create_trainingjob_invalid_training_config(self, mock1):
        trainingmgr_main.LOGGER.debug("******* test_CreateTrainingJob POST *******")
        expected_data = {'Exception': 'The TrainingConfig is not correct'}
        trainingjob_req = {
            "modelId": {"modelname": "test_model", "modelversion": "1.0"},
            "model_location": "s3://model-location",
            "training_config": {"invalid_config": "value"}
        }

        response = self.client.post("/ai-ml-model-training/v1/training-jobs", data=json.dumps(trainingjob_req),
                                    content_type="application/json")

        self.logger.debug(response.data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert expected_data == response.json

    @patch('trainingmgr.trainingmgr_main.TRAININGMGR_CONFIG_OBJ', return_value=mocked_TRAININGMGR_CONFIG_OBJ)
    def test_create_trainingjob_model_not_registered(self, mock1):
        expected_data = {
            "Exception": "modelId test_model and 1.0 is not registered at MME, Please first register at MME and then continue"
        }
        trainingjob_req = {
            "modelId": {"modelname": "test_model", "modelversion": "1.0"},
            "model_location": "s3://model-location",
            "training_config": {"config": "valid"}
        }

        with mock.patch('trainingmgr.service.mme_service.get_modelinfo_by_modelId_service', return_value=None):
            response = self.client.post("/ai-ml-model-training/v1/training-jobs", data=json.dumps(trainingjob_req),
                                        content_type="application/json")

        self.logger.debug(response.data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert expected_data == response.json

    @patch('trainingmgr.trainingmgr_main.TRAININGMGR_CONFIG_OBJ', return_value=mocked_TRAININGMGR_CONFIG_OBJ)
    def test_create_trainingjob_model_location_mismatch(self, mock1):
        expected_data = {
            "Exception": "modelId test_model and 1.0 and trainingjob created does not have same modelLocation, Please first register at MME properly and then continue"
        }
        trainingjob_req = {
            "modelId": {"modelname": "test_model", "modelversion": "1.0"},
            "model_location": "s3://model-location",
            "training_config": {"config": "valid"}
        }

        registered_model_list = [{"modelLocation": "s3://different-location"}]
        with mock.patch('trainingmgr.service.mme_service.get_modelinfo_by_modelId_service', return_value=registered_model_list):
            response = self.client.post("/ai-ml-model-training/v1/training-jobs", data=json.dumps(trainingjob_req),
                                        content_type="application/json")

        self.logger.debug(response.data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert expected_data == response.json

class Test_DeleteTrainingJob:
    def setup_method(self):
        self.client = trainingmgr_main.APP.test_client(self)
        self.logger = trainingmgr_main.LOGGER

    mocked_TRAININGMGR_CONFIG_OBJ = mock.Mock(name="TRAININGMGR_CONFIG_OBJ")
    attrs_TRAININGMGR_CONFIG_OBJ = {'kf_adapter_ip.return_value': '123', 'kf_adapter_port.return_value': '100'}
    mocked_TRAININGMGR_CONFIG_OBJ.configure_mock(**attrs_TRAININGMGR_CONFIG_OBJ)


    @patch('trainingmgr.trainingmgr_main.TRAININGMGR_CONFIG_OBJ', return_value=mocked_TRAININGMGR_CONFIG_OBJ)
    def test_delete_trainingjob_success(self, mock1):
        training_job_id = 123
        with mock.patch('trainingmgr.service.training_job_service.delete_training_job', return_value=True):
            response = self.client.delete(f"/ai-ml-model-training/v1/training-jobs/{training_job_id}")

        self.logger.debug(response.data)
        assert response.status_code == status.HTTP_204_NO_CONTENT

    @patch('trainingmgr.trainingmgr_main.TRAININGMGR_CONFIG_OBJ', return_value=mocked_TRAININGMGR_CONFIG_OBJ)
    def test_delete_trainingjob_not_found(self, mock1):
        training_job_id = 123
        expected_data = {'message': 'training job with given id is not found'}
        with mock.patch('trainingmgr.service.training_job_service.delete_training_job', return_value=False):
            response = self.client.delete(f"/ai-ml-model-training/v1/training-jobs/{training_job_id}")

        self.logger.debug(response.data)
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert expected_data == response.json


class Test_GetTrainingJobs:
    def setup_method(self):
        self.client = trainingmgr_main.APP.test_client(self)
        self.logger = trainingmgr_main.LOGGER

    db_result2 = [('usecase1', 'uc1', '*', 'qoe Pipeline lat v2', 'Default', '{"arguments": {"epochs": "1", "trainingjob_name": "usecase1"}}',
                   '', datetime.datetime(2022, 10, 12, 10, 0, 59, 923588), '51948a12-aee9-42e5-93a0-b8f4a15bca33',
                   '{"DATA_EXTRACTION": "FINISHED", "DATA_EXTRACTION_AND_TRAINING": "FINISHED", "TRAINING": "FINISHED", "TRAINING_AND_TRAINED_MODEL": "FINISHED", "TRAINED_MODEL": "FAILED"}',
                   datetime.datetime(2022, 10, 12, 10, 2, 31, 888830), 1, False, '3', '{"datalake_source": {"InfluxSource": {}}}', 'No data available.', '', 'liveCell', 'UEData', False)]

    @patch('trainingmgr.trainingmgr_main.get_trainingjob_info_by_name', return_value=db_result2)
    def test_get_trainingjobs(self, mock1):
        expected_data = [{"job_id": 1, "status": "completed"}]
        response = self.client.get("/ai-ml-model-training/v1/training-jobs/")

        self.logger.debug(response.data)
        assert response.status_code == status.HTTP_200_OK
        assert expected_data == response.json


class Test_GetTrainingJob:
    def setup_method(self):
        self.client = trainingmgr_main.APP.test_client(self)
        self.logger = trainingmgr_main.LOGGER

    db_result2 = [('usecase1', 'uc1', '*', 'qoe Pipeline lat v2', 'Default', '{"arguments": {"epochs": "1", "trainingjob_name": "usecase1"}}',
                   '', datetime.datetime(2022, 10, 12, 10, 0, 59, 923588), '51948a12-aee9-42e5-93a0-b8f4a15bca33',
                   '{"DATA_EXTRACTION": "FINISHED", "DATA_EXTRACTION_AND_TRAINING": "FINISHED", "TRAINING": "FINISHED", "TRAINING_AND_TRAINED_MODEL": "FINISHED", "TRAINED_MODEL": "FAILED"}',
                   datetime.datetime(2022, 10, 12, 10, 2, 31, 888830), 1, False, '3', '{"datalake_source": {"InfluxSource": {}}}', 'No data available.', '', 'liveCell', 'UEData', False)]

    @patch('trainingmgr.trainingmgr_main.get_trainingjob_info_by_name', return_value=db_result2)
    def test_get_trainingjob(self, mock1):
        training_job_id = 123
        expected_data = {"job_id": 123, "status": "completed"}
        response = self.client.get(f"/ai-ml-model-training/v1/training-jobs/{training_job_id}")

        self.logger.debug(response.data)
        assert response.status_code == status.HTTP_200_OK
        assert expected_data == response.json


class Test_GetTrainingJobStatus:
    def setup_method(self):
        self.client = trainingmgr_main.APP.test_client(self)
        self.logger = trainingmgr_main.LOGGER
    
    mocked_TRAININGMGR_CONFIG_OBJ = mock.Mock(name="TRAININGMGR_CONFIG_OBJ")
    attrs_TRAININGMGR_CONFIG_OBJ = {'kf_adapter_ip.return_value': '123', 'kf_adapter_port.return_value': '100'}
    mocked_TRAININGMGR_CONFIG_OBJ.configure_mock(**attrs_TRAININGMGR_CONFIG_OBJ)

    @patch('trainingmgr.trainingmgr_main.TRAININGMGR_CONFIG_OBJ', return_value=mocked_TRAININGMGR_CONFIG_OBJ)
    def test_get_trainingjob_status(self, mock1):
        training_job_id = 123
        expected_data = {"status": "running"}
        with mock.patch('trainingmgr.service.training_job_service.get_steps_state', return_value=json.dumps(expected_data)):
            response = self.client.get(f"/ai-ml-model-training/v1/training-jobs/{training_job_id}/status")

        self.logger.debug(response.data)
        assert response.status_code == status.HTTP_200_OK
        assert expected_data == response.json

