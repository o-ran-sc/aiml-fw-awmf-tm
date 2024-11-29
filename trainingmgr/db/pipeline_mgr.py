# ==================================================================================
#
#       Copyright (c) 2024 Samsung Electronics Co., Ltd. All Rights Reserved.
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

from trainingmgr.common.trainingmgr_config import TrainingMgrConfig
import requests
from trainingmgr.common.exceptions_utls import TMException
from flask_api import status
import requests


LOGGER = TrainingMgrConfig().logger

# Constants
MIMETYPE_JSON = "application/json"
ERROR_TYPE_KF_ADAPTER_JSON = "Kf adapter doesn't sends json type response"


class PipelineMgr:    
    __instance = None

    def __new__(cls):
        if cls.__instance is None:
            cls.__instance = super(PipelineMgr, cls).__new__(cls)
            cls.__instance.__initialized = False
        return cls.__instance
    
    def __init__(self):
        if self.__initialized:
            return

        self.kf_adapter_ip = TrainingMgrConfig().kf_adapter_ip
        self.kf_adapter_port = TrainingMgrConfig().kf_adapter_port
        
        self.__initialized = True
    
        
    def get_all_pipelines(self):
        """
            This function returns the information for all pipelines
        """
        try:
            url = f'http://{self.kf_adapter_ip}:{self.kf_adapter_port}/pipelines'
            LOGGER.debug(f"Requesting pipelines from: {url}")
            response = requests.get(url)
            if response.status_code == 200:
                if response.headers['content-type'] != MIMETYPE_JSON:
                    err_msg = ERROR_TYPE_KF_ADAPTER_JSON
                    LOGGER.error(err_msg)
                    raise TMException(err_msg)

                return response.json()
            else:
                err_msg = f"Unexpected response from KFAdapter: {response.status_code}"
                LOGGER.error(err_msg)
                return TMException(err_msg)

        except requests.RequestException as err:
            err_msg = f"Error communicating with KFAdapter : {str(err)}"
            LOGGER.error(err_msg)
            raise TMException(err_msg)
        except Exception as err:
            err_msg = f"Unexpected error in get_pipeline_info_by_name: {str(err)}"
            LOGGER.error(err_msg)
            raise TMException(err_msg)
        
        
    def get_all_pipeline_versions(self, pipeline_name):
        """
            This function returns the version-list for input pipeline
        """
        try:
            url = f'http://{self.kf_adapter_ip}:{self.kf_adapter_port}/pipelines/{pipeline_name}/versions'
            LOGGER.debug(f"Requesting pipelines Versions from: {url}")
            response = requests.get(url)
            if response.status_code == 200:
                if response.headers['content-type'] != MIMETYPE_JSON:
                    err_msg = ERROR_TYPE_KF_ADAPTER_JSON
                    LOGGER.error(err_msg)
                    raise TMException(err_msg)

                return response.json()
            else:
                err_msg = f"Unexpected response from KFAdapter: {response.status_code}"
                LOGGER.error(err_msg)
                return TMException(err_msg)

        except requests.RequestException as err:
            err_msg = f"Error communicating with KFAdapter : {str(err)}"
            LOGGER.error(err_msg)
            raise TMException(err_msg)
        except Exception as err:
            err_msg = f"Unexpected error in get_all_pipeline_versions: {str(err)}"
            LOGGER.error(err_msg)
            raise TMException(err_msg)
    
    def upload_pipeline_file(self, pipeline_name, filepath, description):
        '''
            Uploads the File to KfAdapter
        '''
        try:
            url = f'http://{self.kf_adapter_ip}:{self.kf_adapter_port}/pipelineIds/{pipeline_name}'
            with open(filepath, 'rb') as file:
                files = {'file': file.read()}
                
            resp = requests.post(url, files=files, data={"description": description})
            LOGGER.debug(resp.text)
            if resp.status_code == status.HTTP_200_OK:
                LOGGER.debug("Pipeline uploaded :%s", pipeline_name)
                return True
            else:
                LOGGER.error(resp.json()["message"])
                raise TMException("Error while uploading pipeline | " + resp.json()["message"])
        except Exception as err:
            err_msg = f"Unexpected error in upload_pipeline_file: {str(err)}"
            LOGGER.error(err_msg)
            raise TMException(err_msg)