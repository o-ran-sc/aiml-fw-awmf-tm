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

#!/usr/bin/python3

"""tmgr_logger.py
This module is for Initializing Logger Framework
"""

import logging
import logging.config
import yaml


class TMLogger(object):# pylint: disable=too-few-public-methods
    """
    This is a class for initiliazing logger configuration for TMLogger
    Attributes: None
    """

    def __init__(self, conf_file):
        """
        The constructor for TMLogger class.

        Parameters
        ----------
        conf_file : str
            a file path for the logger configuration
        """
        try:
            with open(conf_file, 'r') as file:
                log_config = yaml.safe_load(file.read())
            logging.config.dictConfig(log_config)
            self.log_level = log_config["root"]["level"]
            self.logger = logging.getLogger(__name__)
        except FileNotFoundError as err:
            print("error opening yaml config file")
            print(err)

    @property
    def get_logger(self):
        """
        Function for giving logger instance to the caller of the function
        Args:None
        Returns:
            logger: logger handle to be used in other modules
        """
        return self.logger
    
    @property
    def get_log_level(self):
        return self.log_level
    
