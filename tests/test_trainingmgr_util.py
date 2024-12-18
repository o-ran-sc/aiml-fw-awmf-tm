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
# from pickle import FALSE
# import sys
# from unittest import mock
# from mock import patch
# from threading import Lock
# import pytest
# import datetime
# from dotenv import load_dotenv
# from flask_api import status
# import logging

# from trainingmgr.db.trainingmgr_ps_db import PSDB
# import trainingmgr.trainingmgr_main
# from trainingmgr.common import trainingmgr_util 
# from trainingmgr.common.tmgr_logger import TMLogger
# from trainingmgr.common.trainingmgr_config import TrainingMgrConfig
# from trainingmgr.common.trainingmgr_util import response_for_training, check_key_in_dictionary,check_trainingjob_data, \
#     get_one_key, get_metrics, handle_async_feature_engineering_status_exception_case, get_one_word_status, check_trainingjob_data, \
#     check_feature_group_data, get_feature_group_by_name, edit_feature_group_by_name
# from requests.models import Response   
# from trainingmgr import trainingmgr_main
# # from trainingmgr.common.tmgr_logger import TMLogger
# from trainingmgr.common.exceptions_utls import APIException,TMException,DBException
# trainingmgr_main.LOGGER = pytest.logger
# from trainingmgr.models import FeatureGroup
# from trainingmgr.trainingmgr_main import APP

# @pytest.mark.skip("")
# class Test_response_for_training:
#     def setup_method(self):
#         self.client = trainingmgr_main.APP.test_client(self)
#         self.logger = trainingmgr_main.LOGGER

#     fs_result = Response()
#     fs_result.status_code = status.HTTP_200_OK
#     fs_result.headers={'content-type': 'application/json'}

#     fs_content_type_error_result = Response()
#     fs_content_type_error_result.status_code = status.HTTP_200_OK
#     fs_content_type_error_result.headers={'content-type': 'application/jn'}

#     fs_status_code_error_result = Response()
#     fs_status_code_error_result.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
#     fs_status_code_error_result.headers={'content-type': 'application/json'}

#     @patch('trainingmgr.common.trainingmgr_util.get_field_by_latest_version', return_value=[['www.google.com','h1','h2'], ['www.google.com','h1','h2'], ['www.google.com','h1','h2']])
#     @patch('trainingmgr.common.trainingmgr_util.change_field_of_latest_version', return_value=True)
#     @patch('trainingmgr.common.trainingmgr_util.get_metrics',return_value="PRESENT")
#     @patch('trainingmgr.common.trainingmgr_util.get_latest_version_trainingjob_name', return_value=1)
#     @patch('trainingmgr.common.trainingmgr_util.requests.post', return_value=fs_result)
#     def test_response_for_training_success(self, mock1, mock2, mock3, mock4, mock5):
#         code_success = status.HTTP_200_OK
#         code_fail = status.HTTP_500_INTERNAL_SERVER_ERROR
#         message_success = "Pipeline notification success."
#         message_fail = "Pipeline not successful for "
#         logger = trainingmgr_main.LOGGER
#         is_success = True
#         is_fail = False
#         trainingjob_name = "usecase7"
#         mm_sdk = ()
#         result = response_for_training(code_success, message_success, logger, is_success, trainingjob_name, mm_sdk)
#         assert message_success == result[0]['result']
#         result = response_for_training(code_fail, message_fail, logger, is_fail, trainingjob_name, mm_sdk)
#         assert message_fail == result[0]['Exception']

#     @patch('trainingmgr.common.trainingmgr_util.get_field_by_latest_version', return_value=[['www.google.com','h1','h2'], ['www.google.com','h1','h2'], ['www.google.com','h1','h2']])
#     @patch('trainingmgr.common.trainingmgr_util.change_field_of_latest_version', return_value=True)
#     @patch('trainingmgr.common.trainingmgr_util.get_metrics', return_value="PRESENT")
#     @patch('trainingmgr.common.trainingmgr_util.get_latest_version_trainingjob_name', return_value=1)
#     @patch('trainingmgr.common.trainingmgr_util.requests.post', side_effect = Exception)
#     @patch('trainingmgr.common.trainingmgr_util.change_in_progress_to_failed_by_latest_version', return_value=True)
#     def test_response_for_training_fail_post_req(self, mock1, mock2, mock3, mock4, mock5, mock6):
#         code = status.HTTP_200_OK
#         message = "Pipeline notification success."
#         logger = trainingmgr_main.LOGGER
#         is_success = True
#         trainingjob_name = "usecase7"
#         mm_sdk = ()
#         try:
#             response_for_training(code, message, logger, is_success, trainingjob_name, mm_sdk)
#             assert False
#         except APIException as err:
#             assert err.code == status.HTTP_500_INTERNAL_SERVER_ERROR
#         except Exception:
#             assert False
    
#     @patch('trainingmgr.common.trainingmgr_util.get_field_by_latest_version', return_value=[['www.google.com','h1','h2'], ['www.google.com','h1','h2'], ['www.google.com','h1','h2']])
#     @patch('trainingmgr.common.trainingmgr_util.change_field_of_latest_version', return_value=True)
#     @patch('trainingmgr.common.trainingmgr_util.get_metrics', return_value="PRESENT")
#     @patch('trainingmgr.common.trainingmgr_util.get_latest_version_trainingjob_name', return_value=1)
#     @patch('trainingmgr.common.trainingmgr_util.requests.post', return_value=fs_content_type_error_result)
#     @patch('trainingmgr.common.trainingmgr_util.change_in_progress_to_failed_by_latest_version', return_value=True)
#     def test_response_for_training_fail_res_content_type(self, mock1, mock2, mock3, mock4, mock5, mock6):
#         code = status.HTTP_200_OK
#         message = "Pipeline notification success."
#         logger = trainingmgr_main.LOGGER
#         is_success = True
#         trainingjob_name = "usecase7"
#         mm_sdk = ()
#         try:
#             response_for_training(code, message, logger, is_success, trainingjob_name, mm_sdk)
#             assert False
#         except APIException as err:
#             assert "Failed to notify the subscribed url " + trainingjob_name in err.message
#         except Exception:
#             assert False

#     @patch('trainingmgr.common.trainingmgr_util.get_field_by_latest_version', return_value=[['www.google.com','h1','h2'], ['www.google.com','h1','h2'], ['www.google.com','h1','h2']])
#     @patch('trainingmgr.common.trainingmgr_util.change_field_of_latest_version', return_value=True)
#     @patch('trainingmgr.common.trainingmgr_util.get_metrics', return_value="PRESENT")
#     @patch('trainingmgr.common.trainingmgr_util.get_latest_version_trainingjob_name', return_value=1)
#     @patch('trainingmgr.common.trainingmgr_util.requests.post', return_value=fs_status_code_error_result)
#     @patch('trainingmgr.common.trainingmgr_util.change_in_progress_to_failed_by_latest_version', return_value=True)
#     def test_response_for_training_fail_res_status_code(self, mock1, mock2, mock3, mock4, mock5, mock6):
#         code = status.HTTP_200_OK
#         message = "Pipeline notification success."
#         logger = trainingmgr_main.LOGGER
#         is_success = True
#         trainingjob_name = "usecase7"
#         mm_sdk = ()
#         try:
#             response_for_training(code, message, logger, is_success, trainingjob_name, mm_sdk)
#             assert False
#         except APIException as err:
#             assert "Failed to notify the subscribed url " + trainingjob_name in err.message
#         except Exception:
#             assert False
    
#     @patch('trainingmgr.common.trainingmgr_util.get_field_by_latest_version', return_value=None)
#     def test_response_for_training_none_get_field_by_latest_version(self, mock1):
#         code_success = status.HTTP_200_OK
#         code_fail = status.HTTP_500_INTERNAL_SERVER_ERROR
#         message_success = "Pipeline notification success."
#         message_fail = "Pipeline not successful for "
#         logger = trainingmgr_main.LOGGER
#         is_success = True
#         is_fail = False
#         trainingjob_name = "usecase7"
#         mm_sdk = ()
#         result = response_for_training(code_success, message_success, logger, is_success, trainingjob_name, mm_sdk)
#         assert message_success == result[0]['result']
#         result = response_for_training(code_fail, message_fail, logger, is_fail, trainingjob_name, mm_sdk)
#         assert message_fail == result[0]['Exception']

#     @patch('trainingmgr.common.trainingmgr_util.get_field_by_latest_version', side_effect = Exception)
#     @patch('trainingmgr.common.trainingmgr_util.change_in_progress_to_failed_by_latest_version', return_value=True)
#     def test_response_for_training_fail_get_field_by_latest_version(self, mock1, mock2):
#         code = status.HTTP_200_OK
#         message = "Pipeline notification success."
#         logger = trainingmgr_main.LOGGER
#         is_success = True
#         trainingjob_name = "usecase7"
#         mm_sdk = ()
#         try:
#             response_for_training(code, message, logger, is_success, trainingjob_name, mm_sdk)
#             assert False
#         except APIException as err:
#             assert err.code == status.HTTP_500_INTERNAL_SERVER_ERROR
#         except Exception:
#             assert False

#     @patch('trainingmgr.common.trainingmgr_util.get_field_by_latest_version', return_value=[['www.google.com','h1','h2'], ['www.google.com','h1','h2'], ['www.google.com','h1','h2']])
#     @patch('trainingmgr.common.trainingmgr_util.get_latest_version_trainingjob_name', side_effect = Exception)
#     @patch('trainingmgr.common.trainingmgr_util.change_in_progress_to_failed_by_latest_version', return_value=True)
#     def test_response_for_training_fail_get_latest_version_trainingjob_name(self, mock1, mock2, mock3):
#         code = status.HTTP_200_OK
#         message = "Pipeline notification success."
#         logger = trainingmgr_main.LOGGER
#         is_success = True
#         trainingjob_name = "usecase7"
#         mm_sdk = ()
#         try:
#             response_for_training(code, message, logger, is_success, trainingjob_name, mm_sdk)
#             assert False
#         except APIException as err:
#             assert err.code == status.HTTP_500_INTERNAL_SERVER_ERROR
#         except Exception:
#             assert False

#     @patch('trainingmgr.common.trainingmgr_util.get_field_by_latest_version', return_value=[['www.google.com','h1','h2'], ['www.google.com','h1','h2'], ['www.google.com','h1','h2']])
#     @patch('trainingmgr.common.trainingmgr_util.get_latest_version_trainingjob_name', return_value=1)
#     @patch('trainingmgr.common.trainingmgr_util.get_metrics', side_effect = Exception)
#     @patch('trainingmgr.common.trainingmgr_util.change_in_progress_to_failed_by_latest_version', return_value=True)
#     def test_response_for_training_fail_get_metrics(self, mock1, mock2, mock3, mock4):
#         code = status.HTTP_200_OK
#         message = "Pipeline notification success."
#         logger = trainingmgr_main.LOGGER
#         is_success = True
#         trainingjob_name = "usecase7"
#         mm_sdk = ()
#         try:
#             response_for_training(code, message, logger, is_success, trainingjob_name, mm_sdk)
#             assert False
#         except APIException as err:
#             assert err.code == status.HTTP_500_INTERNAL_SERVER_ERROR
#         except Exception:
#             assert False

#     #TODO It needs to check DBException instead of APIException is correct.
#     @patch('trainingmgr.common.trainingmgr_util.get_field_by_latest_version', return_value=[['www.google.com','h1','h2'], ['www.google.com','h1','h2'], ['www.google.com','h1','h2']])
#     @patch('trainingmgr.common.trainingmgr_util.get_latest_version_trainingjob_name', return_value=1)
#     @patch('trainingmgr.common.trainingmgr_util.get_metrics', return_value="PRESENT")
#     @patch('trainingmgr.common.trainingmgr_util.requests.post', return_value=fs_result)
#     @patch('trainingmgr.common.trainingmgr_util.change_in_progress_to_failed_by_latest_version', side_effect = Exception)
#     def test_response_for_training_fail_change_in_progress_to_failed_by_latest_version(self, mock1, mock2, mock3, mock4, mock5):
#         code = status.HTTP_200_OK
#         message = "Pipeline notification success."
#         logger = trainingmgr_main.LOGGER
#         is_success = True
#         trainingjob_name = "usecase7"
#         mm_sdk = ()
#         try:
#             response_for_training(code, message, logger, is_success, trainingjob_name, mm_sdk)
#             assert False
#         except Exception:
#             assert True

# class Test_check_key_in_dictionary:
#     def test_check_key_in_dictionary(self):
#         fields = ["model","brand","year"]
#         dictionary =  {
#                                     "brand": "Ford",
#                                     "model": "Mustang",
#                                     "year": 1964
#                       }
#         assert check_key_in_dictionary(fields, dictionary) == True, "data not equal"

#     def test_check_key_in_dictionary(self):
#         fields = ["model","brand","type"]
#         dictionary =  {
#                                     "brand": "Ford",
#                                     "model": "Mustang",
#                                     "year": 1964
#                       }
#         assert check_key_in_dictionary(fields, dictionary) == False, "data not equal"
    
#     def test_negative_check_key_in_dictionary_1(self):
#         fields = ["Ford","Apple","Mosquito"]
#         dictionary =  {
#                                     "brand": "Ford",
#                                     "model": "Mustang",
#                                     "year": 1964
#                       }
#         try:
#             check_key_in_dictionary(fields, dictionary)
#             assert False
#         except Exception:
#             assert True

# @pytest.mark.skip("")
# class Test_check_trainingjob_data:    
#     @patch('trainingmgr.common.trainingmgr_util.check_key_in_dictionary',return_value=True)
#     @patch('trainingmgr.common.trainingmgr_util.isinstance',return_value=True)  
#     def test_check_trainingjob_data(self,mock1,mock2):
#         usecase_name = "usecase8"
#         json_data = { "description":"unittest", "featureGroup_name": "group1" , "pipeline_name":"qoe" , "experiment_name":"experiment1" , "arguments":"arguments1" , "query_filter":"query1" , "enable_versioning":True , "target_deployment":"Near RT RIC" , "pipeline_version":1 , "datalake_source":"cassandra db" , "incremental_training":True , "model":"usecase7" , "model_version":1 }
    
#         expected_data = ("group1", 'unittest', 'qoe', 'experiment1', 'arguments1', 'query1', True, 1, 'cassandra db')
#         assert check_trainingjob_data(usecase_name, json_data) == expected_data,"data not equal"
    
#     def test_negative_check_trainingjob_data_1(self):
#         usecase_name = "usecase8"
#         json_data = { "description":"unittest", "featureGroup_name": "group1" , "pipeline_name":"qoe" , "experiment_name":"experiment1" , "arguments":"arguments1" , "query_filter":"query1" , "enable_versioning":True , "target_deployment":"Near RT RIC" , "pipeline_version":1 , "datalake_source":"cassandra db" , "incremental_training":True , "model":"usecase7" , "model_version":1 , "_measurement":2 , "bucket":"bucket1", "is_mme":False, "model_name":""}
    
#         expected_data = ("group1", 'unittest', 'qoe', 'experiment1', 'arguments1', 'query1', True, 1, 'cassandra db', 2, 'bucket1',False, "")
#         try:
#             assert check_trainingjob_data(usecase_name, json_data) == expected_data,"data not equal"
#             assert False
#         except Exception:
#             assert True

#     @patch('trainingmgr.common.trainingmgr_util.check_key_in_dictionary',return_value=True)
#     def test_negative_check_trainingjob_data_2(self,mock1):
#         usecase_name = "usecase8"
#         json_data = { "description":"unittest", "featureGroup_name": "group1" , "pipeline_name":"qoe" , "experiment_name":"experiment1" , "arguments":"arguments1" , "query_filter":"query1" , "enable_versioning":True , "target_deployment":"Near RT RIC" , "pipeline_version":1 , "datalake_source":"cassandra db" , "incremental_training":True , "model":"usecase7" , "model_version":1 , "_measurement":2 , "bucket":"bucket1"}
    
#         expected_data = ("group1", 'unittest', 'qoe', 'experiment1', 'arguments1', 'query1', True, 1, 'cassandra db', 2, 'bucket1')
#         try:
#             assert check_trainingjob_data(usecase_name, json_data) == expected_data,"data not equal"
#             assert False
#         except Exception:
#             assert True
    
#     @patch('trainingmgr.common.trainingmgr_util.isinstance',return_value=True)
#     def test_negative_check_trainingjob_data_3(self,mock1):
#         usecase_name = "usecase8"
#         json_data = None
#         expected_data = ("group1", 'unittest', 'qoe', 'experiment1', 'arguments1', 'query1', True, 1, 'cassandra db', 2, 'bucket1')
#         try:
#             assert check_trainingjob_data(usecase_name, json_data) == expected_data,"data not equal"
#             assert False
#         except Exception:
#             assert True

# class Test_get_one_key:
#     def test_get_one_key(self):
#         dictionary = {
#                         "brand": "Ford",
#                         "model": "Mustang",
#                         "year": 1964
#                     }
#         only_key = "year"
#         expected_data = only_key
#         assert get_one_key(dictionary) == expected_data,"data not equal"
    
#     def test_get_one_key_2(self):
#         dictionary = {'name': 'Jack', 'age': 26}
#         only_key = "age"
#         expected_data = only_key
#         assert get_one_key(dictionary) == expected_data,"data not equal"
    
#     def test_negative_get_one_key_1(self):
#         dictionary = {
#                         "brand": "Ford",
#                         "model": "Mustang",
#                         "year": 1964
#                     }
#         only_key = "model"
#         expected_data = only_key
#         try:
#             assert get_one_key(dictionary) == expected_data,"data not equal"
#             assert False
#         except Exception:
#             assert True
    
#     def test_negative_get_one_key_2(self):
#         dictionary = {'name': 'Jack', 'age': 26}
#         only_key = "name"
#         expected_data = only_key
#         try:
#             assert get_one_key(dictionary) == expected_data,"data not equal"
#             assert False
#         except Exception:
#             assert True

# @pytest.mark.skip("")
# class dummy_mmsdk:
#     def check_object(self, param1, param2, param3):
#         return True
    
#     def get_metrics(self, usecase_name, version):
#         thisdict = {
#                      "brand": "Ford",
#                      "model": "Mustang",
#                      "year": 1964
#                     }
#         return thisdict
    
# @pytest.mark.skip("")
# class Test_get_metrics:   
#     @patch('trainingmgr.common.trainingmgr_util.json.dumps',return_value='usecase_data')
#     def test_get_metrics_with_version(self,mock1):
#         usecase_name = "usecase7"
#         version = 1
#         mm_sdk = dummy_mmsdk()
#         expected_data = 'usecase_data'
#         get_metrics(usecase_name, version, dummy_mmsdk())
#         assert get_metrics(usecase_name, version, mm_sdk) == expected_data, "data not equal"

#     @patch('trainingmgr.common.trainingmgr_util.json.dumps',return_value=None)
#     def test_negative_get_metrics_1(self,mock1):
#         usecase_name = "usecase7"
#         version = 1
#         mm_sdk = dummy_mmsdk()
#         expected_data = 'usecase_data'
#         try:
#             assert get_metrics(usecase_name, version, mm_sdk) == expected_data, "data not equal"
#             assert False
#         except Exception:
#             assert True
    
#     @patch('trainingmgr.common.trainingmgr_util.json.dumps',return_value=Exception("Problem while downloading metrics"))
#     def test_negative_get_metrics_2(self,mock1):
#         usecase_name = "usecase7"
#         version = 1
#         mm_sdk = dummy_mmsdk()
#         expected_data = 'usecase_data'
#         try:
#             assert get_metrics(usecase_name, version, mm_sdk) == expected_data, "data not equal"
#             assert False
#         except Exception:
#             assert True

#     def test_negative_get_metrics_3(self):
#         usecase_name = "usecase7"
#         version = 1
#         mm_sdk = dummy_mmsdk()
#         expected_data = 'final_data'
#         try:
#             get_metrics(usecase_name, version, dummy_mmsdk())
#             assert get_metrics(usecase_name, version, mm_sdk) == expected_data, "data not equal"
#             assert False
#         except Exception:
#             assert True

# class dummy_mmsdk_1:
#     def check_object(self, param1, param2, param3):
#         return False
    
#     def get_metrics(self, usecase_name, version):
#         thisdict = {
#                      "brand": "Ford",
#                      "model": "Mustang",
#                      "year": 1964
#                     }
#         return thisdict

# class Test_get_metrics_2:   
#     @patch('trainingmgr.common.trainingmgr_util.json.dumps',return_value='usecase_data')
#     def test_negative_get_metrics_2_1(self,mock1):
#         usecase_name = "usecase7"
#         version = 1
#         mm_sdk = dummy_mmsdk_1()
#         expected_data = 'usecase_data'
#         get_metrics(usecase_name, version, dummy_mmsdk())
#         try:
#             get_metrics(usecase_name, version, dummy_mmsdk())
#             assert get_metrics(usecase_name, version, mm_sdk) == expected_data, "data not equal"
#             assert False
#         except Exception:
#             assert True

# @pytest.mark.skip("")
# class Test_handle_async_feature_engineering_status_exception_case:
#     @patch('trainingmgr.common.trainingmgr_util.change_in_progress_to_failed_by_latest_version',return_value=True)
#     @patch('trainingmgr.common.trainingmgr_util.response_for_training',return_value=True)
#     def test_handle_async_feature_engineering_status_exception_case(self, mock1, mock2):
#            lock = Lock()
#            featurestore_job_cache = {'usecase7': 'Geeks', 2: 'For', 3: 'Geeks'}
#            code = 123
#            message = "Into the field" 
#            logger = "123"
#            is_success = True
#            usecase_name = "usecase7"
#            mm_sdk = ()       
#            assert handle_async_feature_engineering_status_exception_case(lock, featurestore_job_cache, code,
#                                                            message, logger, is_success,
#                                                            usecase_name, mm_sdk) == None,"data not equal"
    
#     @patch('trainingmgr.common.trainingmgr_util.change_in_progress_to_failed_by_latest_version',return_value=True)
#     @patch('trainingmgr.common.trainingmgr_util.response_for_training',return_value=True)
#     # @patch('trainingmgr.common.trainingmgr_util.dataextraction_job_cache',return_value = Exception("Could not get info from db for "))
#     def test_negative_handle_async_feature_engineering_status_exception_case(self, mock1, mock2):
#            lock = Lock()
#            featurestore_job_cache = {'usecase7': 'Geeks', 2: 'For', 3: 'Geeks'}
#            code = 123
#            message = "Into the field" 
#            logger = "123"
#            is_success = True
#            usecase_name = ""
#            ps_db_obj = () 
#            mm_sdk = ()    
#            try:   
#                handle_async_feature_engineering_status_exception_case(lock, featurestore_job_cache, code,
#                                                            message, logger, is_success,
#                                                            usecase_name, ps_db_obj, mm_sdk)
#                assert handle_async_feature_engineering_status_exception_case(lock, featurestore_job_cache, code,
#                                                            message, logger, is_success,
#                                                            usecase_name, ps_db_obj, mm_sdk) == None,"data not equal"
#                assert False
#            except Exception:
#                assert True

# class Test_get_one_word_status:
#     def test_get_one_word_status(self):
#            steps_state = {
#                     "DATA_EXTRACTION": "NOT_STARTED",
#                     "DATA_EXTRACTION_AND_TRAINING": "NOT_STARTED",
#                     "TRAINED_MODEL": "NOT_STARTED",
#                     "TRAINING": "NOT_STARTED",
#                     "TRAINING_AND_TRAINED_MODEL": "NOT_STARTED"
#                 }
#            expected_data = "NOT_STARTED"
#            assert get_one_word_status(steps_state) == expected_data,"data not equal"


# @pytest.mark.skip("")
# class Test_check_feature_group_data:
#     @patch('trainingmgr.common.trainingmgr_util.check_key_in_dictionary',return_value=True)
#     def test_check_feature_group_data(self, mock1):
#         json_data={
#                             "featureGroupName": "test",
#                             "feature_list": "",
#                             "datalake_source": "",
#                             "enable_Dme": False,
#                             "Host": "",
#                             "Port": "",
#                             "bucket": "",
#                             "dmePort":"",
#                             '_measurement':"",
#                             "token": "",
#                             "source_name": "",
#                             "measured_obj_class":"",
#                             "dbOrg": ""
#                                 }
#         expected_data=("test", "", "",False,"","","","","","","","","")
#         assert check_feature_group_data(json_data)==expected_data, "data not equal"

#     @patch('trainingmgr.common.trainingmgr_util.check_key_in_dictionary',return_value=False)
#     def test_negative_check_feature_group_data(self, mock1):
#         json_data={
#                             "featureGroupName": "test",
#                             "feature_list": "",
#                             "datalake_source": "",
#                             "enable_Dme": False,
#                             "Host": "",
#                             "Port": "",
#                             "bucket": "",
#                             '_measurement':"",
#                             "dmePort":"",
#                             "token": "",
#                             "source_name": "",
#                             "measured_obj_class":"",
#                             "dbOrg": ""
#                                 }
#         expected_data=("test", "", "",False,"","","","","","","","","")
#         try:
#             assert check_feature_group_data(json_data)==expected_data, 'data not equal'
#             assert False
#         except:
#             assert True
# @pytest.mark.skip("")
# class Test_get_feature_group_by_name:
#     fg_dict ={'id': 21, 'featuregroup_name': 'testing', 'feature_list': '', 'datalake_source': 'InfluxSource', 'host': '127.0.0.21', 'port': '8086', 'bucket': '', 'token': '', 'db_org': '', 'measurement': '', 'enable_dme': False, 'measured_obj_class': '', 'dme_port': '', 'source_name': ''} 
#     featuregroup = FeatureGroup()
#     @patch('trainingmgr.common.trainingmgr_util.get_feature_group_by_name_db', return_value=featuregroup)
#     @patch('trainingmgr.common.trainingmgr_util.check_trainingjob_name_or_featuregroup_name', return_value=True)
#     def test_get_feature_group_by_name(self, mock1, mock2):

#         logger = trainingmgr_main.LOGGER
#         fg_name='testing'
#         expected_data = {'bucket': None, 'datalake_source': None, 'db_org': None, 'dme_port': None, 'enable_dme': None, 'feature_list': None, 'featuregroup_name': None, 'host': None, 'id': None, 'measured_obj_class': None, 'measurement': None, 'port': None, 'source_name': None, 'token': None}
        
#         with APP.app_context():
#             api_response, status_code = get_feature_group_by_name(fg_name, logger)
#         json_data = api_response.json
#         assert status_code == 200, "status code is not equal"
#         assert json_data == expected_data, json_data
        
#     @patch('trainingmgr.common.trainingmgr_util.get_feature_group_by_name_db')
#     @patch('trainingmgr.common.trainingmgr_util.check_trainingjob_name_or_featuregroup_name')
#     def test_negative_get_feature_group_by_name(self, mock1, mock2):

#         logger = trainingmgr_main.LOGGER
#         fg_name='testing'

#         mock1.side_effect = [True, True]
#         mock2.side_effect = [None, DBException("Failed to execute query in get_feature_groupsDB ERROR")]

#         # Case 1
#         expected_data = {'error': "featuregroup with name 'testing' not found"}

#         with APP.app_context():
#             api_response, status_code = get_feature_group_by_name(fg_name, logger)
#         json_data = api_response.json
#         assert status_code == 404, "status code is not equal"
#         assert json_data == expected_data, json_data

#         # Case 2
#         expected_data = {"Exception": "Failed to execute query in get_feature_groupsDB ERROR"}
#         json_data, status_code = get_feature_group_by_name(fg_name, logger)
#         assert status_code == 500, "status code is not equal"
#         assert json_data == expected_data, json_data
    
#     def test_negative_get_feature_group_by_name_with_incorrect_name(self):
#         logger= trainingmgr_main.LOGGER
#         fg_name='usecase*'
#         expected_data = {"Exception":"The featuregroup_name is not correct"}
#         json_data, status_code = get_feature_group_by_name(fg_name, logger)
#         assert status_code == 400, "status code is not equal"
#         assert json_data == expected_data, json_data
        
# @pytest.mark.skip("")
# class Test_edit_feature_group_by_name:

#     fg_init = [('testing', '', 'InfluxSource', '127.0.0.21', '8080', '', '', '', '', False, '', '', '')]

#     fg_edit = [('testing', 'testing', 'InfluxSource', '127.0.0.21', '8080', 'testing', '', '', '', False, '', '', '')]
#     fg_edit_dme = [('testing', 'testing', 'InfluxSource', '127.0.0.21', '8080', 'testing', '', '', '', True, '', '31823', '')]
    
#     # In the case where the feature group is edited while DME is disabled
#     feature_group_data1=('testing','testing','InfluxSource',False,'127.0.0.1', '8080', '','testing','','','','','')
    
#     @pytest.fixture
#     def get_sample_feature_group(self):
#         return FeatureGroup(
#         featuregroup_name="SampleFeatureGroup",
#         feature_list="feature1,feature2,feature3",
#         datalake_source="datalake_source_url",
#         host="localhost",
#         port="12345",
#         bucket="my_bucket",
#         token="auth_token",
#         db_org="organization_name",
#         measurement="measurement_name",
#         enable_dme=False,
#         measured_obj_class="object_class",
#         dme_port="6789",
#         source_name="source_name"
#         )
    
#     @patch('trainingmgr.common.trainingmgr_util.edit_featuregroup')
#     @patch('trainingmgr.common.trainingmgr_util.check_feature_group_data', return_value=feature_group_data1)
#     @patch('trainingmgr.common.trainingmgr_util.get_feature_group_by_name_db', return_value=fg_init)
#     def test_edit_feature_group_by_name_1(self, mock1, mock2, mock3, get_sample_feature_group):
#         tm_conf_obj=()
#         logger = trainingmgr_main.LOGGER
#         expected_data = {"result": "Feature Group Edited"}
        
#         json_data, status_code = edit_feature_group_by_name(get_sample_feature_group.featuregroup_name, get_sample_feature_group, logger, tm_conf_obj)
#         assert status_code == 200, "status code is not equal"
#         assert json_data == expected_data, json_data

#     # In the case where the feature group is edited, including DME(disabled to enabled)
#     the_response2= Response()
#     the_response2.status_code = status.HTTP_201_CREATED
#     the_response2.headers={"content-type": "application/json"}
#     the_response2._content = b''
#     mocked_TRAININGMGR_CONFIG_OBJ=mock.Mock(name="TRAININGMGR_CONFIG_OBJ")
#     feature_group_data2=('testing','testing','InfluxSource',True,'127.0.0.1', '8080', '31823','testing','','','','','')
#     @patch('trainingmgr.common.trainingmgr_util.create_dme_filtered_data_job', return_value=the_response2)
#     @patch('trainingmgr.common.trainingmgr_util.edit_featuregroup')
#     @patch('trainingmgr.trainingmgr_main.TRAININGMGR_CONFIG_OBJ', return_value = mocked_TRAININGMGR_CONFIG_OBJ)
#     @patch('trainingmgr.common.trainingmgr_util.check_feature_group_data', return_value=feature_group_data2)
#     @patch('trainingmgr.common.trainingmgr_util.get_feature_group_by_name_db', return_value=fg_init)
#     @patch('trainingmgr.common.trainingmgr_util.delete_feature_group_by_name')
#     def test_edit_feature_group_by_name_2(self, mock1, mock2, mock3, mock4, mock5, mock6, get_sample_feature_group):
#         tm_conf_obj=()
#         logger = trainingmgr_main.LOGGER
#         fg_name='testing'
#         expected_data = {"result": "Feature Group Edited"}

#         json_data, status_code = edit_feature_group_by_name(get_sample_feature_group.featuregroup_name, get_sample_feature_group, logger, tm_conf_obj)
#         assert status_code == 200, "status code is not equal"
#         assert json_data == expected_data, json_data
    
#     the_response3= Response()
#     the_response3.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
#     the_response3.headers={"content-type": "application/json"}
#     the_response3._content = b''
#     feature_group_data3=('testing','testing','InfluxSource',True,'127.0.0.1', '8080', '31823','testing','','','','','')
#     @patch('trainingmgr.common.trainingmgr_util.create_dme_filtered_data_job', return_value=the_response3)
#     @patch('trainingmgr.common.trainingmgr_util.edit_featuregroup')
#     @patch('trainingmgr.common.trainingmgr_util.check_feature_group_data', return_value=feature_group_data3)
#     @patch('trainingmgr.common.trainingmgr_util.get_feature_group_by_name_db', return_value=fg_init)
#     @patch('trainingmgr.common.trainingmgr_util.delete_feature_group_by_name')
#     @pytest.mark.skip("")
#     def test_negative_edit_feature_group_by_name(self, mock1, mock2, mock3, mock4, mock5, get_sample_feature_group):
#         tm_conf_obj=()
#         ps_db_obj=()
#         logger = trainingmgr_main.LOGGER
#         fg_name='testing'
#         json_request = {
#                 "featureGroupName": fg_name,
#                 "feature_list": self.fg_edit[0][1],
#                 "datalake_source": self.fg_edit[0][2],
#                 "Host": self.fg_edit[0][3],
#                 "Port": self.fg_edit[0][4],
#                 "bucket": self.fg_edit[0][5],
#                 "token": self.fg_edit[0][6],
#                 "dbOrg": self.fg_edit[0][7],
#                 "_measurement": self.fg_edit[0][8],
#                 "enable_Dme": self.fg_edit[0][9],
#                 "measured_obj_class": self.fg_edit[0][10],
#                 "dmePort": self.fg_edit[0][11],
#                 "source_name": self.fg_edit[0][12]
#             }
    
#         # Case 1
#         mock1.side_effect = [DBException("Failed to execute query in delete_feature_groupDB ERROR"), None]
#         expected_data={"Exception": "Failed to edit the feature Group "}
#         json_data, status_code = edit_feature_group_by_name(tm_conf_obj, ps_db_obj, logger, fg_name, json_request)
#         # NOTE: This part is a test code that deliberately triggers a DBException even when DME is successfully created, so note that the status_code is 200.
#         assert status_code == 200, "status code is not equal"
#         assert json_data == expected_data, json_data

#         # Case 2 
#         mock1.side_effect = None
#         expected_data={"Exception": "Cannot create dme job"}
#         json_data, status_code = edit_feature_group_by_name(tm_conf_obj, ps_db_obj, logger, fg_name, json_request)
#         assert status_code == 400, "status code is not equal"
#         assert json_data == expected_data, json_data
#     @pytest.mark.skip("")
#     def test_negative_edit_feature_group_by_name_with_incorrect_name(self):
#         tm_conf_obj=()
#         ps_db_obj=()
#         logger = trainingmgr_main.LOGGER
#         fg_name='usecase*'
#         expected_data = {"Exception":"The featuregroup_name is not correct"}
#         json_request={}
#         json_data, status_code = edit_feature_group_by_name(tm_conf_obj, ps_db_obj, logger, fg_name, json_request)
#         assert status_code == 400, "status code is not equal"
#         assert json_data == expected_data, json_data

#     # TODO: Test Code in the case where DME is edited from enabled to disabled)
