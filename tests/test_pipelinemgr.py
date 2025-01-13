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

    @patch("requests.get")
    def test_get_all_pipeline_versions_success(self, mock_get, pipeline_mgr):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {"content-type": "application/json"}
        mock_response.json.return_value = [{"version": "1.0"}, {"version": "2.0"}]
        mock_get.return_value = mock_response
        result = pipeline_mgr.get_all_pipeline_versions("pipeline1")
        assert len(result) == 2
        assert result[0]["version"] == "1.0"

    @patch("requests.post")
    def test_upload_pipeline_file_success(self, mock_post, pipeline_mgr, tmp_path):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        # Create a temporary file for testing
        file_path = tmp_path / "test_pipeline.yaml"
        file_path.write_text("pipeline content")
        result = pipeline_mgr.upload_pipeline_file("pipeline1", str(file_path), "Test pipeline")
        assert result is True

    @patch("requests.post")
    def test_upload_pipeline_file_failure(self, mock_post, pipeline_mgr, tmp_path):
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.json.return_value = {"message": "Invalid file"}
        mock_post.return_value = mock_response
        # Create a temporary file for testing
        file_path = tmp_path / "test_pipeline.yaml"
        file_path.write_text("pipeline content")
        with pytest.raises(TMException, match="Error while uploading pipeline"):
            pipeline_mgr.upload_pipeline_file("pipeline1", str(file_path), "Test pipeline")
            
    @patch("requests.post")
    def test_start_training_success(self, mock_post, pipeline_mgr):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        training_details = {"param1": "value1"}
        response = pipeline_mgr.start_training(training_details, "trainingjob1")
        assert response.status_code == 200
