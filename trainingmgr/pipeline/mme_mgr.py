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
import json

LOGGER = TrainingMgrConfig().logger

# Constants
MIMETYPE_JSON = "application/json"
ERROR_TYPE_KF_ADAPTER_JSON = "Kf adapter doesn't sends json type response"


class MmeMgr:    
    __instance = None

    def __new__(cls):
        if cls.__instance is None:
            cls.__instance = super(MmeMgr, cls).__new__(cls)
            cls.__instance.__initialized = False
        return cls.__instance
    
    def __init__(self):
        if self.__initialized:
            return

        self.mme_ip = TrainingMgrConfig().model_management_service_ip
        self.mme_port = TrainingMgrConfig().model_management_service_port
        
        self.__initialized = True
    
        
    def get_modelInfo_by_modelId(self, modelName, modelVersion):
        """
            This function returns the model information for given modelName and ModelVersion from MME
        """
        try:
            url = f'http://{self.mme_ip}:{self.mme_port}/models/?model-name={modelName}&model-version={int(modelVersion)}'
            LOGGER.debug(f"Requesting modelInfo from: {url}")
            response = requests.get(url)
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                # The modelinfo is NOT FOUND i.e. model is not registered
                LOGGER.debug(f"ModelName = {modelName}, ModelVersion = {modelVersion} is not registered on MME")
                return None                
            else:
                err_msg = f"Unexpected response from mme: {response.status_code}"
                LOGGER.error(err_msg)
                raise TMException(err_msg)

        except requests.RequestException as err:
            err_msg = f"Error communicating with MME : {str(err)}"
            LOGGER.error(err_msg)
            raise TMException(err_msg)
        except Exception as err:
            err_msg = f"Unexpected error in get_modelInfo_by_modelId: {str(err)}"
            LOGGER.error(err_msg)
            raise TMException(err_msg)
        
    