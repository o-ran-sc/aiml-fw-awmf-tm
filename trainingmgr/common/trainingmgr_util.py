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

""""
This file contains Training management utility functions
"""
from flask import jsonify
import json
import re
from flask_api import status
from marshmallow import ValidationError
from trainingmgr.db.common_db_fun import change_in_progress_to_failed_by_latest_version
from trainingmgr.db.featuregroup_db import edit_featuregroup, \
get_feature_group_by_name_db, delete_feature_group_by_name
from trainingmgr.constants.states import States
from trainingmgr.common.exceptions_utls import APIException,TMException,DBException
from trainingmgr.common.trainingmgr_operations import create_dme_filtered_data_job
from trainingmgr.schemas import FeatureGroupSchema
from trainingmgr.constants.steps import Steps

ERROR_TYPE_KF_ADAPTER_JSON = "Kf adapter doesn't sends json type response"
MIMETYPE_JSON = "application/json"
PATTERN = re.compile(r"\w+")

featuregroup_schema = FeatureGroupSchema()
featuregroups_schema = FeatureGroupSchema(many = True)


def check_key_in_dictionary(fields, dictionary):
    '''
    This function raises exception if any string from fields list does not present in a dictionary
    as a key
    '''
    iskeyavailable = True
    for field_name in fields:
        if field_name not in dictionary:
            iskeyavailable = False
            break
            #Log (field_name + " not provide")
    return iskeyavailable

def get_one_word_status(steps_state):
    """
    Converts steps_state to a single word status (overall_status) and returns it.
    """
    status_counts = {
        States.FAILED.name: 0,
        States.FINISHED.name: 0,
        States.NOT_STARTED.name: 0,
        States.IN_PROGRESS.name: 0,
    }
   
    for step_status in steps_state.values():
        status_counts[step_status] += 1
   
    if status_counts[States.FAILED.name] > 0:
        return States.FAILED.name
    if status_counts[States.NOT_STARTED.name] == len(steps_state):
        return States.NOT_STARTED.name
    if status_counts[States.FINISHED.name] == len(steps_state):
        return States.FINISHED.name
   
    return States.IN_PROGRESS.name


def get_step_in_progress_state(steps_state):
    '''
        This function return the first step which is currently In-Progress state.
    '''
    for step in sorted(Steps, key=lambda x: x.value):
        if steps_state[step.name] == States.IN_PROGRESS.name:
            return step
    
    return None

def check_trainingjob_data(trainingjob_name, json_data):
    """
    This function checks validation for json_data dictionary and return tuple which conatins
    values of different keys in jsn_data.
    """
    try:
        if check_key_in_dictionary(["featureGroup_name", "pipeline_version", \
                                 "pipeline_name", "experiment_name",
                                 "arguments", "enable_versioning",
                                 "datalake_source", "description",
                                 "query_filter"], json_data):

            description = json_data["description"]
            feature_list = json_data["featureGroup_name"]
            pipeline_name = json_data["pipeline_name"]
            experiment_name = json_data["experiment_name"]
            arguments = json_data["arguments"]

            if not isinstance(arguments, dict):
                raise TMException("Please pass agruments as dictionary for " + trainingjob_name)
            query_filter = json_data["query_filter"]
            enable_versioning = json_data["enable_versioning"]
            pipeline_version = json_data["pipeline_version"]
            datalake_source = json_data["datalake_source"]
        else :
            raise TMException("check_trainingjob_data- supplied data doesn't have" + \
                                "all the required fields ")
    except Exception as err:
        raise APIException(status.HTTP_400_BAD_REQUEST,
                           str(err)) from None
    return (feature_list, description, pipeline_name, experiment_name,
            arguments, query_filter, enable_versioning, pipeline_version,
            datalake_source)

def check_feature_group_data(json_data):
    """
    This function checks validation for json_data dictionary and return tuple which conatins
    values of different keys in jsn_data.
    """
    try:
        if check_key_in_dictionary(["featureGroupName", "feature_list", \
                                    "datalake_source", "enable_Dme", "Host", 
                                    "Port", "dmePort","bucket", "token", "source_name", "measured_obj_class", "_measurement"], json_data):
            feature_group_name=json_data["featureGroupName"]
            features=json_data["feature_list"]
            datalake_source=json_data["datalake_source"]
            enable_dme=json_data["enable_Dme"]
            measurement = json_data["_measurement"]
            host=json_data["Host"]
            port=json_data["Port"]
            dme_port=json_data["dmePort"]
            bucket=json_data["bucket"]
            token=json_data["token"]
            source_name=json_data["source_name"]
            db_org=json_data["dbOrg"]
            measured_obj_class = json_data["measured_obj_class"]
        else :
            raise TMException("check_featuregroup_data- supplied data doesn't have" + \
                                " all the required fields ")
    
    except Exception as err:
        raise APIException(status.HTTP_400_BAD_REQUEST, str(err)) from None
    
    return (feature_group_name, features, datalake_source, enable_dme, host, port,dme_port, bucket, token, source_name,db_org, measured_obj_class, measurement)

def get_feature_group_by_name(featuregroup_name, logger):
    """
    Function fetching a feature group

    Args in function:
        featuregroup_name: str
            name of featuregroup_name.
    Returns:
        api response: dict
            info of featuregroup
        status code:
            HTTP status code 200

    Exceptions:
        all exception are provided with exception message and HTTP status code.
    """
    api_response={}
    response_code=status.HTTP_500_INTERNAL_SERVER_ERROR
    if not check_trainingjob_name_or_featuregroup_name(featuregroup_name):
        return {"Exception":"The featuregroup_name is not correct"}, status.HTTP_400_BAD_REQUEST
    logger.debug("Request for getting a feature group with name = "+ featuregroup_name)
    try:
        featuregroup= get_feature_group_by_name_db(featuregroup_name)
        if not featuregroup:
            return jsonify({"error":f"featuregroup with name '{featuregroup_name}' not found"}), 404
        api_response = featuregroup_schema.jsonify(featuregroup)
        response_code = status.HTTP_200_OK
        
    except Exception as err:
        api_response = {"Exception": str(err)}
        logger.error(str(err))
    return api_response, response_code

from trainingmgr.models.featuregroup import FeatureGroup 
def edit_feature_group_by_name(featuregroup_name: str, 
                               featuregroup: FeatureGroup, logger, tm_conf_obj):
    """
    Function fetching a feature group

    Args in function:
        featuregroup_name: str
            name of featuregroup_name.
        json_data: dict
            info of changed featuregroup_name
    Returns:
        api response: dict
            response message
        status code:
            HTTP status code 200

    Exceptions:
        all exception are provided with exception message and HTTP status code.
    """
    api_response= {}
    response_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    if not check_trainingjob_name_or_featuregroup_name(featuregroup_name):
        return {"Exception":"The featuregroup_name is not correct"}, status.HTTP_400_BAD_REQUEST
    
    logger.debug("Request for editing a feature group with name = "+ featuregroup_name)
    # logger.debug("db info before the edit : %s", get_feature_group_by_name_db(ps_db_obj, featuregroup_name))
    try:
        # the features are stored in string format in the db, and has to be passed as list of feature to the dme. Hence the conversion.
        featuregroup_dict = featuregroup_schema.dump(featuregroup)
        edit_featuregroup(featuregroup_name, featuregroup_dict)
        api_response={"result": "Feature Group Edited"}
        response_code =status.HTTP_200_OK
        # TODO: Implement the process where DME edits from the dashboard are applied to the endpoint
        if featuregroup.enable_dme == True :
            response= create_dme_filtered_data_job(tm_conf_obj, featuregroup.source_name, featuregroup.feature_list, featuregroup.featuregroup_name,
                                                   featuregroup.host, featuregroup.port, 
                                                   featuregroup.measured_obj_class)
            if response.status_code != 201:
                api_response={"Exception": "Cannot create dme job"}
                delete_feature_group_by_name(featuregroup)
                response_code=status.HTTP_400_BAD_REQUEST
    except ValidationError as err:
        return {"Exception": str(err)}, 400
    except DBException as err:
        return {"Exception": str(err)}, 400
    except Exception as e:
        api_response = {"Exception":str(e)}
        logger.error(str(e))
    
    return api_response, response_code

def get_one_key(dictionary):
    '''
    this function finds any one key from dictionary and return it.
    '''
    only_key = None
    for key in dictionary:
        only_key = key
    return only_key


def get_metrics(trainingjob_name, version, mm_sdk):
    """
    Download metrics from object database and returns metrics as string if metrics presents,
    otherwise returns "No data available" string for <trainingjob_name, version> trainingjob.
    """
    data = None
    try:
        present = mm_sdk.check_object(trainingjob_name, version, "metrics.json")
        if present:
            data = json.dumps(mm_sdk.get_metrics(trainingjob_name, version))
            if data is None:
                raise TMException("Problem while downloading metrics")
        else:
            data = "No data available"
    except Exception as err:
        errmsg = str(err)
        raise TMException ( "Problem while downloading metric" + errmsg)
    return data


# TODO: Remove the fxn since it is not called anywhere
def handle_async_feature_engineering_status_exception_case(lock, dataextraction_job_cache, code,
                                                           message, logger, is_success,
                                                           trainingjob_name, mm_sdk):
    """
    This function changes IN_PROGRESS state to FAILED state and calls response_for_training function
    and remove trainingjob_name from dataextraction_job_cache.
    """
    try:
        change_in_progress_to_failed_by_latest_version(trainingjob_name)
        response_for_training(code, message, logger, is_success, trainingjob_name, mm_sdk)
    except Exception as err:
        logger.error("Failed in handle_async_feature_engineering_status_exception_case" + str(err))
    finally:
        #Post success/failure handle,process next item from DATAEXTRACTION_JOBS_CACHE
        with lock:
            try:
                dataextraction_job_cache.pop(trainingjob_name)
            except KeyError as key_err:
                logger.error("The training job key doesn't exist in DATAEXTRACTION_JOBS_CACHE: " + str(key_err))
    

def check_trainingjob_name_and_version(trainingjob_name, version):
    if (re.fullmatch(PATTERN, trainingjob_name) and version.isnumeric()):
        return True
    return False

def check_trainingjob_name_or_featuregroup_name(name):
    if re.fullmatch(PATTERN, name):
        return True
    return False    