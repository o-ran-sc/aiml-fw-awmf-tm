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
from trainingmgr.service.training_job_service import ( 
    get_training_job,
    get_trainining_jobs,
    create_training_job,
    delete_training_job,
    get_trainingjob_by_modelId,
    fetch_trainingjob_infos_from_modelId,
    update_artifact_version,
    training,
)

class TestGetTrainingJob:
    @patch('trainingmgr.service.training_job_service.get_trainingjob', return_value = {"id": 1, "name": "Test Job"} )
    def test_get_training_job_success(self, mock_get_trainingjob):
        # Mock successful database response
        result = get_training_job(1)
        assert result == {"id": 1, "name": "Test Job"}

    @patch('trainingmgr.service.training_job_service.get_trainingjob')
    def test_get_training_job_db_exception(self, mock_get_trainingjob):

        mock_get_trainingjob.side_effect = DBException("Database error")
        with pytest.raises(TMException) as exc_info:
            get_training_job(1)
        assert "get_training_job by id failed with exception" in str(exc_info.value)


class TestGetTrainingJobs:
    @patch('trainingmgr.service.training_job_service.get_trainingjob')
    def test_get_trainining_jobs_success(self, mock_get_trainingjob):
        # Mock successful database response
        mock_get_trainingjob.return_value = [{"id": 1, "name": "Test Job"}]
        result = get_trainining_jobs()
        assert result == [{"id": 1, "name": "Test Job"}]

    @patch('trainingmgr.service.training_job_service.get_trainingjob')
    def test_get_trainining_jobs_db_exception(self, mock_get_trainingjob):
        # Simulate a database exception
        mock_get_trainingjob.side_effect = DBException("Database error")
        with pytest.raises(TMException) as exc_info:
            get_trainining_jobs()
        assert "get_training_jobs failed with exception" in str(exc_info.value)


class TestCreateTrainingJob:
    @pytest.fixture
    def mock_modelInfo(self):
        return type("ModelID", (), {
            "id": 1,
            "modelname": "Test Model",
            "modelversion": "v1"
        })()

    @patch('trainingmgr.service.training_job_service.get_featuregroup_from_inputDataType', return_value="feature_group_1")
    @patch('trainingmgr.service.training_job_service.create_trainingjob', return_value=None)
    @patch('trainingmgr.service.training_job_service.get_model_by_modelId')
    @patch('trainingmgr.service.training_job_service.training')
    def test_create_training_job_success(self, mock_training, mock_get_model_by_modelId, mock_create_trainingjob, mock_get_featuregroup, mock_modelInfo):
        mock_get_model_by_modelId.return_value = mock_modelInfo
        trainingjob = type("TrainingJob", (), {})()
        trainingjob.id = 123
        trainingjob.training_config = {
            "description": "trainingjob for testing",
            "dataPipeline": {
                "feature_group_name": "testing_influxdb_01",
                "query_filter": "",
                "arguments": "{'epochs': 1'}"
            },
            "trainingPipeline": {
                "training_pipeline_name": "qoe_Pipeline",
                "training_pipeline_version": "qoe_Pipeline",
                "retraining_pipeline_name": "qoe_PipelineRetrain",
                "retraining_pipeline_version": "qoe_PipelineRetrain",
            }
        }
        trainingjob.modelId = type("ModelId", (), {"modelname": "Test Model", "modelversion": "v1"})()
        result = create_training_job(trainingjob, {"modelInformation": {"inputDataType": "type1"}})
        assert result is not None
    
    @patch('trainingmgr.service.training_job_service.get_featuregroup_from_inputDataType', return_value="feature_group_1")
    @patch('trainingmgr.service.training_job_service.get_model_by_modelId')
    @patch('trainingmgr.service.training_job_service.create_trainingjob')
    @patch('trainingmgr.service.training_job_service.training')
    def test_feature_group_name_resolution(self, mock_training, mock_create_trainingjob, mock_get_model_by_modelId, mock_get_featuregroup, mock_modelInfo):
        mock_get_model_by_modelId.return_value = mock_modelInfo
        trainingjob = type("TrainingJob", (), {})()
        trainingjob.id = 123
        trainingjob.training_config = {
            "description": "trainingjob for testing",
            "dataPipeline": {
                "feature_group_name": "",
                "query_filter": "",
                "arguments": "{'epochs': 1'}"
            },
            "trainingPipeline": {
                "training_pipeline_name": "qoe_Pipeline",
                "training_pipeline_version": "qoe_Pipeline",
                "retraining_pipeline_name": "qoe_PipelineRetrain",
                "retraining_pipeline_version": "qoe_PipelineRetrain",
            }
        }
        trainingjob.modelId = type("ModelId", (), {"modelname": "Test Model", "modelversion": "v1"})()
        result = create_training_job(trainingjob, {"modelInformation": {"inputDataType": "type1"}})
        assert result is not None
    
    @patch('trainingmgr.service.training_job_service.create_trainingjob')
    def test_create_training_job_db_exception(self, mock_create_trainingjob):
        mock_create_trainingjob.side_effect = DBException("Database error")
        trainingjob = type("TrainingJob", (), {})()
        trainingjob.id = 123
        trainingjob.training_config = {
            "description": "trainingjob for testing",
            "dataPipeline": {
                "feature_group_name": "testing_influxdb_01",
                "query_filter": "",
                "arguments": "{'epochs': 1'}"
            },
            "trainingPipeline": {
                "training_pipeline_name": "qoe_Pipeline",
                "training_pipeline_version": "qoe_Pipeline",
                "retraining_pipeline_name": "qoe_PipelineRetrain",
                "retraining_pipeline_version": "qoe_PipelineRetrain",
            }
        }
        trainingjob.modelId = type("ModelId", (), {"modelname": "Test Model", "modelversion": "v1"})()
        with pytest.raises(TMException) as exc_info:
            create_training_job(trainingjob, {})
        assert "create_training_job failed with exception" in str(exc_info.value)

class TestDeleteTrainingJob:

    @pytest.fixture
    def mock_training_job(self):
        TrainingJob = MagicMock()
        TrainingJob.id = 1
        TrainingJob.training_config = {
            "description": "Test description",
            "dataPipeline": {
                "feature_group_name": "test_feature_group",
                "query_filter": "",
                "arguments": {"epochs" : 1, "trainingjob_name": "test_job"}
            },
            "trainingPipeline": {
                    "pipeline_name": "test_pipeline",
                    "pipeline_version": "2",
                    "enable_versioning": True
            }
        }
        mock_steps_state = MagicMock()
        mock_steps_state.states = json.dumps({"DATA_EXTRACTION":"FINISHED", 
                            "DATA_EXTRACTION_AND_TRAINING":"FINISHED", 
                            "TRAINING":"IN_PROGRESS"})  
        TrainingJob.steps_state = mock_steps_state
        TrainingJob.deletion_in_progress = False
        return TrainingJob

    @patch('trainingmgr.service.training_job_service.get_trainingjob')
    @patch('trainingmgr.service.training_job_service.delete_trainingjob_by_id', return_value = True)
    @patch('trainingmgr.service.training_job_service.change_field_value')
    @patch('trainingmgr.service.training_job_service.terminate_training_service')
    def test_delete_training_job_success(self, mock_terminate_training, mock_field_value, mock_delete_trainingjob_by_id, mock_get_trainingjob, mock_training_job):
        mock_get_trainingjob.return_value = mock_training_job
        result = delete_training_job(1)
        assert result is True

    @patch('trainingmgr.service.training_job_service.get_trainingjob')
    def test_delete_training_job_no_result(self, mock_get_trainingjob):
        # Simulate no result found
        mock_get_trainingjob.side_effect = NoResultFound
        result = delete_training_job(1)
        assert result is False

    @patch('trainingmgr.service.training_job_service.get_trainingjob')
    def test_delete_training_job_exception(self, mock_get_trainingjob):
        # Simulate a generic exception
        mock_get_trainingjob.side_effect = Exception("Unexpected error")
        with pytest.raises(DBException) as exc_info:
            delete_training_job(1)
        assert "delete_trainining_job failed with exception" in str(exc_info.value)

class TestUpdateArtifactVersion:
    @patch('trainingmgr.service.training_job_service.changeartifact')
    def test_update_artifact_version_success(self, mock_changeartifact):
        result = update_artifact_version(1, "1.0.0", "minor")
        assert result == "1.1.0"

    def test_update_artifact_version_invalid_level(self):
        with pytest.raises(TMException) as exc_info:
            update_artifact_version(1, "1.0.0", "invalid")
        assert "Invalid level passed" in str(exc_info.value)

    @patch('trainingmgr.service.training_job_service.changeartifact')
    def test_update_artifact_version_exception(self, mock_changeartifact):
        mock_changeartifact.side_effect = Exception("Database error")
        with pytest.raises(TMException) as exc_info:
            update_artifact_version(1, "1.0.0", "major")
        assert "failed to update_artifact_version with exception" in str(exc_info.value)

class TestTraining:
    @pytest.fixture
    def mock_FeatureGroup(self):
        return type("FeatureGroup", (), {
            "id": 1,
            "featuregroup_name" : "testing_influxdb_01",
            "feature_list" : "f1,f2",
            "datalake_source" : "InfluxDB",
            "host" : "0.0.0.0",
            "port" : "0",
            "bucket" : "1",
            "token" : "123",
            "db_org" : "db",
            "source_name" : "source",
            "measurement" : "measurement"
        })()

    @pytest.fixture
    def mock_Trainingjob(self):
        return type("Trainingjob", (), {
            "id": 1,
            "training_config": json.dumps({
                "description": "trainingjob for testing",
                "dataPipeline": {
                    "feature_group_name": "testing_influxdb_01",
                    "query_filter": "",
                    "arguments": {"epochs": 1}
                },
                "trainingPipeline": {
                    "training_pipeline_name": "qoe_Pipeline",
                    "training_pipeline_version": "qoe_Pipeline",
                    "retraining_pipeline_name": "qoe_PipelineRetrain",
                    "retraining_pipeline_version": "qoe_PipelineRetrain",
                }
            })
        })()

    mocked_TRAININGMGR_CONFIG_OBJ=mock.Mock(name="TRAININGMGR_CONFIG_OBJ")
    attrs_TRAININGMGR_CONFIG_OBJ = {'kf_adapter_ip.return_value': '123', 'kf_adapter_port.return_value' : '100'}
    mocked_TRAININGMGR_CONFIG_OBJ.configure_mock(**attrs_TRAININGMGR_CONFIG_OBJ)

    @patch('trainingmgr.service.training_job_service.data_extraction_start')
    @patch('trainingmgr.service.training_job_service.get_featuregroup_by_name')
    @patch('trainingmgr.service.training_job_service.getField', return_value = "testing_influxdb_01")
    @patch('trainingmgr.service.training_job_service.change_status_tj')
    @patch('trainingmgr.service.training_job_service.notification_rapp')
    @patch('trainingmgr.service.training_job_service.jsonify')
    def test_training_success(self, mock_jsonify, mock_notif_rapp, mock_change_tj, mock_getField, mock_get_featuregroup, mock_data_extraction_start, 
    mock_FeatureGroup, mock_Trainingjob):
        mock_get_featuregroup.return_value = mock_FeatureGroup
        mock_data_extraction_start.return_value = type("Response", (), {"status_code": 200, "json": lambda: {"status": "success"}})
        response, status_code = training(mock_Trainingjob)
        assert status_code == 201

    @patch('trainingmgr.service.training_job_service.data_extraction_start')
    @patch('trainingmgr.service.training_job_service.get_featuregroup_by_name')
    @patch('trainingmgr.service.training_job_service.getField', return_value = "testing_influxdb_01")
    @patch('trainingmgr.service.training_job_service.change_status_tj')
    @patch('trainingmgr.service.training_job_service.notification_rapp')
    @patch('trainingmgr.service.training_job_service.change_state_to_failed')
    @patch('trainingmgr.service.training_job_service.check_key_in_dictionary', return_value = True)
    @patch('trainingmgr.service.training_job_service.jsonify')
    def test_training_failure(self, mock_jsonify, mock_check_dict, mock_chg_to_failed, mock_notif_rapp, mock_change_tj, mock_getField, 
    mock_get_featuregroup, mock_data_extraction_start, mock_FeatureGroup, mock_Trainingjob):
        mock_get_featuregroup.return_value = mock_FeatureGroup
        
        mock_response = mock.Mock()
        mock_response.status_code = 500
        mock_response.headers = {'content-type': MIMETYPE_JSON}
        mock_response.json.return_value = {"result": "error occurred"}
        mock_data_extraction_start.return_value = mock_response

        response, status_code = training(mock_Trainingjob)
        assert status_code == 500

class TestFetchTrainingJobInfosFromModelId:
    @patch('trainingmgr.service.training_job_service.get_trainingjobs_by_modelId_db')
    def test_success(self, mock_gettrainingJob):
        model_name = "abc"
        model_version = "1"
        trainingjobs_info = fetch_trainingjob_infos_from_modelId(model_name, model_version)
        assert True # Reached here without error, test-passed
    
    
    @patch('trainingmgr.service.training_job_service.get_trainingjobs_by_modelId_db', side_effect = Exception("Generic exception"))
    def test_internalError(self, mock_gettrainingJob):
        model_name = "abc"
        model_version = "1"
        try:
            trainingjobs_info = fetch_trainingjob_infos_from_modelId(model_name, model_version)
            assert False, "The test should have raised an Exception, but It didn't"
        except Exception as e:
            # Signifies test-passed
            pass
            
            

    