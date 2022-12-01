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
from trainingmgr.common import trainingmgr_config
from trainingmgr.common.trainingmgr_config import TrainingMgrConfig
from trainingmgr.common.tmgr_logger import TMLogger
from trainingmgr import trainingmgr_main
trainingmgr_main.LOGGER = pytest.logger

class Test_trainingmgr_config:
    @patch('trainingmgr.common.trainingmgr_config.TMLogger', return_value = TMLogger("tests/common/conf_log.yaml"))
    def setup_method(self,mock1,mock2):
        self.client = trainingmgr_main.APP.test_client(self)
        self.logger = trainingmgr_main.LOGGER
        load_dotenv('tests/test.env')
        self.TRAININGMGR_CONFIG_OBJ = TrainingMgrConfig()   
   
    def test_kf_adapter_port(self):
        expected_data = '5001'
        result = self.TRAININGMGR_CONFIG_OBJ.kf_adapter_port
        assert result == expected_data

    def test_kf_adapter_ip(self):
        expected_data = 'localhost'
        result = self.TRAININGMGR_CONFIG_OBJ.kf_adapter_ip
        assert result == expected_data

    def test_data_extraction_port(self):
        expected_data = '32000'
        result = self.TRAININGMGR_CONFIG_OBJ.data_extraction_port
        assert result == expected_data

    def test_data_extraction_ip(self):
        expected_data = 'localhost'
        result = self.TRAININGMGR_CONFIG_OBJ.data_extraction_ip
        assert result == expected_data

    def test_my_port(self):
        expected_data = '32002'
        x = TrainingMgrConfig
        result = self.TRAININGMGR_CONFIG_OBJ.my_port
        assert result == expected_data

    def test_my_ip(self):
        expected_data = 'localhost'
        result = self.TRAININGMGR_CONFIG_OBJ.my_ip
        assert result == expected_data
    
    def test_logger(self):
        expected_data = TMLogger("tests/common/conf_log.yaml").logger
        result = self.TRAININGMGR_CONFIG_OBJ.logger
        assert result == expected_data

    def test_ps_user(self):
        expected_data = 'postgres'
        result = self.TRAININGMGR_CONFIG_OBJ.ps_user
        assert result == expected_data

    def test_ps_password(self):
        expected_data = "abcd"
        result = self.TRAININGMGR_CONFIG_OBJ.ps_password
        assert result == expected_data

    def test_ps_ip(self):
        expected_data = 'localhost'
        result = self.TRAININGMGR_CONFIG_OBJ.ps_ip
        assert result == expected_data

    def test_ps_port(self):
        expected_data = '30001'
        x = TrainingMgrConfig
        result = self.TRAININGMGR_CONFIG_OBJ.ps_port
        assert result == expected_data

    def test_is_config_loaded_properly(self):
        expected_data = True
        result = TrainingMgrConfig.is_config_loaded_properly(self.TRAININGMGR_CONFIG_OBJ)
        assert result == expected_data

