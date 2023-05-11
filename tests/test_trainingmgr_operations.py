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
from mock import patch
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
from trainingmgr.common.trainingmgr_config import TrainingMgrConfig
trainingmgr_main.LOGGER = pytest.logger
trainingmgr_main.LOCK = Lock()
trainingmgr_main.DATAEXTRACTION_JOBS_CACHE = {}

class DummyVariable:
        kf_adapter_ip = "localhost"
        kf_adapter_port = 5001
        logger = trainingmgr_main.LOGGER

class Test_training_start:
    def setup_method(self): 
        self.client = trainingmgr_main.APP.test_client(self)
        self.logger = trainingmgr_main.LOGGER
    
    def test_negative_training_start(self):
        training_config_obj =  DummyVariable()
        dict_data = {
                        "brand": "Ford",
                        "model": "Mustang",
                        "year": 1964
                    }
        trainingjob_name = "usecase12"
        expected_data = {
                        "brand": "Ford",
                        "model": "Mustang",
                        "year": 1964
                    }
        try:
            response = trainingmgr_operations.training_start(training_config_obj,dict_data,trainingjob_name)
            assert response == expected_data,"data not equal"
            assert False
        except Exception:
            assert True

class Test_upload_pipeline:
    def setup_method(self):
        self.client = trainingmgr_main.APP.test_client(self)
        self.logger = trainingmgr_main.LOGGER

    mocked_TRAININGMGR_CONFIG_OBJ=mock.Mock(name="TRAININGMGR_CONFIG_OBJ")
    attrs_TRAININGMGR_CONFIG_OBJ = {'kf_adapter_ip.return_value': '123', 'kf_adapter_port.return_value' : '100'}
    mocked_TRAININGMGR_CONFIG_OBJ.configure_mock(**attrs_TRAININGMGR_CONFIG_OBJ)
    @patch('trainingmgr.trainingmgr_main.TRAININGMGR_CONFIG_OBJ', return_value = mocked_TRAININGMGR_CONFIG_OBJ)
    def test_upload_pipeline_negative(self, mock1):
        expected_data = "result"
        trainingjob_req = {
                    "pipe_name":"usecase1",
                    }
        response = self.client.post("/pipelines/<pipe_name>/upload".format("usecase1"), data=json.dumps(trainingjob_req),
                                    content_type="application/json")
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert expected_data in response.json.keys() 

class Test_create_dme_filtered_data_job:

    the_response=Response()
    the_response.status_code=status.HTTP_201_CREATED
    @patch('trainingmgr.common.trainingmgr_operations.requests.put', return_value=the_response)
    def test_create_dme_filtered_data_job(self, mock1):
        mocked_TRAININGMGR_CONFIG_OBJ=mock.Mock(name="TRAININGMGR_CONFIG_OBJ")
        attrs_TRAININGMGR_CONFIG_OBJ = {'kf_adapter_ip.return_value': '123', 'kf_adapter_port.return_value' : '100'}
        mocked_TRAININGMGR_CONFIG_OBJ.configure_mock(**attrs_TRAININGMGR_CONFIG_OBJ)
        source_name=""
        db_org=""
        bucket_name=""
        token=""
        features=[]
        feature_group_name="test"
        host="10.0.0.50"
        port="31840"
        response=trainingmgr_operations.create_dme_filtered_data_job(mocked_TRAININGMGR_CONFIG_OBJ, source_name, db_org, bucket_name, token, features, feature_group_name, host, port)
        assert response.status_code==201, "create_dme_filtered_data_job failed"

    @patch('trainingmgr.common.trainingmgr_operations.create_url_host_port', side_effect=Exception("Mocked Error"))
    def test_negative_create_dme_filtered_data_job(self, mock1):
        mocked_TRAININGMGR_CONFIG_OBJ=mock.Mock(name="TRAININGMGR_CONFIG_OBJ")
        attrs_TRAININGMGR_CONFIG_OBJ = {'kf_adapter_ip.return_value': '123', 'kf_adapter_port.return_value' : '100'}
        mocked_TRAININGMGR_CONFIG_OBJ.configure_mock(**attrs_TRAININGMGR_CONFIG_OBJ)
        source_name=""
        db_org=""
        bucket_name=""
        token=""
        features=[]
        feature_group_name="test"
        host="10.0.0.50"
        port="31840"
        try:
            response=trainingmgr_operations.create_dme_filtered_data_job(mocked_TRAININGMGR_CONFIG_OBJ, source_name, db_org, bucket_name, token, features, feature_group_name, host, port)
            assert False
        except Exception:
            assert True
