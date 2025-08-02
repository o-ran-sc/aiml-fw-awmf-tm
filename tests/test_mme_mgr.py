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
    @patch("requests.get")
    def test_get_modelInfo_success(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"model": "info"}
        mock_get.return_value = mock_response

        mme_mgr = MmeMgr()
        result = mme_mgr.get_modelInfo_by_modelId("model1", "1")
        assert result == {"model": "info"}

    @patch("requests.get")
    def test_get_modelInfo_not_found(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        mme_mgr = MmeMgr()
        result = mme_mgr.get_modelInfo_by_modelId("model1", "999")
        assert result is None

    @patch("requests.get")
    def test_get_modelInfo_error(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_get.return_value = mock_response

        mme_mgr = MmeMgr()
        with pytest.raises(TMException, match="Unexpected response from mme"):
            mme_mgr.get_modelInfo_by_modelId("model1", "1")
