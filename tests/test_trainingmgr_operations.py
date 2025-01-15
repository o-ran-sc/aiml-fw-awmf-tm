# # ==================================================================================
# #
# #       Copyright (c) 2022 Samsung Electronics Co., Ltd. All Rights Reserved.
# #
# #   Licensed under the Apache License, Version 2.0 (the "License");
# #   you may not use this file except in compliance with the License.
# #   You may obtain a copy of the License at
# #
# #          http://www.apache.org/licenses/LICENSE-2.0
# #
# #   Unless required by applicable law or agreed to in writing, software
# #   distributed under the License is distributed on an "AS IS" BASIS,
# #   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# #   See the License for the specific language governing permissions and
# #   limitations under the License.
# #
# # ==================================================================================
from mock import patch
import pytest
from requests.models import Response
from threading import Lock
from flask_api import status
from trainingmgr import trainingmgr_main 
from trainingmgr.common import trainingmgr_operations
from trainingmgr.common.exceptions_utls import TMException
from trainingmgr.common.trainingmgr_util import MIMETYPE_JSON
from trainingmgr.constants.steps import Steps
from trainingmgr.constants.states import States
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

class DummyStepsState:
    def __init__(self, states):
        self.states = states

class DummyTrainingJob:
    def __init__(self, cur_state, notification_url):
        self.steps_state = DummyStepsState(cur_state)
        self.notification_url = notification_url

class Test_data_extraction_start:
    def setup_method(self):
        self.client = trainingmgr_main.APP.test_client(self)
        self.logger = trainingmgr_main.LOGGER

    de_result = Response()
    de_result.status_code = status.HTTP_200_OK
    de_result.headers={'content-type': MIMETYPE_JSON}
    @patch('trainingmgr.common.trainingmgr_operations.requests.post', return_value = de_result)
    def test_success(self, mock1):
        trainingjob_id = 1
        featuregroup_name = "base1"
        training_config_obj = DummyVariable()
        feature_list = "*"
        query_filter = ""
        datalake_source = {"InfluxSource": {}}
        _measurement = "liveCell"
        influxdb_info_dict={'host': '', 'port': '', 'token': '', 'source_name': '', 'db_org': '', 'bucket': ''}
        try:
            response = trainingmgr_operations.data_extraction_start(training_config_obj, trainingjob_id, feature_list,
                                                                    query_filter, datalake_source, _measurement, influxdb_info_dict, featuregroup_name)
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
        featuregroup_name = "base1"
        trainingjob_id = 1
        training_config_obj = DummyVariable()
        try:
            response = trainingmgr_operations.data_extraction_status(featuregroup_name, trainingjob_id, training_config_obj)
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
        trainingjob_id = 1
        dict_data = {
            "pipeline_name": "qoe",
            "experiment_name": "default",
            "arguments": "{epoches : 1}",
            "pipeline_version": 1
        }
        training_config_obj = DummyVariable()
        try:
            response = trainingmgr_operations.training_start(training_config_obj, dict_data, trainingjob_id)
            assert response.headers['content-type'] == MIMETYPE_JSON
            assert response.status_code == status.HTTP_200_OK
        except Exception:
            assert False

    def test_fail(self):
        trainingjob_id = 1
        dict_data = {
            "pipeline_name": "qoe",
            "experiment_name": "default",
            "arguments": "{epoches : 1}",
            "pipeline_version": 1
        }
        training_config_obj = DummyVariable()
        try:
            trainingmgr_operations.training_start(training_config_obj, dict_data, trainingjob_id)
            assert False
        except TMException:
            assert True
        except Exception:
            # Any other Exception signifies test-failure
            assert False


class Test_create_url_host_port:
    def test_success(self):
        expected_url = "http://10.0.0.7:38012/training"
        url = trainingmgr_operations.create_url_host_port("http", "10.0.0.7", "38012", "training")
        assert url == expected_url, "create_url_host_port Failed"
        
    def test_failure(self):
        try:
            trainingmgr_operations.create_url_host_port("http", "HOST ERROR", "38012", "training")
            assert False
        except TMException as err:
            assert "URL validation error: " in err.message
        except Exception:
            assert False


class Test_create_dme_filtered_data_job:
    the_response=Response()
    the_response.status_code=status.HTTP_201_CREATED
    @patch('trainingmgr.common.trainingmgr_operations.requests.put', return_value=the_response)
    def test_success(self, mock1):
        training_config_obj = DummyVariable()
        source_name="GNBDU324"
        features= "pdcpBytesUl, pdcpBytesDl"
        feature_group_name="test"
        host="10.0.0.50"
        port="31840"
        measured_obj_class="NRCellDU"
        response=trainingmgr_operations.create_dme_filtered_data_job(training_config_obj, source_name, features, feature_group_name, host, port, measured_obj_class)
        assert response.status_code==status.HTTP_201_CREATED, "create_dme_filtered_data_job failed"


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
        assert response.status_code == status.HTTP_204_NO_CONTENT, "delete_dme_filtered_data_job failed"

class Test_notification_rapp:
    steps_state = {
            Steps.DATA_EXTRACTION.name: States.NOT_STARTED.name,
            Steps.DATA_EXTRACTION_AND_TRAINING.name: States.NOT_STARTED.name,
            Steps.TRAINING.name: States.NOT_STARTED.name,
            Steps.TRAINING_AND_TRAINED_MODEL.name: States.NOT_STARTED.name,
            Steps.TRAINED_MODEL.name: States.NOT_STARTED.name
        }
    the_response=Response()
    the_response.status_code=status.HTTP_200_OK
    @patch('trainingmgr.common.trainingmgr_operations.get_trainingjob', return_value = DummyTrainingJob(steps_state, "dummy_url"))
    @patch('trainingmgr.common.trainingmgr_operations.requests.post', return_value=the_response)
    def test_success(self, mock1, mock2):
        trainingmgr_operations.notification_rapp(1)
        
    the_response=Response()
    the_response.status_code=status.HTTP_404_NOT_FOUND
    @patch('trainingmgr.common.trainingmgr_operations.get_trainingjob', return_value = DummyTrainingJob(steps_state, "dummy_url"))
    @patch('trainingmgr.common.trainingmgr_operations.requests.post', return_value=the_response)
    def test_failure(self, mock1, mock2):
        resp = trainingmgr_operations.notification_rapp(1)
        assert resp is None, f"notification_rapp is supposed to fail and return None, but except it returned {resp}"
        
        