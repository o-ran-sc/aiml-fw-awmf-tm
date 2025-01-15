# # ==================================================================================
# #
# #       Copyright (c) 2022 Samsung Electronics Co., Ltd. All Rights Reserved.
# #
# #   Licensed under the Apache License, Version 2.0 (the "License");
# #   you may not use this file except in compliance with the License.
# #   You may obtain a copy of the License at
# #
# #          http://www.apache.org/licenses/LICENSE-2.0
# #
# #   Unless required by applicable law or agreed to in writing, software
# #   distributed under the License is distributed on an "AS IS" BASIS,
# #   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# #   See the License for the specific language governing permissions and
# #   limitations under the License.
# #
# # ==================================================================================

# """"
# This file contains the unittesting for Training management utility functions
# """
from mock import patch
import pytest
from flask_api import status
from trainingmgr.common.trainingmgr_util import check_key_in_dictionary, get_metrics , get_one_word_status, \
    get_feature_group_by_name, edit_feature_group_by_name, get_step_in_progress_state
from requests.models import Response   
from trainingmgr import trainingmgr_main
from trainingmgr.common.exceptions_utls import TMException,DBException
trainingmgr_main.LOGGER = pytest.logger
from trainingmgr.models import FeatureGroup
from trainingmgr.trainingmgr_main import APP
from trainingmgr.constants.steps import Steps
import json

class Test_check_key_in_dictionary:
    def test_check_key_in_dictionary(self):
        fields = ["model","brand","year"]
        dictionary =  {
                                    "brand": "Ford",
                                    "model": "Mustang",
                                    "year": 1964
                      }
        assert check_key_in_dictionary(fields, dictionary) == True, "All keys are present, but test-result is False"

    def test_check_key_in_dictionary(self):
        fields = ["model","brand","type"]
        dictionary =  {
                                    "brand": "Ford",
                                    "model": "Mustang",
                                    "year": 1964
                      }
        assert check_key_in_dictionary(fields, dictionary) == False, "Some keys are not present, but test-result is True"
    
    def test_negative_check_key_in_dictionary_1(self):
        fields = ["Ford","Apple","Mosquito"]
        dictionary =  {
                                    "brand": "Ford",
                                    "model": "Mustang",
                                    "year": 1964
                      }
        try:
            check_key_in_dictionary(fields, dictionary)
            assert False
        except Exception:
            assert True


class dummy_mmsdk:
    def __init__(self, check_obj_output, stored_metrics):
        self.check_object_output = check_obj_output
        self.stored_metrics = stored_metrics
    
    def check_object(self, param1, param2, param3):
        return self.check_object_output
    
    def get_metrics(self, trainingjob_name, version):
        return self.stored_metrics


class Test_get_metrics:   
    def test_get_metrics_with_version(self):
        trainingjob_name = "model1"
        version = 1
        expected_metrics = {"a" : 1, "b" : 3}
        got = get_metrics(trainingjob_name, version, dummy_mmsdk(True, expected_metrics))
        assert json.loads(got) == expected_metrics, "data not equal"

    @patch('trainingmgr.common.trainingmgr_util.json.dumps',return_value=None)
    def test_negative_get_metrics_1(self, mock1):
        trainingjob_name = "model1"
        version = 1
        mm_sdk = dummy_mmsdk(True, None)
        try:
            # It MUST Fail
            get_metrics(trainingjob_name, version, mm_sdk)
            assert False
        except TMException as err:
            assert "Problem while downloading metrics" in str(err)
        except Exception as err:
            # Any other exeception leads to test-failure
            print("Your Error as ", err)
            assert False
    
    @patch('trainingmgr.common.trainingmgr_util.json.dumps',return_value=Exception("Problem while downloading metrics"))
    def test_negative_get_metrics_2(self,mock1):
        trainingjob_name = "model1"
        version = 1
        mm_sdk = dummy_mmsdk(True, None)
        try:
            get_metrics(trainingjob_name, version, mm_sdk)
            assert False
        except Exception:
            assert True

    def test_get_metrics_metrics_not_present(self):
        trainingjob_name = "model1"
        version = 1
        expected_metrics = "No data available"
        got = get_metrics(trainingjob_name, version, dummy_mmsdk(False, {}))
        assert got == expected_metrics, "data not equal"


class Test_get_one_word_status:
    def test_get_one_word_status_not_started(self):
           steps_state = {
                    "DATA_EXTRACTION": "NOT_STARTED",
                    "DATA_EXTRACTION_AND_TRAINING": "NOT_STARTED",
                    "TRAINED_MODEL": "NOT_STARTED",
                    "TRAINING": "NOT_STARTED",
                    "TRAINING_AND_TRAINED_MODEL": "NOT_STARTED"
                }
           expected_data = "NOT_STARTED"
           assert get_one_word_status(steps_state) == expected_data,"data not equal"
           
    def test_get_one_word_status_failed(self):
           steps_state = {
                    "DATA_EXTRACTION": "FINISHED",
                    "DATA_EXTRACTION_AND_TRAINING": "FINISHED",
                    "TRAINED_MODEL": "FAILED",
                    "TRAINING": "NOT_STARTED",
                    "TRAINING_AND_TRAINED_MODEL": "NOT_STARTED"
                }
           expected_data = "FAILED"
           assert get_one_word_status(steps_state) == expected_data,"data not equal"
           
    def test_get_one_word_status_finished(self):
           steps_state = {
                    "DATA_EXTRACTION": "FINISHED",
                    "DATA_EXTRACTION_AND_TRAINING": "FINISHED",
                    "TRAINED_MODEL": "FINISHED",
                    "TRAINING": "FINISHED",
                    "TRAINING_AND_TRAINED_MODEL": "FINISHED"
                }
           expected_data = "FINISHED"
           assert get_one_word_status(steps_state) == expected_data,"data not equal"


class Test_get_feature_group_by_name:
    
    featuregroup = FeatureGroup()
    @patch('trainingmgr.common.trainingmgr_util.get_feature_group_by_name_db', return_value=featuregroup)
    def test_get_feature_group_by_name(self, mock1):
        logger = trainingmgr_main.LOGGER
        featuregroup_name = 'testing'
        expected_data = {'bucket': None, 'datalake_source': None, 'db_org': None, 'dme_port': None, 'enable_dme': None, 'feature_list': None, 'featuregroup_name': None, 'host': None, 'id': None, 'measured_obj_class': None, 'measurement': None, 'port': None, 'source_name': None, 'token': None}
        
        with APP.app_context():
            api_response, status_code = get_feature_group_by_name(featuregroup_name, logger)
        json_data = api_response.json
        assert status_code == 200, "status code is not equal"
        assert json_data == expected_data, json_data
        
    @patch('trainingmgr.common.trainingmgr_util.get_feature_group_by_name_db')
    @patch('trainingmgr.common.trainingmgr_util.check_trainingjob_name_or_featuregroup_name')
    def test_negative_get_feature_group_by_name(self, mock1, mock2):

        logger = trainingmgr_main.LOGGER
        fg_name='testing'

        mock1.side_effect = [True, True]
        mock2.side_effect = [None, DBException("Failed to execute query in get_feature_groupsDB ERROR")]

        # Case 1
        expected_data = {'error': "featuregroup with name 'testing' not found"}

        with APP.app_context():
            api_response, status_code = get_feature_group_by_name(fg_name, logger)
        json_data = api_response.json
        assert status_code == 404, "status code is not equal"
        assert json_data == expected_data, json_data

        # Case 2
        expected_data = {"Exception": "Failed to execute query in get_feature_groupsDB ERROR"}
        json_data, status_code = get_feature_group_by_name(fg_name, logger)
        assert status_code == 500, "status code is not equal"
        assert json_data == expected_data, json_data
    
    def test_negative_get_feature_group_by_name_with_incorrect_name(self):
        logger= trainingmgr_main.LOGGER
        fg_name = 'tj*'
        expected_data = {"Exception":"The featuregroup_name is not correct"}
        json_data, status_code = get_feature_group_by_name(fg_name, logger)
        assert status_code == 400, "status code is not equal"
        assert json_data == expected_data, json_data
        

class Test_edit_feature_group_by_name:
    @pytest.fixture
    def get_sample_feature_group(self):
        return FeatureGroup(
        featuregroup_name="SampleFeatureGroup",
        feature_list="feature1,feature2,feature3",
        datalake_source="datalake_source_url",
        host="localhost",
        port="12345",
        bucket="my_bucket",
        token="auth_token",
        db_org="organization_name",
        measurement="measurement_name",
        enable_dme=False,
        measured_obj_class="object_class",
        dme_port="6789",
        source_name="source_name"
        )
    
    @patch('trainingmgr.common.trainingmgr_util.edit_featuregroup')
    def test_edit_feature_group_by_name_dme_disabled(self, mock1, get_sample_feature_group):
        tm_conf_obj=()
        logger = trainingmgr_main.LOGGER
        expected_data = {"result": "Feature Group Edited"}
        
        json_data, status_code = edit_feature_group_by_name(get_sample_feature_group.featuregroup_name, get_sample_feature_group, logger, tm_conf_obj)
        assert status_code == 200, "status code is not equal"
        assert json_data == expected_data, json_data

    # In the case where the feature group is edited, including DME(disabled to enabled)
    the_response2= Response()
    the_response2.status_code = status.HTTP_201_CREATED
    the_response2.headers={"content-type": "application/json"}
    the_response2._content = b''
    @patch('trainingmgr.common.trainingmgr_util.create_dme_filtered_data_job', return_value=the_response2)
    @patch('trainingmgr.common.trainingmgr_util.edit_featuregroup')
    def test_edit_feature_group_by_name_dme_enabled(self, mock1, mock2, get_sample_feature_group):
        tm_conf_obj=()
        logger = trainingmgr_main.LOGGER
        expected_data = {"result": "Feature Group Edited"}
        get_sample_feature_group.enable_dme = True
        json_data, status_code = edit_feature_group_by_name(get_sample_feature_group.featuregroup_name, get_sample_feature_group, logger, tm_conf_obj)
        assert status_code == 200, "status code is not equal"
        assert json_data == expected_data, json_data
    
    
    the_response3= Response()
    the_response3.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    the_response3.headers={"content-type": "application/json"}
    the_response3._content = b''
    @patch('trainingmgr.common.trainingmgr_util.create_dme_filtered_data_job', return_value=the_response3)
    @patch('trainingmgr.common.trainingmgr_util.edit_featuregroup')
    @patch('trainingmgr.common.trainingmgr_util.delete_feature_group_by_name')
    def test_negative_edit_feature_group_by_name(self, mock1, mock2, mock3, get_sample_feature_group):
        tm_conf_obj=()
        logger = trainingmgr_main.LOGGER
        
        # Case 1
        DB_error = DBException("Failed to execute query in delete_feature_groupDB ERROR")
        mock1.side_effect = [DB_error, None]
        expected_data={"Exception": str(DB_error)}
        get_sample_feature_group.enable_dme = True
        json_data, status_code = edit_feature_group_by_name(get_sample_feature_group.featuregroup_name, get_sample_feature_group, logger, tm_conf_obj)
        assert status_code == 400, "status code is not equal"
        assert json_data == expected_data, json_data
        
        # Case 2
        # General Exception
        generalException = Exception("Something went wrong")
        mock1.side_effect = [generalException, None]
        expected_data={"Exception": str(generalException)}
        json_data, status_code = edit_feature_group_by_name(get_sample_feature_group.featuregroup_name, get_sample_feature_group, logger, tm_conf_obj)
        assert status_code == 400, "status code is not equal"
        assert json_data == expected_data, json_data
        
        # Case 3
        mock1.side_effect = None
        expected_data={"Exception": "Cannot create dme job"}
        json_data, status_code = edit_feature_group_by_name(get_sample_feature_group.featuregroup_name, get_sample_feature_group, logger, tm_conf_obj)
        assert status_code == 400, "status code is not equal"
        assert json_data == expected_data, json_data
        
        
    def test_negative_edit_feature_group_by_name_with_incorrect_name(self, get_sample_feature_group):
        tm_conf_obj=()
        logger = trainingmgr_main.LOGGER
        get_sample_feature_group.featuregroup_name = "***" #incorrect-name
        expected_data = {"Exception":"The featuregroup_name is not correct"}
        json_data, status_code = edit_feature_group_by_name(get_sample_feature_group.featuregroup_name, get_sample_feature_group, logger, tm_conf_obj)
        assert status_code == 400, "status code is not equal"
        assert json_data == expected_data, "NOt Correct"

class Test_get_step_in_progress_state:
    def test_success(self):
        steps_state = {
                    "DATA_EXTRACTION": "IN_PROGRESS",
                    "DATA_EXTRACTION_AND_TRAINING": "NOT_STARTED",
                    "TRAINED_MODEL": "NOT_STARTED",
                    "TRAINING": "NOT_STARTED",
                    "TRAINING_AND_TRAINED_MODEL": "NOT_STARTED"
                }
        got = get_step_in_progress_state(steps_state)
        expected = Steps.DATA_EXTRACTION
        assert got == expected, "Data Not equal"
        
    def test_no_state(self):
        steps_state = {
                    "DATA_EXTRACTION": "NOT_STARTED",
                    "DATA_EXTRACTION_AND_TRAINING": "NOT_STARTED",
                    "TRAINED_MODEL": "NOT_STARTED",
                    "TRAINING": "NOT_STARTED",
                    "TRAINING_AND_TRAINED_MODEL": "NOT_STARTED"
                }
        got = get_step_in_progress_state(steps_state)
        expected = None
        assert got == expected, "Data Not equal"
