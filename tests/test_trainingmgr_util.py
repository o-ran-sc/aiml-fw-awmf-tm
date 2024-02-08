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

""""
This file contains the unittesting for Training management utility functions
"""
from pickle import FALSE
import sys
from unittest import mock
from mock import patch
from threading import Lock
import pytest
import datetime
from dotenv import load_dotenv
from flask_api import status
import logging

from trainingmgr.db.trainingmgr_ps_db import PSDB
import trainingmgr.trainingmgr_main
from trainingmgr.common import trainingmgr_util 
from trainingmgr.common.tmgr_logger import TMLogger
from trainingmgr.common.trainingmgr_config import TrainingMgrConfig
from trainingmgr.common.trainingmgr_util import response_for_training, check_key_in_dictionary,check_trainingjob_data, \
    get_one_key, get_metrics, handle_async_feature_engineering_status_exception_case, get_one_word_status, check_trainingjob_data, \
    validate_trainingjob_name, get_all_pipeline_names_svc, check_feature_group_data
from requests.models import Response   
from trainingmgr import trainingmgr_main
from trainingmgr.common.tmgr_logger import TMLogger
from trainingmgr.common.exceptions_utls import APIException,TMException,DBException
trainingmgr_main.LOGGER = pytest.logger

class Test_response_for_training:
    def setup_method(self):
        self.client = trainingmgr_main.APP.test_client(self)
        self.logger = trainingmgr_main.LOGGER

    fs_result = Response()
    fs_result.status_code = status.HTTP_200_OK
    fs_result.headers={'content-type': 'application/json'}

    fs_content_type_error_result = Response()
    fs_content_type_error_result.status_code = status.HTTP_200_OK
    fs_content_type_error_result.headers={'content-type': 'application/jn'}

    fs_status_code_error_result = Response()
    fs_status_code_error_result.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    fs_status_code_error_result.headers={'content-type': 'application/json'}

    @patch('trainingmgr.common.trainingmgr_util.get_field_by_latest_version', return_value=[['www.google.com','h1','h2'], ['www.google.com','h1','h2'], ['www.google.com','h1','h2']])
    @patch('trainingmgr.common.trainingmgr_util.change_field_of_latest_version', return_value=True)
    @patch('trainingmgr.common.trainingmgr_util.get_metrics',return_value="PRESENT")
    @patch('trainingmgr.common.trainingmgr_util.get_latest_version_trainingjob_name', return_value=1)
    @patch('trainingmgr.common.trainingmgr_util.requests.post', return_value=fs_result)
    def test_response_for_training_success(self, mock1, mock2, mock3, mock4, mock5):
        code_success = status.HTTP_200_OK
        code_fail = status.HTTP_500_INTERNAL_SERVER_ERROR
        message_success = "Pipeline notification success."
        message_fail = "Pipeline not successful for "
        logger = trainingmgr_main.LOGGER
        is_success = True
        is_fail = False
        trainingjob_name = "usecase7"
        ps_db_obj = ()
        mm_sdk = ()
        result = response_for_training(code_success, message_success, logger, is_success, trainingjob_name, ps_db_obj, mm_sdk)
        assert message_success == result[0]['result']
        result = response_for_training(code_fail, message_fail, logger, is_fail, trainingjob_name, ps_db_obj, mm_sdk)
        assert message_fail == result[0]['Exception']

    @patch('trainingmgr.common.trainingmgr_util.get_field_by_latest_version', return_value=[['www.google.com','h1','h2'], ['www.google.com','h1','h2'], ['www.google.com','h1','h2']])
    @patch('trainingmgr.common.trainingmgr_util.change_field_of_latest_version', return_value=True)
    @patch('trainingmgr.common.trainingmgr_util.get_metrics', return_value="PRESENT")
    @patch('trainingmgr.common.trainingmgr_util.get_latest_version_trainingjob_name', return_value=1)
    @patch('trainingmgr.common.trainingmgr_util.requests.post', side_effect = Exception)
    @patch('trainingmgr.common.trainingmgr_util.change_in_progress_to_failed_by_latest_version', return_value=True)
    def test_response_for_training_fail_post_req(self, mock1, mock2, mock3, mock4, mock5, mock6):
        code = status.HTTP_200_OK
        message = "Pipeline notification success."
        logger = trainingmgr_main.LOGGER
        is_success = True
        trainingjob_name = "usecase7"
        ps_db_obj = ()
        mm_sdk = ()
        try:
            response_for_training(code, message, logger, is_success, trainingjob_name, ps_db_obj, mm_sdk)
            assert False
        except APIException as err:
            assert err.code == status.HTTP_500_INTERNAL_SERVER_ERROR
        except Exception:
            assert False
    
    @patch('trainingmgr.common.trainingmgr_util.get_field_by_latest_version', return_value=[['www.google.com','h1','h2'], ['www.google.com','h1','h2'], ['www.google.com','h1','h2']])
    @patch('trainingmgr.common.trainingmgr_util.change_field_of_latest_version', return_value=True)
    @patch('trainingmgr.common.trainingmgr_util.get_metrics', return_value="PRESENT")
    @patch('trainingmgr.common.trainingmgr_util.get_latest_version_trainingjob_name', return_value=1)
    @patch('trainingmgr.common.trainingmgr_util.requests.post', return_value=fs_content_type_error_result)
    @patch('trainingmgr.common.trainingmgr_util.change_in_progress_to_failed_by_latest_version', return_value=True)
    def test_response_for_training_fail_res_content_type(self, mock1, mock2, mock3, mock4, mock5, mock6):
        code = status.HTTP_200_OK
        message = "Pipeline notification success."
        logger = trainingmgr_main.LOGGER
        is_success = True
        trainingjob_name = "usecase7"
        ps_db_obj = ()
        mm_sdk = ()
        try:
            response_for_training(code, message, logger, is_success, trainingjob_name, ps_db_obj, mm_sdk)
            assert False
        except APIException as err:
            assert "Failed to notify the subscribed url " + trainingjob_name in err.message
        except Exception:
            assert False

    @patch('trainingmgr.common.trainingmgr_util.get_field_by_latest_version', return_value=[['www.google.com','h1','h2'], ['www.google.com','h1','h2'], ['www.google.com','h1','h2']])
    @patch('trainingmgr.common.trainingmgr_util.change_field_of_latest_version', return_value=True)
    @patch('trainingmgr.common.trainingmgr_util.get_metrics', return_value="PRESENT")
    @patch('trainingmgr.common.trainingmgr_util.get_latest_version_trainingjob_name', return_value=1)
    @patch('trainingmgr.common.trainingmgr_util.requests.post', return_value=fs_status_code_error_result)
    @patch('trainingmgr.common.trainingmgr_util.change_in_progress_to_failed_by_latest_version', return_value=True)
    def test_response_for_training_fail_res_status_code(self, mock1, mock2, mock3, mock4, mock5, mock6):
        code = status.HTTP_200_OK
        message = "Pipeline notification success."
        logger = trainingmgr_main.LOGGER
        is_success = True
        trainingjob_name = "usecase7"
        ps_db_obj = ()
        mm_sdk = ()
        try:
            response_for_training(code, message, logger, is_success, trainingjob_name, ps_db_obj, mm_sdk)
            assert False
        except APIException as err:
            assert "Failed to notify the subscribed url " + trainingjob_name in err.message
        except Exception:
            assert False
    
    @patch('trainingmgr.common.trainingmgr_util.get_field_by_latest_version', return_value=None)
    def test_response_for_training_none_get_field_by_latest_version(self, mock1):
        code_success = status.HTTP_200_OK
        code_fail = status.HTTP_500_INTERNAL_SERVER_ERROR
        message_success = "Pipeline notification success."
        message_fail = "Pipeline not successful for "
        logger = trainingmgr_main.LOGGER
        is_success = True
        is_fail = False
        trainingjob_name = "usecase7"
        ps_db_obj = ()
        mm_sdk = ()
        result = response_for_training(code_success, message_success, logger, is_success, trainingjob_name, ps_db_obj, mm_sdk)
        assert message_success == result[0]['result']
        result = response_for_training(code_fail, message_fail, logger, is_fail, trainingjob_name, ps_db_obj, mm_sdk)
        assert message_fail == result[0]['Exception']

    @patch('trainingmgr.common.trainingmgr_util.get_field_by_latest_version', side_effect = Exception)
    @patch('trainingmgr.common.trainingmgr_util.change_in_progress_to_failed_by_latest_version', return_value=True)
    def test_response_for_training_fail_get_field_by_latest_version(self, mock1, mock2):
        code = status.HTTP_200_OK
        message = "Pipeline notification success."
        logger = trainingmgr_main.LOGGER
        is_success = True
        trainingjob_name = "usecase7"
        ps_db_obj = ()
        mm_sdk = ()
        try:
            response_for_training(code, message, logger, is_success, trainingjob_name, ps_db_obj, mm_sdk)
            assert False
        except APIException as err:
            assert err.code == status.HTTP_500_INTERNAL_SERVER_ERROR
        except Exception:
            assert False

    @patch('trainingmgr.common.trainingmgr_util.get_field_by_latest_version', return_value=[['www.google.com','h1','h2'], ['www.google.com','h1','h2'], ['www.google.com','h1','h2']])
    @patch('trainingmgr.common.trainingmgr_util.get_latest_version_trainingjob_name', side_effect = Exception)
    @patch('trainingmgr.common.trainingmgr_util.change_in_progress_to_failed_by_latest_version', return_value=True)
    def test_response_for_training_fail_get_latest_version_trainingjob_name(self, mock1, mock2, mock3):
        code = status.HTTP_200_OK
        message = "Pipeline notification success."
        logger = trainingmgr_main.LOGGER
        is_success = True
        trainingjob_name = "usecase7"
        ps_db_obj = ()
        mm_sdk = ()
        try:
            response_for_training(code, message, logger, is_success, trainingjob_name, ps_db_obj, mm_sdk)
            assert False
        except APIException as err:
            assert err.code == status.HTTP_500_INTERNAL_SERVER_ERROR
        except Exception:
            assert False

    @patch('trainingmgr.common.trainingmgr_util.get_field_by_latest_version', return_value=[['www.google.com','h1','h2'], ['www.google.com','h1','h2'], ['www.google.com','h1','h2']])
    @patch('trainingmgr.common.trainingmgr_util.get_latest_version_trainingjob_name', return_value=1)
    @patch('trainingmgr.common.trainingmgr_util.get_metrics', side_effect = Exception)
    @patch('trainingmgr.common.trainingmgr_util.change_in_progress_to_failed_by_latest_version', return_value=True)
    def test_response_for_training_fail_get_metrics(self, mock1, mock2, mock3, mock4):
        code = status.HTTP_200_OK
        message = "Pipeline notification success."
        logger = trainingmgr_main.LOGGER
        is_success = True
        trainingjob_name = "usecase7"
        ps_db_obj = ()
        mm_sdk = ()
        try:
            response_for_training(code, message, logger, is_success, trainingjob_name, ps_db_obj, mm_sdk)
            assert False
        except APIException as err:
            assert err.code == status.HTTP_500_INTERNAL_SERVER_ERROR
        except Exception:
            assert False

    #TODO It needs to check DBException instead of APIException is correct.
    @patch('trainingmgr.common.trainingmgr_util.get_field_by_latest_version', return_value=[['www.google.com','h1','h2'], ['www.google.com','h1','h2'], ['www.google.com','h1','h2']])
    @patch('trainingmgr.common.trainingmgr_util.get_latest_version_trainingjob_name', return_value=1)
    @patch('trainingmgr.common.trainingmgr_util.get_metrics', return_value="PRESENT")
    @patch('trainingmgr.common.trainingmgr_util.requests.post', return_value=fs_result)
    @patch('trainingmgr.common.trainingmgr_util.change_in_progress_to_failed_by_latest_version', side_effect = Exception)
    def test_response_for_training_fail_change_in_progress_to_failed_by_latest_version(self, mock1, mock2, mock3, mock4, mock5):
        code = status.HTTP_200_OK
        message = "Pipeline notification success."
        logger = trainingmgr_main.LOGGER
        is_success = True
        trainingjob_name = "usecase7"
        ps_db_obj = ()
        mm_sdk = ()
        try:
            response_for_training(code, message, logger, is_success, trainingjob_name, ps_db_obj, mm_sdk)
            assert False
        except Exception:
            assert True

class Test_check_key_in_dictionary:
    def test_check_key_in_dictionary(self):
        fields = ["model","brand","year"]
        dictionary =  {
                                    "brand": "Ford",
                                    "model": "Mustang",
                                    "year": 1964
                      }
        assert check_key_in_dictionary(fields, dictionary) == True, "data not equal"

    def test_check_key_in_dictionary(self):
        fields = ["model","brand","type"]
        dictionary =  {
                                    "brand": "Ford",
                                    "model": "Mustang",
                                    "year": 1964
                      }
        assert check_key_in_dictionary(fields, dictionary) == False, "data not equal"
    
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

class Test_check_trainingjob_data:    
    @patch('trainingmgr.common.trainingmgr_util.check_key_in_dictionary',return_value=True)
    @patch('trainingmgr.common.trainingmgr_util.isinstance',return_value=True)  
    def test_check_trainingjob_data(self,mock1,mock2):
        usecase_name = "usecase8"
        json_data = { "description":"unittest", "featureGroup_name": "group1" , "pipeline_name":"qoe" , "experiment_name":"experiment1" , "arguments":"arguments1" , "query_filter":"query1" , "enable_versioning":True , "target_deployment":"Near RT RIC" , "pipeline_version":1 , "datalake_source":"cassandra db" , "incremental_training":True , "model":"usecase7" , "model_version":1 , "_measurement":2 , "bucket":"bucket1", "is_mme":False, "model_name":""}
    
        expected_data = ("group1", 'unittest', 'qoe', 'experiment1', 'arguments1', 'query1', True, 1, 'cassandra db', 2, 'bucket1',False, "")
        assert check_trainingjob_data(usecase_name, json_data) == expected_data,"data not equal"
    
    def test_negative_check_trainingjob_data_1(self):
        usecase_name = "usecase8"
        json_data = { "description":"unittest", "featureGroup_name": "group1" , "pipeline_name":"qoe" , "experiment_name":"experiment1" , "arguments":"arguments1" , "query_filter":"query1" , "enable_versioning":True , "target_deployment":"Near RT RIC" , "pipeline_version":1 , "datalake_source":"cassandra db" , "incremental_training":True , "model":"usecase7" , "model_version":1 , "_measurement":2 , "bucket":"bucket1", "is_mme":False, "model_name":""}
    
        expected_data = ("group1", 'unittest', 'qoe', 'experiment1', 'arguments1', 'query1', True, 1, 'cassandra db', 2, 'bucket1',False, "")
        try:
            assert check_trainingjob_data(usecase_name, json_data) == expected_data,"data not equal"
            assert False
        except Exception:
            assert True

    @patch('trainingmgr.common.trainingmgr_util.check_key_in_dictionary',return_value=True)
    def test_negative_check_trainingjob_data_2(self,mock1):
        usecase_name = "usecase8"
        json_data = { "description":"unittest", "featureGroup_name": "group1" , "pipeline_name":"qoe" , "experiment_name":"experiment1" , "arguments":"arguments1" , "query_filter":"query1" , "enable_versioning":True , "target_deployment":"Near RT RIC" , "pipeline_version":1 , "datalake_source":"cassandra db" , "incremental_training":True , "model":"usecase7" , "model_version":1 , "_measurement":2 , "bucket":"bucket1"}
    
        expected_data = ("group1", 'unittest', 'qoe', 'experiment1', 'arguments1', 'query1', True, 1, 'cassandra db', 2, 'bucket1')
        try:
            assert check_trainingjob_data(usecase_name, json_data) == expected_data,"data not equal"
            assert False
        except Exception:
            assert True
    
    @patch('trainingmgr.common.trainingmgr_util.isinstance',return_value=True)
    def test_negative_check_trainingjob_data_3(self,mock1):
        usecase_name = "usecase8"
        json_data = None
        expected_data = ("group1", 'unittest', 'qoe', 'experiment1', 'arguments1', 'query1', True, 1, 'cassandra db', 2, 'bucket1')
        try:
            assert check_trainingjob_data(usecase_name, json_data) == expected_data,"data not equal"
            assert False
        except Exception:
            assert True

class Test_get_one_key:
    def test_get_one_key(self):
        dictionary = {
                        "brand": "Ford",
                        "model": "Mustang",
                        "year": 1964
                    }
        only_key = "year"
        expected_data = only_key
        assert get_one_key(dictionary) == expected_data,"data not equal"
    
    def test_get_one_key_2(self):
        dictionary = {'name': 'Jack', 'age': 26}
        only_key = "age"
        expected_data = only_key
        assert get_one_key(dictionary) == expected_data,"data not equal"
    
    def test_negative_get_one_key_1(self):
        dictionary = {
                        "brand": "Ford",
                        "model": "Mustang",
                        "year": 1964
                    }
        only_key = "model"
        expected_data = only_key
        try:
            assert get_one_key(dictionary) == expected_data,"data not equal"
            assert False
        except Exception:
            assert True
    
    def test_negative_get_one_key_2(self):
        dictionary = {'name': 'Jack', 'age': 26}
        only_key = "name"
        expected_data = only_key
        try:
            assert get_one_key(dictionary) == expected_data,"data not equal"
            assert False
        except Exception:
            assert True

class dummy_mmsdk:
    def check_object(self, param1, param2, param3):
        return True
    
    def get_metrics(self, usecase_name, version):
        thisdict = {
                     "brand": "Ford",
                     "model": "Mustang",
                     "year": 1964
                    }
        return thisdict
    
class Test_get_metrics:   
    @patch('trainingmgr.common.trainingmgr_util.json.dumps',return_value='usecase_data')
    def test_get_metrics_with_version(self,mock1):
        usecase_name = "usecase7"
        version = 1
        mm_sdk = dummy_mmsdk()
        expected_data = 'usecase_data'
        get_metrics(usecase_name, version, dummy_mmsdk())
        assert get_metrics(usecase_name, version, mm_sdk) == expected_data, "data not equal"

    @patch('trainingmgr.common.trainingmgr_util.json.dumps',return_value=None)
    def test_negative_get_metrics_1(self,mock1):
        usecase_name = "usecase7"
        version = 1
        mm_sdk = dummy_mmsdk()
        expected_data = 'usecase_data'
        try:
            assert get_metrics(usecase_name, version, mm_sdk) == expected_data, "data not equal"
            assert False
        except Exception:
            assert True
    
    @patch('trainingmgr.common.trainingmgr_util.json.dumps',return_value=Exception("Problem while downloading metrics"))
    def test_negative_get_metrics_2(self,mock1):
        usecase_name = "usecase7"
        version = 1
        mm_sdk = dummy_mmsdk()
        expected_data = 'usecase_data'
        try:
            assert get_metrics(usecase_name, version, mm_sdk) == expected_data, "data not equal"
            assert False
        except Exception:
            assert True

    def test_negative_get_metrics_3(self):
        usecase_name = "usecase7"
        version = 1
        mm_sdk = dummy_mmsdk()
        expected_data = 'final_data'
        try:
            get_metrics(usecase_name, version, dummy_mmsdk())
            assert get_metrics(usecase_name, version, mm_sdk) == expected_data, "data not equal"
            assert False
        except Exception:
            assert True

class dummy_mmsdk_1:
    def check_object(self, param1, param2, param3):
        return False
    
    def get_metrics(self, usecase_name, version):
        thisdict = {
                     "brand": "Ford",
                     "model": "Mustang",
                     "year": 1964
                    }
        return thisdict

class Test_get_metrics_2:   
    @patch('trainingmgr.common.trainingmgr_util.json.dumps',return_value='usecase_data')
    def test_negative_get_metrics_2_1(self,mock1):
        usecase_name = "usecase7"
        version = 1
        mm_sdk = dummy_mmsdk_1()
        expected_data = 'usecase_data'
        get_metrics(usecase_name, version, dummy_mmsdk())
        try:
            get_metrics(usecase_name, version, dummy_mmsdk())
            assert get_metrics(usecase_name, version, mm_sdk) == expected_data, "data not equal"
            assert False
        except Exception:
            assert True

class Test_handle_async_feature_engineering_status_exception_case:
    @patch('trainingmgr.common.trainingmgr_util.change_in_progress_to_failed_by_latest_version',return_value=True)
    @patch('trainingmgr.common.trainingmgr_util.response_for_training',return_value=True)
    def test_handle_async_feature_engineering_status_exception_case(self, mock1, mock2):
           lock = Lock()
           featurestore_job_cache = {'usecase7': 'Geeks', 2: 'For', 3: 'Geeks'}
           code = 123
           message = "Into the field" 
           logger = "123"
           is_success = True
           usecase_name = "usecase7"
           ps_db_obj = () 
           mm_sdk = ()       
           assert handle_async_feature_engineering_status_exception_case(lock, featurestore_job_cache, code,
                                                           message, logger, is_success,
                                                           usecase_name, ps_db_obj, mm_sdk) == None,"data not equal"
    
    @patch('trainingmgr.common.trainingmgr_util.change_in_progress_to_failed_by_latest_version',return_value=True)
    @patch('trainingmgr.common.trainingmgr_util.response_for_training',return_value=True)
    # @patch('trainingmgr.common.trainingmgr_util.dataextraction_job_cache',return_value = Exception("Could not get info from db for "))
    def test_negative_handle_async_feature_engineering_status_exception_case(self, mock1, mock2):
           lock = Lock()
           featurestore_job_cache = {'usecase7': 'Geeks', 2: 'For', 3: 'Geeks'}
           code = 123
           message = "Into the field" 
           logger = "123"
           is_success = True
           usecase_name = ""
           ps_db_obj = () 
           mm_sdk = ()    
           try:   
               handle_async_feature_engineering_status_exception_case(lock, featurestore_job_cache, code,
                                                           message, logger, is_success,
                                                           usecase_name, ps_db_obj, mm_sdk)
               assert handle_async_feature_engineering_status_exception_case(lock, featurestore_job_cache, code,
                                                           message, logger, is_success,
                                                           usecase_name, ps_db_obj, mm_sdk) == None,"data not equal"
               assert False
           except Exception:
               assert True

class Test_get_one_word_status:
    def test_get_one_word_status(self):
           steps_state = [0,1,2,3]
           expected_data = "IN_PROGRESS"
           assert get_one_word_status(steps_state) == expected_data,"data not equal"

class Test_validate_trainingjob_name:
    @patch('trainingmgr.common.trainingmgr_util.get_all_versions_info_by_name',return_value=True)
    def test_validate_trainingjob_name_1(self,mock1):
        trainingjob_name = "usecase8"
        ps_db_obj = ()
        expected_data = True
        assert validate_trainingjob_name(trainingjob_name,ps_db_obj) == expected_data,"data not equal"

    @patch('trainingmgr.common.trainingmgr_util.get_all_versions_info_by_name', side_effect = DBException)
    def test_validate_trainingjob_name_2(self,mock1):
        trainingjob_name = "usecase8"
        ps_db_obj = ()
        try:
            validate_trainingjob_name(trainingjob_name,ps_db_obj)
            assert False
        except DBException as err:
            assert 'Could not get info from db for ' + trainingjob_name in str(err)
    
    def test_negative_validate_trainingjob_name(self):
        short_name = "__"
        long_name = "abcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyz"
        not_allowed_symbol_name = "case@#"
        ps_db_obj = ()
        try:
            validate_trainingjob_name(short_name,ps_db_obj)
            assert False
        except TMException as err:
            assert str(err) == "The name of training job is invalid."
        try:
            validate_trainingjob_name(long_name,ps_db_obj)
        except TMException as err:
            assert str(err) == "The name of training job is invalid."
        try:
            validate_trainingjob_name(not_allowed_symbol_name,ps_db_obj)
        except TMException as err:
            assert str(err) == "The name of training job is invalid."

class Test_get_all_pipeline_names_svc:
    # testing the get_all_pipeline service
    def setup_method(self):
        self.client = trainingmgr_main.APP.test_client(self)
        self.logger = trainingmgr_main.LOGGER
    
    the_response = Response()
    the_response.code = "expired"
    the_response.error_type = "expired"
    the_response.status_code = 200
    the_response.headers={"content-type": "application/json"}
    the_response._content = b'{ "qoe_Pipeline":"id1"}'

    mocked_TRAININGMGR_CONFIG_OBJ=mock.Mock(name="TRAININGMGR_CONFIG_OBJ")
    attrs_TRAININGMGR_CONFIG_OBJ = {'kf_adapter_ip.return_value': '123', 'kf_adapter_port.return_value' : '100'}
    mocked_TRAININGMGR_CONFIG_OBJ.configure_mock(**attrs_TRAININGMGR_CONFIG_OBJ)
    
    @patch('trainingmgr.trainingmgr_main.TRAININGMGR_CONFIG_OBJ', return_value = mocked_TRAININGMGR_CONFIG_OBJ)
    @patch('trainingmgr.trainingmgr_main.requests.get', return_value = the_response)
    def test_get_all_pipeline_names(self,mock1, mock2):
        expected_data=['qoe_Pipeline']
        assert get_all_pipeline_names_svc(self.mocked_TRAININGMGR_CONFIG_OBJ) ==expected_data, "Not equal"

class Test_check_feature_group_data:
    @patch('trainingmgr.common.trainingmgr_util.check_key_in_dictionary',return_value=True)
    def test_check_feature_group_data(self, mock1):
        json_data={
                            "featureGroupName": "test",
                            "feature_list": "",
                            "datalake_source": "",
                            "enable_Dme": False,
                            "Host": "",
                            "Port": "",
                            "bucket": "",
                            "dmePort":"",
                            '_measurement':"",
                            "token": "",
                            "source_name": "",
                            "measured_obj_class":"",
                            "dbOrg": ""
                                }
        expected_data=("test", "", "",False,"","","","","","","","","")
        assert check_feature_group_data(json_data)==expected_data, "data not equal"

    @patch('trainingmgr.common.trainingmgr_util.check_key_in_dictionary',return_value=False)
    def test_negative_check_feature_group_data(self, mock1):
        json_data={
                            "featureGroupName": "test",
                            "feature_list": "",
                            "datalake_source": "",
                            "enable_Dme": False,
                            "Host": "",
                            "Port": "",
                            "bucket": "",
                            '_measurement':"",
                            "dmePort":"",
                            "token": "",
                            "source_name": "",
                            "measured_obj_class":"",
                            "dbOrg": ""
                                }
        expected_data=("test", "", "",False,"","","","","","","","","")
        try:
            assert check_feature_group_data(json_data)==expected_data, 'data not equal'
            assert False
        except:
            assert True
