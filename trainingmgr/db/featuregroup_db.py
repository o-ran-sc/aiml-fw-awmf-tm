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

from trainingmgr.common.exceptions_utls import DBException
from sqlalchemy.exc import IntegrityError
from psycopg2.errors import UniqueViolation
from trainingmgr.models import db, FeatureGroup
from trainingmgr.common.trainingmgr_config import TrainingMgrConfig

LOGGER = TrainingMgrConfig().logger

DB_QUERY_EXEC_ERROR = "Failed to execute query in "

def add_featuregroup(featuregroup):
    """
    This function add the new row with given information
    """
    try:
        db.session.add(featuregroup)
        db.session.commit()
    except IntegrityError as e:
        if isinstance(e.orig, UniqueViolation):
            LOGGER.error(f"failed to add featuregroup due to: {str(e)}")
            raise DBException(f"Featuregroup with featuregroup_name {featuregroup.featuregroup_name} already exist")
    except Exception as err:
        LOGGER.error(f"failed to add featuregroup due to: {str(err)}")
        db.session.rollback()
        raise DBException(DB_QUERY_EXEC_ERROR + " failed to add feature group")

def edit_featuregroup(featuregroup_name, featuregroup):
    """
    This function update existing row with given information
    """
    
    featuregroup_info = FeatureGroup.query.filter_by(featuregroup_name=featuregroup_name).first()
    for key, value in featuregroup.items():
        if(key == 'id'):
            continue
        setattr(featuregroup_info, key, value)

    try:
        db.session.commit()
    except Exception as err:
        raise DBException(DB_QUERY_EXEC_ERROR+"failed to update the "+ featuregroup_name+ str(err))
    
    return

def get_feature_groups_db():
    """
    This function returns feature_groups
    """
    featureGroups = FeatureGroup.query.all()
    return featureGroups

def get_feature_group_by_name_db(featuregroup_name):
    """
    This Function return a feature group with name "featuregroup_name"
    """
    return FeatureGroup.query.filter_by(featuregroup_name=featuregroup_name).one()

def get_feature_groups_from_inputDataType_db(inputDataType):
    """
        This Function return all feature group with feature_list as "inputDataType"
        Return type is a list of tuples
    """
    try:
        return FeatureGroup.query.with_entities(FeatureGroup.featuregroup_name).filter_by(feature_list=inputDataType).all()
    except Exception as err:
        raise DBException(DB_QUERY_EXEC_ERROR + "in get_feature_groups_from_inputDataType_db with error : " + str(err))

def delete_feature_group_by_name(featuregroup_name):
    """
    This function is used to delete the feature group from db
    """
    featuregroup = FeatureGroup.query.filter_by(featuregroup_name = featuregroup_name).first()
    if featuregroup:
        db.session.delete(featuregroup)
        db.session.commit()
    return



