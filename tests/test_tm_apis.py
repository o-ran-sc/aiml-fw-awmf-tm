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
load_dotenv('tests/test.env')
from trainingmgr.constants.states import States
from threading import Lock
from trainingmgr import trainingmgr_main
from trainingmgr.common.tmgr_logger import TMLogger
from trainingmgr.common.trainingmgr_config import TrainingMgrConfig
from trainingmgr.common.exceptions_utls import DBException, TMException
from trainingmgr.models import TrainingJob

trainingmgr_main.LOGGER = pytest.logger
trainingmgr_main.LOCK = Lock()
trainingmgr_main.DATAEXTRACTION_JOBS_CACHE = {}

@pytest.mark.skip("")
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

@pytest.mark.skip("")
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
        
@pytest.mark.skip("")
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
        expected_data =  b'{"trainingjobs": []}'
        response = self.client.get("/trainingjobs/latest",content_type="application/json")
        trainingmgr_main.LOGGER.debug(response.data)    
        assert response.status_code == status.HTTP_200_OK, "Return status code NOT equal"
        assert expected_data in response.data

@pytest.mark.skip("")
class Test_pipeline_notification:
    def setup_method(self):
        self.client = trainingmgr_main.APP.test_client(self)
        self.logger = trainingmgr_main.LOGGER
        
    mocked_mm_sdk=mock.Mock(name="MM_SDK")
    attrs_mm_sdk = {'check_object.return_value': True, 'get_model_zip.return_value':""}
    mocked_mm_sdk.configure_mock(**attrs_mm_sdk)
    mocked_TRAININGMGR_CONFIG_OBJ=mock.Mock(name="TRAININGMGR_CONFIG_OBJ")
    attrs_TRAININGMGR_CONFIG_OBJ = {'my_ip.return_value': 123, 'my_port.return_value' : 100, 'model_management_service_ip.return_value': 123, 'model_management_service_port.return_value' : 100}
    mocked_TRAININGMGR_CONFIG_OBJ.configure_mock(**attrs_TRAININGMGR_CONFIG_OBJ)
    message1="Pipeline notification success."
    code1=status.HTTP_200_OK
    response_tuple1=({"result": message1}, code1)
    db_result = [('usecase1', 'uc1', '*', 'qoe Pipeline lat v2', 'Default', '{"arguments": {"epochs": "1", "trainingjob_name": "usecase1"}}',
     '', datetime.datetime(2022, 10, 12, 10, 0, 59, 923588), '51948a12-aee9-42e5-93a0-b8f4a15bca33',
      '{"DATA_EXTRACTION": "FINISHED", "DATA_EXTRACTION_AND_TRAINING": "FINISHED", "TRAINING": "FINISHED", "TRAINING_AND_TRAINED_MODEL": "FINISHED", "TRAINED_MODEL": "FAILED"}',
       datetime.datetime(2022, 10, 12, 10, 2, 31, 888830), 1, False, '3', '{"datalake_source": {"InfluxSource": {}}}', 'No data available.', '', 'liveCell', 'UEData', False, False, "","")]
    @patch('trainingmgr.trainingmgr_main.MM_SDK', return_value = mocked_mm_sdk)
    @patch('trainingmgr.trainingmgr_main.TRAININGMGR_CONFIG_OBJ', return_value = mocked_TRAININGMGR_CONFIG_OBJ) 
    @patch('trainingmgr.trainingmgr_main.change_steps_state_of_latest_version')
    @patch('trainingmgr.trainingmgr_main.update_model_download_url')
    @patch('trainingmgr.trainingmgr_main.get_trainingjob_info_by_name', return_value=db_result)
    @patch('trainingmgr.trainingmgr_main.get_latest_version_trainingjob_name', return_value = "usecase1")
    @patch('trainingmgr.trainingmgr_main.response_for_training', return_value = response_tuple1)
    def test_pipeline_notification(self,mock1, mock2, mock3, mock4, mock5, mock6, mock7):
        trainingmgr_main.LOGGER.debug("******* test_pipeline_notification post *******")
        trainingjob_req = {
                    "trainingjob_name":"usecase1",
                    "run_status":"SUCCEEDED",
                    }
        expected_data = "Pipeline notification success."
        response = self.client.post("/trainingjob/pipelineNotification".format("usecase1"),data=json.dumps(trainingjob_req),
                                    content_type="application/json")
        trainingmgr_main.LOGGER.debug(response.data)    
        assert response.status_code == status.HTTP_200_OK, "Return status code NOT equal"
        assert expected_data in str(response.data)

    db_result = [('usecase1', 'uc1', '*', 'qoe Pipeline lat v2', 'Default', '{"arguments": {"epochs": "1", "trainingjob_name": "usecase1"}}',
     '', datetime.datetime(2022, 10, 12, 10, 0, 59, 923588), '51948a12-aee9-42e5-93a0-b8f4a15bca33',
      '{"DATA_EXTRACTION": "FINISHED", "DATA_EXTRACTION_AND_TRAINING": "FINISHED", "TRAINING": "FINISHED", "TRAINING_AND_TRAINED_MODEL": "FINISHED", "TRAINED_MODEL": "FAILED"}',
       datetime.datetime(2022, 10, 12, 10, 2, 31, 888830), 1, False, '3', '{"datalake_source": {"InfluxSource": {}}}', 'No data available.', '', 'liveCell', 'UEData', False, True, "","")]
    the_response_upload=Response()
    the_response_upload.status_code=200
    @patch('trainingmgr.trainingmgr_main.MM_SDK', return_value = mocked_mm_sdk)
    @patch('trainingmgr.trainingmgr_main.TRAININGMGR_CONFIG_OBJ', return_value = mocked_TRAININGMGR_CONFIG_OBJ) 
    @patch('trainingmgr.trainingmgr_main.change_steps_state_of_latest_version')
    @patch('trainingmgr.trainingmgr_main.update_model_download_url')
    @patch('trainingmgr.trainingmgr_main.get_trainingjob_info_by_name', return_value=db_result)
    @patch('trainingmgr.trainingmgr_main.requests.post', return_value=the_response_upload)
    @patch('trainingmgr.trainingmgr_main.get_latest_version_trainingjob_name', return_value = "usecase1")
    @patch('trainingmgr.trainingmgr_main.response_for_training', return_value = response_tuple1)
    def test_pipeline_notification_mme(self,mock1, mock2, mock3, mock4, mock5, mock6, mock7, mock8):
        trainingmgr_main.LOGGER.debug("******* test_pipeline_notification post *******")
        trainingjob_req = {
                    "trainingjob_name":"usecase1",
                    "run_status":"SUCCEEDED",
                    }
        expected_data = "Pipeline notification success."
        response = self.client.post("/trainingjob/pipelineNotification".format("usecase1"),data=json.dumps(trainingjob_req),
                                    content_type="application/json")
        trainingmgr_main.LOGGER.debug(response.data)    
        assert response.status_code == status.HTTP_200_OK, "Return status code NOT equal"
        assert expected_data in str(response.data)

    db_result = [('usecase1', 'uc1', '*', 'qoe Pipeline lat v2', 'Default', '{"arguments": {"epochs": "1", "trainingjob_name": "usecase1"}}',
     '', datetime.datetime(2022, 10, 12, 10, 0, 59, 923588), '51948a12-aee9-42e5-93a0-b8f4a15bca33',
      '{"DATA_EXTRACTION": "FINISHED", "DATA_EXTRACTION_AND_TRAINING": "FINISHED", "TRAINING": "FINISHED", "TRAINING_AND_TRAINED_MODEL": "FINISHED", "TRAINED_MODEL": "FAILED"}',
       datetime.datetime(2022, 10, 12, 10, 2, 31, 888830), 1, False, '3', '{"datalake_source": {"InfluxSource": {}}}', 'No data available.', '', 'liveCell', 'UEData', False, True, "","")]
    the_response_upload=Response()
    the_response_upload.status_code=500
    @patch('trainingmgr.trainingmgr_main.MM_SDK', return_value = mocked_mm_sdk)
    @patch('trainingmgr.trainingmgr_main.TRAININGMGR_CONFIG_OBJ', return_value = mocked_TRAININGMGR_CONFIG_OBJ) 
    @patch('trainingmgr.trainingmgr_main.change_steps_state_of_latest_version')
    @patch('trainingmgr.trainingmgr_main.update_model_download_url')
    @patch('trainingmgr.trainingmgr_main.get_trainingjob_info_by_name', return_value=db_result)
    @patch('trainingmgr.trainingmgr_main.requests.post', return_value=the_response_upload)
    @patch('trainingmgr.trainingmgr_main.get_latest_version_trainingjob_name', return_value = "usecase1")
    @patch('trainingmgr.trainingmgr_main.response_for_training', return_value = response_tuple1)
    def test__negative_pipeline_notification_mme(self,mock1, mock2, mock3, mock4, mock5, mock6, mock7, mock8):
        trainingmgr_main.LOGGER.debug("******* test_pipeline_notification post *******")
        trainingjob_req = {
                    "trainingjob_name":"usecase1",
                    "run_status":"SUCCEEDED",
                    }
        try:
            response = self.client.post("/trainingjob/pipelineNotification".format("usecase1"),data=json.dumps(trainingjob_req),
                                    content_type="application/json")
        except TMException as err:
            assert "Upload to mme failed" in err.message

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
        response = self.client.get("/trainingjobs/{trainingjobname}/{version}/steps_state".format(trainingjobname="usecase1", version="1"),
                                    content_type="application/json")
        trainingmgr_main.LOGGER.debug(response.data)    
        assert response.status_code == status.HTTP_200_OK, "Return status code NOT equal"
        assert expected_data in str(response.data)

    db_result5 = []
    @patch('trainingmgr.trainingmgr_main.get_field_of_given_version', return_value = db_result5)
    def test_negative_get_steps_state_2(self,mock1):
        expected_data = "Exception"
        response = self.client.get("/trainingjobs/{trainingjobname}/{version}/steps_state".format(trainingjobname="usecase1", version="1"),
                                    content_type="application/json")
        trainingmgr_main.LOGGER.debug(response.data)    
        assert response.status_code == status.HTTP_404_NOT_FOUND, "Return status code NOT equal"
        assert expected_data in str(response.data)


class Test_get_trainingjob_by_name_version:
    def setup_method(self):
        self.client = trainingmgr_main.APP.test_client(self)
        self.logger = trainingmgr_main.LOGGER


    @pytest.fixture
    def mock_training_job(self):
        """Create a mock TrainingJob object."""
        creation_time = datetime.datetime.now()
        updation_time = datetime.datetime.now()
        return TrainingJob(
            trainingjob_name="test_job",
            description="Test description",
            feature_group_name="test_feature_group",
            pipeline_name="test_pipeline",
            experiment_name="test_experiment",
            arguments=json.dumps({"param1": "value1"}),
            query_filter="test_filter",
            creation_time=creation_time,
            run_id="test_run_id",
            steps_state=json.dumps({"step1": "completed"}),
            updation_time=updation_time,
            version=1,
            enable_versioning=True,
            pipeline_version="v1",
            datalake_source=json.dumps({"datalake_source": {"source1": "path1"}}),
            model_url="http://test.model.url",
            notification_url="http://test.notification.url",
            deletion_in_progress=False,
            is_mme=True,
            model_name="test_model",
            model_info="test_model_info"
        )

    @pytest.fixture
    def mock_metrics(self):
        """Create mock metrics data."""
        return {"accuracy": "0.95", "precision": "0.92"}
    
    def test_successful_get_trainingjob(self, mock_training_job, mock_metrics):
        """Test successful retrieval of training job."""
        with patch('trainingmgr.trainingmgr_main.get_info_by_version') as mock_get_info, \
             patch('trainingmgr.trainingmgr_main.get_metrics') as mock_get_metrics, \
             patch('trainingmgr.trainingmgr_main.check_trainingjob_name_and_version', return_value=True):

            mock_get_info.return_value = mock_training_job
            mock_get_metrics.return_value = mock_metrics

            response = self.client.get('/trainingjobs/test_job/1')
           
            assert response.status_code == status.HTTP_200_OK
            data = json.loads(response.data)
           
            assert 'trainingjob' in data
            job_data = data['trainingjob']
            assert job_data['trainingjob_name'] == "test_job"
            assert job_data['description'] == "Test description"
            assert job_data['feature_list'] == "test_feature_group"
            assert job_data['pipeline_name'] == "test_pipeline"
            assert job_data['experiment_name'] == "test_experiment"
            assert job_data['is_mme'] is True
            assert job_data['model_name'] == "test_model"
            assert job_data['model_info'] == "test_model_info"
            assert job_data['accuracy'] == mock_metrics

    def test_invalid_name_version(self):
        """Test with invalid training job name or version."""
        with patch('trainingmgr.trainingmgr_main.check_trainingjob_name_and_version', return_value=False):
            response = self.client.get('/trainingjobs/invalid_*job/999')
           
            assert response.status_code == status.HTTP_400_BAD_REQUEST
            data = json.loads(response.data)
            assert "Exception" in data
            assert "trainingjob_name or version is not correct" in data["Exception"]

    def test_nonexistent_trainingjob(self):
        """Test when training job doesn't exist in database."""
        with patch('trainingmgr.trainingmgr_main.check_trainingjob_name_and_version', return_value=True), \
             patch('trainingmgr.trainingmgr_main.get_info_by_version', return_value=None), \
             patch('trainingmgr.trainingmgr_main.get_metrics', return_value = "No data available"):
            
            response = self.client.get('/trainingjobs/nonexistent_job/1')
           
            assert response.status_code == status.HTTP_404_NOT_FOUND
            data = json.loads(response.data)
            assert "Exception" in data
            assert "Not found given trainingjob with version" in data["Exception"]

    def test_database_error(self):
        """Test handling of database errors."""
        with patch('trainingmgr.trainingmgr_main.check_trainingjob_name_and_version', return_value=True), \
             patch('trainingmgr.trainingmgr_main.get_info_by_version', side_effect=Exception("Database error")):

            response = self.client.get('/trainingjobs/test_job/1')
           
            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            data = json.loads(response.data)
            assert "Exception" in data
            assert "Database error" in data["Exception"]

    def test_metrics_error(self, mock_training_job):
        """Test handling of metrics retrieval error."""
        with patch('trainingmgr.trainingmgr_main.check_trainingjob_name_and_version', return_value=True), \
             patch('trainingmgr.trainingmgr_main.get_info_by_version', return_value=mock_training_job), \
             patch('trainingmgr.trainingmgr_main.get_metrics', side_effect=Exception("Metrics error")):

            response = self.client.get('/trainingjobs/test_job/1')
           
            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            data = json.loads(response.data)
            assert "Exception" in data
            assert "Metrics error" in data["Exception"]

    def test_datalake_source_parsing(self, mock_training_job):
        """Test correct parsing of datalake_source JSON."""
        with patch('trainingmgr.trainingmgr_main.check_trainingjob_name_and_version', return_value=True), \
             patch('trainingmgr.trainingmgr_main.get_info_by_version', return_value=mock_training_job), \
             patch('trainingmgr.trainingmgr_main.get_metrics', return_value={}), \
             patch('trainingmgr.trainingmgr_main.get_one_key', return_value="source1"):

            response = self.client.get('/trainingjobs/test_job/1')
           
            assert response.status_code == status.HTTP_200_OK
            data = json.loads(response.data)
            assert data['trainingjob']['datalake_source'] == "source1"
@pytest.mark.skip("")
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
@pytest.mark.skip("")
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
        
      def test_negative_get_steps_state_by_name_and_version(self):
        usecase_name = "usecase7*"
        version = "1"
        response = self.client.get("/trainingjobs/{}/{}/steps_state".format(usecase_name, version))
        assert response.status_code == status.HTTP_400_BAD_REQUEST, "not equal status code"
        assert response.data == b'{"Exception":"The trainingjob_name or version is not correct"}\n'
        usecase_name="usecase7"
        version="a"
        response = self.client.get("/trainingjobs/{}/{}/steps_state".format(usecase_name, version))
        assert response.status_code == status.HTTP_400_BAD_REQUEST, "not equal status code"
        assert response.data == b'{"Exception":"The trainingjob_name or version is not correct"}\n'
          
@pytest.mark.skip("")
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
                    "featureGroup_name":"group",
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
                    "bucket":"UEData",
                    "is_mme":False,
                    "model_name": ""
                    }
        expected_data = b'{"result": "Information stored in database."}'
        response = self.client.post("/trainingjobs/{}".format("usecase1"),
                                    data=json.dumps(trainingjob_req),
                                    content_type="application/json")
        trainingmgr_main.LOGGER.debug(response.data)    
        assert response.data == expected_data
        assert response.status_code == status.HTTP_201_CREATED, "Return status code NOT equal" 

    model_info_json={'model-name': 'qoe_93', 'rapp-id': 'rapp_1', 'meta-info': {'accuracy': '90', 'feature-list': ['*'], 'model-type': 'timeseries'}}
    db_result_fg=[('group','*','')]
    mocked_TRAININGMGR_CONFIG_OBJ=mock.Mock(name="TRAININGMGR_CONFIG_OBJ")
    attrs_TRAININGMGR_CONFIG_OBJ = {'pipeline.return_value':''}
    mocked_TRAININGMGR_CONFIG_OBJ.configure_mock(**attrs_TRAININGMGR_CONFIG_OBJ)
    @patch('trainingmgr.trainingmgr_main.validate_trainingjob_name', return_value = False)
    @patch('trainingmgr.trainingmgr_main.check_trainingjob_data', return_value = ("group1", 'unittest', 'qoe', 'experiment1', 'arguments1', 'query1', True, 1, 'cassandra db',True, ""))
    @patch('trainingmgr.trainingmgr_main.TRAININGMGR_CONFIG_OBJ', return_value = mocked_TRAININGMGR_CONFIG_OBJ)
    @patch('trainingmgr.trainingmgr_main.get_model_info', return_value=model_info_json)
    @patch('trainingmgr.trainingmgr_main.json.loads',return_value={'timeseries':''})
    @patch('trainingmgr.trainingmgr_main.get_feature_groups_db', return_value=db_result_fg)
    @patch('trainingmgr.trainingmgr_main.add_update_trainingjob')
    def test_trainingjob_operations2(self,mock1,mock2, mock3, mock4, mock5, mock6, mock7):
        trainingmgr_main.LOGGER.debug("******* test_trainingjob_operations post *******")
        trainingjob_req = {
                    "trainingjob_name":"usecase1",
                    "pipeline_name":"qoe Pipeline lat v2",
                    "experiment_name":"Default",
                    "featureGroup_name":"group",
                    "query_filter":"",
                    "arguments":{
                        "epochs":"1",
                        "trainingjob_name":"usecase1"
                    },
                    "enable_versioning":False,
                    "description":"uc1",
                    "pipeline_version":"3",
                    "datalake_source":"InfluxSource",
                    "is_mme":True,
                    "model_name": ""
                    }
        expected_data = b'{"result": "Information stored in database."}'
        response = self.client.post("/trainingjobs/{}".format("usecase1"),
                                    data=json.dumps(trainingjob_req),
                                    content_type="application/json")
        trainingmgr_main.LOGGER.debug(response.data)    
        assert response.data == expected_data
        assert response.status_code == status.HTTP_201_CREATED, "Return status code NOT equal" 

    model_info_json={'model-name': 'qoe_93', 'rapp-id': 'rapp_1', 'meta-info': {'accuracy': '90', 'feature-list': ['*'], 'model-type': 'timeseries'}}
    db_result_fg=[('group','*','')]
    mocked_TRAININGMGR_CONFIG_OBJ=mock.Mock(name="TRAININGMGR_CONFIG_OBJ")
    attrs_TRAININGMGR_CONFIG_OBJ = {'pipeline.return_value':''}
    mocked_TRAININGMGR_CONFIG_OBJ.configure_mock(**attrs_TRAININGMGR_CONFIG_OBJ)
    @patch('trainingmgr.trainingmgr_main.validate_trainingjob_name', return_value = False)
    @patch('trainingmgr.trainingmgr_main.check_trainingjob_data', return_value = ("group1", 'unittest', 'qoe', 'experiment1', 'arguments1', 'query1', True, 1, 'cassandra db',True, ""))
    @patch('trainingmgr.trainingmgr_main.TRAININGMGR_CONFIG_OBJ', return_value = mocked_TRAININGMGR_CONFIG_OBJ)
    @patch('trainingmgr.trainingmgr_main.get_model_info', return_value=model_info_json)
    @patch('trainingmgr.trainingmgr_main.json.loads',return_value='')
    @patch('trainingmgr.trainingmgr_main.get_feature_groups_db', return_value=db_result_fg)
    @patch('trainingmgr.trainingmgr_main.add_update_trainingjob')
    def test_negative_trainingjob_operations2(self,mock1,mock2, mock3, mock4, mock5, mock6, mock7):
        trainingmgr_main.LOGGER.debug("******* test_trainingjob_operations post *******")
        trainingjob_req = {
                    "trainingjob_name":"usecase1",
                    "pipeline_name":"qoe Pipeline lat v2",
                    "experiment_name":"Default",
                    "featureGroup_name":"group",
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
                    "bucket":"UEData",
                    "is_mme":True,
                    "model_name": ""
                    }
        expected_data = b'{"Exception": "Doesn\'t support the model type"}'
        response = self.client.post("/trainingjobs/{}".format("usecase1"),
                                    data=json.dumps(trainingjob_req),
                                    content_type="application/json")
        trainingmgr_main.LOGGER.debug(response.data)    
        assert response.data == expected_data
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR, "Return status code NOT equal" 

    model_info_json={'model-name': 'qoe_93', 'rapp-id': 'rapp_1', 'meta-info': {'accuracy': '90', 'feature-list': ['*'], 'model-type': 'timeseries'}}
    db_result_fg=[('group','abc','')]
    mocked_TRAININGMGR_CONFIG_OBJ=mock.Mock(name="TRAININGMGR_CONFIG_OBJ")
    attrs_TRAININGMGR_CONFIG_OBJ = {'pipeline.return_value':''}
    mocked_TRAININGMGR_CONFIG_OBJ.configure_mock(**attrs_TRAININGMGR_CONFIG_OBJ)
    @patch('trainingmgr.trainingmgr_main.validate_trainingjob_name', return_value = False)
    @patch('trainingmgr.trainingmgr_main.check_trainingjob_data', return_value = ("", 'unittest', '', 'experiment1', 'arguments1', 'query1', True, 1, 'cassandra db',True, ""))
    @patch('trainingmgr.trainingmgr_main.TRAININGMGR_CONFIG_OBJ', return_value = mocked_TRAININGMGR_CONFIG_OBJ)
    @patch('trainingmgr.trainingmgr_main.get_model_info', return_value=model_info_json)
    @patch('trainingmgr.trainingmgr_main.json.loads',return_value={"timeseries": "qoe_pipeline_h_release"})
    @patch('trainingmgr.trainingmgr_main.get_feature_groups_db', return_value=db_result_fg)
    @patch('trainingmgr.trainingmgr_main.add_update_trainingjob')
    def test_negative_trainingjob_operations3(self,mock1,mock2, mock3, mock4, mock5, mock6, mock7):
        trainingmgr_main.LOGGER.debug("******* test_trainingjob_operations post *******")
        trainingjob_req = {
                    "trainingjob_name":"usecase1",
                    "pipeline_name":"",
                    "experiment_name":"Default",
                    "featureGroup_name":"",
                    "query_filter":"",
                    "arguments":{
                        "epochs":"1",
                        "trainingjob_name":"usecase1"
                    },
                    "enable_versioning":False,
                    "description":"uc1",
                    "pipeline_version":"",
                    "datalake_source":"InfluxSource",
                    "_measurement":"liveCell",
                    "bucket":"UEData",
                    "is_mme":True,
                    "model_name": "qoe_121"
                    }
        expected_data = b'{"Exception":"The no feature group with mentioned feature list, create a feature group"}\n'
        response = self.client.post("/trainingjobs/{}".format("usecase1"),
                                    data=json.dumps(trainingjob_req),
                                    content_type="application/json")
        trainingmgr_main.LOGGER.debug(response.data)
        print(response.data)  
        assert response.data == expected_data
        assert response.status_code == status.HTTP_406_NOT_ACCEPTABLE, "Return status code NOT equal" 
        
    db_result = [('my_testing_new_7', 'testing', 'testing_influxdb', 'pipeline_kfp2.2.0_5', 'Default', '{"arguments": {"epochs": "1", "trainingjob_name": "my_testing_new_7"}}', '', datetime.datetime(2024, 6, 21, 8, 57, 48, 408725), '432516c9-29d2-4f90-9074-407fe8f77e4f', '{"DATA_EXTRACTION": "FINISHED", "DATA_EXTRACTION_AND_TRAINING": "FINISHED", "TRAINING": "FINISHED", "TRAINING_AND_TRAINED_MODEL": "FINISHED", "TRAINED_MODEL": "FINISHED"}', datetime.datetime(2024, 6, 21, 9, 1, 54, 388278), 1, False, 'pipeline_kfp2.2.0_5', '{"datalake_source": {"InfluxSource": {}}}', 'http://10.0.0.10:32002/model/my_testing_new_7/1/Model.zip', '', False, False, '', '')]

    
    training_data = ('','','','','','','','','',False,'')
    @patch('trainingmgr.trainingmgr_main.validate_trainingjob_name', return_value = True)
    @patch('trainingmgr.trainingmgr_main.get_trainingjob_info_by_name', return_value = db_result)
    @patch('trainingmgr.trainingmgr_main.check_trainingjob_data', return_value = training_data)
    @patch('trainingmgr.trainingmgr_main.add_update_trainingjob')
    def test_trainingjob_operations_put(self,mock1,mock2,mock3,mock4):
        trainingmgr_main.LOGGER.debug("******* test_trainingjob_operations_put *******")
        trainingjob_req = {
                "trainingjob_name": "my_testing_new_7",
                "is_mme": False,
                "model_name": False,
                "pipeline_name": "pipeline",
                "experiment_name": "Default",
                "featureGroup_name": "testing",
                "query_filter": "",
                "arguments": {
                    "epochs": "1",
                    "trainingjob_name": "my_testing"
                },
                "enable_versioning": False,
                "description": "testing",
                "pipeline_version": "pipeline",
                "datalake_source": "InfluxSource"
            }
            
        expected_data = 'Information updated in database'
        response = self.client.put("/trainingjobs/{}".format("my_testing_new_7"),
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
                    "featureGroup_name":"group",
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
        response = self.client.post("/trainingjobs/{}".format("usecase1"),
                                    data=json.dumps(trainingjob_req),
                                    content_type="application/json")
        trainingmgr_main.LOGGER.debug(response.data)           
        assert response.status_code == status.HTTP_409_CONFLICT, "Return status code NOT equal"
        assert expected_data in str(response.data)


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
    db_result2=[('testing_hash', '', 'InfluxSource', '127.0.0.21', '8080', '', '', '', False, '', '', '')]

    @patch('trainingmgr.trainingmgr_main.validate_trainingjob_name', return_value = True)
    @patch('trainingmgr.trainingmgr_main.get_trainingjob_info_by_name', return_value = db_result)
    @patch('trainingmgr.trainingmgr_main.get_feature_group_by_name_db', return_value = db_result2)
    @patch('trainingmgr.trainingmgr_main.data_extraction_start', return_value = de_response)
    @patch('trainingmgr.trainingmgr_main.change_steps_state_of_latest_version')
    def test_training(self,mock1,mock2,mock3,mock4, mock5):
        trainingmgr_main.LOGGER.debug("******* test_trainingjob_operations post *******")
        expected_data = 'Data Pipeline Execution Completed"'
        response = self.client.post("/trainingjobs/{}/training".format("usecase1"),
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
    @patch('trainingmgr.trainingmgr_main.get_feature_group_by_name_db', return_value = db_result2)
    @patch('trainingmgr.trainingmgr_main.data_extraction_start', return_value = de_response1)
    @patch('trainingmgr.trainingmgr_main.change_steps_state_of_latest_version')
    def test_training_negative_de_failed(self,mock1,mock2,mock3,mock4, mock5):
        trainingmgr_main.LOGGER.debug("******* test_trainingjob_operations post *******")
        expected_data = 'Data Pipeline Execution Failed'
        response = self.client.post("/trainingjobs/{}/training".format("usecase1"),
                                    content_type="application/json")
        trainingmgr_main.LOGGER.debug(response.data)
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR, "Return status code NOT equal" 
        assert expected_data in str(response.data) 
    
    def test_negative_training_by_trainingjob_name(self):
        trainingjob_name="usecase*"
        response=self.client.post('/trainingjobs/{}'.format(trainingjob_name), content_type="application/json")
        assert response.status_code==status.HTTP_400_BAD_REQUEST
        assert response.data == b'{"Exception":"The trainingjob_name is not correct"}\n'
        response=self.client.post('/trainingjobs/{}/training'.format(trainingjob_name), content_type="application/json")
        assert response.status_code==status.HTTP_400_BAD_REQUEST
        assert response.data == b'{"Exception":"The trainingjob_name is not correct"}\n'


@pytest.mark.skip("")
class Test_get_versions_for_pipeline:
    @patch('trainingmgr.common.trainingmgr_config.TMLogger', return_value = TMLogger("tests/common/conf_log.yaml"))
    def setup_method(self,mock1,mock2):
        self.client = trainingmgr_main.APP.test_client(self)
        self.logger = trainingmgr_main.LOGGER
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
    @patch('trainingmgr.trainingmgr_main.get_pipelines_details', return_value=
            {"next_page_token":"next-page-token","pipelines":[{"created_at":"created-at","description":"pipeline-description","display_name":"pipeline-name","pipeline_id":"pipeline-id"}],"total_size":"total-size"}
	)
    def test_get_versions_for_pipeline_positive(self,mock1,mock2, mock3):
        response = self.client.get("/pipelines/{}/versions".format("pipeline-name"))
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
    
@pytest.mark.skip("")
class Test_get_pipelines_details:
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
    def test_get_pipelines_details(self,mock1):
        response = self.client.get("/pipelines")      
        assert response.content_type == "application/json", "not equal content type"
        assert response.status_code == 500, "Return status code NOT equal"   
        
    @patch('trainingmgr.trainingmgr_main.requests.get', side_effect = requests.exceptions.ConnectionError('Mocked error'))
    def test_negative_get_pipelines_details_1(self,mock1):
        response = self.client.get("/pipelines")       
        print(response.data)
        assert response.content_type == "application/json", "not equal content type"
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR, "Should have thrown the exception "
        
    @patch('trainingmgr.trainingmgr_main.requests.get', side_effect = TypeError('Mocked error'))
    def test_negative_get_pipelines_details_2(self,mock1):
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
    def test_negative_get_pipelines_details_3(self,mock1):
        response = self.client.get("/pipelines")       
        print(response.data)
        assert response.content_type != "application/text", "not equal content type"

@pytest.mark.skip("")
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
        assert response.status_code == 500, "Return status code NOT equal"   
        
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

@pytest.mark.skip("")
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

    def test_negative_get_metadata_by_name(self):
        trainingjob_name="usecase*"
        response=self.client.get('/trainingjobs/metadata/{}'.format(trainingjob_name), content_type="application/json")
        print(response.data)
        assert response.status_code==status.HTTP_400_BAD_REQUEST
        assert response.data == b'{"Exception":"The trainingjob_name is not correct"}\n'

@pytest.mark.skip("")
class Test_get_model:
        def setup_method(self):
            self.client = trainingmgr_main.APP.test_client(self)
            trainingmgr_main.LOGGER = TMLogger("tests/common/conf_log.yaml").logger
            self.logger = trainingmgr_main.LOGGER
    
        @patch('trainingmgr.trainingmgr_main.send_file', return_value = 'File')
        def test_negative_get_model(self,mock1):
            trainingjob_name = "usecase777"
            version = "2"
            result = 'File'
            response = trainingmgr_main.get_model(trainingjob_name,version)
            assert response[1] == 500, "The function get_model Failed" 
    
        def test_negative_get_model_by_name_or_version(self):
            usecase_name = "usecase7*"
            version = "1"
            response = self.client.get("/model/{}/{}/Model.zip".format(usecase_name, version))
            assert response.status_code == status.HTTP_400_BAD_REQUEST, "not equal status code"
            assert response.data == b'{"Exception":"The trainingjob_name or version is not correct"}\n'
            usecase_name="usecase7"
            version="a"
            response = self.client.get("/model/{}/{}/Model.zip".format(usecase_name, version))
            assert response.status_code == status.HTTP_400_BAD_REQUEST, "not equal status code"
            assert response.data == b'{"Exception":"The trainingjob_name or version is not correct"}\n'


@pytest.mark.skip("")
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
        response = self.client.post("/trainingjobs/{}/training".format("usecase1"),
                                    content_type="application/json")
        trainingmgr_main.LOGGER.debug(response.data)
        assert response.status_code == status.HTTP_404_NOT_FOUND, "Return status code NOT equal"

## Retraining API test
@pytest.mark.skip("")
class Test_retraining:
    @patch('trainingmgr.common.trainingmgr_config.TMLogger', return_value = TMLogger("tests/common/conf_log.yaml"))
    def setup_method(self,mock1,mock2):
        self.client = trainingmgr_main.APP.test_client(self)
        self.logger = trainingmgr_main.LOGGER
        
    #test_positive_1
    db_result = [('my_testing_new_7', 'testing', 'testing_influxdb', 'pipeline_kfp2.2.0_5', 'Default', '{"arguments": {"epochs": "1", "trainingjob_name": "my_testing_new_7"}}', '', datetime.datetime(2024, 6, 21, 8, 57, 48, 408725), '432516c9-29d2-4f90-9074-407fe8f77e4f', '{"DATA_EXTRACTION": "FINISHED", "DATA_EXTRACTION_AND_TRAINING": "FINISHED", "TRAINING": "FINISHED", "TRAINING_AND_TRAINED_MODEL": "FINISHED", "TRAINED_MODEL": "FINISHED"}', datetime.datetime(2024, 6, 21, 9, 1, 54, 388278), 1, False, 'pipeline_kfp2.2.0_5', '{"datalake_source": {"InfluxSource": {}}}', 'http://10.0.0.10:32002/model/my_testing_new_7/1/Model.zip', '', False, False, '', '')]
    mocked_TRAININGMGR_CONFIG_OBJ=mock.Mock(name="TRAININGMGR_CONFIG_OBJ")
    attrs_TRAININGMGR_CONFIG_OBJ = {'my_ip.return_value': '123'}
    mocked_TRAININGMGR_CONFIG_OBJ.configure_mock(**attrs_TRAININGMGR_CONFIG_OBJ)
    #postive_1
    tmres = Response()
    tmres.code = "expired"
    tmres.error_type = "expired"
    tmres.status_code = status.HTTP_200_OK
    tmres.headers={"content-type": "application/json"}
    tmres._content = b'{"task_status": "Completed", "result": "Data Pipeline Execution Completed"}'  
    @patch('trainingmgr.trainingmgr_main.check_key_in_dictionary',return_value=True) 
    @patch('trainingmgr.trainingmgr_main.get_info_of_latest_version', return_value= db_result)
    @patch('trainingmgr.trainingmgr_main.TRAININGMGR_CONFIG_OBJ', return_value = mocked_TRAININGMGR_CONFIG_OBJ)
    @patch('trainingmgr.trainingmgr_main.add_update_trainingjob',return_value="")
    @patch('trainingmgr.trainingmgr_main.get_one_word_status',return_value = States.FINISHED.name)
    @patch('trainingmgr.trainingmgr_main.requests.post',return_value = tmres)
    def test_retraining(self,mock1, mock2, mock3,mock4, mock5, mock6):
        retrain_req = {"trainingjobs_list": [{"trainingjob_name": "mynetwork"}]}
        response = self.client.post("/trainingjobs/retraining", data=json.dumps(retrain_req),content_type="application/json")   
        data=json.loads(response.data)
        assert response.status_code == status.HTTP_200_OK, "Return status code NOT equal"
        assert data["success count"]==1 , "Return success count NOT equal"

    #Negative_1
    @patch('trainingmgr.trainingmgr_main.check_key_in_dictionary',side_effect = Exception('Mocked error'))
    def test_negative_retraining_1(self,mock1):
        retrain_req = {"trainingjobs_list": [{"trainingjob_name": "mynetwork"}]}
        response = self.client.post("/trainingjobs/retraining", data=json.dumps(retrain_req),content_type="application/json")   
        assert response.status_code == status.HTTP_400_BAD_REQUEST, "Return status code NOT equal"  


    #Negative_2
    @patch('trainingmgr.trainingmgr_main.check_key_in_dictionary')
    @patch('trainingmgr.trainingmgr_main.get_info_of_latest_version', side_effect = Exception('Mocked error'))
    def test_negative_retraining_2(self,mock1,mock2):
        retrain_req = {"trainingjobs_list": [{"trainingjob_name": "mynetwork"}]}
        response = self.client.post("/trainingjobs/retraining", data=json.dumps(retrain_req),content_type="application/json")   
        data = json.loads(response.data)
        assert response.status_code == status.HTTP_200_OK, "Return status code NOT equal"
        assert data["failure count"] == 1, "Return failure count NOT equal"
        

    #Negative_3_when_deletion_in_progress
    db_result2 = [('mynetwork', 'testing', '*', 'testing_pipeline', 'Default', '{"arguments": {"epochs": "1", "trainingjob_name": "mynetwork"}}', '', datetime.datetime(2023, 2, 9, 9, 2, 11, 13916), 'No data available', '{"DATA_EXTRACTION": "FINISHED", "DATA_EXTRACTION_AND_TRAINING": "IN_PROGRESS", "TRAINING": "NOT_STARTED", "TRAINING_AND_TRAINED_MODEL": "NOT_STARTED", "TRAINED_MODEL": "NOT_STARTED"}', datetime.datetime(2023, 2, 9, 9, 2, 11, 13916), 1, False, '2', '{"datalake_source": {"InfluxSource": {}}}', 'No data available.', '', 'liveCell', 'UEData', True)]
  
    @patch('trainingmgr.trainingmgr_main.check_key_in_dictionary') 
    @patch('trainingmgr.trainingmgr_main.get_info_of_latest_version', return_value= db_result2)
    def test_negative_retraining_3(self,mock1, mock2):
        retrain_req = {"trainingjobs_list": [{"trainingjob_name": "mynetwork"}]}
        response = self.client.post("/trainingjobs/retraining", data=json.dumps(retrain_req),content_type="application/json")   
        data=json.loads(response.data)
        assert response.status_code == status.HTTP_200_OK, "Return status code NOT equal"
        assert data["failure count"]==1, "Return failure count NOT equal"


    #Negative_4
    db_result = [('mynetwork', 'testing', '*', 'testing_pipeline', 'Default', '{"arguments": {"epochs": "1", "trainingjob_name": "mynetwork"}}', '', datetime.datetime(2023, 2, 9, 9, 2, 11, 13916), 'No data available', '{"DATA_EXTRACTION": "FINISHED", "DATA_EXTRACTION_AND_TRAINING": "IN_PROGRESS", "TRAINING": "NOT_STARTED", "TRAINING_AND_TRAINED_MODEL": "NOT_STARTED", "TRAINED_MODEL": "NOT_STARTED"}', datetime.datetime(2023, 2, 9, 9, 2, 11, 13916), 1, False, '2', '{"datalake_source": {"InfluxSource": {}}}', 'No data available.', '', 'liveCell', 'UEData', False)]
      
    @patch('trainingmgr.trainingmgr_main.check_key_in_dictionary',return_value="") 
    @patch('trainingmgr.trainingmgr_main.get_info_of_latest_version', return_value= db_result)
    @patch('trainingmgr.trainingmgr_main.add_update_trainingjob',side_effect = Exception('Mocked error'))
    def test_negative_retraining_4(self,mock1, mock2, mock3):
        retrain_req = {"trainingjobs_list": [{"trainingjob_name": "mynetwork"}]}
        response = self.client.post("/trainingjobs/retraining", data=json.dumps(retrain_req),content_type="application/json")   
        data=json.loads(response.data)
        assert response.status_code == status.HTTP_200_OK, "Return status code NOT equal"
        assert data["failure count"]==1, "Return failure count NOT equal"


    #Negative_5
    db_result = [('mynetwork', 'testing', '*', 'testing_pipeline', 'Default', '{"arguments": {"epochs": "1", "trainingjob_name": "mynetwork"}}', '', datetime.datetime(2023, 2, 9, 9, 2, 11, 13916), 'No data available', '{"DATA_EXTRACTION": "FINISHED", "DATA_EXTRACTION_AND_TRAINING": "IN_PROGRESS", "TRAINING": "NOT_STARTED", "TRAINING_AND_TRAINED_MODEL": "NOT_STARTED", "TRAINED_MODEL": "NOT_STARTED"}', datetime.datetime(2023, 2, 9, 9, 2, 11, 13916), 1, False, '2', '{"datalake_source": {"InfluxSource": {}}}', 'No data available.', '', 'liveCell', 'UEData', False)]
    

    tmres = Response()
    tmres.code = "expired"
    tmres.error_type = "expired"
    tmres.status_code = status.HTTP_204_NO_CONTENT
    tmres.headers={"content-type": "application/json"}
    tmres._content = b'{"task_status": "Completed", "result": "Data Pipeline Execution Completed"}'  
    @patch('trainingmgr.trainingmgr_main.check_key_in_dictionary',return_value="") 
    @patch('trainingmgr.trainingmgr_main.get_info_of_latest_version', return_value= db_result)
    @patch('trainingmgr.trainingmgr_main.add_update_trainingjob',return_value="")
    @patch('trainingmgr.trainingmgr_main.requests.post',return_value = tmres)
    def test_negative_retraining_5(self,mock1, mock2, mock3,mock4):
        retrain_req = {"trainingjobs_list": [{"trainingjob_name": "mynetwork"}]}
        response = self.client.post("/trainingjobs/retraining", data=json.dumps(retrain_req),content_type="application/json")   
        data=json.loads(response.data)
        assert response.status_code == status.HTTP_200_OK, "Return status code NOT equal" 
        assert data["failure count"]==1, "Return failure count NOT equal"

      
    #Negative_6
    db_result3 = [] 
    @patch('trainingmgr.trainingmgr_main.check_key_in_dictionary') 
    @patch('trainingmgr.trainingmgr_main.get_info_of_latest_version', return_value= db_result3)
    def test_negative_retraining_6(self,mock1, mock2):
        retrain_req = {"trainingjobs_list": [{"trainingjob_name": "mynetwork"}]}
        response = self.client.post("/trainingjobs/retraining", data=json.dumps(retrain_req),content_type="application/json")   
        data=json.loads(response.data)
        assert response.status_code == status.HTTP_200_OK, "Return status code NOT equal"
        assert data["failure count"]==1, "Return failure count NOT equal"


@pytest.mark.skip("")
class Test_create_featuregroup:
    def setup_method(self):
        self.client = trainingmgr_main.APP.test_client(self)
        self.logger = trainingmgr_main.LOGGER
    
    feature_group_data2=('testing_hash','pdcpBytesDl,pdcpBytesUl','InfluxSource',False,'','','','','','', '','', '')
    @patch('trainingmgr.trainingmgr_main.check_feature_group_data', return_value=feature_group_data2)
    @patch('trainingmgr.trainingmgr_main.get_feature_group_by_name_db', return_value=False)
    @patch('trainingmgr.trainingmgr_main.add_featuregroup')
    def test_create_featuregroup_1(self, mock1, mock2, mock3):
        create_featuregroup_req={"featureGroupName":"testing_hash",
                                 "feature_list":"pdcpBytesDl,pdcpBytesUl",
                                 "datalake_source":"InfluxSource",
                                 "enable_Dme":False,
                                 "Host":"",
                                 "Port":"",
                                 "dmePort":"",
                                 "bucket":"",
                                 "_measurement":"",
                                 "token":"",
                                 "source_name":"",
                                 "measured_obj_class":"",
                                 "dbOrg":""}
        expected_response=b'{"result": "Feature Group Created"}'
        response=self.client.post("/featureGroup", data=json.dumps(create_featuregroup_req),
                                  content_type="application/json")
        trainingmgr_main.LOGGER.debug(response.data)
        assert response.data==expected_response
        assert response.status_code ==status.HTTP_200_OK, "Return status code not equal"  
    
    the_response1 = Response()
    the_response1.status_code = status.HTTP_201_CREATED
    the_response1.headers={"content-type": "application/json"}
    the_response1._content = b''
    mocked_TRAININGMGR_CONFIG_OBJ=mock.Mock(name="TRAININGMGR_CONFIG_OBJ")
    feature_group_data2=('testing_hash','pdcpBytesDl,pdcpBytesUl','InfluxSource',True,'127.0.0.1','31823','pm-bucket','','','','','','')
    @patch('trainingmgr.trainingmgr_main.check_feature_group_data', return_value=feature_group_data2)
    @patch('trainingmgr.trainingmgr_main.get_feature_group_by_name_db', return_value=False)
    @patch('trainingmgr.trainingmgr_main.add_featuregroup')
    @patch('trainingmgr.trainingmgr_main.create_dme_filtered_data_job', return_value=the_response1)
    @patch('trainingmgr.trainingmgr_main.TRAININGMGR_CONFIG_OBJ', return_value = mocked_TRAININGMGR_CONFIG_OBJ)
    @patch('trainingmgr.trainingmgr_main.delete_feature_group_by_name')
    def test_create_featuregroup_2(self, mock1, mock2, mock3, mock4, mock5, mock6):
        create_featuregroup_req={
                            "featureGroupName": "testing_hash",
                            "feature_list": "pdcpBytesDl,pdcpBytesUl",
                            "datalake_source": "InfluxSource",
                            "enable_Dme": True,
                            "host": "",
                            "port": "",
                            "bucket": "",
                            "_measurement":"",
                            "dmePort":"",
                            "token": "",
                            "source_name": "",
                            "measured_obj_class":"",
                            "dbOrg": ""
                                }
        expected_response=b'{"result": "Feature Group Created"}'
        response=self.client.post("/featureGroup", data=json.dumps(create_featuregroup_req),
                                  content_type="application/json")
        trainingmgr_main.LOGGER.debug(response.data)
        assert response.data==expected_response
        assert response.status_code ==status.HTTP_200_OK, "Return status code not equal"

    the_response2= Response()
    the_response2.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    the_response2.headers={"content-type": "application/json"}
    the_response2._content = b''
    mocked_TRAININGMGR_CONFIG_OBJ=mock.Mock(name="TRAININGMGR_CONFIG_OBJ")
    feature_group_data3=('testing_hash','pdcpBytesDl,pdcpBytesUl','InfluxSource',True,'127.0.0.1','31823','pm-bucket','','','','','','')
    @patch('trainingmgr.trainingmgr_main.check_feature_group_data', return_value=feature_group_data3)
    @patch('trainingmgr.trainingmgr_main.get_feature_group_by_name_db', return_value=False)
    @patch('trainingmgr.trainingmgr_main.add_featuregroup')
    @patch('trainingmgr.trainingmgr_main.create_dme_filtered_data_job', return_value=the_response2)
    @patch('trainingmgr.trainingmgr_main.TRAININGMGR_CONFIG_OBJ', return_value = mocked_TRAININGMGR_CONFIG_OBJ)
    @patch('trainingmgr.trainingmgr_main.delete_feature_group_by_name')
    def test_negative_create_featuregroup_1(self, mock1, mock2, mock3, mock4, mock5, mock6):
        create_featuregroup_req={
                            "featureGroupName": "testing_hash",
                            "feature_list": "pdcpBytesDl,pdcpBytesUl",
                            "datalake_source": "InfluxSource",
                            "enable_Dme": True,
                            "host": "",
                            "port": "",
                            "bucket": "",
                            "_measurement":"",
                            "dmePort":"",
                            "token": "",
                            "source_name": "",
                            "measured_obj_class":"",
                            "dbOrg": ""
                                }
        expected_response=b'{"Exception": "Cannot create dme job"}'
        response=self.client.post("/featureGroup", data=json.dumps(create_featuregroup_req),
                                  content_type="application/json")
        trainingmgr_main.LOGGER.debug(response.data)
        assert response.data==expected_response
        assert response.status_code ==status.HTTP_400_BAD_REQUEST, "Return status code not equal"


    feature_group_data3=('testing_hash','pdcpBytesDl,pdcpBytesUl','InfluxSource',True,'127.0.0.1','31823','pm-bucket','','','','','','')
    @patch('trainingmgr.trainingmgr_main.check_feature_group_data', return_value=feature_group_data3)
    @patch('trainingmgr.trainingmgr_main.get_feature_group_by_name_db', return_value=False)
    @patch('trainingmgr.trainingmgr_main.add_featuregroup',side_effect = Exception('Mocked error'))
    @patch('trainingmgr.trainingmgr_main.delete_feature_group_by_name')
    def test_neagtive_create_featuregroup_2(self, mock1, mock2, mock3, mock4):
        create_featuregroup_req={
                            "featureGroupName": "testing_hash",
                            "feature_list": "pdcpBytesDl,pdcpBytesUl",
                            "datalake_source": "InfluxSource",
                            "enable_Dme": False,
                            "host": "",
                            "port": "",
                            "bucket": "",
                            "_measurement":"",
                            "dmePort":"",
                            "token": "",
                            "source_name": "",
                            "measured_obj_class":"",
                            "dbOrg": ""
                                }
        expected_response=b'{"Exception": "Failed to create the feature Group "}'
        response=self.client.post("/featureGroup", data=json.dumps(create_featuregroup_req),
                                  content_type="application/json")
        trainingmgr_main.LOGGER.debug(response.data)
        assert response.data==expected_response
        assert response.status_code ==status.HTTP_500_INTERNAL_SERVER_ERROR, "Return status code not equal"  

    feature_group_data3=('testing_hash!@','pdcpBytesDl,pdcpBytesUl','InfluxSource',True,'127.0.0.1','31823','pm-bucket','','','','','','')
    @patch('trainingmgr.trainingmgr_main.check_feature_group_data', return_value=feature_group_data3)
    @patch('trainingmgr.trainingmgr_main.get_feature_group_by_name_db', return_value=True)
    def test_neagtive_create_featuregroup_3(self, mock1, mock2):
        create_featuregroup_req={
                            "featureGroupName": "testing_hash!@",
                            "feature_list": "pdcpBytesDl,pdcpBytesUl",
                            "datalake_source": "InfluxSource",
                            "enable_Dme": False,
                            "host": "",
                            "port": "",
                            "bucket": "",
                            "dmePort":"",
                            "_measurement":"",
                            "token": "",
                            "source_name": "",
                            "measured_obj_class":"",
                            "dbOrg": ""
                                }
        expected_response=b'{"Exception": "Failed to create the feature group since feature group not valid or already present"}'
        response=self.client.post("/featureGroup", data=json.dumps(create_featuregroup_req),
                                  content_type="application/json")
        trainingmgr_main.LOGGER.debug(response.data)
        assert response.data==expected_response
        assert response.status_code==status.HTTP_400_BAD_REQUEST, "Return status code not equal"


@pytest.mark.skip("")
class Test_get_feature_group:
    def setup_method(self):
        self.client = trainingmgr_main.APP.test_client(self)
        self.logger = trainingmgr_main.LOGGER

    result=[('testing', '', 'InfluxSource', '', '', '', '', '', '',True, '', '', '')]
    @patch('trainingmgr.trainingmgr_main.get_feature_groups_db', return_value=result)
    def test_get_feature_group(self,mock1):
        expected_data=b'{"featuregroups": [{"featuregroup_name": "testing", "features": "", "datalake": "InfluxSource", "dme": true}]}'
        response=self.client.get('/featureGroup')
        assert response.status_code==200, "status code returned is not equal"
        assert response.data==expected_data

    @patch('trainingmgr.trainingmgr_main.get_feature_groups_db', side_effect=DBException('Failed to execute query in get_feature_groupsDB ERROR'))
    def test_negative_get_feature_group(self, mock1):
        expected_data=b'{"Exception": "Failed to execute query in get_feature_groupsDB ERROR"}'
        response=self.client.get('/featureGroup')
        assert response.status_code== status.HTTP_500_INTERNAL_SERVER_ERROR, "status code is not equal"
        assert response.data == expected_data

@pytest.mark.skip("")
class Test_feature_group_by_name:
    def setup_method(self):
        self.client = trainingmgr_main.APP.test_client(self)
        self.logger = trainingmgr_main.LOGGER

    # Test Code for GET endpoint (In the case where dme is disabled)
    fg_target = [('testing', '', 'InfluxSource', '127.0.0.21', '8080', '', '', '', '', False, '', '', '')]

    @patch('trainingmgr.common.trainingmgr_util.get_feature_group_by_name_db', return_value=fg_target)
    def test_feature_group_by_name_get_api(self, mock1):
        expected_data = b'{}\n'
        fg_name = 'testing'
        response = self.client.get('/featureGroup/{}'.format(fg_name))
        assert response.status_code == 200, "status code is not equal"
        assert response.data == expected_data, response.data
    
    @patch('trainingmgr.common.trainingmgr_util.get_feature_group_by_name_db', return_value=None)
    def test_negative_feature_group_by_name_get_api_1(self, mock1):
        expected_data=b'{"error":"featuregroup with name \'testing\' not found"}\n'
        fg_name='testing'
        response=self.client.get('/featureGroup/{}'.format(fg_name))
        assert response.status_code == 404 , "status code is not equal"
        assert response.data == expected_data, response.data
    
    @patch('trainingmgr.common.trainingmgr_util.get_feature_group_by_name_db', side_effect=DBException("Failed to execute query in get_feature_groupsDB ERROR"))
    def test_negative_feature_group_by_name_get_api_2(self, mock1):
        expected_data=b'{"Exception":"Failed to execute query in get_feature_groupsDB ERROR"}\n'
        fg_name='testing'
        response=self.client.get('/featureGroup/{}'.format(fg_name))
        assert response.status_code == 500 , "status code is not equal"
        assert response.data == expected_data, response.data
    
    def test_negative_feature_group_by_name_get_api_with_incorrect_name(self):
        expected_data=b'{"Exception":"The featuregroup_name is not correct"}\n'
        fg_name="usecase*"
        response=self.client.get('/featureGroup/{}'.format(fg_name))
        assert response.status_code == 400, "status code is not equal"
        assert response.data == expected_data, response.data


    # Test Code for PUT endpoint (In the case where DME is edited from disabled to enabled)    
    fg_init = [('testing', '', 'InfluxSource', '127.0.0.21', '8080', '', '', '', '', False, '', '', '')]
    fg_edit = [('testing', 'testing', 'InfluxSource', '127.0.0.21', '8080', 'testing', '', '', '', True, '', '31823', '')]

    the_response= Response()
    the_response.status_code = status.HTTP_201_CREATED
    the_response.headers={"content-type": "application/json"}
    the_response._content = b''
    mocked_TRAININGMGR_CONFIG_OBJ=mock.Mock(name="TRAININGMGR_CONFIG_OBJ")
    feature_group_data1=('testing','testing','InfluxSource',True,'127.0.0.1', '8080', '31823','testing','','','','','')
    @patch('trainingmgr.common.trainingmgr_util.create_dme_filtered_data_job', return_value=the_response)
    @patch('trainingmgr.trainingmgr_main.TRAININGMGR_CONFIG_OBJ', return_value = mocked_TRAININGMGR_CONFIG_OBJ)
    @patch('trainingmgr.common.trainingmgr_util.edit_featuregroup')
    @patch('trainingmgr.common.trainingmgr_util.check_feature_group_data', return_value=feature_group_data1)
    @patch('trainingmgr.common.trainingmgr_util.get_feature_group_by_name_db', return_value=fg_init)
    @patch('trainingmgr.common.trainingmgr_util.delete_feature_group_by_name')
    def test_feature_group_by_name_put_api(self, mock1, mock2, mock3, mock4, mock5, mock6):
        expected_data = b'{"result": "Feature Group Edited"}'
        fg_name='testing'
        featuregroup_req = {
                "featureGroupName": fg_name,
                "feature_list": self.fg_edit[0][1],
                "datalake_source": self.fg_edit[0][2],
                "Host": self.fg_edit[0][3],
                "Port": self.fg_edit[0][4],
                "bucket": self.fg_edit[0][5],
                "token": self.fg_edit[0][6],
                "dbOrg": self.fg_edit[0][7],
                "_measurement": self.fg_edit[0][8],
                "enable_Dme": self.fg_edit[0][9],
                "measured_obj_class": self.fg_edit[0][10],
                "dmePort": self.fg_edit[0][11],
                "source_name": self.fg_edit[0][12]
            }
        response = self.client.put("/featureGroup/{}".format(fg_name),
                                    data=json.dumps(featuregroup_req),
                                    content_type="application/json")
        assert response.status_code == 200, "status code is not equal"
        assert response.data == expected_data, response.data

    the_response1= Response()
    the_response1.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    the_response1.headers={"content-type": "application/json"}
    the_response1._content = b''
    mocked_TRAININGMGR_CONFIG_OBJ=mock.Mock(name="TRAININGMGR_CONFIG_OBJ")
    feature_group_data2=('testing','testing','InfluxSource',True,'127.0.0.1', '8080', '31823','testing','','','','','')
    @patch('trainingmgr.common.trainingmgr_util.create_dme_filtered_data_job', return_value=the_response1)
    @patch('trainingmgr.trainingmgr_main.TRAININGMGR_CONFIG_OBJ', return_value = mocked_TRAININGMGR_CONFIG_OBJ)
    @patch('trainingmgr.common.trainingmgr_util.edit_featuregroup')
    @patch('trainingmgr.common.trainingmgr_util.check_feature_group_data', return_value=feature_group_data2)
    @patch('trainingmgr.common.trainingmgr_util.get_feature_group_by_name_db', return_value=fg_init)
    @patch('trainingmgr.common.trainingmgr_util.delete_feature_group_by_name')
    def test_negative_feature_group_by_name_put_api_1(self, mock1, mock2, mock3, mock4, mock5, mock6):
        expected_data = b'{"Exception": "Cannot create dme job"}'
        fg_name='testing'
        featuregroup_req = {
                "featureGroupName": fg_name,
                "feature_list": self.fg_edit[0][1],
                "datalake_source": self.fg_edit[0][2],
                "Host": self.fg_edit[0][3],
                "Port": self.fg_edit[0][4],
                "bucket": self.fg_edit[0][5],
                "token": self.fg_edit[0][6],
                "dbOrg": self.fg_edit[0][7],
                "_measurement": self.fg_edit[0][8],
                "enable_Dme": self.fg_edit[0][9],
                "measured_obj_class": self.fg_edit[0][10],
                "dmePort": self.fg_edit[0][11],
                "source_name": self.fg_edit[0][12]
            }
        response = self.client.put("/featureGroup/{}".format(fg_name),
                                    data=json.dumps(featuregroup_req),
                                    content_type="application/json")
        assert response.status_code == 400, "status code is not equal"
        assert response.data == expected_data, response.data

    the_response2= Response()
    the_response2.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    the_response2.headers={"content-type": "application/json"}
    the_response2._content = b''
    mocked_TRAININGMGR_CONFIG_OBJ=mock.Mock(name="TRAININGMGR_CONFIG_OBJ")
    feature_group_data2=('testing','testing','InfluxSource',True,'127.0.0.1', '8080', '31823','testing','','','','','')
    @patch('trainingmgr.common.trainingmgr_util.create_dme_filtered_data_job', return_value=the_response2)
    @patch('trainingmgr.trainingmgr_main.TRAININGMGR_CONFIG_OBJ', return_value = mocked_TRAININGMGR_CONFIG_OBJ)
    @patch('trainingmgr.common.trainingmgr_util.edit_featuregroup')
    @patch('trainingmgr.common.trainingmgr_util.check_feature_group_data', return_value=feature_group_data2)
    @patch('trainingmgr.common.trainingmgr_util.get_feature_group_by_name_db', return_value=fg_init)
    @patch('trainingmgr.common.trainingmgr_util.delete_feature_group_by_name')
    def test_negative_feature_group_by_name_put_api_2(self, mock1, mock2, mock3, mock4, mock5, mock6):
        expected_data= b'{"Exception": "Failed to edit the feature Group "}'
        fg_name='testing'
        featuregroup_req = {
                "featureGroupName": fg_name,
                "feature_list": self.fg_edit[0][1],
                "datalake_source": self.fg_edit[0][2],
                "Host": self.fg_edit[0][3],
                "Port": self.fg_edit[0][4],
                "bucket": self.fg_edit[0][5],
                "token": self.fg_edit[0][6],
                "dbOrg": self.fg_edit[0][7],
                "_measurement": self.fg_edit[0][8],
                "enable_Dme": self.fg_edit[0][9],
                "measured_obj_class": self.fg_edit[0][10],
                "dmePort": self.fg_edit[0][11],
                "source_name": self.fg_edit[0][12]
            }
        mock1.side_effect = [DBException("Failed to execute query in delete_feature_groupDB ERROR"), None]
        response = self.client.put("/featureGroup/{}".format(fg_name),
                                    data=json.dumps(featuregroup_req),
                                    content_type="application/json")
        assert response.data == expected_data, response.data
        assert response.status_code == 200, "status code is not equal"

    def test_negative_feature_group_by_name_put_api_with_incorrect_name(self):
        expected_data=b'{"Exception": "The featuregroup_name is not correct"}'
        fg_name="usecase*"
        response=self.client.get('/featureGroup/{}'.format(fg_name))
        assert response.status_code == 400, "status code is not equal"
        assert response.data == expected_data, response.data

    # TODO: Test Code for PUT endpoint (In the case where DME is edited from enabled to disabled)
   
        
@pytest.mark.skip("")
class Test_delete_list_of_feature_group:
    @patch('trainingmgr.common.trainingmgr_config.TMLogger', return_value = TMLogger("tests/common/conf_log.yaml"))
    def setup_method(self,mock1,mock2):
        self.client = trainingmgr_main.APP.test_client(self)
        self.logger = trainingmgr_main.LOGGER

    mocked_TRAININGMGR_CONFIG_OBJ=mock.Mock(name="TRAININGMGR_CONFIG_OBJ")
    attrs_TRAININGMGR_CONFIG_OBJ = {'my_ip.return_value': '123'}
    mocked_TRAININGMGR_CONFIG_OBJ.configure_mock(**attrs_TRAININGMGR_CONFIG_OBJ)
    resp=Response()
    resp.status_code=status.HTTP_204_NO_CONTENT
    the_result=[('testing_hash', '', 'InfluxSource', '127.0.0.21', '8080', '', '', '', False, '', '', '')]
    @patch('trainingmgr.trainingmgr_main.check_key_in_dictionary', return_value=True)
    @patch('trainingmgr.trainingmgr_main.get_feature_group_by_name_db', return_value=the_result)
    @patch('trainingmgr.trainingmgr_main.delete_feature_group_by_name')
    @patch('trainingmgr.trainingmgr_main.delete_dme_filtered_data_job', return_value=resp)
    @patch('trainingmgr.trainingmgr_main.TRAININGMGR_CONFIG_OBJ', return_value = mocked_TRAININGMGR_CONFIG_OBJ)
    def test_delete_list_of_feature_group(self, mock1, mock2, mock3, mock4, mock5):
        delete_req={"featuregroups_list":[{"featureGroup_name":"testing_hash"}]}
        expected_response=b'{"success count": 1, "failure count": 0}'
        response=self.client.delete('/featureGroup', data=json.dumps(delete_req), content_type="application/json")
        assert response.data==expected_response, "response is not equal"
        assert response.status_code==200, "status code not equal"
    
    @patch('trainingmgr.trainingmgr_main.check_key_in_dictionary', return_value=False)
    def test_negative_delete_list_of_feature_group(self, mock1):
        delete_req=delete_req={"featuregroups_list":[{"featureGroup_name":"testing_hash"}]}
        expected_response=b'{"Exception": "Wrong Request syntax"}'
        response=self.client.delete('/featureGroup', data=json.dumps(delete_req), content_type="application/json")
        assert response.data==expected_response
        assert response.status_code==400, "status code not equal"
    
    @patch('trainingmgr.trainingmgr_main.check_key_in_dictionary', return_value=True)
    @patch('trainingmgr.trainingmgr_main.isinstance', return_value=False)
    def test_negative_delete_list_of_feature_group_2(self, mock1, mock2):
        delete_req=delete_req={"featuregroups_list":[{"featureGroup_name":"testing_hash"}]}
        expected_response=b'{"Exception": "not given as list"}'
        response=self.client.delete('/featureGroup', data=json.dumps(delete_req), content_type="application/json")
        assert response.data==expected_response
        assert response.status_code==400, "status code not equal"

    def test_negative_delete_list_of_feature_group_3(self):
        delete_req=delete_req={"featuregroups_list":[("featureGroup_name")]}
        expected_response=b'{"success count": 0, "failure count": 1}'
        response=self.client.delete('/featureGroup', data=json.dumps(delete_req), content_type="application/json")
        assert response.data==expected_response
        assert response.status_code==200, "status code not equal"
    
    def test_negative_delete_list_of_feature_group_4(self):
        delete_req=delete_req={"featuregroups_list":[{"version":"1"}]}
        expected_response=b'{"success count": 0, "failure count": 1}'
        response=self.client.delete('/featureGroup', data=json.dumps(delete_req), content_type="application/json")
        assert response.data==expected_response
        assert response.status_code==200, "status code not equal"

    @patch('trainingmgr.trainingmgr_main.get_feature_group_by_name_db', side_effect=Exception("Mocked Error"))
    def test_negative_delete_list_of_feature_group_5(self, mock1):
        delete_req=delete_req={"featuregroups_list":[{"featureGroup_name":"testing_hash"}]}
        expected_response=b'{"success count": 0, "failure count": 1}'
        response=self.client.delete('/featureGroup', data=json.dumps(delete_req), content_type="application/json")
        assert response.data==expected_response
        assert response.status_code==200, "status code not equal"

    @patch('trainingmgr.trainingmgr_main.get_feature_group_by_name_db', return_value=None)
    def test_negative_delete_list_of_feature_group_6(self, mock1):
        delete_req=delete_req={"featuregroups_list":[{"featureGroup_name":"testing_hash"}]}
        expected_response=b'{"success count": 0, "failure count": 1}'
        response=self.client.delete('/featureGroup', data=json.dumps(delete_req), content_type="application/json")
        assert response.data==expected_response
        assert response.status_code==200, "status code not equal"

    the_result2=[('testing_hash', '', 'InfluxSource', '127.0.0.21', '8080', '', '', '', False, '', '', '')]
    @patch('trainingmgr.trainingmgr_main.get_feature_group_by_name_db', return_value=the_result2)
    @patch('trainingmgr.trainingmgr_main.delete_feature_group_by_name', side_effect=Exception("Mocked Error"))
    def test_negative_delete_list_of_feature_group_7(self, mock1, mock2):
        delete_req=delete_req={"featuregroups_list":[{"featureGroup_name":"testing_hash"}]}
        expected_response=b'{"success count": 0, "failure count": 1}'
        response=self.client.delete('/featureGroup', data=json.dumps(delete_req), content_type="application/json")
        assert response.data==expected_response
        assert response.status_code==200, "status code not equal"

@pytest.mark.skip("")
class Test_delete_list_of_trainingjob_version:
    @patch('trainingmgr.common.trainingmgr_config.TMLogger', return_value = TMLogger("tests/common/conf_log.yaml"))
    def setup_method(self,mock1,mock2):
        self.client = trainingmgr_main.APP.test_client(self)
        self.logger = trainingmgr_main.LOGGER
    
    mocked_TRAININGMGR_CONFIG_OBJ=mock.Mock(name="TRAININGMGR_CONFIG_OBJ")
    attrs_TRAININGMGR_CONFIG_OBJ = {'my_ip.return_value': '123'}
    mocked_TRAININGMGR_CONFIG_OBJ.configure_mock(**attrs_TRAININGMGR_CONFIG_OBJ)
    mocked_mm_sdk=mock.Mock(name="MM_SDK")
    attrs_mm_sdk = {'is_bucket_present.return_value': True}
    attrs_mm_sdk = {'delete_model_metric.return_value': True}
    mocked_mm_sdk.configure_mock(**attrs_mm_sdk)
    the_result=[('usecase7', 'auto test', '*', 'prediction with model name', 'Default', '{"arguments": {"epochs": "1", "usecase": "usecase7"}}', 'Enb=20 and Cellnum=6', datetime.datetime(2022, 9, 20,11, 40, 30), '7d09c0bf-7575-4475-86ff-5573fb3c4716', '{"DATA_EXTRACTION": "FINISHED", "DATA_EXTRACTION_AND_TRAINING": "FINISHED", "TRAINING": "FINISHED", "TRAINING_AND_TRAINED_MODEL": "FINISHED", "TRAINED_MODEL": "FINISHED"}', datetime.datetime(2022, 9, 20, 11, 42, 20), 1, True, 'Near RT RIC', '{"datalake_source": {"CassandraSource": {}}}', '{"datalake_source": {"CassandraSource": {}}}','http://10.0.0.47:32002/model/usecase7/1/Model.zip','','','','','')]
    @patch('trainingmgr.trainingmgr_main.check_key_in_dictionary', return_value=True)
    @patch('trainingmgr.trainingmgr_main.isinstance', return_value=True)
    @patch('trainingmgr.trainingmgr_main.TRAININGMGR_CONFIG_OBJ', return_value = mocked_TRAININGMGR_CONFIG_OBJ)
    @patch('trainingmgr.trainingmgr_main.get_info_by_version', return_value=the_result)
    @patch('trainingmgr.trainingmgr_main.get_one_word_status', return_value="FINISHED")
    @patch('trainingmgr.trainingmgr_main.change_field_value_by_version')
    @patch('trainingmgr.trainingmgr_main.MM_SDK', return_value = mocked_mm_sdk)
    @patch('trainingmgr.trainingmgr_main.delete_trainingjob_version')
    def test_delete_list_of_trainingjob_version(self, mock1, mock2, mock3, mock4, mock5, mock6, mock7, mock8):
        delete_req={"list":[{"trainingjob_name":"testing_dme_02","version":1}]}
        expected_res=b'{"success count": 1, "failure count": 0}'
        response=self.client.delete('/trainingjobs', data=json.dumps(delete_req), content_type="application/json")
        assert response.data==expected_res
        assert response.status_code == 200 , "status code is not equal"
    
    @patch('trainingmgr.trainingmgr_main.check_key_in_dictionary', return_value=False)
    def test_negative_delete_list_of_trainingjob_version_1(self, mock1):
        delete_req={"list":[{"trainingjob_name":"testing_dme_02","version":1}]}
        expected_response=b'{"Exception": "Wrong Request syntax"}'
        response=self.client.delete('/trainingjobs', data=json.dumps(delete_req), content_type="application/json")
        assert response.data==expected_response
        assert response.status_code==400, "status code not equal"

    @patch('trainingmgr.trainingmgr_main.check_key_in_dictionary', return_value=True)
    @patch('trainingmgr.trainingmgr_main.isinstance', return_value=False)
    def test_negative_delete_list_of_trainingjob_version_2(self, mock1, mock2):
        delete_req={"list":[{"trainingjob_name":"testing_dme_02","version":1}]}
        expected_response=b'{"Exception": "not given as list"}'
        response=self.client.delete('/trainingjobs', data=json.dumps(delete_req), content_type="application/json")
        assert response.data==expected_response
        assert response.status_code==400, "status code not equal"
    
    @patch('trainingmgr.trainingmgr_main.check_key_in_dictionary', return_value=True)
    def test_negative_delete_list_of_trainingjob_version_3(self, mock1):
        delete_req=delete_req={"list":[("trainingjob_name")]}
        expected_response=b'{"success count": 0, "failure count": 1}'
        response=self.client.delete('/trainingjobs', data=json.dumps(delete_req), content_type="application/json")
        assert response.data==expected_response
        assert response.status_code==200, "status code not equal"
    
    def test_negative_delete_list_of_trainingjob_version_4(self):
        delete_req=delete_req={"list":[{"trainingjob_name":"testing_dme_02"}]}
        expected_response=b'{"success count": 0, "failure count": 1}'
        response=self.client.delete('/trainingjobs', data=json.dumps(delete_req), content_type="application/json")
        assert response.data==expected_response
        assert response.status_code==200, "status code not equal"
    
    mocked_TRAININGMGR_CONFIG_OBJ=mock.Mock(name="TRAININGMGR_CONFIG_OBJ")
    attrs_TRAININGMGR_CONFIG_OBJ = {'my_ip.return_value': '123'}
    mocked_TRAININGMGR_CONFIG_OBJ.configure_mock(**attrs_TRAININGMGR_CONFIG_OBJ)
    @patch('trainingmgr.trainingmgr_main.check_key_in_dictionary', return_value=True)
    @patch('trainingmgr.trainingmgr_main.isinstance', return_value=True)
    @patch('trainingmgr.trainingmgr_main.TRAININGMGR_CONFIG_OBJ', return_value = mocked_TRAININGMGR_CONFIG_OBJ)
    @patch('trainingmgr.trainingmgr_main.get_info_by_version', side_effect=Exception("Mocked Error"))
    def test_negative_delete_list_of_trainingjob_version_5(self, mock1, mock2, mock3,mock4):
        delete_req=delete_req={"list":[{"trainingjob_name":"testing_dme_02","version":1}]}
        expected_response=b'{"success count": 0, "failure count": 1}'
        response=self.client.delete('/trainingjobs', data=json.dumps(delete_req), content_type="application/json")
        assert response.data==expected_response
        assert response.status_code==200, "status code not equal"
    
    mocked_TRAININGMGR_CONFIG_OBJ=mock.Mock(name="TRAININGMGR_CONFIG_OBJ")
    attrs_TRAININGMGR_CONFIG_OBJ = {'my_ip.return_value': '123'}
    mocked_TRAININGMGR_CONFIG_OBJ.configure_mock(**attrs_TRAININGMGR_CONFIG_OBJ)
    the_result2=[('mynetwork', 'testing', '*', 'testing_pipeline', 'Default', '{"arguments": {"epochs": "1", "trainingjob_name": "mynetwork"}}', '', datetime.datetime(2023, 2, 9, 9, 2, 11, 13916), 'No data available', '{"DATA_EXTRACTION": "FINISHED", "DATA_EXTRACTION_AND_TRAINING": "IN_PROGRESS", "TRAINING": "NOT_STARTED", "TRAINING_AND_TRAINED_MODEL": "NOT_STARTED", "TRAINED_MODEL": "NOT_STARTED"}', datetime.datetime(2023, 2, 9, 9, 2, 11, 13916), 1, False, '2', '{"datalake_source": {"InfluxSource": {}}}', 'No data available.', '', 'liveCell', 'UEData', True)]
    @patch('trainingmgr.trainingmgr_main.check_key_in_dictionary', return_value=True)
    @patch('trainingmgr.trainingmgr_main.isinstance', return_value=True)
    @patch('trainingmgr.trainingmgr_main.TRAININGMGR_CONFIG_OBJ', return_value = mocked_TRAININGMGR_CONFIG_OBJ)
    @patch('trainingmgr.trainingmgr_main.get_info_by_version', return_value=the_result2)
    def test_negative_delete_list_of_trainingjob_version_6(self, mock1, mock2, mock3,mock4):
        delete_req=delete_req={"list":[{"trainingjob_name":"testing_dme_02","version":1}]}
        expected_response=b'{"success count": 0, "failure count": 1}'
        response=self.client.delete('/trainingjobs', data=json.dumps(delete_req), content_type="application/json")
        assert response.data==expected_response
        assert response.status_code==200, "status code not equal"
    
    mocked_TRAININGMGR_CONFIG_OBJ=mock.Mock(name="TRAININGMGR_CONFIG_OBJ")
    attrs_TRAININGMGR_CONFIG_OBJ = {'my_ip.return_value': '123'}
    mocked_TRAININGMGR_CONFIG_OBJ.configure_mock(**attrs_TRAININGMGR_CONFIG_OBJ)
    the_result3=[('mynetwork', 'testing', '*', 'testing_pipeline', 'Default', '{"arguments": {"epochs": "1", "trainingjob_name": "mynetwork"}}', '', datetime.datetime(2023, 2, 9, 9, 2, 11, 13916), 'No data available', '{"DATA_EXTRACTION": "FINISHED", "DATA_EXTRACTION_AND_TRAINING": "IN_PROGRESS", "TRAINING": "NOT_STARTED", "TRAINING_AND_TRAINED_MODEL": "NOT_STARTED", "TRAINED_MODEL": "NOT_STARTED"}', datetime.datetime(2023, 2, 9, 9, 2, 11, 13916), 1, False, '2', '{"datalake_source": {"InfluxSource": {}}}', 'No data available.', '', 'liveCell', 'UEData', False)]
    @patch('trainingmgr.trainingmgr_main.check_key_in_dictionary', return_value=True)
    @patch('trainingmgr.trainingmgr_main.isinstance', return_value=True)
    @patch('trainingmgr.trainingmgr_main.TRAININGMGR_CONFIG_OBJ', return_value = mocked_TRAININGMGR_CONFIG_OBJ)
    @patch('trainingmgr.trainingmgr_main.get_info_by_version', return_value=the_result3)
    @patch('trainingmgr.trainingmgr_main.get_one_word_status', return_value="wrong status")
    def test_negative_delete_list_of_trainingjob_version_7(self, mock1, mock2, mock3,mock4, mock5):
        delete_req=delete_req={"list":[{"trainingjob_name":"testing_dme_02","version":1}]}
        expected_response=b'{"success count": 0, "failure count": 1}'
        response=self.client.delete('/trainingjobs', data=json.dumps(delete_req), content_type="application/json")
        assert response.data==expected_response
        assert response.status_code==200, "status code not equal"
    
    mocked_TRAININGMGR_CONFIG_OBJ=mock.Mock(name="TRAININGMGR_CONFIG_OBJ")
    attrs_TRAININGMGR_CONFIG_OBJ = {'my_ip.return_value': '123'}
    mocked_TRAININGMGR_CONFIG_OBJ.configure_mock(**attrs_TRAININGMGR_CONFIG_OBJ)
    the_result4=[('mynetwork', 'testing', '*', 'testing_pipeline', 'Default', '{"arguments": {"epochs": "1", "trainingjob_name": "mynetwork"}}', '', datetime.datetime(2023, 2, 9, 9, 2, 11, 13916), 'No data available', '{"DATA_EXTRACTION": "FINISHED", "DATA_EXTRACTION_AND_TRAINING": "IN_PROGRESS", "TRAINING": "NOT_STARTED", "TRAINING_AND_TRAINED_MODEL": "NOT_STARTED", "TRAINED_MODEL": "NOT_STARTED"}', datetime.datetime(2023, 2, 9, 9, 2, 11, 13916), 1, False, '2', '{"datalake_source": {"InfluxSource": {}}}', 'No data available.', '', 'liveCell', 'UEData', False)]
    @patch('trainingmgr.trainingmgr_main.check_key_in_dictionary', return_value=True)
    @patch('trainingmgr.trainingmgr_main.isinstance', return_value=True)
    @patch('trainingmgr.trainingmgr_main.TRAININGMGR_CONFIG_OBJ', return_value = mocked_TRAININGMGR_CONFIG_OBJ)
    @patch('trainingmgr.trainingmgr_main.get_info_by_version', return_value=the_result4)
    @patch('trainingmgr.trainingmgr_main.get_one_word_status', return_value="FINISHED")
    @patch('trainingmgr.trainingmgr_main.change_field_value_by_version',side_effect=Exception("Mocked Error"))
    def test_negative_delete_list_of_trainingjob_version_8(self, mock1, mock2, mock3,mock4, mock5, mock6):
        delete_req=delete_req={"list":[{"trainingjob_name":"testing_dme_02","version":1}]}
        expected_response=b'{"success count": 0, "failure count": 1}'
        response=self.client.delete('/trainingjobs', data=json.dumps(delete_req), content_type="application/json")
        assert response.data==expected_response
        assert response.status_code==200, "status code not equal"

    mocked_TRAININGMGR_CONFIG_OBJ=mock.Mock(name="TRAININGMGR_CONFIG_OBJ")
    attrs_TRAININGMGR_CONFIG_OBJ = {'my_ip.return_value': '123'}
    mocked_TRAININGMGR_CONFIG_OBJ.configure_mock(**attrs_TRAININGMGR_CONFIG_OBJ)
    mocked_mm_sdk=mock.Mock(name="MM_SDK")
    attrs_mm_sdk = {'is_bucket_present.return_value': True}
    attrs_mm_sdk = {'delete_model_metric.return_value': True}
    mocked_mm_sdk.configure_mock(**attrs_mm_sdk)
    the_result=[('usecase7', 'auto test', '*', 'prediction with model name', 'Default', '{"arguments": {"epochs": "1", "usecase": "usecase7"}}', 'Enb=20 and Cellnum=6', datetime.datetime(2022, 9, 20,11, 40, 30), '7d09c0bf-7575-4475-86ff-5573fb3c4716', '{"DATA_EXTRACTION": "FINISHED", "DATA_EXTRACTION_AND_TRAINING": "FINISHED", "TRAINING": "FINISHED", "TRAINING_AND_TRAINED_MODEL": "FINISHED", "TRAINED_MODEL": "FINISHED"}', datetime.datetime(2022, 9, 20, 11, 42, 20), 1, True, 'Near RT RIC', '{"datalake_source": {"CassandraSource": {}}}', '{"datalake_source": {"CassandraSource": {}}}','http://10.0.0.47:32002/model/usecase7/1/Model.zip','','','','','')]
    @patch('trainingmgr.trainingmgr_main.check_key_in_dictionary', return_value=True)
    @patch('trainingmgr.trainingmgr_main.isinstance', return_value=True)
    @patch('trainingmgr.trainingmgr_main.TRAININGMGR_CONFIG_OBJ', return_value = mocked_TRAININGMGR_CONFIG_OBJ)
    @patch('trainingmgr.trainingmgr_main.get_info_by_version', return_value=the_result)
    @patch('trainingmgr.trainingmgr_main.get_one_word_status', return_value="FINISHED")
    @patch('trainingmgr.trainingmgr_main.change_field_value_by_version')
    @patch('trainingmgr.trainingmgr_main.MM_SDK', return_value = mocked_mm_sdk)
    @patch('trainingmgr.trainingmgr_main.delete_trainingjob_version', side_effect=Exception("Mocked Error"))
    def test_negative_delete_list_of_trainingjob_version_9(self, mock1, mock2, mock3, mock4, mock5, mock6, mock7, mock8):
        delete_req={"list":[{"trainingjob_name":"testing_dme_02","version":1}]}
        expected_res=b'{"success count": 0, "failure count": 1}'
        response=self.client.delete('/trainingjobs', data=json.dumps(delete_req), content_type="application/json")
        assert response.data==expected_res
        assert response.status_code == 200 , "status code is not equal"

    mocked_TRAININGMGR_CONFIG_OBJ=mock.Mock(name="TRAININGMGR_CONFIG_OBJ")
    attrs_TRAININGMGR_CONFIG_OBJ = {'my_ip.return_value': '123'}
    mocked_TRAININGMGR_CONFIG_OBJ.configure_mock(**attrs_TRAININGMGR_CONFIG_OBJ)
    @patch('trainingmgr.trainingmgr_main.check_key_in_dictionary', return_value=True)
    @patch('trainingmgr.trainingmgr_main.isinstance', return_value=True)
    @patch('trainingmgr.trainingmgr_main.TRAININGMGR_CONFIG_OBJ', return_value = mocked_TRAININGMGR_CONFIG_OBJ)
    @patch('trainingmgr.trainingmgr_main.get_info_by_version', return_value=None)
    def test_negative_delete_list_of_trainingjob_version_10(self, mock1, mock2, mock3, mock4):
        delete_req={"list":[{"trainingjob_name":"testing_dme_02","version":1}]}
        expected_res=b'{"success count": 0, "failure count": 1}'
        response=self.client.delete('/trainingjobs', data=json.dumps(delete_req), content_type="application/json")
        assert response.data==expected_res
        assert response.status_code == 200 , "status code is not equal"
