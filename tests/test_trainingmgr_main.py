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
from requests.models import Response
from threading import Lock
import os
import sys
import datetime
from flask_api import status
from flask import send_file
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
from trainingmgr.controller import featuregroup_controller, training_job_controller
from trainingmgr.controller.pipeline_controller import pipeline_controller
from trainingmgr.handler.async_handler import Model_Metrics_Sdk
from middleware.loggingMiddleware import LoggingMiddleware
from io import BytesIO

#mock ModelMetricsSdk before importing
mock_modelmetrics_sdk = MagicMock()
sys.modules["trainingmgr.handler.async_handler"] = MagicMock(ModelMetricsSdk=mock_modelmetrics_sdk)
TRAININGMGR_CONFIG_OBJ = TrainingMgrConfig()
from trainingmgr import trainingmgr_main

class TestGetModel:
    def setup_method(self):
        self.client = trainingmgr_main.APP.test_client(self)
    
    mocked_mm_sdk=mock.Mock(name="MM_SDK")
    attrs_mm_sdk = {'check_object.return_value': True, 'get_model_zip.return_value':"model.zip"}
    mocked_mm_sdk.configure_mock(**attrs_mm_sdk)

    @patch('trainingmgr.trainingmgr_main.MM_SDK', return_value = mocked_mm_sdk)
    @patch('trainingmgr.trainingmgr_main.send_file')
    def test_getmodel_valid_data(self, mock_sendfile, mock_model_metrics_sdk):
        mock_sendfile.return_value = trainingmgr_main.APP.response_class(
            response=b'model.zip',
            status=200,
            mimetype='application/zip'
        )
        response = self.client.get("/model/{modelname}/{modelversion}/{artifactversion}/Model.zip".format(modelname="valid_model",
                                modelversion="1.0", artifactversion = "1.0"), content_type="application/json")
        print(response.data)
        assert response.status_code == 200
        assert b'model.zip' == response.data

    @patch('trainingmgr.trainingmgr_main.MM_SDK', return_value=mocked_mm_sdk)
    @patch('trainingmgr.trainingmgr_main.send_file')
    def test_getmodel_model_not_found(self, mock_sendfile, mock_model_metrics_sdk):
        mock_sendfile.side_effect = Exception("An error occurred (404) when calling the HeadObject operation: Not Found")
        response = self.client.get(
            "/model/{modelname}/{modelversion}/{artifactversion}/Model.zip".format(
                modelname="nonexistent_model", modelversion="1.0", artifactversion="1.0"
            ),
            content_type="application/json",
        )
        assert response.status_code == 404
        # Expected response adjusted to match actual API output
        expected_response = {
            "Exception": {
                "error": "Error while downloading model",
                "Model Name": "nonexistent_model",
                "Model Version": "1.0",
                "Artifact Version": "1.0",
                "message": "Model not found"
            }
        }
        actual_response = response.get_json()
        assert actual_response == expected_response, f"Expected: {expected_response}, Got: {actual_response}"
           
    @patch('trainingmgr.trainingmgr_main.MM_SDK', return_value=mocked_mm_sdk)
    @patch('trainingmgr.trainingmgr_main.send_file')
    def test_getmodel_internal_server_error(self, mock_sendfile, mock_model_metrics_sdk):
        mock_sendfile.side_effect = Exception("Some general error occurred")
        response = self.client.get("/model/{modelname}/{modelversion}/{artifactversion}/Model.zip".format(modelname="invalid_model",
                                modelversion="1.0", artifactversion = "1.0"), content_type="application/json")
        
        assert response.status_code == 500
        assert b"error while downloading model" in response.data
    

class TestDataExtractionNotification:
    def setup_method(self):
        self.client = trainingmgr_main.APP.test_client(self)
    
    @pytest.fixture        
    def mock_training_job(self):
        TrainingJob = MagicMock()
        TrainingJob.id = 1
        
        mock_modelId = MagicMock()
        
        mock_modelId.modelname = 'test_model'  # Set the modelname attribute
        mock_modelId.modelversion = '1.0'     # Set the modelversion attribute
        
        TrainingJob.modelId.return_value = mock_modelId
        TrainingJob.model_location = "s3://model-location"
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


    @patch('trainingmgr.trainingmgr_main.check_key_in_dictionary', return_value = False)
    def test_dataextraction_keynotindict(self, mock_check_dict):        
        trainingjob_req = {
                     "trainingjob_id":"123"
        }
        response = self.client.post('/trainingjob/dataExtractionNotification', data = json.dumps(trainingjob_req),
                                    content_type="application/json")
        assert response.status_code == 400
        assert "featuregroup_name or trainingjob_id key not available in request" in str(response.data)
    

    registered_model_list1 = [{ 
        "modelId" : { 
            "artifactVersion" : "0.0.0"
        },
        "modelLocation": "s3://different-location"
    }]
    @patch('trainingmgr.trainingmgr_main.check_key_in_dictionary', return_value = True)
    @patch('trainingmgr.trainingmgr_main.get_training_job')
    @patch('trainingmgr.trainingmgr_main.get_modelinfo_by_modelId_service', return_value = registered_model_list1)
    @patch('trainingmgr.trainingmgr_main.fetch_pipelinename_and_version', return_value = ("", ""))
    def test_dataextraction_trainingModel_error(self, mock_fetchname, mock_getmodelInfo, mock_get_trainingjob, mock_check_dict, mock_training_job):        
        mock_get_trainingjob.return_value = mock_training_job
        trainingjob_req = {
                     "trainingjob_id":"123"
        }
        response = self.client.post('/trainingjob/dataExtractionNotification', data = json.dumps(trainingjob_req),
                                    content_type="application/json")
        assert response.status_code == 500
        assert "Provide retraining pipeline name and version" in str(response.data)
    

    registered_model_list2 = [{ 
        "modelId" : { 
            "artifactVersion" : "0.1.0"
        },
    }]
    @patch('trainingmgr.trainingmgr_main.check_key_in_dictionary', return_value = True)
    @patch('trainingmgr.trainingmgr_main.get_training_job')
    @patch('trainingmgr.trainingmgr_main.get_modelinfo_by_modelId_service', return_value = registered_model_list2)
    @patch('trainingmgr.trainingmgr_main.fetch_pipelinename_and_version', return_value = ("", ""))
    def test_dataextraction_retrainingModel_error(self, mock_fetch_pipeline, mock_getmodelInfo, mock_get_trainingjob, mock_check_dict, mock_training_job):        
        mock_get_trainingjob.return_value = mock_training_job
        trainingjob_req = {
                     "trainingjob_id":"123"
        }
        response = self.client.post('/trainingjob/dataExtractionNotification', data = json.dumps(trainingjob_req),
                                    content_type="application/json")
        assert response.status_code == 500
        assert "Provide retraining pipeline name and version" in str(response.data)


    registered_model_list3 = [{ 
        "modelId" : { 
            "artifactVersion" : "0.0.0"
        },
        "modelLocation": ""
    }]
    @patch('trainingmgr.trainingmgr_main.check_key_in_dictionary', return_value = True)
    @patch('trainingmgr.trainingmgr_main.get_training_job')
    @patch('trainingmgr.trainingmgr_main.get_modelinfo_by_modelId_service', return_value = registered_model_list3)
    @patch('trainingmgr.trainingmgr_main.fetch_pipelinename_and_version', return_value = ("qoe_pipeline", "v1"))
    @patch('trainingmgr.trainingmgr_main.training_start')
    def test_dataextraction_trainingModel_invalidresponse_kf(self, mock_training_start, mock_fetch_pipeline, 
    mock_getmodelInfo, mock_get_trainingjob, mock_check_dict, mock_training_job):        
         
        mock_response_invalid = MagicMock()
        mock_response_invalid.headers = {'content-type': 'text/plain'}
        mock_response_invalid.status_code = 500
        mock_training_start.return_value = mock_response_invalid

        mock_get_trainingjob.return_value = mock_training_job
        trainingjob_req = {
                     "trainingjob_id":"123"
        }

        response = self.client.post('/trainingjob/dataExtractionNotification', data = json.dumps(trainingjob_req), content_type="application/json")
        assert response.status_code == 500


    @patch('trainingmgr.trainingmgr_main.check_key_in_dictionary', return_value = True)
    @patch('trainingmgr.trainingmgr_main.get_training_job')
    @patch('trainingmgr.trainingmgr_main.get_modelinfo_by_modelId_service', return_value = registered_model_list3)
    @patch('trainingmgr.trainingmgr_main.fetch_pipelinename_and_version', return_value = ("qoe_pipeline", "v1"))
    @patch('trainingmgr.trainingmgr_main.training_start')
    @patch('trainingmgr.trainingmgr_main.change_status_tj')
    @patch('trainingmgr.trainingmgr_main.change_update_field_value')
    def test_dataextraction_trainingModel_validresponse_kf(self, mock_update_field_val, mock_change_status,
     mock_training_start, mock_fetch_pipeline, mock_getmodelInfo, mock_get_trainingjob, mock_check_dict, mock_training_job):        
         
        mock_response_valid = MagicMock()
        mock_response_valid.headers = {'content-type': 'application/json'}
        mock_response_valid.status_code = 200
        mock_response_valid.json.return_value = {'run_status': 'scheduled', 'run_id': '123'}
        mock_training_start.return_value = mock_response_valid

        mock_get_trainingjob.return_value = mock_training_job
        trainingjob_req = {
                     "trainingjob_id":"123"
        }
        response = self.client.post('/trainingjob/dataExtractionNotification', data = json.dumps(trainingjob_req),
                                    content_type="application/json")
        assert response.status_code == 200
        assert "pipeline is scheduled" in str(response.data)


class TestPipelineNotification:

    def setup_method(self):
        self.client = trainingmgr_main.APP.test_client(self)

    mocked_mm_sdk = mock.Mock(name="MM_SDK")
    @pytest.fixture        
    def mock_training_job(self):
        TrainingJob = MagicMock()
        TrainingJob.id = 1

        TrainingJob.model_location = "s3://model-location"
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
    
    registered_model_list = [{ 
        "modelId" : { 
            "artifactVersion" : "1.0"
        },
        "modelLocation": "s3://different-location"
    }]
        
    @patch('trainingmgr.trainingmgr_main.MM_SDK', return_value = mocked_mm_sdk)
    @patch('trainingmgr.trainingmgr_main.check_key_in_dictionary', return_value = True)
    @patch('trainingmgr.trainingmgr_main.get_training_job')
    @patch('trainingmgr.trainingmgr_main.change_status_tj')
    @patch('trainingmgr.trainingmgr_main.notification_rapp')
    @patch('trainingmgr.trainingmgr_main.get_modelinfo_by_modelId_service', return_value = registered_model_list)
    @patch('trainingmgr.trainingmgr_main.change_update_field_value')
    
    def test_success(self, mock_update_field_value, mock_get_modelinfo, mock_notification_rapp, mock_change_status, 
    mock_get_trainingjob, mock_check_in_dict, mock_mmsdk, mock_training_job):
        mock_mmsdk.check_object.return_value = True
        mock_get_trainingjob.return_value = mock_training_job
        trainingjob_req = {
                     "trainingjob_id" : "123",
                     "run_status" : "SUCCEEDED"
        }
        response = self.client.post('/trainingjob/pipelineNotification', data = json.dumps(trainingjob_req),
                                    content_type="application/json")
        assert response.status_code == 200
        assert response.json == {'Message': 'Training successful'}


    mocked_mm_sdk_false = mock.Mock(name="MM_SDK")
    @patch('trainingmgr.trainingmgr_main.MM_SDK', return_value = mocked_mm_sdk)
    @patch('trainingmgr.trainingmgr_main.check_key_in_dictionary', return_value = True)
    @patch('trainingmgr.trainingmgr_main.get_training_job')
    @patch('trainingmgr.trainingmgr_main.change_status_tj')
    @patch('trainingmgr.trainingmgr_main.notification_rapp')
    @patch('trainingmgr.trainingmgr_main.get_modelinfo_by_modelId_service', return_value = registered_model_list)
    
    def test_unsuccess_object_not_present_in_mmsdk(self, mock_get_modelinfo, mock_notification_rapp, mock_change_status, 
    mock_get_trainingjob, mock_check_in_dict, mock_mmsdk, mock_training_job):  
        mock_mmsdk.check_object.return_value = False
        mock_get_trainingjob.return_value = mock_training_job
        trainingjob_req = {
                     "trainingjob_id" : "123",
                     "run_status" : "SUCCEEDED"
        }
        response = self.client.post('/trainingjob/pipelineNotification', data = json.dumps(trainingjob_req),
                                    content_type="application/json")
        assert response.status_code == 500    

    @patch('trainingmgr.trainingmgr_main.check_key_in_dictionary', return_value = True)
    @patch('trainingmgr.trainingmgr_main.get_training_job')
    @patch('trainingmgr.trainingmgr_main.change_status_tj')
    @patch('trainingmgr.trainingmgr_main.notification_rapp')
    def test_unsuccess(self, mock_notification_rapp, mock_change_status, mock_get_trainingjob, mock_check_in_dict, 
     mock_training_job):
        mock_get_trainingjob.return_value = mock_training_job
        trainingjob_req = {
                     "trainingjob_id" : "123",
                     "run_status" : "UNSUCCEEDED"
        }
        response = self.client.post('/trainingjob/pipelineNotification', data = json.dumps(trainingjob_req),
                                    content_type="application/json")
        assert response.status_code == 500

class TestFeatureGroupByName:

    def setup_method(self):
        self.client = trainingmgr_main.APP.test_client(self)
    
    @pytest.fixture
    def mock_feature_group(self):
        mock_fg = MagicMock()
        mock_fg.featuregroup_name = "test_featuregroup"
        return mock_fg

    @patch('trainingmgr.trainingmgr_main.get_feature_group_by_name')
    def test_get_feature_group_success(self, mock_get_feature_group):
        mock_get_feature_group.return_value = {"featuregroup_name": "test_featuregroup", "status": "success"}, status.HTTP_200_OK
        
        response = self.client.get("/featureGroup/{featuregroup_name}".format(featuregroup_name = "test_featuregroup"), content_type="application/json")
        assert response.status_code == 200
        assert response.json == {"featuregroup_name": "test_featuregroup", "status": "success"}

    @patch('trainingmgr.trainingmgr_main.get_feature_group_by_name')
    def test_get_feature_group_not_found(self, mock_get_feature_group):
        mock_get_feature_group.return_value = {"Exception": "Feature group not found"}, status.HTTP_404_NOT_FOUND
        
        response = self.client.get("/featureGroup/{featuregroup_name}".format(featuregroup_name = "invalid"), content_type="application/json")
        assert response.status_code == 404
        assert response.json == {"Exception": "Feature group not found"}
    
    @patch('trainingmgr.trainingmgr_main.edit_feature_group_by_name')
    @patch('trainingmgr.trainingmgr_main.FeatureGroupSchema.load')
    def test_put_feature_group_success(self, mock_load, mock_edit_feature_group, mock_feature_group):   
        mock_load.return_value = mock_feature_group
        mock_edit_feature_group.return_value = {"featuregroup_name": "test_featuregroup", "status": "updated"}, status.HTTP_200_OK
        put_data = {"featuregroup_name": "test_featuregroup", "new_field": "value"}
        
        response = self.client.put("/featureGroup/{featuregroup_name}".format(featuregroup_name = "test_featuregroup"), json = put_data)
        assert response.status_code == 200
        assert response.json == {"featuregroup_name": "test_featuregroup", "status": "updated"}


class TestDeleteListOfFeatureGroup:
    
    def setup_method(self):
        self.client = trainingmgr_main.APP.test_client(self)

    @patch('trainingmgr.trainingmgr_main.check_key_in_dictionary', return_value = True)
    @patch('trainingmgr.trainingmgr_main.get_feature_group_by_name_db')
    @patch('trainingmgr.trainingmgr_main.delete_feature_group_by_name')
    @patch('trainingmgr.trainingmgr_main.delete_dme_filtered_data_job')
    def test_delete_feature_group_success(self, mock_delete_dme, mock_delete_fg, mock_get_fg, mock_check_key):
        mock_get_fg.return_value = MagicMock(enable_dme=True, host="localhost", dme_port=8080)
        mock_delete_fg.return_value = None
        mock_delete_dme.return_value.status_code = status.HTTP_204_NO_CONTENT
        
        request_data = {
            "featuregroups_list": [
                {"featureGroup_name": "test_featuregroup"}
            ]
        }
        response = self.client.delete('/featureGroup', json=request_data)
        assert response.status_code == 200
        assert response.json == {"success count": 1, "failure count": 0}

    
    @patch('trainingmgr.trainingmgr_main.check_key_in_dictionary', return_value = True)
    @patch('trainingmgr.trainingmgr_main.get_feature_group_by_name_db')
    @patch('trainingmgr.trainingmgr_main.delete_feature_group_by_name')
    @patch('trainingmgr.trainingmgr_main.delete_dme_filtered_data_job')
    def test_delete_feature_group_failure(self, mock_delete_dme, mock_delete_fg, mock_get_fg, mock_check_key):
        mock_get_fg.return_value = MagicMock(enable_dme=True, host="localhost", dme_port=8080)
        mock_delete_fg.side_effect = Exception("Failed to delete feature group")
        
        request_data = {
            "featuregroups_list": [
                {"featureGroup_name": "test_featuregroup"}
            ]
        }
        response = self.client.delete('/featureGroup', json=request_data)
        assert response.status_code == 200
        assert response.json == {"success count": 0, "failure count": 1}
    
    @patch('trainingmgr.trainingmgr_main.check_key_in_dictionary', return_value = False)
    @patch('trainingmgr.trainingmgr_main.get_feature_group_by_name_db')
    @patch('trainingmgr.trainingmgr_main.delete_feature_group_by_name')
    @patch('trainingmgr.trainingmgr_main.delete_dme_filtered_data_job')
    def test_delete_feature_group_invalid_key(self, mock_delete_dme, mock_delete_fg, mock_get_fg, mock_check_key):
        
        request_data = {
            "featuregroups_list": [
                {"featuregroup_name": "test_featuregroup"}
            ]
        }
        response = self.client.delete('/featureGroup', json=request_data)
        assert response.status_code == 400
        assert "Wrong Request syntax" in response.json["Exception"]

