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

from trainingmgr.db.featuregroup_db import get_feature_group_by_name_db, get_feature_groups_from_inputDataType_db
from trainingmgr.common.exceptions_utls import TMException, DBException
from trainingmgr.common.trainingmgr_config import TrainingMgrConfig

LOGGER = TrainingMgrConfig().logger

def get_featuregroup_by_name(featuregroup_name:str):
    LOGGER.debug(f'service for get featuregroup by name')
    try:
        featuregroup = get_feature_group_by_name_db(featuregroup_name)
        return featuregroup
    except DBException as err:
        raise TMException(f"get featuregroup by name service failed with exception : {str(err)}")
    
def get_featuregroup_from_inputDataType(inputDataType):
    LOGGER.debug(f'Deducing featuregroupName from InputDataType : {inputDataType}')
    try:
        candidate_list = get_feature_groups_from_inputDataType_db(inputDataType)
        LOGGER.debug(f'Candidates for inputDataType {inputDataType} are f{candidate_list}')
        if(len(candidate_list) == 0):
            raise TMException(f'No featureGroup is available for inputDataType {inputDataType}')
        elif(len(candidate_list) == 1):
            selected_featuregroup = candidate_list[0][0]
            LOGGER.debug(f'FeatureGroup Selected for InputDataType {inputDataType} is {selected_featuregroup}')
            return selected_featuregroup
        else:
            raise TMException(f'2 or more featureGroup are available for inputDataType : {inputDataType}\n Available featuregroups are {candidate_list}\n Please specify one featuregroup_name in trainingConfig to resolve conflict')
    except DBException as err:
        raise TMException(f"get get_featuregroup_from_inputDataType service failed with exception : {str(err)}")
    except Exception as err:
        raise err
            
        
    