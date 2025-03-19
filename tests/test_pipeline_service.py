# ==================================================================================
#
#      Copyright (c) 2025 Samsung Electronics Co., Ltd. All Rights Reserved.
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
from unittest.mock import patch, MagicMock, mock_open
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
from io import BytesIO
from werkzeug.datastructures import FileStorage
from trainingmgr.service.pipeline_service import (
    get_all_pipelines,
    get_single_pipeline,
    get_all_pipeline_versions,
    upload_pipeline_service,
    start_training_service,
    terminate_training_service,
    list_experiments_service
)

class TestGetAllPipelines:
    @patch("trainingmgr.pipeline.pipeline_mgr.PipelineMgr.get_all_pipelines")
    def test_success(self, mock_get_all_pipelines):
        mock_get_all_pipelines.return_value = {"pipelines": [{"name": "pipeline1"}, {"name": "pipeline2"}]}

        result = get_all_pipelines()
        assert result == {"pipelines": [{"name": "pipeline1"}, {"name": "pipeline2"}]}


class TestGetSinglePipeline:
    @patch("trainingmgr.pipeline.pipeline_mgr.PipelineMgr.get_all_pipelines")
    def test_pipeline_found(self, mock_get_all_pipelines):
        mock_get_all_pipelines.return_value = {
            "pipelines": [{"display_name": "test_pipeline", "pipeline_id": "123", "description": "Test", "created_at": "2024-01-01"}]
        }

        result = get_single_pipeline("test_pipeline")

        assert result == {
            "pipeline_id": "123",
            "display_name": "test_pipeline",
            "description": "Test",
            "created_at": "2024-01-01"
        }

    @patch("trainingmgr.pipeline.pipeline_mgr.PipelineMgr.get_all_pipelines")
    def test_pipeline_not_found(self, mock_get_all_pipelines):
        mock_get_all_pipelines.return_value = {"pipelines": [{"display_name": "another_pipeline"}]}

        result = get_single_pipeline("test_pipeline")
        assert result is None

class TestGetAllPipelineVersions:
    @patch("trainingmgr.service.pipeline_service.get_single_pipeline", return_value={"display_name": "test_pipeline"})
    @patch("trainingmgr.pipeline.pipeline_mgr.PipelineMgr.get_all_pipeline_versions")
    def test_success(self, mock_get_all_versions, mock_get_pipeline):
        """Test when pipeline versions are successfully retrieved"""
        mock_get_all_versions.return_value = {"versions_list": ["v1", "v2"]}

        result = get_all_pipeline_versions("test_pipeline")

        assert result == ["v1", "v2"]
        mock_get_all_versions.assert_called_once_with("test_pipeline")

    @patch("trainingmgr.service.pipeline_service.get_single_pipeline", return_value=None)
    def test_pipeline_not_found(self, mock_get_pipeline):
        """Test when the requested pipeline does not exist"""
        result = get_all_pipeline_versions("unknown_pipeline")

        assert result is None

