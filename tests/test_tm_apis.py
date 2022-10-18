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
from trainingmgr import trainingmgr_main 
from trainingmgr.common.tmgr_logger import TMLogger
trainingmgr_main.LOGGER = TMLogger("./trainingmgr/common/conf_log.yaml").logger
trainingmgr_main.LOCK = Lock()
trainingmgr_main.DATAEXTRACTION_JOBS_CACHE = {}
class Test_training_main:
    def setup_method(self):
        self.client = trainingmgr_main.APP.test_client(self)
        self.logger = trainingmgr_main.LOGGER

    ## Postive_1
    #@pytest.mark.skip()
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

    ## Postive_2
    db_result = [('usecase1', 'uc1', '*', 'qoe Pipeline lat v2', 'Default', '{"arguments": {"epochs": "1", "trainingjob_name": "usecase1"}}',
     '', datetime.datetime(2022, 10, 12, 10, 0, 59, 923588), '51948a12-aee9-42e5-93a0-b8f4a15bca33',
      '{"DATA_EXTRACTION": "FINISHED", "DATA_EXTRACTION_AND_TRAINING": "FINISHED", "TRAINING": "FINISHED", "TRAINING_AND_TRAINED_MODEL": "FINISHED", "TRAINED_MODEL": "FAILED"}',
       datetime.datetime(2022, 10, 12, 10, 2, 31, 888830), 1, False, '3', '{"datalake_source": {"InfluxSource": {}}}', 'No data available.', '', 'liveCell', 'UEData', False)]
    
    training_data = ('','','','','','','','','','','')
    #@pytest.mark.skip()
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

    #@pytest.mark.skip()
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


    # ***** Start training test ****
    # Positive_1
    #@pytest.mark.skip()
    db_result = [('usecase1', 'uc1', '*', 'qoe Pipeline lat v2', 'Default', '{"arguments": {"epochs": "1", "trainingjob_name": "usecase1"}}',
    '', datetime.datetime(2022, 10, 12, 10, 0, 59, 923588), '51948a12-aee9-42e5-93a0-b8f4a15bca33',
    '{"DATA_EXTRACTION": "FINISHED", "DATA_EXTRACTION_AND_TRAINING": "FINISHED", "TRAINING": "FINISHED", "TRAINING_AND_TRAINED_MODEL": "FINISHED", "TRAINED_MODEL": "FAILED"}',
    datetime.datetime(2022, 10, 12, 10, 2, 31, 888830), 1, False, '3', '{"datalake_source": {"InfluxSource": {}}}', 'No data available.', '', 'liveCell', 'UEData', False)]

    de_response = Response()
    de_response = Response()
    de_response.code = "expired"
    de_response.error_type = "expired"
    de_response.status_code = status.HTTP_200_OK
    de_response.headers={"content-type": "application/json"}
    de_response._content = b'{"task_status": "Completed", "result": "Data Pipeline Execution Completed"}'

    #@pytest.mark.skip()
    @patch('trainingmgr.trainingmgr_main.validate_trainingjob_name', return_value = True)
    @patch('trainingmgr.trainingmgr_main.get_trainingjob_info_by_name', return_value = db_result)
    @patch('trainingmgr.trainingmgr_main.data_extraction_start', return_value = de_response)
    @patch('trainingmgr.trainingmgr_main.change_steps_state_of_latest_version')
    def test_training(self,mock1,mock2,mock3,mock4):
        trainingmgr_main.LOGGER.debug("******* test_trainingjob_operations post *******")
        expected_data = 'Data Pipeline Execution Completed"'
        response = self.client.post("/trainingjobs/<trainingjob_name>/training".format("usecase1"),
                                    content_type="application/json")
        trainingmgr_main.LOGGER.debug(response.data)    
        assert response.status_code == status.HTTP_200_OK, "Return status code NOT equal"
        assert expected_data in str(response.data) 

 

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