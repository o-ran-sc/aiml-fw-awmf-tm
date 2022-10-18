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
This module contains Steps class for different training manager's steps.
"""
from enum import Enum
class Steps(Enum):
    """
    This class contains different usecase's steps.
    """
    DATA_EXTRACTION = 1
    DATA_EXTRACTION_AND_TRAINING = 2
    TRAINING = 3
    TRAINING_AND_TRAINED_MODEL = 4
    TRAINED_MODEL = 5
