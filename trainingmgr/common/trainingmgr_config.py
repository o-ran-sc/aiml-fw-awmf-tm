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

    def __init__(self):
        """
        This constructor filling configuration varibles.
        """
        self.__kf_adapter_port = getenv('KF_ADAPTER_PORT').rstrip()
        self.__kf_adapter_ip = getenv('KF_ADAPTER_IP').rstrip()

        self.__data_extraction_port = getenv('DATA_EXTRACTION_API_PORT').rstrip()
        self.__data_extraction_ip = getenv('DATA_EXTRACTION_API_IP').rstrip()

        self.__my_port = getenv('TRAINING_MANAGER_PORT').rstrip()
        self.__my_ip = getenv('TRAINING_MANAGER_IP').rstrip()

        self.__ps_user = getenv('PS_USER').rstrip()
        self.__ps_password = getenv('PS_PASSWORD').rstrip()
        self.__ps_ip = getenv('PS_IP').rstrip()
        self.__ps_port = getenv('PS_PORT').rstrip()
        self.__allow_control_access_origin = getenv('ACCESS_CONTROL_ALLOW_ORIGIN').rstrip()

        self.tmgr_logger = TMLogger("common/conf_log.yaml")
        self.__logger = self.tmgr_logger.logger

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
    def allow_control_access_origin(self):
        """
        Function for getting allow_control_access_origin

        Args: None

        Returns:
            string allow_control_access_origin
        
        """
        return self.__allow_control_access_origin

    def is_config_loaded_properly(self):
        """
        This function checks where all environment variable got value or not.
        if all environment variables got value then function returns True
        otherwise it return False.
        """
        all_present = True

        for var in [self.__kf_adapter_ip, self.__kf_adapter_port,
                    self.__data_extraction_ip, self.__data_extraction_port,
                    self.__my_port, self.__ps_ip, self.__ps_port, self.__ps_user,
                    self.__ps_password, self.__my_ip, self.__allow_control_access_origin, self.__logger]:
            if var is None:
                all_present = False
        return all_present
