# ==================================================================================
#
#      Copyright (c) 2025 Gyuri Park <inglifestora@naver.com>
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
from trainingmgr.pipeline.mme_mgr import MmeMgr
from trainingmgr.common.exceptions_utls import TMException

class TestMmeMgr:
    @pytest.mark.parametrize("status_code, expected", [
        (200, {"model": "info"}),
        (404, None),
    ])
    @patch("requests.get")
    def test_get_modelInfo_success_or_not_found(self, mock_get, status_code, expected):
        mock_response = MagicMock()
        mock_response.status_code = status_code
        if expected is not None:
            mock_response.json.return_value = expected
        mock_get.return_value = mock_response

        mme_mgr = MmeMgr()
        result = mme_mgr.get_modelInfo_by_modelId("dummy_model", "1")
        assert result == expected

    @patch("requests.get")
    def test_get_modelInfo_error(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_get.return_value = mock_response

        mme_mgr = MmeMgr()
        with pytest.raises(TMException, match="Unexpected response from mme"):
            mme_mgr.get_modelInfo_by_modelId("dummy_model", "1")
