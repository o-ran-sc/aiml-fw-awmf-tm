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
from trainingmgr.models import ModelID, FeatureGroup, TrainingJob
from sqlalchemy.orm.exc import NoResultFound
MIMETYPE_JSON = "application/json"

mock_modelmetrics_sdk = MagicMock()
sys.modules["trainingmgr.handler.async_handler"] = MagicMock(ModelMetricsSdk=mock_modelmetrics_sdk)

from trainingmgr.db.trainingjob_db import (
    change_state_to_failed, delete_trainingjob_by_id, create_trainingjob,
    get_trainingjob, get_trainingjob_by_modelId_db, change_steps_state,
    change_field_value, change_steps_state_df, changeartifact
)
from trainingmgr.common.exceptions_utls import DBException, TMException
from trainingmgr.common.trainingConfig_parser import getField, setField
from trainingmgr.handler.async_handler import DATAEXTRACTION_JOBS_CACHE
from trainingmgr.schemas import TrainingJobSchema
from trainingmgr.common.trainingmgr_util import check_key_in_dictionary, get_one_word_status, get_step_in_progress_state
from trainingmgr.service.featuregroup_service import ( 
    get_featuregroup_by_name,
    get_featuregroup_from_inputDataType,
    get_all_featuregroups
)

class TestGetFeaturegroupByName:
    
    expectedVal = {"featuregroup_name": "test_group"}
    @patch('trainingmgr.service.featuregroup_service.get_feature_group_by_name_db', return_value = expectedVal) 
    def test_getFeatureGroupName_success(self, mock_get_feature_group_by_name_db):
        result = get_featuregroup_by_name("test_group")
        print(result)        
        assert result == {"featuregroup_name": "test_group"}

    @patch("trainingmgr.service.featuregroup_service.get_feature_group_by_name_db")
    def test_getFeatureGroupName_testexception(self, mock_get_feature_group_by_name_db):
        mock_get_feature_group_by_name_db.side_effect = Exception("DB error")
        with pytest.raises(TMException) as exc_info:
            get_featuregroup_by_name("invalid_group")
        assert "get featuregroup by name service failed with exception : DB error" in str(exc_info.value)

class TestGetFeaturegroupFromInputDataType:
    @patch("trainingmgr.service.featuregroup_service.get_feature_groups_from_inputDataType_db")
    def test_single_result(self, mock_get_feature_groups):
        mock_get_feature_groups.return_value = [("test_group",)]
        result = get_featuregroup_from_inputDataType("some_type") 
        assert result == "test_group"

    @patch("trainingmgr.service.featuregroup_service.get_feature_groups_from_inputDataType_db", return_value = [])
    def test_no_result(self, mock_get_feature_groups):
        with pytest.raises(TMException) as exc_info:
            get_featuregroup_from_inputDataType("some_type")
        assert "No featureGroup is available for inputDataType some_type" in str(exc_info.value)

    @patch("trainingmgr.service.featuregroup_service.get_feature_groups_from_inputDataType_db")
    def test_multiple_results(self, mock_get_feature_groups):
        mock_get_feature_groups.return_value = [("group1",), ("group2",)]
        with pytest.raises(TMException) as exc_info: 
            get_featuregroup_from_inputDataType("some_type")
        assert "2 or more featureGroup are available for inputDataType" in str(exc_info.value)


    @patch("trainingmgr.service.featuregroup_service.get_feature_groups_from_inputDataType_db")
    def test_db_exception(self, mock_get_feature_groups):
        mock_get_feature_groups.side_effect = DBException("DB connection failed")
        with pytest.raises(TMException) as exc_info:
            get_featuregroup_from_inputDataType("some_type")
        assert "get_featuregroup_from_inputDataType service failed with exception" in str(exc_info.value)

    @patch("trainingmgr.service.featuregroup_service.get_feature_groups_from_inputDataType_db")
    def test_unexpected_exception(self, mock_get_feature_groups):
        mock_get_feature_groups.side_effect = Exception("Unexpected error")
        with pytest.raises(Exception) as exc_info:
            get_featuregroup_from_inputDataType("some_type")
        assert "Unexpected error" in str(exc_info.value)


class TestGetAllFeaturegroups:
    expected_value =  [
            {"featuregroup_name": "group1"},
            {"featuregroup_name": "group2"},
        ]
    
    @patch("trainingmgr.service.featuregroup_service.get_feature_groups_db", return_value = expected_value)
    def test_success(self, mock_get_feature_groups_db):
        result = get_all_featuregroups()
        assert result == [
            {"featuregroup_name": "group1"},
            {"featuregroup_name": "group2"},
        ]

    @patch("trainingmgr.service.featuregroup_service.get_feature_groups_db")
    def test_exception(self, mock_get_feature_groups_db):
        mock_get_feature_groups_db.side_effect = Exception("DB error")

        with pytest.raises(TMException) as exc_info:
            get_all_featuregroups()
        assert "get all featuregroups service failed with exception : DB error" in str(exc_info.value)

