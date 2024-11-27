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

from os import getenv
from trainingmgr.common.trainingmgr_config import TrainingMgrConfig
import requests
from trainingmgr.common.exceptions_utls import TMException

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