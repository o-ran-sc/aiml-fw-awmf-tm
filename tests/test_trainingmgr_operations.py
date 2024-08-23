# ==================================================================================
#
#       Copyright (c) 2022 Samsung Electronics Co., Ltd. All Rights Reserved.
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#          http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
# ==================================================================================
import json
import requests
from unittest import mock
from mock import patch, MagicMock
import pytest
import flask
from requests.models import Response
from threading import Lock
import os
import sys
import datetime
from flask_api import status
from dotenv import load_dotenv
from threading import Lock
from trainingmgr import trainingmgr_main 
from trainingmgr.common import trainingmgr_operations
from trainingmgr.common.tmgr_logger import TMLogger
from trainingmgr.common.exceptions_utls import TMException
from trainingmgr.common.trainingmgr_util import MIMETYPE_JSON
from trainingmgr.common.trainingmgr_config import TrainingMgrConfig

trainingmgr_main.LOGGER = pytest.logger
trainingmgr_main.LOCK = Lock()
trainingmgr_main.DATAEXTRACTION_JOBS_CACHE = {}

class DummyVariable:
    kf_adapter_ip = "localhost"
    kf_adapter_port = 5001
    data_extraction_ip = "localhost"
    data_extraction_port = 32000
    model_management_service_ip="localhost"
    model_management_service_port=123123
    logger = trainingmgr_main.LOGGER

class Test_data_extraction_start:
    def setup_method(self):
        self.client = trainingmgr_main.APP.test_client(self)
        self.logger = trainingmgr_main.LOGGER

    de_result = Response()
    de_result.status_code = status.HTTP_200_OK
    de_result.headers={'content-type': MIMETYPE_JSON}
    @patch('trainingmgr.common.trainingmgr_operations.requests.post', return_value = de_result)
    def test_success(self, mock1):
        trainingjob_name = "usecase12"
        training_config_obj = DummyVariable()
        feature_list = "*"
        query_filter = ""
        datalake_source = {"InfluxSource": {}}
        _measurement = "liveCell"
        influxdb_info_dict={'host': '', 'port': '', 'token': '', 'source_name': '', 'db_org': '', 'bucket': ''}
        try:
            response = trainingmgr_operations.data_extraction_start(training_config_obj, trainingjob_name, feature_list,
                                                                    query_filter, datalake_source, _measurement, influxdb_info_dict)
            assert response.status_code == status.HTTP_200_OK
            assert response.headers['content-type'] == MIMETYPE_JSON
        except:
            assert False

class Test_data_extraction_status:
    def setup_method(self):
        self.client = trainingmgr_main.APP.test_client(self)
        self.logger = trainingmgr_main.LOGGER

    de_result = Response()
    de_result.status_code = status.HTTP_200_OK
    de_result.headers={'content-type': MIMETYPE_JSON}
    @patch('trainingmgr.common.trainingmgr_operations.requests.get', return_value = de_result)
    def test_success(self, mock1):
        trainingjob_name = "usecase12"
        training_config_obj = DummyVariable()
        try:
            response = trainingmgr_operations.data_extraction_status(trainingjob_name, training_config_obj)
            assert response.status_code == status.HTTP_200_OK
            assert response.headers['content-type'] == MIMETYPE_JSON
        except:
            assert False

class Test_training_start:
    def setup_method(self): 
        self.client = trainingmgr_main.APP.test_client(self)
        self.logger = trainingmgr_main.LOGGER

    ts_result = Response()
    ts_result.status_code = status.HTTP_200_OK
    ts_result.headers={'content-type': MIMETYPE_JSON}
    @patch('trainingmgr.common.trainingmgr_operations.requests.post', return_value = ts_result)
    def test_success(self, mock1):
        trainingjob_name = "usecase12"
        dict_data = {
            "pipeline_name": "qoe",
            "experiment_name": "default",
            "arguments": "{epoches : 1}",
            "pipeline_version": 1
        }
        training_config_obj = DummyVariable()
        try:
            response = trainingmgr_operations.training_start(training_config_obj,dict_data,trainingjob_name)
            assert response.headers['content-type'] == MIMETYPE_JSON
            assert response.status_code == status.HTTP_200_OK
        except Exception:
            assert False

    def test_fail(self):
        trainingjob_name = "usecase12"
        dict_data = {
            "pipeline_name": "qoe",
            "experiment_name": "default",
            "arguments": "{epoches : 1}",
            "pipeline_version": 1
        }
        training_config_obj = DummyVariable()
        try:
            trainingmgr_operations.training_start(training_config_obj,dict_data,trainingjob_name)
            assert False
        except requests.exceptions.ConnectionError:
            assert True
        except Exception:
            assert False

class Test_create_dme_filtered_data_job:
    the_response=Response()
    the_response.status_code=status.HTTP_201_CREATED
    @patch('trainingmgr.common.trainingmgr_operations.requests.put', return_value=the_response)
    def test_success(self, mock1):
        training_config_obj = DummyVariable()
        source_name=""
        features=[]
        feature_group_name="test"
        host="10.0.0.50"
        port="31840"
        measured_obj_class="NRCellDU"
        response=trainingmgr_operations.create_dme_filtered_data_job(training_config_obj, source_name, features, feature_group_name, host, port, measured_obj_class)
        assert response.status_code==status.HTTP_201_CREATED, "create_dme_filtered_data_job failed"

    def test_create_url_host_port_fail(self):
        training_config_obj = DummyVariable()
        source_name=""
        features=[]
        feature_group_name="test"
        measured_obj_class="NRCellDU"
        host="url error"
        port="31840"
        try:
            response=trainingmgr_operations.create_dme_filtered_data_job(training_config_obj, source_name, features, feature_group_name, host, port, measured_obj_class)
            assert False
        except TMException as err:
            assert "URL validation error: " in err.message
        except Exception:
            assert False

class Test_delete_dme_filtered_data_job:
    the_response=Response()
    the_response.status_code=status.HTTP_204_NO_CONTENT
    @patch('trainingmgr.common.trainingmgr_operations.requests.delete', return_value=the_response)
    def test_success(self, mock1):
        training_config_obj = DummyVariable()
        feature_group_name="test"
        host="10.0.0.50"
        port="31840"
        response=trainingmgr_operations.delete_dme_filtered_data_job(training_config_obj, feature_group_name, host, port)
        assert response.status_code==status.HTTP_204_NO_CONTENT, "delete_dme_filtered_data_job failed"

    def test_create_url_host_port_fail(self):
        training_config_obj = DummyVariable()
        feature_group_name="test"
        host="url error"
        port="31840"
        try:
            response=trainingmgr_operations.delete_dme_filtered_data_job(training_config_obj, feature_group_name, host, port)
            assert False
        except TMException as err:
            assert "URL validation error: " in err.message
        except Exception:
            assert False

class Test_get_model_info:

    @patch('trainingmgr.common.trainingmgr_operations.requests.get')
    def test_get_model_info(self,mock_requests_get):
        training_config_obj = DummyVariable()
        model_name="qoe"
        rapp_id = "rapp_1"
        meta_info = {
            "test": "test"
        }
        
        model_data = {
            "model-name": model_name,
            "rapp-id": rapp_id,
            "meta-info": meta_info
        }
        mock_response=MagicMock(spec=Response)
        mock_response.status_code=200
        mock_response.json.return_value={'message': {"name": model_name, "data": json.dumps(model_data)}}
        mock_requests_get.return_value= mock_response
        model_info=trainingmgr_operations.get_model_info(training_config_obj, model_name)
        expected_model_info={
            "model-name": model_name,
            "rapp-id": rapp_id,
            "meta-info": meta_info
        }
        assert model_info==expected_model_info, "get model info failed"

    @patch('trainingmgr.common.trainingmgr_operations.requests.get')
    def test_negative_get_model_info(self,mock_requests_get):
        training_config_obj = DummyVariable()
        model_name="qoe"
        rapp_id = "rapp_1"
        meta_info = {
            "test": "test"
        }
        
        model_data = {
            "model-name": model_name,
            "rapp-id": rapp_id,
            "meta-info": meta_info
        }
        mock_response=MagicMock(spec=Response)
        mock_response.status_code=500
        mock_response.json.return_value={'message': {"name": model_name, "data": json.dumps(model_data)}}
        mock_requests_get.return_value= mock_response
        try:
            model_info=trainingmgr_operations.get_model_info(training_config_obj, model_name)
        except TMException as err:
            assert "model info can't be fetched, model_name:" in err.message
