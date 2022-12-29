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
import json
import requests
from unittest import mock
from mock import patch
import pytest
import flask
from requests.models import Response
from threading import Lock
import os
import sys
import datetime
from flask_api import status
from dotenv import load_dotenv
from threading import Lock
from trainingmgr import trainingmgr_main 
trainingmgr_main.LOCK = Lock()
trainingmgr_main.DATAEXTRACTION_JOBS_CACHE = {}
from trainingmgr.common.tmgr_logger import TMLogger
from trainingmgr import trainingmgr_main
trainingmgr_main.LOGGER = pytest.logger
from trainingmgr.common.trainingmgr_config import TrainingMgrConfig

class err:
    def __init__(self):
        self.message = "Error occured while execution"
        self.code = status.HTTP_500_INTERNAL_SERVER_ERROR

class Test_error:
    def setup_method(self):
         self.client = trainingmgr_main.APP.test_client(self)
         self.logger = trainingmgr_main.LOGGER

    def test_error(self):
        expected_data = "result"
        err_data = err()
        response = trainingmgr_main.error(err_data)
        assert response.status == '500 INTERNAL SERVER ERROR'

class Test_upload_pipeline:
     def setup_method(self):
         self.client = trainingmgr_main.APP.test_client(self)
         self.logger = trainingmgr_main.LOGGER
 
     mocked_TRAININGMGR_CONFIG_OBJ=mock.Mock(name="TRAININGMGR_CONFIG_OBJ")
     attrs_TRAININGMGR_CONFIG_OBJ = {'kf_adapter_ip.return_value': '123', 'kf_adapter_port.return_value' : '100'}
     mocked_TRAININGMGR_CONFIG_OBJ.configure_mock(**attrs_TRAININGMGR_CONFIG_OBJ)
     @patch('trainingmgr.trainingmgr_main.TRAININGMGR_CONFIG_OBJ', return_value = mocked_TRAININGMGR_CONFIG_OBJ)
     def test_upload_pipeline_negative(self, mock1):
         trainingmgr_main.LOGGER.debug("*******  *******")
         expected_data = "result"
         trainingjob_req = {
                     "pipe_name":"usecase1",
                     }
         response = self.client.post("/pipelines/<pipe_name>/upload".format("usecase1"), data=json.dumps(trainingjob_req),
                                     content_type="application/json")
 
         trainingmgr_main.LOGGER.debug(response.data)
         assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
         assert expected_data in response.json.keys() 

class dummy_class_requests:
    def json(var):
        Dict = {"trainingjob_name": 'testcases21', 2: 'For', 3: 'Geeks'}
        return Dict

class response_dummy2:
       headers={"content-type": "application/json"}
       status_code = status.HTTP_200_OK
       def json():
          my_dict = {
                    "task_status": "Error",
                    "model": "Mustang",
                    "year": 1964
                  }
          return my_dict

class Dummy_response:
    def setup(self):
        self.code = "expired"
        self.error_type = "expired"
        self.status_code = 500
        self.headers={'content-type': "applicationnnnnnnnnn/json"}
        self._content = b'{"task_status": "Completed", "result": "Data Extraction Completed"}'
        self.example_dict = {"run_status": 'scheduled', "Italy": "Rome", "England": "London"}
    def json(self):
        return self.example_dict

class Dummy_response_true_input:
    def setup(self):
        self.code = "expired"
        self.error_type = "expired"
        self.status_code = status.HTTP_200_OK
        self.headers={'content-type': "application/json"}
        self._content = b'{"task_status": "Completed", "result": "Data Extraction Completed"}'
        self.example_dict = {"run_status": 'scheduled', "Italy": "Rome", "England": "London"}
    def json(self):
        return self.example_dict

class Test_data_extraction_notification:
    def setup_method(self):
        self.client = trainingmgr_main.APP.test_client(self)
        self.logger = trainingmgr_main.LOGGER

    db_result2 = [('usecase1', 'uc1', '*', 'qoe Pipeline lat v2', 'Default', '{"arguments": {"epochs": "1", "trainingjob_name": "usecase1"}}',
    '', datetime.datetime(2022, 10, 12, 10, 0, 59, 923588), '51948a12-aee9-42e5-93a0-b8f4a15bca33',
    '{"DATA_EXTRACTION": "FINISHED", "DATA_EXTRACTION_AND_TRAINING": "FINISHED", "TRAINING": "FINISHED", "TRAINING_AND_TRAINED_MODEL": "FINISHED", "TRAINED_MODEL": "FAILED"}',
    datetime.datetime(2022, 10, 12, 10, 2, 31, 888830), 1, False, '3', '{"datalake_source": {"InfluxSource": {}}}', 'No data available.', '', 'liveCell', 'UEData', False)]

    de_response2 = Response()
    de_response2.code = "expired"
    de_response2.error_type = "expired"
    de_response2.status_code = status.HTTP_200_OK
    de_response2.headers={"content-type": "application/json"}
    de_response2._content = b'{"task_status": "Completed", "result": "Data Extraction Completed"}'
    resp= ({"str1":"rp1","str2":"rp2"} ,status.HTTP_200_OK)
    
    @patch('trainingmgr.trainingmgr_main.get_trainingjob_info_by_name', return_value = db_result2)  
    @patch('trainingmgr.trainingmgr_main.training_start', return_value = de_response2)
    @patch('trainingmgr.trainingmgr_main.change_steps_state_of_latest_version')  
    @patch('trainingmgr.trainingmgr_main.change_field_of_latest_version')        
    @patch('trainingmgr.trainingmgr_main.change_in_progress_to_failed_by_latest_version', return_value = True)
    @patch('trainingmgr.trainingmgr_main.response_for_training', return_value = resp) 
    def test_data_extraction_notification(self, mock1, mock2, mock3, mock4, mock5, mock6):
        trainingmgr_main.LOGGER.debug("******* Data_Extraction_Notification *******")
        trainingjob_req = {
                    "trainingjob_name":"usecase1",
                    }
        expected_data = "Data Extraction Completed"
        response = self.client.post("/trainingjob/dataExtractionNotification".format("usecase1"),
                                    data=json.dumps(trainingjob_req),
                                    content_type="application/json")
        trainingmgr_main.LOGGER.debug(response.data)
        assert response.status_code == status.HTTP_200_OK
    
    @patch('trainingmgr.trainingmgr_main.get_trainingjob_info_by_name', return_value = db_result2)  
    @patch('trainingmgr.trainingmgr_main.training_start', return_value = de_response2)
    @patch('trainingmgr.trainingmgr_main.change_steps_state_of_latest_version')  
    @patch('trainingmgr.trainingmgr_main.change_field_of_latest_version')        
    @patch('trainingmgr.trainingmgr_main.change_in_progress_to_failed_by_latest_version', return_value = True)
    @patch('trainingmgr.trainingmgr_main.response_for_training', return_value = resp) 
    @patch('trainingmgr.trainingmgr_main.Logger.error', return_value = True)
    def test_negative_data_extraction_notification(self, mock1, mock2, mock3, mock4, mock5, mock6, mock7):
        trainingjob_req = {
                    "trainingjob_name":"usecase1",
                    }
        expected_data = "Data Extraction Completed"
        response = self.client.post("/trainingjob/dataExtractionNotification".format("usecase1"),
                                    data=json.dumps(trainingjob_req),
                                    content_type="application/json")
        trainingmgr_main.LOGGER.debug(response.data)
        assert response.status_code == status.HTTP_200_OK

class Test_negative_data_extraction_notification:
    def setup_method(self):
        self.client = trainingmgr_main.APP.test_client(self)
        self.logger = trainingmgr_main.LOGGER

    db_result2 = [('usecase1', 'uc1', '*', 'qoe Pipeline lat v2', 'Default', '{"arguments": {"epochs": "1", "trainingjob_name": "usecase1"}}',
    '', datetime.datetime(2022, 10, 12, 10, 0, 59, 923588), '51948a12-aee9-42e5-93a0-b8f4a15bca33',
    '{"DATA_EXTRACTION": "FINISHED", "DATA_EXTRACTION_AND_TRAINING": "FINISHED", "TRAINING": "FINISHED", "TRAINING_AND_TRAINED_MODEL": "FINISHED", "TRAINED_MODEL": "FAILED"}',
    datetime.datetime(2022, 10, 12, 10, 2, 31, 888830), 1, False, '3', '{"datalake_source": {"InfluxSource": {}}}', 'No data available.', '', 'liveCell', 'UEData', False)]

    de_response2 = Response()
    de_response2.code = "expired"
    de_response2.error_type = "expired"
    de_response2.status_code = 500
    de_response2.headers={"content-type": "application/json"}
    de_response2._content = b'{"task_status": "Completed", "result": "Data Extraction Completed"}'
    resp= ({"str1":"rp1","str2":"rp2"} ,status.HTTP_200_OK)
    
    @patch('trainingmgr.trainingmgr_main.get_trainingjob_info_by_name', return_value = db_result2)  
    @patch('trainingmgr.trainingmgr_main.training_start', return_value = Dummy_response_true_input)   
    @patch('trainingmgr.trainingmgr_main.change_in_progress_to_failed_by_latest_version', return_value = False)
    @patch('trainingmgr.trainingmgr_main.response_for_training', return_value = resp) 
    @patch('trainingmgr.trainingmgr_main.check_key_in_dictionary', return_value = True)
    @patch('trainingmgr.trainingmgr_main.Logger.error', return_value = True)
    def test_positive_data_extraction_notification_100(self, mock1, mock2, mock3, mock4, mock5, mock6):
        trainingmgr_main.LOGGER.debug("******* Data_Extraction_Notification *******")
        trainingjob_req = {
                    "trainingjob_name":"usecase1",
                    }
        expected_data = "Data Extraction Completed"
        response = self.client.post("/trainingjob/dataExtractionNotification".format("usecase1"),
                                    data=json.dumps(trainingjob_req),
                                    content_type="application/json")
        # assert response == status.HTTP_200_OK
        assert response.status == '200 OK'
    ##Do Changes here only
    ######################################################################################
    de_response2 = Response()
    de_response2.code = "expired"
    de_response2.error_type = "expired"
    de_response2.status_code = 500
    de_response2.headers={"content-type": "application/json"}
    de_response2._content = b'{"task_status": "Completed", "result": "Data Extraction Completed"}'
    resp= ({"str1":"rp1","str2":"rp2"} ,status.HTTP_200_OK)
    
    @patch('trainingmgr.trainingmgr_main.get_trainingjob_info_by_name', return_value = db_result2)  
    # @patch('trainingmgr.trainingmgr_main.training_start', return_value = de_response2)   
    @patch('trainingmgr.trainingmgr_main.change_in_progress_to_failed_by_latest_version', return_value = False)
    @patch('trainingmgr.trainingmgr_main.response_for_training', return_value = resp) 
    @patch('trainingmgr.trainingmgr_main.check_key_in_dictionary', return_value = True)
    @patch('trainingmgr.trainingmgr_main.Logger.error', return_value = True)
    def test_positive_data_extraction_notification_101(self, mock1, mock2, mock3, mock4, mock5):
        trainingmgr_main.LOGGER.debug("******* Data_Extraction_Notification *******")
        trainingjob_req = {
                    "trainingjob_name":"usecase1",
                    }
        expected_data = "Data Extraction Completed"
        response = self.client.post("/trainingjob/dataExtractionNotification".format("usecase1"),
                                    data=json.dumps(trainingjob_req),
                                    content_type="application/json")
        assert response.status == '200 OK'
    ######################################################################################

    @patch('trainingmgr.trainingmgr_main.get_trainingjob_info_by_name', return_value = db_result2)  
    @patch('trainingmgr.trainingmgr_main.training_start', return_value = Dummy_response_true_input)
    @patch('trainingmgr.trainingmgr_main.change_steps_state_of_latest_version')  
    @patch('trainingmgr.trainingmgr_main.change_field_of_latest_version')        
    @patch('trainingmgr.trainingmgr_main.change_in_progress_to_failed_by_latest_version', return_value = False)
    @patch('trainingmgr.trainingmgr_main.response_for_training', return_value = resp) 
    @patch('trainingmgr.trainingmgr_main.check_key_in_dictionary', return_value = True)
    def test_negative_data_extraction_notification_3(self, mock1, mock2, mock3, mock4, mock5, mock6, mock7):
        trainingmgr_main.LOGGER.debug("******* Data_Extraction_Notification *******")
        trainingjob_req = {
                    "trainingjob_name":"usecase1",
                    }
        expected_data = "Data Extraction Completed"
        response = self.client.post("/trainingjob/dataExtractionNotification".format("usecase1"),
                                    data=json.dumps(trainingjob_req),
                                    content_type="application/json")
        trainingmgr_main.LOGGER.debug(response.data)
        # assert response == status.HTTP_200_OK
        # assert response.status_code == status.HTTP_200_OK   

    @patch('trainingmgr.trainingmgr_main.get_trainingjob_info_by_name', return_value = db_result2)  
    @patch('trainingmgr.trainingmgr_main.training_start', return_value = Dummy_response_true_input)
    @patch('trainingmgr.trainingmgr_main.change_steps_state_of_latest_version')  
    @patch('trainingmgr.trainingmgr_main.change_field_of_latest_version')        
    @patch('trainingmgr.trainingmgr_main.change_in_progress_to_failed_by_latest_version', return_value = False)
    @patch('trainingmgr.trainingmgr_main.response_for_training', return_value = resp) 
    @patch('trainingmgr.trainingmgr_main.check_key_in_dictionary', return_value = False)
    def test_negative_data_extraction_notification_4(self, mock1, mock2, mock3, mock4, mock5, mock6, mock7):
        trainingmgr_main.LOGGER.debug("******* Data_Extraction_Notification *******")
        trainingjob_req = {
                    "trainingjob_name":"usecase1",
                    }
        expected_data = "Data Extraction Completed"
        response = self.client.post("/trainingjob/dataExtractionNotification".format("usecase1"),
                                    data=json.dumps(trainingjob_req),
                                    content_type="application/json")
        trainingmgr_main.LOGGER.debug(response.data)
        # assert response == status.HTTP_200_OK
        # assert response.status_code == status.HTTP_200_OK    
    
    @patch('trainingmgr.trainingmgr_main.get_trainingjob_info_by_name', return_value = db_result2)  
    @patch('trainingmgr.trainingmgr_main.training_start', return_value = Dummy_response)
    @patch('trainingmgr.trainingmgr_main.change_steps_state_of_latest_version')  
    @patch('trainingmgr.trainingmgr_main.change_field_of_latest_version')        
    @patch('trainingmgr.trainingmgr_main.change_in_progress_to_failed_by_latest_version', return_value = False)
    @patch('trainingmgr.trainingmgr_main.response_for_training', return_value = resp) 
    @patch('trainingmgr.trainingmgr_main.check_key_in_dictionary', return_value = True)
    def test_negative_data_extraction_notification_5(self, mock1, mock2, mock3, mock4, mock5, mock6, mock7):
        trainingmgr_main.LOGGER.debug("******* Data_Extraction_Notification *******")
        trainingjob_req = {
                    "trainingjob_name":"usecase1",
                    }
        expected_data = "Data Extraction Completed"
        response = self.client.post("/trainingjob/dataExtractionNotification".format("usecase1"),
                                    data=json.dumps(trainingjob_req),
                                    content_type="application/json")
        trainingmgr_main.LOGGER.debug(response.data)
        # assert response == status.HTTP_200_OK
        # assert response.status_code == status.HTTP_200_OK 

    @patch('trainingmgr.trainingmgr_main.get_trainingjob_info_by_name', return_value = db_result2)  
    @patch('trainingmgr.trainingmgr_main.training_start', return_value = Dummy_response)
    @patch('trainingmgr.trainingmgr_main.change_steps_state_of_latest_version')  
    @patch('trainingmgr.trainingmgr_main.change_field_of_latest_version')        
    @patch('trainingmgr.trainingmgr_main.change_in_progress_to_failed_by_latest_version', return_value = False)
    @patch('trainingmgr.trainingmgr_main.response_for_training', return_value = resp) 
    @patch('trainingmgr.trainingmgr_main.check_key_in_dictionary', return_value = False)
    def test_negative_data_extraction_notification_6(self, mock1, mock2, mock3, mock4, mock5, mock6, mock7):
        trainingmgr_main.LOGGER.debug("******* Data_Extraction_Notification *******")
        trainingjob_req = {
                    "trainingjob_name":"usecase1",
                    }
        expected_data = "Data Extraction Completed"
        response = self.client.post("/trainingjob/dataExtractionNotification".format("usecase1"),
                                    data=json.dumps(trainingjob_req),
                                    content_type="application/json")
        trainingmgr_main.LOGGER.debug(response.data)
        # assert response == status.HTTP_200_OK
        # assert response.status_code == status.HTTP_200_OK 
    
    @patch('trainingmgr.trainingmgr_main.get_trainingjob_info_by_name', return_value = db_result2)  
    @patch('trainingmgr.trainingmgr_main.training_start', return_value = Dummy_response)   
    @patch('trainingmgr.trainingmgr_main.change_in_progress_to_failed_by_latest_version', return_value = False)
    @patch('trainingmgr.trainingmgr_main.response_for_training', return_value = resp) 
    @patch('trainingmgr.trainingmgr_main.check_key_in_dictionary', return_value = False)
    @patch('trainingmgr.trainingmgr_main.Logger.error', return_value = True)
    def test_negative_data_extraction_notification_7(self, mock1, mock2, mock3, mock4, mock5, mock6):
        trainingmgr_main.LOGGER.debug("******* Data_Extraction_Notification *******")
        trainingjob_req = {
                    "trainingjob_name":"usecase1",
                    }
        expected_data = "Data Extraction Completed"
        response = self.client.post("/trainingjob/dataExtractionNotification".format("usecase1"),
                                    data=json.dumps(trainingjob_req),
                                    content_type="application/json")
        trainingmgr_main.LOGGER.debug(response.data)
        # assert response == status.HTTP_200_OK
        # assert response.status_code == status.HTTP_200_OK 
    
    @patch('trainingmgr.trainingmgr_main.get_trainingjob_info_by_name', return_value = db_result2)  
    @patch('trainingmgr.trainingmgr_main.training_start', return_value = de_response2)   
    @patch('trainingmgr.trainingmgr_main.change_in_progress_to_failed_by_latest_version', return_value = False)
    @patch('trainingmgr.trainingmgr_main.response_for_training', return_value = resp) 
    @patch('trainingmgr.trainingmgr_main.check_key_in_dictionary', return_value = True)
    @patch('trainingmgr.trainingmgr_main.Logger.error', return_value = True)
    def test_negative_data_extraction_notification_8(self, mock1, mock2, mock3, mock4, mock5, mock6):
        trainingmgr_main.LOGGER.debug("******* Data_Extraction_Notification *******")
        trainingjob_req = {
                    "trainingjob_name":"usecase1",
                    }
        expected_data = "Data Extraction Completed"
        response = self.client.post("/trainingjob/dataExtractionNotification".format("usecase1"),
                                    data=json.dumps(trainingjob_req),
                                    content_type="application/json")
        trainingmgr_main.LOGGER.debug(response.data)
        # assert response == status.HTTP_200_OK
        # assert response.status_code == status.HTTP_200_OK 

#67-68, 345-347, 406-426, 428-432, 443, 508-510, 520, 616, 621-650, 656-660, 663-664, 708, 901-902, 908, 912, 1019, 1040, 1044-1045, 1062-1075
    @patch('trainingmgr.trainingmgr_main.get_trainingjob_info_by_name', return_value = db_result2)  
    @patch('trainingmgr.trainingmgr_main.training_start', return_value = Dummy_response_true_input)   
    @patch('trainingmgr.trainingmgr_main.change_in_progress_to_failed_by_latest_version', return_value = False)
    @patch('trainingmgr.trainingmgr_main.response_for_training', return_value = resp) 
    @patch('trainingmgr.trainingmgr_main.check_key_in_dictionary', return_value = True)
    @patch('trainingmgr.trainingmgr_main.Logger.error', return_value = True)
    def test_negative_data_extraction_notification_9(self, mock1, mock2, mock3, mock4, mock5, mock6):
        trainingmgr_main.LOGGER.debug("******* Data_Extraction_Notification *******")
        trainingjob_req = {
                    "trainingjob_name":"usecase1",
                    }
        expected_data = "Data Extraction Completed"
        response = self.client.post("/trainingjob/dataExtractionNotification".format("usecase1"),
                                    data=json.dumps(trainingjob_req),
                                    content_type="application/json")
        trainingmgr_main.LOGGER.debug(response.data)
        # assert response == status.HTTP_200_OK
        # assert response.status_code == status.HTTP_200_OK






class Test_trainingjobs_operations:
    def setup_method(self):
        self.client = trainingmgr_main.APP.test_client(self)
        self.logger = trainingmgr_main.LOGGER

    db_result2 = [('usecase2', 'version2', '{"overall_status":"status_ok"}')]
    @patch('trainingmgr.trainingmgr_main.get_all_jobs_latest_status_version', return_value = db_result2)
    @patch('trainingmgr.trainingmgr_main.get_one_word_status', return_value = "status OK")
    def test_trainingjobs_operations(self,mock1,mock2):
        trainingmgr_main.LOGGER.debug("******* test_trainingjobs_operations get *******")
        expected_data = '{"trainingjobs": [{"trainingjob_name": "usecase2", "version": "version2", "overall_status": "status OK"}]}'
        response = self.client.get("/trainingjobs/latest",content_type="application/json")
        trainingmgr_main.LOGGER.debug(response.data)    
        assert response.status_code == status.HTTP_200_OK, "Return status code NOT equal"
        assert expected_data in str(response.data)

    db_result3 = [] 
    @patch('trainingmgr.trainingmgr_main.get_all_jobs_latest_status_version', return_value = db_result3)
    @patch('trainingmgr.trainingmgr_main.get_one_word_status', return_value = "status OK")
    def test_trainingjobs_operations_get_exception(self,mock1,mock2):
        trainingmgr_main.LOGGER.debug("******* test_trainingjobs_operations get exception*******")
        expected_data = "Failed to fetch training job info from db"
        response = self.client.get("/trainingjobs/latest",content_type="application/json")
        trainingmgr_main.LOGGER.debug(response.data)    
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR, "Return status code NOT equal"
        assert expected_data in str(response.data)

import signal
from contextlib import contextmanager
class TimeoutException(Exception): pass
@contextmanager
def time_limit(seconds):
    def signal_handler(signum, frame):
        raise TimeoutException("Timed out!")
    signal.signal(signal.SIGALRM, signal_handler)
    signal.alarm(seconds)
    try:
        yield
    finally:
        signal.alarm(0)

class response_dummy:
       headers={"content-type": "application/json"}
       status_code = status.HTTP_200_OK
       def json():
          my_dict = {
                    "task_status": "Completed",
                    "model": "Mustang",
                    "year": 1964
                  }
          return my_dict
          
class response_dummy2:
       headers={"content-type": "application/json"}
       status_code = status.HTTP_200_OK
       def json():
          my_dict = {
                    "task_status": "Error",
                    "model": "Mustang",
                    "year": 1964
                  }
          return my_dict

class TRAININGMGR_CONFIG_OBJ_dummy:
       my_ip = "1.0.0.1"
       my_port = "10.0.0.47"
       def pop(value):
           return True
                 
class Test_async_feature_engineering_status:
    def setup_method(self):
         self.client = trainingmgr_main.APP.test_client(self)
         self.logger = trainingmgr_main.LOGGER
 
    mocked_TRAININGMGR_CONFIG_OBJ=mock.Mock(name="TRAININGMGR_CONFIG_OBJ")
    attrs_TRAININGMGR_CONFIG_OBJ = {'kf_adapter_ip.return_value': '123', 'kf_adapter_port.return_value' : '100'}
    mocked_TRAININGMGR_CONFIG_OBJ.configure_mock(**attrs_TRAININGMGR_CONFIG_OBJ)
    mocked_mm_sdk=mock.Mock(name="MM_SDK")
    attrs_mm_sdk = {'check_object.return_value': True}
    mocked_mm_sdk.configure_mock(**attrs_mm_sdk)
    mocked_TRAININGMGR_CONFIG_OBJ=mock.Mock(name="TRAININGMGR_CONFIG_OBJ")
    attrs_TRAININGMGR_CONFIG_OBJ = {'my_ip.return_value': 123, 'my_port.return_value' : 100}
    mocked_TRAININGMGR_CONFIG_OBJ.configure_mock(**attrs_TRAININGMGR_CONFIG_OBJ)
    message1="Pipeline notification success."
    code1=status.HTTP_200_OK
    response_tuple1=({"result": message1}, code1)
    @patch('trainingmgr.trainingmgr_main.MM_SDK', return_value = mocked_mm_sdk)
    @patch('trainingmgr.trainingmgr_main.TRAININGMGR_CONFIG_OBJ', return_value = mocked_TRAININGMGR_CONFIG_OBJ)
    @patch('trainingmgr.trainingmgr_main.data_extraction_status', return_value = response_dummy)
    @patch('trainingmgr.trainingmgr_main.list', return_value = ['usecase1','usecase2','usecase3','usecase4'])
    @patch('trainingmgr.trainingmgr_main.change_steps_state_of_latest_version', return_value = True)
    @patch('trainingmgr.trainingmgr_main.requests.post', return_value = response_dummy)  
    @patch('trainingmgr.trainingmgr_main.DATAEXTRACTION_JOBS_CACHE', return_value = TRAININGMGR_CONFIG_OBJ_dummy)
    def test_async_feature_engineering_status(self,mock1, mock2, mock3, mock4, mock5, mock6, mock7):
        trainingmgr_main.LOGGER.debug("******* async_feature_engineering_status test running *******")      
        try:
          with time_limit(2):
              trainingmgr_main.async_feature_engineering_status()
        except TimeoutException as e:
          print("Timed out!")
    
    @patch('trainingmgr.trainingmgr_main.MM_SDK', return_value = mocked_mm_sdk)
    @patch('trainingmgr.trainingmgr_main.TRAININGMGR_CONFIG_OBJ', return_value = mocked_TRAININGMGR_CONFIG_OBJ)
    @patch('trainingmgr.trainingmgr_main.data_extraction_status', return_value = response_dummy)
    @patch('trainingmgr.trainingmgr_main.list', return_value = ['usecase1','usecase2','usecase3','usecase4'])
    @patch('trainingmgr.trainingmgr_main.requests.post', return_value = response_dummy2)  
    @patch('trainingmgr.trainingmgr_main.DATAEXTRACTION_JOBS_CACHE', return_value = TRAININGMGR_CONFIG_OBJ_dummy)
    def test_negative_async_feature_engineering_status(self,mock1, mock2, mock3, mock4, mock5, mock6):
        trainingmgr_main.LOGGER.debug("******* async_feature_engineering_status negative test running *******")      
        try:
          with time_limit(2):
              trainingmgr_main.async_feature_engineering_status()
        except TimeoutException as e:
          print("Timed out!")
      
class  mmSDK_dummy:
    def check_object(self,val1,val2,val3):
        return False

class Test_pipeline_notification:
    def setup_method(self):
        self.client = trainingmgr_main.APP.test_client(self)
        self.logger = trainingmgr_main.LOGGER
        
    #####################CODE HERE###############################################
    mocked_mm_sdk=mock.Mock(name="MM_SDK")
    attrs_mm_sdk = {'check_object.return_value': False}
    mocked_mm_sdk.configure_mock(**attrs_mm_sdk)
    mocked_TRAININGMGR_CONFIG_OBJ=mock.Mock(name="TRAININGMGR_CONFIG_OBJ")
    attrs_TRAININGMGR_CONFIG_OBJ = {'my_ip.return_value': 123, 'my_port.return_value' : 100}
    mocked_TRAININGMGR_CONFIG_OBJ.configure_mock(**attrs_TRAININGMGR_CONFIG_OBJ)
    message1="Pipeline notification success."
    code1=status.HTTP_200_OK
    response_tuple1=({"result": message1}, code1)
    @patch('trainingmgr.trainingmgr_main.MM_SDK', return_value = mmSDK_dummy())
    @patch('trainingmgr.trainingmgr_main.TRAININGMGR_CONFIG_OBJ', return_value = mocked_TRAININGMGR_CONFIG_OBJ) 
    @patch('trainingmgr.trainingmgr_main.change_steps_state_of_latest_version')
    @patch('trainingmgr.trainingmgr_main.update_model_download_url')
    @patch('trainingmgr.trainingmgr_main.get_latest_version_trainingjob_name', return_value = "usecase1")
    @patch('trainingmgr.trainingmgr_main.response_for_training', return_value = response_tuple1)
    @patch('trainingmgr.trainingmgr_main.LOGGER.debug', return_value = True)
    def test_pipeline_notification_33(self,mock1, mock2, mock3, mock4, mock5, mock6, mock7):
        trainingmgr_main.LOGGER.debug("******* test_pipeline_notification post *******")
        trainingjob_req = {
                    "trainingjob_name":"usecase1",
                    "run_status":"Succeeded",
                    }
        expected_data = "Pipeline notification success."
        response = self.client.post("/trainingjob/pipelineNotification".format("usecase1"),data=json.dumps(trainingjob_req),
                                    content_type="application/json")
        trainingmgr_main.LOGGER.debug(response.data)    
        assert response.status_code == status.HTTP_200_OK, "Return status code NOT equal"
        assert expected_data in str(response.data)
    ##################CODE ENDS HERE###############################################
    
    #####################CODE HERE###############################################
    #Testcases for 520 line
    mocked_mm_sdk=mock.Mock(name="MM_SDK")
    attrs_mm_sdk = {'check_object.return_value': False}
    mocked_mm_sdk.configure_mock(**attrs_mm_sdk)
    mocked_TRAININGMGR_CONFIG_OBJ=mock.Mock(name="TRAININGMGR_CONFIG_OBJ")
    attrs_TRAININGMGR_CONFIG_OBJ = {'my_ip.return_value': 123, 'my_port.return_value' : 100}
    mocked_TRAININGMGR_CONFIG_OBJ.configure_mock(**attrs_TRAININGMGR_CONFIG_OBJ)
    message1="Pipeline notification success."
    code1=status.HTTP_200_OK
    response_tuple1=({"result": message1}, code1)
    @patch('trainingmgr.trainingmgr_main.MM_SDK', return_value = mmSDK_dummy())
    @patch('trainingmgr.trainingmgr_main.TRAININGMGR_CONFIG_OBJ', return_value = mocked_TRAININGMGR_CONFIG_OBJ) 
    @patch('trainingmgr.trainingmgr_main.check_key_in_dictionary', return_value = Exception())
    @patch('trainingmgr.trainingmgr_main.update_model_download_url')
    @patch('trainingmgr.trainingmgr_main.get_latest_version_trainingjob_name', return_value = "usecase1")
    @patch('trainingmgr.trainingmgr_main.response_for_training', return_value = response_tuple1)
    @patch('trainingmgr.trainingmgr_main.LOGGER.error', return_value = True)
    def test_pipeline_notification_bb(self,mock1, mock2, mock3, mock4, mock5, mock6, mock7):
        trainingmgr_main.LOGGER.debug("******* test_pipeline_notification post *******")
        trainingjob_req = {
                    "trainingjob_name":"usecase1",
                    "run_status":"Succeeded",
                    }
        expected_data = "Pipeline notification success."
        response = self.client.post("/trainingjob/pipelineNotification".format("usecase1"),data=json.dumps(trainingjob_req),
                                    content_type="application/json")
        trainingmgr_main.LOGGER.debug(response.data)    
        assert response.status_code == 500, "Return status code NOT equal"
    ##################CODE ENDS HERE###############################################
   
    mocked_mm_sdk=mock.Mock(name="MM_SDK")
    attrs_mm_sdk = {'check_object.return_value': True}
    mocked_mm_sdk.configure_mock(**attrs_mm_sdk)
    mocked_TRAININGMGR_CONFIG_OBJ=mock.Mock(name="TRAININGMGR_CONFIG_OBJ")
    attrs_TRAININGMGR_CONFIG_OBJ = {'my_ip.return_value': 123, 'my_port.return_value' : 100}
    mocked_TRAININGMGR_CONFIG_OBJ.configure_mock(**attrs_TRAININGMGR_CONFIG_OBJ)
    message1="Pipeline notification success."
    code1=status.HTTP_200_OK
    response_tuple1=({"result": message1}, code1)
    @patch('trainingmgr.trainingmgr_main.MM_SDK', return_value = mocked_mm_sdk)
    @patch('trainingmgr.trainingmgr_main.TRAININGMGR_CONFIG_OBJ', return_value = mocked_TRAININGMGR_CONFIG_OBJ) 
    @patch('trainingmgr.trainingmgr_main.change_steps_state_of_latest_version')
    @patch('trainingmgr.trainingmgr_main.update_model_download_url')
    @patch('trainingmgr.trainingmgr_main.get_latest_version_trainingjob_name', return_value = "usecase1")
    @patch('trainingmgr.trainingmgr_main.response_for_training', return_value = response_tuple1)
    def test_pipeline_notification(self,mock1, mock2, mock3, mock4, mock5, mock6):
        trainingmgr_main.LOGGER.debug("******* test_pipeline_notification post *******")
        trainingjob_req = {
                    "trainingjob_name":"usecase1",
                    "run_status":"Succeeded",
                    }
        expected_data = "Pipeline notification success."
        response = self.client.post("/trainingjob/pipelineNotification".format("usecase1"),data=json.dumps(trainingjob_req),
                                    content_type="application/json")
        trainingmgr_main.LOGGER.debug(response.data)    
        assert response.status_code == status.HTTP_200_OK, "Return status code NOT equal"
        assert expected_data in str(response.data)

    mocked_mm_sdk=mock.Mock(name="MM_SDK")
    attrs_mm_sdk = {'check_object.return_value': True}
    mocked_mm_sdk.configure_mock(**attrs_mm_sdk)
    mocked_TRAININGMGR_CONFIG_OBJ=mock.Mock(name="TRAININGMGR_CONFIG_OBJ")
    attrs_TRAININGMGR_CONFIG_OBJ = {'my_ip.return_value': 123, 'my_port.return_value' : 100}
    mocked_TRAININGMGR_CONFIG_OBJ.configure_mock(**attrs_TRAININGMGR_CONFIG_OBJ)
    message1="Pipeline notification success."
    code1=status.HTTP_200_OK
    response_tuple1=({"result": message1}, code1)
    @patch('trainingmgr.trainingmgr_main.MM_SDK', return_value = mocked_mm_sdk)
    @patch('trainingmgr.trainingmgr_main.TRAININGMGR_CONFIG_OBJ', return_value = mocked_TRAININGMGR_CONFIG_OBJ) 
    @patch('trainingmgr.trainingmgr_main.change_steps_state_of_latest_version')
    @patch('trainingmgr.trainingmgr_main.update_model_download_url')
    @patch('trainingmgr.trainingmgr_main.get_latest_version_trainingjob_name', return_value = "usecase1")
    @patch('trainingmgr.trainingmgr_main.response_for_training', return_value = response_tuple1)
    def test_pipeline_notification(self,mock1, mock2, mock3, mock4, mock5, mock6):
        trainingmgr_main.LOGGER.debug("******* test_pipeline_notification post *******")
        trainingjob_req = {
                    "trainingjob_name":"usecase1",
                    "run_status":"Succeeded",
                    }
        expected_data = "Pipeline notification success."
        response = self.client.post("/trainingjob/pipelineNotification".format("usecase1"),data=json.dumps(trainingjob_req),
                                    content_type="application/json")
        trainingmgr_main.LOGGER.debug(response.data)    
        assert response.status_code == status.HTTP_200_OK, "Return status code NOT equal"
        assert expected_data in str(response.data)
    
    #####################CODE HERE###############################################
    mocked_mm_sdk=mock.Mock(name="MM_SDK")
    attrs_mm_sdk = {'check_object.return_value': False}
    mocked_mm_sdk.configure_mock(**attrs_mm_sdk)
    mocked_TRAININGMGR_CONFIG_OBJ=mock.Mock(name="TRAININGMGR_CONFIG_OBJ")
    attrs_TRAININGMGR_CONFIG_OBJ = {'my_ip.return_value': 123, 'my_port.return_value' : 100}
    mocked_TRAININGMGR_CONFIG_OBJ.configure_mock(**attrs_TRAININGMGR_CONFIG_OBJ)
    message1="Pipeline notification success."
    code1=status.HTTP_200_OK
    response_tuple1=({"result": message1}, code1)
    @patch('trainingmgr.trainingmgr_main.MM_SDK', return_value = mocked_mm_sdk)
    @patch('trainingmgr.trainingmgr_main.TRAININGMGR_CONFIG_OBJ', return_value = mocked_TRAININGMGR_CONFIG_OBJ) 
    @patch('trainingmgr.trainingmgr_main.change_steps_state_of_latest_version')
    @patch('trainingmgr.trainingmgr_main.update_model_download_url')
    @patch('trainingmgr.trainingmgr_main.get_latest_version_trainingjob_name', return_value = "usecase1")
    @patch('trainingmgr.trainingmgr_main.response_for_training', return_value = response_tuple1)
    def test_pipeline_notification_22(self,mock1, mock2, mock3, mock4, mock5, mock6):
        trainingmgr_main.LOGGER.debug("******* test_pipeline_notification post *******")
        trainingjob_req = {
                    "trainingjob_name":"usecase1",
                    "run_status":"Succeeded",
                    }
        expected_data = "Pipeline notification success."
        response = self.client.post("/trainingjob/pipelineNotification".format("usecase1"),data=json.dumps(trainingjob_req),
                                    content_type="application/json")
        trainingmgr_main.LOGGER.debug(response.data)    
        assert response.status_code == status.HTTP_200_OK, "Return status code NOT equal"
        assert expected_data in str(response.data)

    ##################CODE ENDS HERE###############################################
    message2="Pipeline notification -Training failed "
    code2=status.HTTP_500_INTERNAL_SERVER_ERROR
    response_tuple2=({"result": message2}, code2)
    @patch('trainingmgr.trainingmgr_main.MM_SDK', return_value = mocked_mm_sdk)
    @patch('trainingmgr.trainingmgr_main.TRAININGMGR_CONFIG_OBJ', return_value = mocked_TRAININGMGR_CONFIG_OBJ) 
    @patch('trainingmgr.trainingmgr_main.change_steps_state_of_latest_version')
    @patch('trainingmgr.trainingmgr_main.update_model_download_url')
    @patch('trainingmgr.trainingmgr_main.get_latest_version_trainingjob_name', return_value = "usecase1")
    @patch('trainingmgr.trainingmgr_main.response_for_training', return_value = response_tuple2)
    @patch('trainingmgr.trainingmgr_main.change_in_progress_to_failed_by_latest_version', return_value = True)
    def test_negative_pipeline_notification(self,mock1, mock2, mock3, mock4, mock5, mock6, mock7):
        trainingmgr_main.LOGGER.debug("******* test_pipeline_notification post exception*******")
        trainingjob_req = {
                    "trainingjob_name":"usecase1",
                    "run_status":"Not_Succeeded",
                    }
        expected_data = "Pipeline notification -Training failed "
        response = self.client.post("/trainingjob/pipelineNotification".format("usecase1"),
                                    data=json.dumps(trainingjob_req),
                                    content_type="application/json")
        trainingmgr_main.LOGGER.debug(response.data)    
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR, "Return status code NOT equal"
        assert expected_data in str(response.data)
    
    db_result4 = [("test_data1","test_data2"),("version1")]
    @patch('trainingmgr.trainingmgr_main.get_field_of_given_version', return_value = db_result4)
    def test_get_steps_state_2(self,mock1):
        trainingmgr_main.LOGGER.debug("******* test_get_steps_state get *******")
        expected_data = "test_data1"
        response = self.client.get("/trainingjobs/<trainingjob_name>/<version>/steps_state".format("usecase1"),
                                    content_type="application/json")
        trainingmgr_main.LOGGER.debug(response.data)    
        assert response.status_code == status.HTTP_200_OK, "Return status code NOT equal"
        assert expected_data in str(response.data)

    db_result5 = []
    @patch('trainingmgr.trainingmgr_main.get_field_of_given_version', return_value = db_result5)
    def test_negative_get_steps_state_2(self,mock1):
        expected_data = "Exception"
        response = self.client.get("/trainingjobs/<trainingjob_name>/<version>/steps_state".format("usecase1"),
                                    content_type="application/json")
        trainingmgr_main.LOGGER.debug(response.data)    
        assert response.status_code == status.HTTP_404_NOT_FOUND, "Return status code NOT equal"
        assert expected_data in str(response.data)

class Test_get_trainingjob_by_name_version:
    def setup_method(self):
        self.client = trainingmgr_main.APP.test_client(self)
        self.logger = trainingmgr_main.LOGGER

    @patch('trainingmgr.trainingmgr_main.get_info_by_version',return_value=[('usecase7', 'auto test', '*', 'prediction with model name', 'Default', '{"arguments": {"epochs": "1", "usecase": "usecase7"}}', 'Enb=20 and Cellnum=6', datetime.datetime(2022, 9, 20,11, 40, 30), '7d09c0bf-7575-4475-86ff-5573fb3c4716', '{"DATA_EXTRACTION": "FINISHED", "DATA_EXTRACTION_AND_TRAINING": "FINISHED", "TRAINING": "FINISHED", "TRAINING_AND_TRAINED_MODEL": "FINISHED", "TRAINED_MODEL": "FINISHED"}', datetime.datetime(2022, 9, 20, 11, 42, 20), 1, True, 'Near RT RIC', '{"datalake_source": {"CassandraSource": {}}}', '{"datalake_source": {"CassandraSource": {}}}','http://10.0.0.47:32002/model/usecase7/1/Model.zip','','','','','')])
    @patch('trainingmgr.trainingmgr_main.get_metrics',return_value={"metrics": [{"Accuracy": "0.0"}]})
    @patch('trainingmgr.trainingmgr_main.get_one_key',return_value='cassandra')
    def test_get_trainingjob_by_name_version(self,mock1,mock2,mock3):
        usecase_name = "usecase7"
        version = "1"
        response = self.client.get("/trainingjobs/{}/{}".format(usecase_name, version))
        expected_data = b'{"trainingjob": {"trainingjob_name": "usecase7", "description": "auto test", "feature_list": "*", "pipeline_name": "prediction with model name", "experiment_name": "Default", "arguments": {"epochs": "1", "usecase": "usecase7"}, "query_filter": "Enb=20 and Cellnum=6", "creation_time": "2022-09-20 11:40:30", "run_id": "7d09c0bf-7575-4475-86ff-5573fb3c4716", "steps_state": {"DATA_EXTRACTION": "FINISHED", "DATA_EXTRACTION_AND_TRAINING": "FINISHED", "TRAINING": "FINISHED", "TRAINING_AND_TRAINED_MODEL": "FINISHED", "TRAINED_MODEL": "FINISHED"}, "updation_time": "2022-09-20 11:42:20", "version": 1, "enable_versioning": true, "pipeline_version": "Near RT RIC", "datalake_source": "cassandra", "model_url": "{\\"datalake_source\\": {\\"CassandraSource\\": {}}}", "notification_url": "http://10.0.0.47:32002/model/usecase7/1/Model.zip", "_measurement": "", "bucket": "", "accuracy": {"metrics": [{"Accuracy": "0.0"}]}}}'

        assert response.content_type == "application/json", "not equal content type"
        assert response.status_code == status.HTTP_200_OK, "not equal code"
        assert response.data == expected_data, "not equal data"

    @patch('trainingmgr.trainingmgr_main.get_info_by_version',return_value=False)
    @patch('trainingmgr.trainingmgr_main.get_metrics',return_value={"metrics": [{"Accuracy": "0.0"}]})
    @patch('trainingmgr.trainingmgr_main.get_one_key',return_value='cassandra')
    def test_negative_get_trainingjob_by_name_version(self,mock1,mock2,mock3):
        usecase_name = "usecase7"
        version = "1"
        response = self.client.get("/trainingjobs/{}/{}".format(usecase_name, version))
        expected_data = b'{"trainingjob": {"trainingjob_name": "usecase7", "description": "auto test", "feature_list": "*", "pipeline_name": "prediction with model name", "experiment_name": "Default", "arguments": {"epochs": "1", "usecase": "usecase7"}, "query_filter": "Enb=20 and Cellnum=6", "creation_time": "2022-09-20 11:40:30", "run_id": "7d09c0bf-7575-4475-86ff-5573fb3c4716", "steps_state": {"DATA_EXTRACTION": "FINISHED", "DATA_EXTRACTION_AND_TRAINING": "FINISHED", "TRAINING": "FINISHED", "TRAINING_AND_TRAINED_MODEL": "FINISHED", "TRAINED_MODEL": "FINISHED"}, "updation_time": "2022-09-20 11:42:20", "version": 1, "enable_versioning": true, "pipeline_version": "Near RT RIC", "datalake_source": "cassandra", "model_url": "{\\"datalake_source\\": {\\"CassandraSource\\": {}}}", "notification_url": "http://10.0.0.47:32002/model/usecase7/1/Model.zip", "_measurement": "", "bucket": "", "accuracy": {"metrics": [{"Accuracy": "0.0"}]}}}'

        trainingmgr_main.LOGGER.debug(expected_data)
        trainingmgr_main.LOGGER.debug(response.data)
        assert response.content_type == "application/json", "not equal content type"
        assert response.status_code == 404, "not equal code"

class Test_unpload_pipeline:
    def setup_method(self):
        self.client = trainingmgr_main.APP.test_client(self)
        self.logger = trainingmgr_main.LOGGER
    
    def test_negative_upload_pipeline(self):
        pipeline_name = "qoe"
        response = self.client.post("/pipelines/{}/upload".format(pipeline_name))
        expected = "jjjj"
        assert response.content_type == "application/json", "not equal content type"
        assert response.status_code == 500, "not equal code"

    @patch('trainingmgr.trainingmgr_main.LOGGER.debug', return_value = True)
    def test_negative_upload_pipeline_2(self,mock1):
        pipeline_name = "qoe"
        response = self.client.post("/pipelines/{}/upload".format(pipeline_name))
        expected = ValueError("file not found in request.files")
        assert response.content_type == "application/json", "not equal content type"
        assert response.status_code == 500, "not equal code"

class Test_get_steps_state:
      def setup_method(self):
        self.client = trainingmgr_main.APP.test_client(self)
        self.logger = trainingmgr_main.LOGGER
      
      @patch('trainingmgr.trainingmgr_main.get_field_of_given_version',return_value=[['data_extracted','data_pending'], ['data1','data2']])
      def test_get_steps_state(self,mock1):
          usecase_name = "usecase7"
          version = "1" 
          response = self.client.get("/trainingjobs/{}/{}/steps_state".format(usecase_name, version))
          expected_data = b'data_extracted'
          assert response.content_type == "application/json", "not equal content type"
          assert response.status_code == status.HTTP_200_OK, "not equal code"
          assert response.data == expected_data, "not equal data"

      @patch('trainingmgr.trainingmgr_main.get_field_of_given_version',return_value=False)
      def test_negative_get_steps_state(self,mock1):
          usecase_name = "usecase7"
          version = "1" 
          response = self.client.get("/trainingjobs/{}/{}/steps_state".format(usecase_name, version))
          expected_data = b'data_extracted'
          assert response.content_type == "application/json", "not equal content type"
          assert response.status_code == 404, "not equal code"
    
      @patch('trainingmgr.trainingmgr_main.get_field_of_given_version',return_value=Exception("Not found given trainingjob with version"))
      def test_negative_get_steps_state_2(self,mock1):
          usecase_name = "usecase7"
          version = "1" 
          response = self.client.get("/trainingjobs/{}/{}/steps_state".format(usecase_name, version))
          expected_data = b'data_extracted'
          assert response.status_code == 500, "not equal code"
          
class Test_training_main:
    def setup_method(self):
        self.client = trainingmgr_main.APP.test_client(self)
        self.logger = trainingmgr_main.LOGGER

    @patch('trainingmgr.trainingmgr_main.validate_trainingjob_name', return_value = False)
    @patch('trainingmgr.trainingmgr_main.add_update_trainingjob')
    def test_trainingjob_operations(self,mock1,mock2):
        trainingmgr_main.LOGGER.debug("******* test_trainingjob_operations post *******")
        trainingjob_req = {
                    "trainingjob_name":"usecase1",
                    "pipeline_name":"qoe Pipeline lat v2",
                    "experiment_name":"Default",
                    "feature_list":"*",
                    "query_filter":"",
                    "arguments":{
                        "epochs":"1",
                        "trainingjob_name":"usecase1"
                    },
                    "enable_versioning":False,
                    "description":"uc1",
                    "pipeline_version":"3",
                    "datalake_source":"InfluxSource",
                    "_measurement":"liveCell",
                    "bucket":"UEData"
                    }
        expected_data = b'{"result": "Information stored in database."}'
        response = self.client.post("/trainingjobs/<trainingjob_name>".format("usecase1"),
                                    data=json.dumps(trainingjob_req),
                                    content_type="application/json")
        trainingmgr_main.LOGGER.debug(response.data)    
        assert response.data == expected_data
        assert response.status_code == status.HTTP_201_CREATED, "Return status code NOT equal" 

    db_result = [('usecase1', 'uc1', '*', 'qoe Pipeline lat v2', 'Default', '{"arguments": {"epochs": "1", "trainingjob_name": "usecase1"}}',
     '', datetime.datetime(2022, 10, 12, 10, 0, 59, 923588), '51948a12-aee9-42e5-93a0-b8f4a15bca33',
      '{"DATA_EXTRACTION": "FINISHED", "DATA_EXTRACTION_AND_TRAINING": "FINISHED", "TRAINING": "FINISHED", "TRAINING_AND_TRAINED_MODEL": "FINISHED", "TRAINED_MODEL": "FAILED"}',
       datetime.datetime(2022, 10, 12, 10, 2, 31, 888830), 1, False, '3', '{"datalake_source": {"InfluxSource": {}}}', 'No data available.', '', 'liveCell', 'UEData', False)]
    
    training_data = ('','','','','','','','','','','')
    @patch('trainingmgr.trainingmgr_main.validate_trainingjob_name', return_value = True)
    @patch('trainingmgr.trainingmgr_main.get_trainingjob_info_by_name', return_value = db_result)
    @patch('trainingmgr.trainingmgr_main.check_trainingjob_data', return_value = training_data)
    @patch('trainingmgr.trainingmgr_main.add_update_trainingjob')
    def test_trainingjob_operations_put(self,mock1,mock2,mock3,mock4):
        trainingmgr_main.LOGGER.debug("******* test_trainingjob_operations_put *******")
        trainingjob_req = {
                    "trainingjob_name":"usecase1",
                    "pipeline_name":"qoe Pipeline lat v2",
                    "experiment_name":"Default",
                    "feature_list":"*",
                    "query_filter":"",
                    "arguments":{
                        "epochs":"1",
                        "trainingjob_name":"usecase1"
                    },
                    "enable_versioning":False,
                    "description":"updated",
                    "pipeline_version":"3",
                    "datalake_source":"InfluxSource",
                    "_measurement":"liveCell",
                    "bucket":"UEData"
                    }
            
        expected_data = 'Information updated in database'
        response = self.client.put("/trainingjobs/<trainingjob_name>".format("usecase1"),
                                    data=json.dumps(trainingjob_req),
                                    content_type="application/json")
        trainingmgr_main.LOGGER.debug(response.data)        
        assert response.status_code == status.HTTP_200_OK, "Return status code NOT equal" 
        assert expected_data in str(response.data)

    @patch('trainingmgr.trainingmgr_main.validate_trainingjob_name', return_value = True)
    def test_negative_trainingjob_operations_post_conflit(self,mock1):
        trainingmgr_main.LOGGER.debug("******* test_negative_trainingjob_operations_post_conflit *******")
        trainingjob_req = {
                    "trainingjob_name":"usecase1",
                    "pipeline_name":"qoe Pipeline lat v2",
                    "experiment_name":"Default",
                    "feature_list":"*",
                    "query_filter":"",
                    "arguments":{
                        "epochs":"1",
                        "trainingjob_name":"usecase1"
                    },
                    "enable_versioning":False,
                    "description":"uc1",
                    "pipeline_version":"3",
                    "datalake_source":"InfluxSource",
                    "_measurement":"liveCell",
                    "bucket":"UEData"
                    }
        expected_data = 'is already present in database'
        response = self.client.post("/trainingjobs/<trainingjob_name>".format("usecase1"),
                                    data=json.dumps(trainingjob_req),
                                    content_type="application/json")
        trainingmgr_main.LOGGER.debug(response.data)           
        assert response.status_code == status.HTTP_409_CONFLICT, "Return status code NOT equal"
        assert expected_data in str(response.data)

    db_result = [('usecase1', 'uc1', '*', 'qoe Pipeline lat v2', 'Default', '{"arguments": {"epochs": "1", "trainingjob_name": "usecase1"}}',
    '', datetime.datetime(2022, 10, 12, 10, 0, 59, 923588), '51948a12-aee9-42e5-93a0-b8f4a15bca33',
    '{"DATA_EXTRACTION": "FINISHED", "DATA_EXTRACTION_AND_TRAINING": "FINISHED", "TRAINING": "FINISHED", "TRAINING_AND_TRAINED_MODEL": "FINISHED", "TRAINED_MODEL": "FAILED"}',
    datetime.datetime(2022, 10, 12, 10, 2, 31, 888830), 1, False, '3', '{"datalake_source": {"InfluxSource": {}}}', 'No data available.', '', 'liveCell', 'UEData', False)]

    de_response_fake = Response()
    de_response_fake.code = "expired"
    de_response_fake.error_type = "expired"
    de_response_fake.status_code = status.HTTP_200_OK
    de_response_fake.headers={"content-type": "application/json"}
    de_response_fake._content = b'{"task_status": "Completed", "result": "Data Pipeline Execution Completed"}'

    @patch('trainingmgr.trainingmgr_main.validate_trainingjob_name', return_value = True)
    @patch('trainingmgr.trainingmgr_main.get_trainingjob_info_by_name', return_value = db_result)
    @patch('trainingmgr.trainingmgr_main.data_extraction_start', return_value = de_response_fake)
    @patch('trainingmgr.trainingmgr_main.change_steps_state_of_latest_version')
    def test_training(self,mock1,mock2,mock3,mock4):
        trainingmgr_main.LOGGER.debug("******* test_trainingjob_operations post *******")
        expected_data = 'Data Pipeline Execution Completed"'
        response = self.client.post("/trainingjobs/<trainingjob_name>/training".format("usecase1"),
                                    content_type="application/json")
        trainingmgr_main.LOGGER.debug(response.data)    
        assert response.status_code == 200, "Return status code NOT equal"
        assert expected_data in str(response.data) 
    
    de_response_fake = Response()
    de_response_fake.code = "expired"
    de_response_fake.error_type = "expired"
    de_response_fake.status_code = 500
    de_response_fake.headers={"content-type": "application/json"}
    de_response_fake._content = b'{"task_status": "Completed", "result": "Data Pipeline Execution Completed"}'
    @patch('trainingmgr.trainingmgr_main.validate_trainingjob_name', return_value = True)
    @patch('trainingmgr.trainingmgr_main.get_trainingjob_info_by_name', return_value = db_result)
    @patch('trainingmgr.trainingmgr_main.data_extraction_start', return_value = de_response_fake)
    @patch('trainingmgr.trainingmgr_main.change_steps_state_of_latest_version')
    def test_negative_training(self,mock1,mock2,mock3,mock4):
        trainingmgr_main.LOGGER.debug("******* test_trainingjob_operations post *******")
        expected_data = 'Data Pipeline Execution Completed"'
        response = self.client.post("/trainingjobs/<trainingjob_name>/training".format("usecase1"),
                                    content_type="application/json")
        trainingmgr_main.LOGGER.debug(response.data)    
        assert response.status_code == 500, "Return status code NOT equal"

    de_response_fake = Response()
    de_response_fake.code = "expired"
    de_response_fake.error_type = "expired"
    de_response_fake.status_code = 500
    de_response_fake.headers={"content-type": "applicationn/json"}
    de_response_fake._content = b'{"task_status": "Completed", "result": "Data Pipeline Execution Completed"}'
    @patch('trainingmgr.trainingmgr_main.validate_trainingjob_name', return_value = True)
    @patch('trainingmgr.trainingmgr_main.get_trainingjob_info_by_name', return_value = db_result)
    @patch('trainingmgr.trainingmgr_main.data_extraction_start', return_value = de_response_fake)
    @patch('trainingmgr.trainingmgr_main.change_steps_state_of_latest_version')
    def test_negative_training2(self,mock1,mock2,mock3,mock4):
        trainingmgr_main.LOGGER.debug("******* test_trainingjob_operations post *******")
        expected_data = 'Data Pipeline Execution Completed"'
        response = self.client.post("/trainingjobs/<trainingjob_name>/training".format("usecase1"),
                                    content_type="application/json")
        trainingmgr_main.LOGGER.debug(response.data)    
        assert response.status_code == 500, "Return status code NOT equal"
   
    de_response_fake = Response()
    de_response_fake.code = "expired"
    de_response_fake.error_type = "expired"
    de_response_fake.status_code = 500
    de_response_fake.headers={"content-type": "application/json"}
    de_response_fake._content = b'{"task_status": "Completed", "result": "Data Pipeline Execution Completed"}'
    @patch('trainingmgr.trainingmgr_main.validate_trainingjob_name', return_value = True)
    @patch('trainingmgr.trainingmgr_main.get_trainingjob_info_by_name', return_value = db_result)
    @patch('trainingmgr.trainingmgr_main.data_extraction_start', return_value = de_response_fake)
    @patch('trainingmgr.trainingmgr_main.check_key_in_dictionary', return_value = False)
    def test_negative_training3(self,mock1,mock2,mock3,mock4):
        trainingmgr_main.LOGGER.debug("******* test_trainingjob_operations post *******")
        expected_data = 'Data Pipeline Execution Completed'
        response = self.client.post("/trainingjobs/<trainingjob_name>/training".format("usecase1"),
                                    content_type="application/json")
        trainingmgr_main.LOGGER.debug(response.data)    
        assert response.status_code == 500, "Return status code NOT equal"

    db_result1 = [('usecase1', 'uc1', '*', 'qoe Pipeline lat v2', 'Default', '{"arguments": {"epochs": "1", "trainingjob_name": "usecase1"}}',
    '', datetime.datetime(2022, 10, 12, 10, 0, 59, 923588), '51948a12-aee9-42e5-93a0-b8f4a15bca33',
    '{"DATA_EXTRACTION": "FINISHED", "DATA_EXTRACTION_AND_TRAINING": "FINISHED", "TRAINING": "FINISHED", "TRAINING_AND_TRAINED_MODEL": "FINISHED", "TRAINED_MODEL": "FAILED"}',
    datetime.datetime(2022, 10, 12, 10, 2, 31, 888830), 1, False, '3', '{"datalake_source": {"InfluxSource": {}}}', 'No data available.', '', 'liveCell', 'UEData', False)]

    de_response1 = Response()
    de_response1.code = "expired"
    de_response1.error_type = "expired"
    de_response1.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    de_response1.headers={"content-type": "application/json"}
    de_response1._content = b'{"task_status": "Failed", "result": "Data Pipeline Execution Failed"}'

    @patch('trainingmgr.trainingmgr_main.validate_trainingjob_name', return_value = True)
    @patch('trainingmgr.trainingmgr_main.get_trainingjob_info_by_name', return_value = db_result1)
    @patch('trainingmgr.trainingmgr_main.data_extraction_start', return_value = de_response1)
    @patch('trainingmgr.trainingmgr_main.change_steps_state_of_latest_version')
    def test_training_negative_de_failed(self,mock1,mock2,mock3,mock4):
        trainingmgr_main.LOGGER.debug("******* test_trainingjob_operations post *******")
        expected_data = 'Data Pipeline Execution Failed'
        response = self.client.post("/trainingjobs/<trainingjob_name>/training".format("usecase1"),
                                    content_type="application/json")
        trainingmgr_main.LOGGER.debug(response.data)
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR, "Return status code NOT equal" 
        assert expected_data in str(response.data) 

class Test_get_versions_for_pipeline:
    @patch('trainingmgr.common.trainingmgr_config.TMLogger', return_value = TMLogger("tests/common/conf_log.yaml"))
    def setup_method(self,mock1,mock2):
        self.client = trainingmgr_main.APP.test_client(self)
        self.logger = trainingmgr_main.LOGGER
        load_dotenv('tests/test.env')
        self.TRAININGMGR_CONFIG_OBJ = TrainingMgrConfig()   

    the_response = Response()
    the_response.code = "expired"
    the_response.error_type = "expired"
    the_response.status_code = 200
    the_response.headers={"content-type": "application/json"}
    the_response._content = b'{"versions_list": ["football", "baseball"]}'
    
    mocked_TRAININGMGR_CONFIG_OBJ=mock.Mock(name="TRAININGMGR_CONFIG_OBJ")
    attrs_TRAININGMGR_CONFIG_OBJ = {'kf_adapter_ip.return_value': '123', 'kf_adapter_port.return_value' : '100'}
    mocked_TRAININGMGR_CONFIG_OBJ.configure_mock(**attrs_TRAININGMGR_CONFIG_OBJ)
    @patch('trainingmgr.trainingmgr_main.TRAININGMGR_CONFIG_OBJ', return_value = mocked_TRAININGMGR_CONFIG_OBJ)
    @patch('trainingmgr.trainingmgr_main.requests.get', return_value = the_response)
    def test_get_versions_for_pipeline_positive(self,mock1,mock2):
        response = self.client.get("/pipelines/{}/versions".format("qoe_pipeline"))     
        trainingmgr_main.LOGGER.debug(response.data)
        assert response.content_type == "application/json", "not equal content type"
        assert response.status_code == 200, "Return status code NOT equal"   
        

    @patch('trainingmgr.trainingmgr_main.requests.get', return_value = the_response)
    def test_get_versions_for_pipeline(self,mock1):
        
        response = self.client.get("/pipelines/{}/versions".format("qoe_pipeline"))     
        trainingmgr_main.LOGGER.debug(response.data)
        assert response.content_type == "application/json", "not equal content type"
        assert response.status_code == 500, "Return status code NOT equal"   
        
    @patch('trainingmgr.trainingmgr_main.requests.get', side_effect = requests.exceptions.ConnectionError('Mocked error'))
    def test_negative_get_versions_for_pipeline_1(self,mock1):
        response = self.client.get("/pipelines/{}/versions".format("qoe_pipeline"))       
        print(response.data)
        assert response.content_type == "application/json", "not equal content type"
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR, "Should have thrown the exception "
        
    @patch('trainingmgr.trainingmgr_main.requests.get', side_effect = TypeError('Mocked error'))
    def test_negative_get_versions_for_pipeline_2(self,mock1):
        response = self.client.get("/pipelines/{}/versions".format("qoe_pipeline"))      
        print(response.data)
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR, "Should have thrown the exception "

    the_response1 = Response()
    the_response1.code = "expired"
    the_response1.error_type = "expired"
    the_response1.status_code = 200
    the_response1.headers={"content-type": "application/text"}
    the_response._content = b'{"versions_list": ["football", "baseball"]}'
    @patch('trainingmgr.trainingmgr_main.requests.get', return_value = the_response1)
    def test_negative_get_versions_for_pipeline_3(self,mock1):
        response = self.client.get("/pipelines/{}/versions".format("qoe_pipeline"))       
        print(response.data)
        assert response.content_type != "application/text", "not equal content type"
    
class Test_get_all_pipeline_names:
    @patch('trainingmgr.common.trainingmgr_config.TMLogger', return_value = TMLogger("tests/common/conf_log.yaml"))
    def setup_method(self,mock1,mock2):
        self.client = trainingmgr_main.APP.test_client(self)
        self.logger = trainingmgr_main.LOGGER
        load_dotenv('tests/test.env')
        trainingmgr_main.TRAININGMGR_CONFIG_OBJ = TrainingMgrConfig()   

    the_response = Response()
    the_response.code = "expired"
    the_response.error_type = "expired"
    the_response.status_code = 200
    the_response.headers={"content-type": "application/json"}
    the_response._content = b'{ "exp1":"id1","exp2":"id2"}'
    @patch('trainingmgr.trainingmgr_main.requests.get', return_value = the_response)
    def test_get_all_pipeline_names(self,mock1):
        response = self.client.get("/pipelines")      
        assert response.content_type == "application/json", "not equal content type"
        assert response.status_code == 200, "Return status code NOT equal"   

    @patch('trainingmgr.trainingmgr_main.requests.get', return_value = the_response)
    def test_negative_get_all_pipeline_names_100001(self,mock1):
        response = self.client.get("/pipelines")   
        print("Subhasis Mahana")   
        print(response.data)
        expected_data = b'{"pipeline_names": ["exp1", "exp2"]}'
        assert response.content_type == "application/json", "not equal content type"
        assert response.status_code == 200, "Return status code NOT equal"
        assert response.data == b'{"pipeline_names": ["exp1", "exp2"]}'

    @patch('trainingmgr.trainingmgr_main.requests.get', side_effect = requests.exceptions.ConnectionError('Mocked error'))
    def test_negative_get_all_pipeline_names_1(self,mock1):
        response = self.client.get("/pipelines")       
        assert response.content_type == "application/json", "not equal content type"
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR, "Should have thrown the exception "
        
    @patch('trainingmgr.trainingmgr_main.requests.get', side_effect = TypeError('Mocked error'))
    def test_negative_get_all_pipeline_names_2(self,mock1):
        response = self.client.get("/pipelines")       
        print(response.data)
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR, "Should have thrown the exception "

    the_response1 = Response()
    the_response1.code = "expired"
    the_response1.error_type = "expired"
    the_response1.status_code = 200
    the_response1.headers={"content-type": "application/text"}
    the_response1._content = b'{ "exp1":"id1","exp2":"id2"}'
    @patch('trainingmgr.trainingmgr_main.requests.get', return_value = the_response1)
    def test_negative_get_all_pipeline_names_3(self,mock1):
        response = self.client.get("/pipelines")       
        print(response.data)
        assert response.content_type != "application/text", "not equal content type"

class Test_get_all_exp_names:
    def setup_method(self):
        self.client = trainingmgr_main.APP.test_client(self)
        self.logger = trainingmgr_main.LOGGER

    the_response = Response()
    the_response.code = "expired"
    the_response.error_type = "expired"
    the_response.status_code = 200
    the_response.headers={"content-type": "application/json"}
    the_response._content = b'{ "exp1":"id1","exp2":"id2"}'
    @patch('trainingmgr.trainingmgr_main.requests.get', return_value = the_response)
    def test_get_all_experiment_names(self,mock1):
        response = self.client.get("/experiments")      
        print(response.data)
        assert response.content_type == "application/json", "not equal content type"
        assert response.status_code == 200, "Return status code NOT equal"   
        
    @patch('trainingmgr.trainingmgr_main.requests.get', side_effect = requests.exceptions.ConnectionError('Mocked error'))
    def test_negative_get_all_experiment_names_1(self,mock1):
        response = self.client.get("/experiments")
        assert response.content_type == "application/json", "not equal content type"
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR, "Should have thrown the exception "

    @patch('trainingmgr.trainingmgr_main.requests.get', side_effect = TypeError('Mocked error'))
    def test_negative_get_all_experiment_names_2(self,mock1):
        response = self.client.get("/experiments")       
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR, "Should have thrown the exception "
    
    the_response1 = Response()
    the_response1.code = "expired"
    the_response1.error_type = "expired"
    the_response1.status_code = 200
    the_response1.headers={"content-type": "application/text"}
    the_response1._content = b'{ "exp1":"id1","exp2":"id2"}'
    @patch('trainingmgr.trainingmgr_main.requests.get', return_value = the_response1)
    def test_negative_get_all_experiment_names_3(self,mock1):
        response = self.client.get("/experiments")       
        assert response.content_type != "application/text", "not equal content type"

class Test_get_metadata:
    def setup_method(self):
        self.client = trainingmgr_main.APP.test_client(self)
        self.logger = trainingmgr_main.LOGGER
    
    resulttt = [('usecase7', '1','auto test',
           '*','prediction with model name',
           'Default','Enb=20 and Cellnum=6','epochs:1','FINISHED',
           '{"metrics": "FINISHED"}','Near RT RIC','1',
           'Cassandra DB','usecase7', '1','auto test','*',
           'prediction with model name',
           'Default','Enb=20 and Cellnum=6','epochs:1','{"metrics": [{"Accuracy": "0.0"}]}',
            'Default',False,'Cassandra DB','usecase7', '1','auto test','*','prediction with model name',
           'Default','Enb=20 and Cellnum=6','epochs:1','{"metrics": [{"Accuracy": "0.0"}]}',
           'Near RT RIC','3','Cassandra DB','usecase7', '1','auto test','*',
            'prediction with model name','Default','Enb=20 and Cellnum=6','epochs:1','{"metrics": [{"Accuracy": "0.0"}]}','Near RT RIC','3','Cassandra DB')
             ]
    mock_uc_config_obj = mock.Mock(name='mocked uc_config_obj')
    @patch('trainingmgr.trainingmgr_main.get_all_versions_info_by_name', return_value = resulttt)
    @patch('trainingmgr.trainingmgr_main.get_metrics', return_value = 90)
    @patch('trainingmgr.trainingmgr_main.TRAININGMGR_CONFIG_OBJ', return_value = mock_uc_config_obj)
    def test_get_metadata(self,mock1,mock2,mock3):
        usecase_name = "usecase7"
        response = self.client.get("/trainingjobs/metadata/{}".format(usecase_name))
        assert response.content_type == "application/json", "not equal content type"
        assert response.status_code == status.HTTP_200_OK, "Return status code NOT equal"

    @patch('trainingmgr.trainingmgr_main.get_all_versions_info_by_name', side_effect = Exception('Mocked error'))
    def test_negative_get_metadata_1(self,mock1):
        usecase_name = "usecase7"
        response = self.client.get("/trainingjobs/metadata/{}".format(usecase_name))
        
        print(response.data)
        assert response.content_type == "application/json", "not equal content type"
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR, "Should have thrown the exception "

    class Test_get_model:
         def setup_method(self):
            self.client = trainingmgr_main.APP.test_client(self)
            trainingmgr_main.LOGGER = TMLogger("tests/common/conf_log.yaml").logger
            self.logger = trainingmgr_main.LOGGER
        
         @patch('trainingmgr.trainingmgr_main.send_file', return_value = 'File')
         def test_negative_get_model(self,mock1):
            trainingjob_name = "usecase777"
            version = 2
            result = 'File'
            response = trainingmgr_main.get_model(trainingjob_name,version)
            assert response[1] == 500, "The function get_model Failed" 

class Test_get_metadata_1:
    def setup_method(self):
        self.client = trainingmgr_main.APP.test_client(self)
        self.logger = trainingmgr_main.LOGGER
    
    resulttt = [('usecase7', '1','auto test',
           '*','prediction with model name',
           'Default','Enb=20 and Cellnum=6','epochs:1','FINISHED',
           '{"metrics": "FINISHED"}','Near RT RIC','1',
           'Cassandra DB','usecase7', '1','auto test','*',
           'prediction with model name',
           'Default',False,'Enb=20 and Cellnum=6','epochs:1','{"metrics": [{"Accuracy": "0.0"}]}',
            'Default',False,'Cassandra DB','usecase7', '1','auto test','*','prediction with model name',
           'Default','Enb=20 and Cellnum=6','epochs:1','{"metrics": [{"Accuracy": "0.0"}]}',
           'Near RT RIC','3','Cassandra DB','usecase7', '1','auto test','*',
            'prediction with model name','Default','Enb=20 and Cellnum=6','epochs:1','{"metrics": [{"Accuracy": "0.0"}]}','Near RT RIC','3','Cassandra DB')
             ]

    mock_uc_config_obj = mock.Mock(name='mocked uc_config_obj')
    @patch('trainingmgr.trainingmgr_main.get_all_versions_info_by_name', return_value = resulttt)
    @patch('trainingmgr.trainingmgr_main.get_metrics', return_value = 90)
    @patch('trainingmgr.trainingmgr_main.TRAININGMGR_CONFIG_OBJ', return_value = mock_uc_config_obj)
    def test_get_metadata(self,mock1,mock2,mock3):
        usecase_name = "usecase7"
        response = self.client.get("/trainingjobs/metadata/{}".format(usecase_name))  
        assert response.content_type == "application/json", "not equal content type"
        assert response.status_code == status.HTTP_200_OK, "Return status code NOT equal"

    @patch('trainingmgr.trainingmgr_main.get_all_versions_info_by_name', return_value = None)
    def test_negative_get_metadata_1(self,mock1):
        usecase_name = "usecase7"
        response = self.client.get("/trainingjobs/metadata/{}".format(usecase_name)) 
        print(response.data)
        assert response.content_type == "application/json", "not equal content type"
        assert response.status_code == status.HTTP_404_NOT_FOUND, "Should have thrown the exception "

    @patch('trainingmgr.trainingmgr_main.validate_trainingjob_name', return_value = False)
    def test_training_negative_de_notfound(self,mock1):
        trainingmgr_main.LOGGER.debug("******* test_training_404_NotFound *******")
        expected_data = ''
        response = self.client.post("/trainingjobs/<trainingjob_name>/training".format("usecase1"),
                                    content_type="application/json")
        trainingmgr_main.LOGGER.debug(response.data)
        assert response.status_code == status.HTTP_404_NOT_FOUND, "Return status code NOT equal"
    
# class Test__main__:
#     def setup_method(self):
#         self.client = trainingmgr_main.APP.test_client(self)
#         self.logger = trainingmgr_main.LOGGER
        
#     mocked_TRAININGMGR_CONFIG_OBJ=mock.Mock(name="TRAININGMGR_CONFIG_OBJ")
#     attrs_TRAININGMGR_CONFIG_OBJ = {'kf_adapter_ip.return_value': '123', 'kf_adapter_port.return_value' : '100'}
#     mocked_TRAININGMGR_CONFIG_OBJ.configure_mock(**attrs_TRAININGMGR_CONFIG_OBJ)
#     mocked_mm_sdk=mock.Mock(name="MM_SDK")
#     attrs_mm_sdk = {'check_object.return_value': True}
#     mocked_mm_sdk.configure_mock(**attrs_mm_sdk)
#     mocked_TRAININGMGR_CONFIG_OBJ=mock.Mock(name="TRAININGMGR_CONFIG_OBJ")
#     attrs_TRAININGMGR_CONFIG_OBJ = {'my_ip.return_value': 123, 'my_port.return_value' : 100}
#     mocked_TRAININGMGR_CONFIG_OBJ.configure_mock(**attrs_TRAININGMGR_CONFIG_OBJ)
#     message1="Pipeline notification success."
#     code1=status.HTTP_200_OK
#     response_tuple1=({"result": message1}, code1)
#     @patch('trainingmgr.trainingmgr_main.MM_SDK', return_value = mocked_mm_sdk)
#     @patch('trainingmgr.trainingmgr_main.TRAININGMGR_CONFIG_OBJ', return_value = mocked_TRAININGMGR_CONFIG_OBJ)
#     def test__main__(self,mock1, mock2):
#         trainingmgr_main.main()
#         assert response.status_code == status.HTTP_404_NOT_FOUND, "Return status code NOT equal"
