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
from unittest.mock import patch, MagicMock
from trainingmgr.pipeline.pipeline_mgr import PipelineMgr
from trainingmgr.common.exceptions_utls import TMException

@pytest.fixture
def pipeline_mgr():
    """Fixture to get an instance of PipelineMgr."""
    return PipelineMgr()
    
class TestPipelineMgr:
    @patch("requests.get")
    def test_get_all_pipelines_success(self, mock_get, pipeline_mgr):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {"content-type": "application/json"}
        mock_response.json.return_value = [{"id": "pipeline1"}, {"id": "pipeline2"}]
        mock_get.return_value = mock_response
        result = pipeline_mgr.get_all_pipelines()
        assert len(result) == 2
        assert result[0]["id"] == "pipeline1"
        
    @patch("requests.get")
    def test_get_all_pipelines_invalid_response(self, mock_get, pipeline_mgr):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {"content-type": "text/plain"}
        mock_get.return_value = mock_response
        with pytest.raises(TMException, match="Kf adapter doesn't sends json type response"):
            pipeline_mgr.get_all_pipelines()
