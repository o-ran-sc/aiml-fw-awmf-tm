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

"""
This module is for loading training manager configuration.
"""

from os import getenv
from trainingmgr.common.tmgr_logger import TMLogger


class TrainingMgrConfig:
    """
    This class conatains method for getting configuration varibles.
    """

    __instance = None

    def __new__(cls):
        if cls.__instance is None:
            cls.__instance = super(TrainingMgrConfig, cls).__new__(cls)
            cls.__instance.__initialized = False
        return cls.__instance

    def __init__(self):
        """
        This constructor filling configuration varibles.
        """
        if self.__initialized:
            return
        self.__kf_adapter_port = getenv('KF_ADAPTER_PORT').rstrip() if getenv('KF_ADAPTER_PORT') is not None else None
        self.__kf_adapter_ip = getenv('KF_ADAPTER_IP').rstrip() if getenv('KF_ADAPTER_IP') is not None else None

        self.__data_extraction_port = getenv('DATA_EXTRACTION_API_PORT').rstrip() if getenv('DATA_EXTRACTION_API_PORT') is not None else None
        self.__data_extraction_ip = getenv('DATA_EXTRACTION_API_IP').rstrip() if getenv('DATA_EXTRACTION_API_IP') is not None else None

        self.__my_port = getenv('TRAINING_MANAGER_PORT').rstrip() if getenv('TRAINING_MANAGER_PORT') is not None else None
        self.__my_ip = getenv('TRAINING_MANAGER_IP').rstrip() if getenv('TRAINING_MANAGER_IP') is not None else None

        self.__ps_user = getenv('PS_USER').rstrip() if getenv('PS_USER') is not None else None
        self.__ps_password = getenv('PS_PASSWORD').rstrip() if getenv('PS_PASSWORD') is not None else None
        self.__ps_ip = getenv('PS_IP').rstrip() if getenv('PS_IP') is not None else None
        self.__ps_port = getenv('PS_PORT').rstrip() if getenv('PS_PORT') is not None else None

        self.__model_management_service_ip = getenv('MODEL_MANAGEMENT_SERVICE_IP').rstrip() if getenv('MODEL_MANAGEMENT_SERVICE_IP') is not None else None
        self.__model_management_service_port = getenv('MODEL_MANAGEMENT_SERVICE_PORT').rstrip() if getenv('MODEL_MANAGEMENT_SERVICE_PORT') is not None else None

        self.__allow_control_access_origin = getenv('ACCESS_CONTROL_ALLOW_ORIGIN').rstrip() if getenv('ACCESS_CONTROL_ALLOW_ORIGIN') is not None else None
        self.__pipeline = getenv('PIPELINE').rstrip() if getenv('PIPELINE') is not None else None

        self.tmgr_logger = TMLogger("common/conf_log.yaml")
        self.__logger = self.tmgr_logger.logger
        self.__initialized = True

    @property
    def kf_adapter_port(self):
        """
        Function for getting port number where kf adapter is accessible

        Args:None

        Returns:
            port number where kf adapter is accessible
        """
        return self.__kf_adapter_port

    @property
    def kf_adapter_ip(self):
        """
        Function for getting ip address or service name where kf adapter is accessible

        Args:None

        Returns:
            ip address or service name where kf adapter is accessible
        """
        return self.__kf_adapter_ip

    @property
    def data_extraction_port(self):
        """
        Function for getting port number where data extraction module is accessible

        Args:None

        Returns:
            port number where data extraction module is accessible
        """
        return self.__data_extraction_port

    @property
    def data_extraction_ip(self):
        """
        Function for getting ip address or service name where data extraction module is accessible

        Args:None

        Returns:
            ip address or service name where data extraction module is accessible
        """
        return self.__data_extraction_ip

    @property
    def my_port(self):
        """
        Function for getting port number where training manager is running

        Args:None

        Returns:
            port number where training manager is running
        """
        return self.__my_port

    @property
    def my_ip(self):
        """
        Function for getting ip address where training manager is running

        Args:None

        Returns:
            ip address where training manager is running
        """
        return self.__my_ip

    @property
    def logger(self):
        """
        Function for getting logger instance.

        Args:None

        Returns:
            logger instance.
        """
        return self.__logger

    @property
    def ps_user(self):
        """
        Function for getting postgres db's user.

        Args:None

        Returns:
            postgres db's user.
        """
        return self.__ps_user

    @property
    def ps_password(self):
        """
        Function for getting postgres db's password.

        Args:None

        Returns:
            postgres db's password.
        """
        return self.__ps_password

    @property
    def ps_ip(self):
        """
        Function for getting ip address or service name where postgres db is accessible

        Args:None

        Returns:
            ip address or service name where postgres db is accessible
        """
        return self.__ps_ip

    @property
    def ps_port(self):
        """
        Function for getting port number where postgres db is accessible

        Args:None

        Returns:
            port number where postgres db is accessible
        """
        return self.__ps_port
    
    @property
    def model_management_service_port(self):
        """
        Function for getting model management service port
        Args:None

        Returns:
            string model_management_service_port
        """
        return self.__model_management_service_port
    

    @property
    def model_management_service_ip(self):
        """
        Function for getting model management service ip
        Args:None

        Returns:
            string model_management_service_ip
        """
        return self.__model_management_service_ip

    @property
    def allow_control_access_origin(self):
        """
        Function for getting allow_control_access_origin

        Args: None

        Returns:
            string allow_control_access_origin
        
        """
        return self.__allow_control_access_origin

    @property
    def pipeline(self):
        """
        Function for getting pipelines

        Args: None

        Returns:
            string pipelines
        
        """
        return self.__pipeline

    def is_config_loaded_properly(self):
        """
        This function checks where all environment variable got value or not.
        if all environment variables got value then function returns True
        otherwise it return False.
        """
        return all([val is not None for val in [self.__kf_adapter_ip, 
                                                self.__kf_adapter_port,
                    self.__data_extraction_ip, 
                    self.__data_extraction_port,
                    self.__my_port, 
                    self.__ps_ip, 
                    self.__ps_port, 
                    self.__ps_user,
                    self.__ps_password, 
                    self.__my_ip,
                    self.__model_management_service_ip, 
                    self.__model_management_service_port, 
                    self.__allow_control_access_origin,
                    self.__pipeline, 
                    self.__logger]])

