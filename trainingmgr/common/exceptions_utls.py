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

class APIException(Exception):
    """
    A class used to represent an Api exception

    Attributes
    ----------
    message : str
        a formatted string to print out what is exception
    code : int
        http status code
    """

    def __init__(self, code, message="exception occured"):
        """
        Parameters
        ----------
        message : str
            a formatted string to print out what is exception
        code : int
            http statuse code

        """
        
        self.code = code
        self.message = message
        super().__init__(self.message)

class TMException(Exception):
    """
    A class used to represent an Training Manager exception

    Attributes
    ----------
    message : str
        a formatted string to print out what is exception
    """

    def __init__(self, message="TM exception occured"):
        """
        Parameters
        ----------
        message : str
            a formatted string to print out what is exception
        code : int
            http statuse code

        """
        self.message = message
        super().__init__(self.message)

class DBException(Exception):
    """
    A class used to represent an DB related exception

    Attributes
    ----------
    message : str
        a formatted string to print out what is exception
    """

    def __init__(self, message="DB exception occured"):
        """
        Parameters
        ----------
        message : str
            a formatted string to print out what is exception
        code : int
            http statuse code

        """
        self.message = message
        super().__init__(self.message)
