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
import json
from flask_api import status
import requests
from trainingmgr.db.common_db_fun import change_in_progress_to_failed_by_latest_version, \
    get_field_by_latest_version, change_field_of_latest_version, \
    get_latest_version_trainingjob_name,get_all_versions_info_by_name

from trainingmgr.constants.states import States
from trainingmgr.common.exceptions_utls import APIException,TMException,DBException

def response_for_training(code, message, logger, is_success, trainingjob_name, ps_db_obj, mm_sdk):
    """
    Post training job completion,this function provides notifications to the subscribers, 
    who subscribed for the result of training job and provided a notification url during 
    training job creation.
    returns tuple containing result dictionary and status code.
    """
    logger.debug("Training job result: " + str(code) + " " + message + " " + str(is_success))
    
    try :
        notif_url_result = get_field_by_latest_version(trainingjob_name, ps_db_obj, "notification_url")
        if notif_url_result :
            notification_url = notif_url_result[0][0]
            model_url_result = None
            if notification_url != '':
                model_url_result = get_field_by_latest_version(trainingjob_name, ps_db_obj, "model_url")
                model_url = model_url_result[0][0]
                version = get_latest_version_trainingjob_name(trainingjob_name, ps_db_obj)
                metrics = get_metrics(trainingjob_name, version, mm_sdk)

                req_json = None
                if is_success:
                    req_json = {
                        "result": "success", "model_url": model_url,
                        "trainingjob_name": trainingjob_name, "metrics": metrics
                    }
                else:
                    req_json = {"result": "failed", "trainingjob_name": trainingjob_name}
            
                response = requests.post(notification_url,
                        data=json.dumps(req_json),
                        headers={
                            'content-type': 'application/json',
                            'Accept-Charset': 'UTF-8'
                        })
                if ( response.headers['content-type'] != "application/json" 
                        or response.status_code != status.HTTP_200_OK ):
                    err_msg = "Failed to notify the subscribed url " + trainingjob_name
                    raise TMException(err_msg)
    except Exception as err:
        change_in_progress_to_failed_by_latest_version(trainingjob_name, ps_db_obj)
        raise APIException(status.HTTP_500_INTERNAL_SERVER_ERROR,
                            str(err) + "(trainingjob name is " + trainingjob_name + ")") from None
    if is_success:
        return {"result": message}, code
    return {"Exception": message}, code


def check_key_in_dictionary(fields, dictionary):
    '''
    This function raises exception if any string from fields list does not present in a dictionary
    as a key
    '''
    isKeyAvailable = True
    for field_name in fields:
        if field_name not in dictionary:
            isKeyAvailable = False
            break
            #Log (field_name + " not provide")
    return isKeyAvailable

def get_one_word_status(steps_state):
    """
    This function converts steps_state to one word status(we call it overall_status also)
    and return it.
    """
    failed_count = 0
    finished_count = 0
    not_started_count = 0
    in_progress_count = 0
    for step in steps_state:
        if steps_state[step] == States.FAILED.name:
            failed_count = failed_count + 1
        elif steps_state[step] == States.FINISHED.name:
            finished_count = finished_count + 1
        elif steps_state[step] == States.NOT_STARTED.name:
            not_started_count = not_started_count + 1
        else:
            in_progress_count = in_progress_count + 1
    if failed_count > 0:
        return States.FAILED.name
    if not_started_count == len(steps_state):
        return States.NOT_STARTED.name
    if finished_count == len(steps_state):
        return States.FINISHED.name
    return States.IN_PROGRESS.name


def check_trainingjob_data(trainingjob_name, json_data):
    """
    This function checks validation for json_data dictionary and return tuple which conatins
    values of different keys in jsn_data.
    """
    try:
        if check_key_in_dictionary(["feature_list", "pipeline_version", \
                                 "pipeline_name", "experiment_name",
                                 "arguments", "enable_versioning",
                                 "datalake_source", "description",
                                 "query_filter", "_measurement",
                                 "bucket"], json_data):

            description = json_data["description"]
            feature_list = json_data["feature_list"]
            pipeline_name = json_data["pipeline_name"]
            experiment_name = json_data["experiment_name"]
            arguments = json_data["arguments"]

            if not isinstance(arguments, dict):
                raise TMException("Please pass agruments as dictionary for " + trainingjob_name)
            query_filter = json_data["query_filter"]
            enable_versioning = json_data["enable_versioning"]
            pipeline_version = json_data["pipeline_version"]
            datalake_source = json_data["datalake_source"]
            _measurement = json_data["_measurement"]
            bucket = json_data["bucket"]
        else :
            raise TMException("check_trainingjob_data- supplied data doesn't have" + \
                                "all the required fields ")
    except Exception as err:
        raise APIException(status.HTTP_400_BAD_REQUEST,
                           str(err)) from None
    return (feature_list, description, pipeline_name, experiment_name,
            arguments, query_filter, enable_versioning, pipeline_version,
            datalake_source, _measurement, bucket)


def get_one_key(dictionary):
    '''
    this function finds any one key from dictionary and retuen it.
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
                raise Exception("Problem while downloading metrics")
        else:
            data = "No data available"
    except Exception as err:
        errMsg = str(err)
        raise TMException ( "Problem while downloading metric" + errMsg)
    return data


def handle_async_feature_engineering_status_exception_case(lock, dataextraction_job_cache, code,
                                                           message, logger, is_success,
                                                           trainingjob_name, ps_db_obj, mm_sdk):
    """
    This function changes IN_PROGRESS state to FAILED state and calls response_for_training function
    and remove trainingjob_name from dataextraction_job_cache.
    """
    try:
        change_in_progress_to_failed_by_latest_version(trainingjob_name, ps_db_obj)
        response_for_training(code, message, logger, is_success, trainingjob_name, ps_db_obj, mm_sdk)
    except Exception as err:
        logger.error("Failed in handle_async_feature_engineering_status_exception_case" + str(err))
    finally:
        #Post success/failure handle,process next item from DATAEXTRACTION_JOBS_CACHE
        with lock:
            try:
                dataextraction_job_cache.pop(trainingjob_name)
            except KeyError as key_err:
                logger.error("The training job key doesn't exist in DATAEXTRACTION_JOBS_CACHE: " + str(key_err))

def validate_trainingjob_name(trainingjob_name, ps_db_obj):
    """
    This function returns True if given trainingjob_name exists in db otherwise
    it returns False.
    """
    results = None
    isAvailable = False
    try:
        results = get_all_versions_info_by_name(trainingjob_name, ps_db_obj)
    except Exception as err:
        errMsg = str(err)
        raise DBException("Could not get info from db for " + trainingjob_name + "," + errMsg)
    if results:
        isAvailable = True
    return isAvailable    
