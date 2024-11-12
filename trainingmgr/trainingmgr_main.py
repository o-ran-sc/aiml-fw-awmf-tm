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
This file contains all rest endpoints exposed by Training manager.
"""
import json
import re
from logging import Logger
import os
import traceback
import threading
from threading import Lock
import time
from flask import Flask, request, send_file
from flask_api import status
from flask_migrate import Migrate
from marshmallow import ValidationError
import requests
from flask_cors import CORS
from werkzeug.utils import secure_filename
from modelmetricsdk.model_metrics_sdk import ModelMetricsSdk
from trainingmgr.common.trainingmgr_operations import data_extraction_start, training_start, data_extraction_status, create_dme_filtered_data_job, delete_dme_filtered_data_job, \
    get_model_info
from trainingmgr.common.trainingmgr_config import TrainingMgrConfig
from trainingmgr.common.trainingmgr_util import get_one_word_status, check_trainingjob_data, \
    check_key_in_dictionary, get_one_key, \
    response_for_training, get_metrics, \
    handle_async_feature_engineering_status_exception_case, \
    validate_trainingjob_name, get_pipelines_details, check_feature_group_data, check_trainingjob_name_and_version, check_trainingjob_name_or_featuregroup_name, \
    get_feature_group_by_name, edit_feature_group_by_name, fetch_pipeline_info_by_name
from trainingmgr.common.exceptions_utls import APIException,TMException
from trainingmgr.constants.steps import Steps
from trainingmgr.constants.states import States
from trainingmgr.db.trainingmgr_ps_db import PSDB
from trainingmgr.common.exceptions_utls import DBException
from trainingmgr.db.common_db_fun import get_data_extraction_in_progress_trainingjobs
from trainingmgr.models import db, TrainingJob, FeatureGroup
from trainingmgr.schemas import ma, TrainingJobSchema , FeatureGroupSchema
from trainingmgr.db.featuregroup_db import add_featuregroup, edit_featuregroup, get_feature_groups_db, \
    get_feature_group_by_name_db, delete_feature_group_by_name
from trainingmgr.db.trainingjob_db import add_update_trainingjob, get_trainingjob_info_by_name, \
    get_all_jobs_latest_status_version, change_steps_state_of_latest_version, get_info_by_version, \
    get_steps_state_db, change_field_of_latest_version, get_latest_version_trainingjob_name, get_info_of_latest_version, \
    change_field_value_by_version, delete_trainingjob_version, change_in_progress_to_failed_by_latest_version, \
        update_model_download_url, get_all_versions_info_by_name
from trainingmgr.common.trainingConfig_parser import validateTrainingConfig, getField

APP = Flask(__name__)

from middleware.loggingMiddleware import LoggingMiddleware
APP.wsgi_app = LoggingMiddleware(APP.wsgi_app)
TRAININGMGR_CONFIG_OBJ = None
PS_DB_OBJ = None
LOGGER = None
MM_SDK = None
LOCK = None
DATAEXTRACTION_JOBS_CACHE = None

ERROR_TYPE_KF_ADAPTER_JSON = "Kf adapter doesn't sends json type response"
ERROR_TYPE_DB_STATUS = "Couldn't update the status as failed in db access"
MIMETYPE_JSON = "application/json"
NOT_LIST="not given as list"

trainingjob_schema = TrainingJobSchema()
trainingjobs_schema = TrainingJobSchema(many=True)


@APP.errorhandler(APIException)
def error(err):
    """
    Return response with error message and error status code.
    """
    LOGGER.error(err.message)
    return APP.response_class(response=json.dumps({"Exception": err.message}),
                              status=err.code,
                              mimetype=MIMETYPE_JSON)

# Training-Config Handled
@APP.route('/trainingjobs/<trainingjob_name>/<version>', methods=['GET'])
def get_trainingjob_by_name_version(trainingjob_name, version):
    """
    Rest endpoint to fetch training job details by name and version
    <trainingjob_name, version>.

    Args in function:
        trainingjob_name: str
            name of trainingjob.
        version: int
            version of trainingjob.

    Returns:
        json:
            trainingjob: dict
                     dictionary contains
                         trainingjob_name: str
                             name of trainingjob
                         description: str
                             description
                         featuregroup name: str
                             featuregroup name
                         pipeline_name: str
                             name of pipeline
                         experiment_name: str
                             name of experiment
                         arguments: dict
                             key-value pairs related to hyper parameters and
                             "trainingjob":<trainingjob_name> key-value pair
                         query_filter: str
                             string indication sql where clause for filtering out features
                         creation_time: str
                             time at which <trainingjob_name, version> trainingjob is created
                         run_id: str
                             run id from KF adapter for <trainingjob_name, version> trainingjob
                         steps_state: dict
                             <trainingjob_name, version> trainingjob's each steps and corresponding state
                         accuracy: str
                             metrics of model
                         enable_versioning: bool
                             flag for trainingjob versioning
                         updation_time: str
                             time at which <trainingjob_name, version> trainingjob is updated.
                         version: int
                             trainingjob's version
                         pipeline_version: str
                             pipeline version
                        datalake_source: str
                             string indicating datalake source
                        model_url: str
                             url for downloading model
                        notification_url: str
                             url of notification server
                        is_mme: boolean
                            whether the mme is enabled
                        model_name: str
                            model name 
                        model_info: str
                            model info provided by the mme
        status code:
            HTTP status code 200

    Exceptions:
        all exception are provided with exception message and HTTP status code.

    """
    response_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    response_data = {}
    if not check_trainingjob_name_and_version(trainingjob_name, version):
        return {"Exception":"The trainingjob_name or version is not correct"}, status.HTTP_400_BAD_REQUEST
    
    LOGGER.debug("Request to fetch trainingjob by name and version(trainingjob:" + \
                trainingjob_name + " ,version:" + version + ")")
    response_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    response_data = {}
    try:
        trainingjob = get_info_by_version(trainingjob_name, version)
        data = get_metrics(trainingjob_name, version, MM_SDK)
        if trainingjob:
            dict_data = {
                "trainingjob_name": trainingjob.trainingjob_name,
                "training_config": json.loads(trainingjob.training_config),
                # "description": trainingjob.description,
                # "feature_list": trainingjob.feature_group_name,
                # "pipeline_name": trainingjob.pipeline_name,
                # "experiment_name": trainingjob.experiment_name,
                # "arguments": trainingjob.arguments,
                # "query_filter": trainingjob.query_filter,
                "creation_time": str(trainingjob.creation_time),
                "run_id": trainingjob.run_id,
                "steps_state": json.loads(trainingjob.steps_state),
                "updation_time": str(trainingjob.updation_time),
                "version": trainingjob.version,
                # "enable_versioning": trainingjob.enable_versioning,
                # "pipeline_version": trainingjob.pipeline_version,
                # "datalake_source": get_one_key(json.loads(trainingjob.datalake_source)['datalake_source']),
                "model_url": trainingjob.model_url,
                "notification_url": trainingjob.notification_url,
                # "is_mme": trainingjob.is_mme, 
                "model_name": trainingjob.model_name,
                "model_info": trainingjob.model_info,
                "accuracy": data
            }
            response_data = {"trainingjob": dict_data}
            response_code = status.HTTP_200_OK
        else:
            # no need to change status here because given trainingjob_name,version not found in postgres db.
            response_code = status.HTTP_404_NOT_FOUND
            raise TMException("Not found given trainingjob with version(trainingjob:" + \
                            trainingjob_name + " version: " + version + ") in database")
    except Exception as err:
        LOGGER.error(str(err))
        response_data = {"Exception": str(err)}
        
    return APP.response_class(response=json.dumps(response_data),
                                        status=response_code,
                                        mimetype=MIMETYPE_JSON)

# Training-Config Handled (No Change)
@APP.route('/trainingjobs/<trainingjob_name>/<version>/steps_state', methods=['GET']) 
def get_steps_state(trainingjob_name, version):
    """
    Function handling rest end points to get steps_state information for
    given <trainingjob_name, version>.

    Args in function:
        trainingjob_name: str
            name of trainingjob.
        version: int
            version of trainingjob.

    Args in json:
        not required json

    Returns:
        json:
            DATA_EXTRACTION : str
                this step captures part
                    starting: immediately after quick success response by data extraction module
                    till: ending of data extraction.
            DATA_EXTRACTION_AND_TRAINING : str
                this step captures part
                    starting: immediately after DATA_EXTRACTION is FINISHED
                    till: getting 'scheduled' run status from kf connector
            TRAINING : str
                this step captures part
                    starting: immediately after DATA_EXTRACTION_AND_TRAINING is FINISHED
                    till: getting 'Succeeded' run status from kf connector
            TRAINING_AND_TRAINED_MODEL : str
                this step captures part
                    starting: immediately after TRAINING is FINISHED
                    till: getting version for trainingjob_name trainingjob.
            TRAINED_MODEL : str
                this step captures part
                    starting: immediately after TRAINING_AND_TRAINED_MODEL is FINISHED
                    till: model download url is updated in db.
        status code:
            HTTP status code 200

    Exceptions:
        all exception are provided with exception message and HTTP status code.
    """
    response_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    response_data = {}
    if not check_trainingjob_name_and_version(trainingjob_name, version):
        return {"Exception":"The trainingjob_name or version is not correct"}, status.HTTP_400_BAD_REQUEST

    LOGGER.debug("Request to get steps_state for (trainingjob:" + \
                trainingjob_name + " and version: " + version + ")")
    try:
        steps_state = get_steps_state_db(trainingjob_name, version)
        LOGGER.debug("get_field_of_given_version:" + str(steps_state))
        if steps_state:
            response_data = steps_state
            response_code = status.HTTP_200_OK
        else:
            
            response_code = status.HTTP_404_NOT_FOUND
            raise TMException("Not found given trainingjob in database")
    except Exception as err:
        LOGGER.error(str(err))
        response_data = {"Exception": str(err)}

    return APP.response_class(response=json.dumps(response_data),
                                      status=response_code,
                                      mimetype=MIMETYPE_JSON)

# Training-Config Handled (No Change)
@APP.route('/model/<trainingjob_name>/<version>/Model.zip', methods=['GET'])
def get_model(trainingjob_name, version):
    """
    Function handling rest endpoint to download model zip file of <trainingjob_name, version> trainingjob.

    Args in function:
        trainingjob_name: str
            name of trainingjob.
        version: int
            version of trainingjob.

    Args in json:
        not required json

    Returns:
        zip file of model of <trainingjob_name, version> trainingjob.

    Exceptions:
        all exception are provided with exception message and HTTP status code.
    """
    if not check_trainingjob_name_and_version(trainingjob_name, version):
        return {"Exception":"The trainingjob_name or version is not correct"}, status.HTTP_400_BAD_REQUEST

    try:
        return send_file(MM_SDK.get_model_zip(trainingjob_name, version), mimetype='application/zip')
    except Exception:
        return {"Exception": "error while downloading model"}, status.HTTP_500_INTERNAL_SERVER_ERROR

# Training-Config Handled
@APP.route('/trainingjobs/<trainingjob_name>/training', methods=['POST'])
def training(trainingjob_name):
    """
    Rest end point to start training job.
    It calls data extraction module for data extraction and other training steps

    Args in function:
        trainingjob_name: str
            name of trainingjob.

    Args in json:
        not required json

    Returns:
        json:
            trainingjob_name: str
                name of trainingjob
            result: str
                route of data extraction module for getting data extraction status of
                given trainingjob_name .
        status code:
            HTTP status code 200

    Exceptions:
        all exception are provided with exception message and HTTP status code.
    """
    response_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    response_data = {}
    if not check_trainingjob_name_or_featuregroup_name(trainingjob_name):
        return {"Exception":"The trainingjob_name is not correct"}, status.HTTP_400_BAD_REQUEST
    LOGGER.debug("Request for training trainingjob  %s ", trainingjob_name)
    try:
        isDataAvaible = validate_trainingjob_name(trainingjob_name)
        if not isDataAvaible:
            response_code = status.HTTP_404_NOT_FOUND
            raise TMException("Given trainingjob name is not present in database" + \
                        "(trainingjob: " + trainingjob_name + ")") from None
        else:

            trainingjob = get_trainingjob_info_by_name(trainingjob_name) 
            
            featuregroup= get_feature_group_by_name_db(getField(trainingjob.training_config, "feature_group_name"))
            feature_list_string = featuregroup.feature_list
            influxdb_info_dic={}
            influxdb_info_dic["host"]=featuregroup.host
            influxdb_info_dic["port"]=featuregroup.port
            influxdb_info_dic["bucket"]=featuregroup.bucket
            influxdb_info_dic["token"]=featuregroup.token
            influxdb_info_dic["db_org"] = featuregroup.db_org
            influxdb_info_dic["source_name"]= featuregroup.source_name
            _measurement = featuregroup.measurement
            query_filter = getField(trainingjob.training_config, "query_filter")
            datalake_source = {featuregroup.datalake_source: {}} # Datalake source should be taken from FeatureGroup (not TrainingJob)
            LOGGER.debug('Starting Data Extraction...')
            de_response = data_extraction_start(TRAININGMGR_CONFIG_OBJ, trainingjob_name,
                                         feature_list_string, query_filter, datalake_source,
                                         _measurement, influxdb_info_dic)
            if (de_response.status_code == status.HTTP_200_OK ):
                LOGGER.debug("Response from data extraction for " + \
                        trainingjob_name + " : " + json.dumps(de_response.json()))
                change_steps_state_of_latest_version(trainingjob_name,
                                                    Steps.DATA_EXTRACTION.name,
                                                    States.IN_PROGRESS.name)
                with LOCK:
                    DATAEXTRACTION_JOBS_CACHE[trainingjob_name] = "Scheduled"
                response_data = de_response.json()
                response_code = status.HTTP_200_OK
            elif( de_response.headers['content-type'] == MIMETYPE_JSON ) :
                errMsg = "Data extraction responded with error code."
                LOGGER.error(errMsg)
                json_data = de_response.json()
                LOGGER.debug(str(json_data))
                if check_key_in_dictionary(["result"], json_data):
                    response_data = {"Failed":errMsg + json_data["result"]}
                else:
                    raise TMException(errMsg)
            else:
                raise TMException("Data extraction doesn't send json type response" + \
                        "(trainingjob name is " + trainingjob_name + ")") from None
    except Exception as err:
        # print(traceback.format_exc())
        response_data =  {"Exception": str(err)}
        LOGGER.debug("Error is training, job name:" + trainingjob_name + str(err))         
    return APP.response_class(response=json.dumps(response_data),status=response_code,
                            mimetype=MIMETYPE_JSON)

# Training-Config Handled
@APP.route('/trainingjob/dataExtractionNotification', methods=['POST'])
def data_extraction_notification():
    """
    This rest endpoint will be invoked when data extraction is finished.
    It will further invoke kf-adapter for training, if the response from kf-adapter run_status is "scheduled",
    that means request is accepted by kf-adapter for futher processing.

    Args in function:
        None

    Args in json:
        trainingjob_name: str
            name of trainingjob.

    Returns:
        json:
            result: str
                result message
        status code:
            HTTP status code 200

    Exceptions:
        all exception are provided with exception message and HTTP status code.
    """
    LOGGER.debug("Data extraction notification...")
    err_response_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    results = None
    try:
        if not check_key_in_dictionary(["trainingjob_name"], request.json) :
            err_msg = "Trainingjob_name key not available in request"
            LOGGER.error(err_msg)
            return {"Exception":err_msg}, status.HTTP_400_BAD_REQUEST
            
        trainingjob_name = request.json["trainingjob_name"]
        trainingjob = get_trainingjob_info_by_name(trainingjob_name)
        arguments = getField(trainingjob.training_config, "arguments")
        arguments["version"] = trainingjob.version
        # Arguments values must be of type string
        for key, val in arguments.items():
            if not isinstance(val, str):
                arguments[key] = str(val)
        LOGGER.debug(arguments)
        # Experiment name is harded to be Default
        dict_data = {
            "pipeline_name": getField(trainingjob.training_config, "pipeline_name"), "experiment_name": 'Default',
            "arguments": arguments, "pipeline_version": getField(trainingjob.training_config, "pipeline_version")
        }

        response = training_start(TRAININGMGR_CONFIG_OBJ, dict_data, trainingjob_name)
        if ( response.headers['content-type'] != MIMETYPE_JSON 
                or response.status_code != status.HTTP_200_OK ):
            err_msg = "Kf adapter invalid content-type or status_code for " + trainingjob_name
            raise TMException(err_msg)

        LOGGER.debug("response from kf_adapter for " + \
                    trainingjob_name + " : " + json.dumps(response.json()))
        json_data = response.json()
        
        if not check_key_in_dictionary(["run_status", "run_id"], json_data):
            err_msg = "Kf adapter invalid response from , key not present ,run_status or  run_id for " + trainingjob_name
            Logger.error(err_msg)
            err_response_code = status.HTTP_400_BAD_REQUEST
            raise TMException(err_msg)

        if json_data["run_status"] == 'scheduled':
            change_steps_state_of_latest_version(trainingjob_name,
                                                Steps.DATA_EXTRACTION_AND_TRAINING.name,
                                                States.FINISHED.name)
            change_steps_state_of_latest_version(trainingjob_name,
                                                Steps.TRAINING.name,
                                                States.IN_PROGRESS.name)
            change_field_of_latest_version(trainingjob_name,
                                        "run_id", json_data["run_id"])
        else:
            raise TMException("KF Adapter- run_status in not scheduled")
    except requests.exceptions.ConnectionError as err:
        err_msg = "Failed to connect KF adapter."
        LOGGER.error(err_msg)
        if not change_in_progress_to_failed_by_latest_version(trainingjob_name) :
            LOGGER.error(ERROR_TYPE_DB_STATUS)
        return response_for_training(err_response_code,
                                        err_msg + str(err) + "(trainingjob name is " + trainingjob_name + ")",
                                        LOGGER, False, trainingjob_name, MM_SDK)

    except Exception as err:
        LOGGER.error("Failed to handle dataExtractionNotification. " + str(err))
        if not change_in_progress_to_failed_by_latest_version(trainingjob_name) :
            LOGGER.error(ERROR_TYPE_DB_STATUS)
        return response_for_training(err_response_code,
                                        str(err) + "(trainingjob name is " + trainingjob_name + ")",
                                        LOGGER, False, trainingjob_name, MM_SDK)

    return APP.response_class(response=json.dumps({"result": "pipeline is scheduled"}),
                                    status=status.HTTP_200_OK,
                                    mimetype=MIMETYPE_JSON)

# Training-Config Handled (No Change)
@APP.route('/pipelines/<pipe_name>', methods=['GET'])
def get_pipeline_info_by_name(pipe_name):
    """
    Function handling rest endpoint to get information about a specific pipeline.
    Args in function:
        pipe_name : str
            name of pipeline.
    Args in json:
        no json required
    Returns:
        json:
            pipeline_info : dict
                            Dictionary containing detailed information about the specified pipeline.
        status code:
            HTTP status code 200 if successful, 404 if pipeline not found, or 500 for server errors.
    Exceptions:
        all exceptions are provided with exception message and HTTP status code.
    """
    api_response = {}
    LOGGER.debug(f"Request to get information for pipeline: {pipe_name}")
    response_code = status.HTTP_500_INTERNAL_SERVER_ERROR

    try:
        pipeline_info = fetch_pipeline_info_by_name(TRAININGMGR_CONFIG_OBJ, pipe_name)
        if pipeline_info:
            api_response = {"pipeline_info":pipeline_info}
            response_code = status.HTTP_200_OK
        else:
            api_response = {"error": f"Pipeline '{pipe_name}' not found"}
            response_code = status.HTTP_404_NOT_FOUND

    except TMException as err:
        api_response = {"error": str(err)}
        response_code = status.HTTP_404_NOT_FOUND
        LOGGER.error(f"TrainingManager exception: {str(err)}")
    except Exception as err:
        api_response = {"error": "An unexpected error occurred"}
        LOGGER.error(f"Unexpected error in get_pipeline_info: {str(err)}")

    return APP.response_class(response=json.dumps(api_response),
                              status=response_code,
                              mimetype=MIMETYPE_JSON)

# Training-Config Handled ..
@APP.route('/trainingjob/pipelineNotification', methods=['POST'])
def pipeline_notification():
    """
    Function handling rest endpoint to get notification from kf_adapter and set model download
    url in database(if it presents in model db).

    Args in function: none

    Required Args in json:
        trainingjob_name: str
            name of trainingjob.

        run_status: str
            status of run.

    Returns:
        json:
            result: str
                result message
        status:
            HTTP status code 200

    Exceptions:
        all exception are provided with exception message and HTTP status code.
    """

    LOGGER.debug("Pipeline Notification response from kf_adapter: %s", json.dumps(request.json))
    try:
        check_key_in_dictionary(["trainingjob_name", "run_status"], request.json)
        trainingjob_name = request.json["trainingjob_name"]
        run_status = request.json["run_status"]

        if run_status == 'SUCCEEDED':
            change_steps_state_of_latest_version(trainingjob_name,
                                                    Steps.TRAINING.name,
                                                    States.FINISHED.name)
            change_steps_state_of_latest_version(trainingjob_name,
                                                    Steps.TRAINING_AND_TRAINED_MODEL.name,
                                                    States.IN_PROGRESS.name)
                   
            version = get_latest_version_trainingjob_name(trainingjob_name)
            change_steps_state_of_latest_version(trainingjob_name,
                                                    Steps.TRAINING_AND_TRAINED_MODEL.name,
                                                    States.FINISHED.name)
            change_steps_state_of_latest_version(trainingjob_name,
                                                    Steps.TRAINED_MODEL.name,
                                                    States.IN_PROGRESS.name)
                                                    
            if MM_SDK.check_object(trainingjob_name, version, "Model.zip"):
                model_url = "http://" + str(TRAININGMGR_CONFIG_OBJ.my_ip) + ":" + \
                            str(TRAININGMGR_CONFIG_OBJ.my_port) + "/model/" + \
                            trainingjob_name + "/" + str(version) + "/Model.zip"

                update_model_download_url(trainingjob_name, version, model_url, PS_DB_OBJ)

                
                change_steps_state_of_latest_version(trainingjob_name,
                                                        Steps.TRAINED_MODEL.name,
                                                        States.FINISHED.name)
                # upload to the mme
                trainingjob_info=get_trainingjob_info_by_name(trainingjob_name)

                is_mme = getField(trainingjob_info.training_config, "is_mme")
                if is_mme:   
                    model_name=trainingjob_info.model_name #model_name
                    file=MM_SDK.get_model_zip(trainingjob_name, str(version))
                    url ="http://"+str(TRAININGMGR_CONFIG_OBJ.model_management_service_ip)+":"+str(TRAININGMGR_CONFIG_OBJ.model_management_service_port)+"/uploadModel/{}".format(model_name)
                    LOGGER.debug("url for upload is: ", url)
                    resp2=requests.post(url=url, files={"file":('Model.zip', file, 'application/zip')})
                    if resp2.status_code != status.HTTP_200_OK :
                        errMsg= "Upload to mme failed"
                        LOGGER.error(errMsg + trainingjob_name)
                        raise TMException(errMsg + trainingjob_name)
                    
                    LOGGER.debug("Model uploaded to the MME")
            else:
                errMsg = "Trained model is not available  "
                LOGGER.error(errMsg + trainingjob_name)
                raise TMException(errMsg + trainingjob_name)
        else:
            LOGGER.error("Pipeline notification -Training failed " + trainingjob_name)    
            raise TMException("Pipeline not successful for " + \
                                        trainingjob_name + \
                                        ",request json from kf adapter is: " + json.dumps(request.json))      
    except Exception as err:
        #Training failure response
        LOGGER.error("Pipeline notification failed" + str(err))
        if not change_in_progress_to_failed_by_latest_version(trainingjob_name) :
            LOGGER.error(ERROR_TYPE_DB_STATUS)
        
        return response_for_training(status.HTTP_500_INTERNAL_SERVER_ERROR,
                            str(err) + " (trainingjob " + trainingjob_name + ")",
                            LOGGER, False, trainingjob_name, MM_SDK)
    #Training success response
    return response_for_training(status.HTTP_200_OK,
                                            "Pipeline notification success.",
                                            LOGGER, True, trainingjob_name, MM_SDK)

# Training-Config Handled (No Change)
@APP.route('/trainingjobs/latest', methods=['GET'])
def trainingjobs_operations():
    """
    Rest endpoint to fetch overall status, latest version of all existing training jobs

    Args in function: none
    Required Args in json:
        no json required

    Returns:
        json:
            trainingjobs : list
                       list of dictionaries.
                           dictionary contains
                               trainingjob_name: str
                                   name of trainingjob
                               version: int
                                   trainingjob version
                               overall_status: str
                                   overall status of end to end flow
        status:
            HTTP status code 200

    Exceptions:
        all exception are provided with exception message and HTTP status code.
    """
    LOGGER.debug("Request for getting all trainingjobs with latest version and status.")
    api_response = {}
    response_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    try:
        results = get_all_jobs_latest_status_version()
        trainingjobs = []
        for res in results:
            dict_data = {
                "trainingjob_name": res.trainingjob_name,
                "version": res.version,
                "overall_status": get_one_word_status(json.loads(res.steps_state))
            }
            trainingjobs.append(dict_data)
        api_response = {"trainingjobs": trainingjobs}
        response_code = status.HTTP_200_OK
    except Exception as err:
        api_response =   {"Exception": str(err)}
        LOGGER.error(str(err))
    return APP.response_class(response=json.dumps(api_response),
                        status=response_code,
                        mimetype=MIMETYPE_JSON)

# Training-Config Handled (No Change) ..
@APP.route("/pipelines/<pipe_name>/upload", methods=['POST'])
def upload_pipeline(pipe_name):
    """
    Function handling rest endpoint to upload pipeline.

    Args in function:
        pipe_name: str
            name of pipeline

    Args in json:
        no json required

    but file is required

    Returns:
        json:
            result: str
                result message
        status code:
            HTTP status code 200

    Exceptions:
        all exception are provided with exception message and HTTP status code.
    """
    LOGGER.debug("Request to upload pipeline.")
    result_string = None
    result_code = None
    uploaded_file_path = None
    try:
        LOGGER.debug(str(request))
        LOGGER.debug(str(request.files))
        if 'file' in request.files:
            uploaded_file = request.files['file']
        else:
            result_string = "Didn't get file"
            raise ValueError("file not found in request.files")

        if not check_trainingjob_name_or_featuregroup_name(pipe_name):
            err_msg="the pipeline name is not valid"
            raise TMException(err_msg)
        LOGGER.debug("Uploading received for %s", uploaded_file.filename)
        if uploaded_file.filename != '':
            uploaded_file_path = "/tmp/" + secure_filename(uploaded_file.filename)
            uploaded_file.save(uploaded_file_path)
            LOGGER.debug("File uploaded :%s", uploaded_file_path)
            kf_adapter_ip = TRAININGMGR_CONFIG_OBJ.kf_adapter_ip
            kf_adapter_port = TRAININGMGR_CONFIG_OBJ.kf_adapter_port
            if kf_adapter_ip!=None and kf_adapter_port!=None:
               url = 'http://' + str(kf_adapter_ip) + ':' + str(kf_adapter_port) + \
                  '/pipelineIds/' + pipe_name

            description = ''
            if 'description' in request.form:
                description = request.form['description']
            if uploaded_file_path != None:     
                with open(uploaded_file_path, 'rb') as file:
                    files = {'file': file.read()}

            resp = requests.post(url, files=files, data={"description": description})
            LOGGER.debug(resp.text)
            if resp.status_code == status.HTTP_200_OK:
                LOGGER.debug("Pipeline uploaded :%s", pipe_name)
                result_string = "Pipeline uploaded " + pipe_name
                result_code = status.HTTP_200_OK
            else:
                LOGGER.error(resp.json()["message"])
                result_string = resp.json()["message"]
                result_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        else:
            result_string = "File name not found"
            raise ValueError("filename is not found in request.files")
    except ValueError:
        tbk = traceback.format_exc()
        LOGGER.error(tbk)
        result_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        result_string = "Error while uploading pipeline"
    except TMException:
        tbk = traceback.format_exc()
        LOGGER.error(tbk)
        result_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        result_string = "Pipeline name is not of valid format"
    except Exception:
        tbk = traceback.format_exc()
        LOGGER.error(tbk)
        result_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        result_string = "Error while uploading pipeline cause"

    if uploaded_file_path and os.path.isfile(uploaded_file_path):
        LOGGER.debug("Deleting %s", uploaded_file_path)
        if uploaded_file_path != None:
            os.remove(uploaded_file_path)

    LOGGER.debug("Responding to Client with %d %s", result_code, result_string)
    return APP.response_class(response=json.dumps({'result': result_string}),
                                  status=result_code,
                                  mimetype=MIMETYPE_JSON)


# Training-Config Handled (No Change)
@APP.route("/pipelines/<pipeline_name>/versions", methods=['GET'])
def get_versions_for_pipeline(pipeline_name):
    """
    Function handling rest endpoint to get versions of given pipeline name.

    Args in function:
        pipeline_name : str
            name of pipeline.

    Args in json:
        no json required

    Returns:
        json:
            versions_list : list
                            list containing all versions(as str)
        status code:
            HTTP status code 200

    Exceptions:
        all exception are provided with exception message and HTTP status code.
    """
    valid_pipeline=""
    api_response = {}            
    LOGGER.debug("Request to get all version for given pipeline(" + pipeline_name + ").")
    response_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    try:
        pipelines = get_pipelines_details(TRAININGMGR_CONFIG_OBJ)
        for pipeline in pipelines['pipelines']:
            if pipeline['display_name'] == pipeline_name:
                valid_pipeline = pipeline['display_name']
                break
        if valid_pipeline == "":
            raise TMException("Pipeline name not present")
        kf_adapter_ip = TRAININGMGR_CONFIG_OBJ.kf_adapter_ip
        kf_adapter_port = TRAININGMGR_CONFIG_OBJ.kf_adapter_port
        if kf_adapter_ip!=None and kf_adapter_port!=None :
          url = 'http://' + str(kf_adapter_ip) + ':' + str(
            kf_adapter_port) + '/pipelines/' + valid_pipeline + \
            '/versions'
        LOGGER.debug("URL:" + url)
        response = requests.get(url)
        if response.headers['content-type'] != MIMETYPE_JSON:
            raise TMException(ERROR_TYPE_KF_ADAPTER_JSON)
        api_response = {"versions_list": response.json()['versions_list']}
        response_code = status.HTTP_200_OK
    except Exception as err:
        api_response =  {"Exception": str(err)}
        LOGGER.error(str(err))
    return APP.response_class(response=json.dumps(api_response),
            status=response_code,
            mimetype=MIMETYPE_JSON)
 
# Training-Config Handled (No Change)
@APP.route('/pipelines', methods=['GET'])
def get_pipelines():
    """
    Function handling rest endpoint to get all pipeline names.

    Args in function:
        none

    Args in json:
        no json required

    Returns:
        json:
            pipeline_names : list
                             list containing all pipeline names(as str).
        status code:
            HTTP status code 200

    Exceptions:
        all exception are provided with exception message and HTTP status code.
    """
    LOGGER.debug("Request to get all getting all pipeline names.")
    api_response = {}
    response_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    try:
        pipelines = get_pipelines_details(TRAININGMGR_CONFIG_OBJ)
        api_response = pipelines
        response_code = status.HTTP_200_OK
    except Exception as err:
        LOGGER.error(str(err))
        api_response =  {"Exception": str(err)}
    return APP.response_class(response=json.dumps(api_response),status=response_code,mimetype=MIMETYPE_JSON)

# Training-Config Handled (No Change)
@APP.route('/experiments', methods=['GET'])
def get_all_experiment_names():
    """
    Function handling rest endpoint to get all experiment names.

    Args in function:
        none

    Args in json:
        no json required

    Returns:
        json:
            experiment_names : list
                               list containing all experiment names(as str).
        status code:
            HTTP status code 200

    Exceptions:
        all exception are provided with exception message and HTTP status code.
    """

    LOGGER.debug("request for getting all experiment names is come.")
    api_response = {}
    reponse_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    try:
        kf_adapter_ip = TRAININGMGR_CONFIG_OBJ.kf_adapter_ip
        kf_adapter_port = TRAININGMGR_CONFIG_OBJ.kf_adapter_port
        if kf_adapter_ip!=None and kf_adapter_port!=None: 
            url = 'http://' + str(kf_adapter_ip) + ':' + str(kf_adapter_port) + '/experiments'
        LOGGER.debug("url is :" + url)
        response = requests.get(url)
        if response.headers['content-type'] != MIMETYPE_JSON:
            err_smg = ERROR_TYPE_KF_ADAPTER_JSON
            raise TMException(err_smg)

        experiment_names = []
        for experiment in response.json().keys():
            experiment_names.append(experiment)
        api_response = {"experiment_names": experiment_names}
        reponse_code = status.HTTP_200_OK
    except Exception as err:
        api_response =  {"Exception": str(err)}
        LOGGER.error(str(err))
    return APP.response_class(response=json.dumps(api_response),
                                  status=reponse_code,
                                  mimetype=MIMETYPE_JSON)

# Training-Config handled
@APP.route('/trainingjobs/<trainingjob_name>', methods=['POST', 'PUT'])
def trainingjob_operations(trainingjob_name):
    """
    Rest endpoint to create or update trainingjob
    Precondtion for update : trainingjob's overall_status should be failed
    or finished and deletion processs should not be in progress

    Args in function:
        trainingjob_name: str
            name of trainingjob.

    Args in json:
        if post/put request is called
            json with below fields are given:
                modelName: str
                    Name of model
                trainingConfig: dict
                    Training-Configurations, parameter as follows
                    is_mme: boolean
                        whether mme is enabled
                    description: str
                        description
                    dataPipeline: dict
                        Configurations related to dataPipeline, parameter as follows
                        feature_group_name: str
                            feature group name
                        query_filter: str
                            string indication sql where clause for filtering out features
                        arguments: dict
                            key-value pairs related to hyper parameters and
                            "trainingjob":<trainingjob_name> key-value pair
                    trainingPipeline: dict
                        Configurations related to trainingPipeline, parameter as follows
                        pipeline_name: str
                            name of pipeline
                        pipeline_version: str
                            pipeline version
                        enable_versioning: bool
                            flag for trainingjob versioning 
                
    Returns:
        1. For post request
            json:
                result : str
                    result message
                status code:
                    HTTP status code 201
        2. For put request
            json:
                result : str
                    result message
                status code:
                    HTTP status code 200

    Exceptions:
        All exception are provided with exception message and HTTP status code.
    """
    response_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    api_response = {}
    if not check_trainingjob_name_or_featuregroup_name(trainingjob_name):
        return {"Exception":"The trainingjob_name is not correct"}, status.HTTP_400_BAD_REQUEST
    
    trainingConfig = request.json["training_config"]
    if(not validateTrainingConfig(trainingConfig)):
        return {"Exception":"The TrainingConfig is not correct"}, status.HTTP_400_BAD_REQUEST
    
    LOGGER.debug("Training job create/update request(trainingjob name  %s) ", trainingjob_name )
    try:
        json_data = request.json
        if (request.method == 'POST'):          
            LOGGER.debug("Create request json : " + json.dumps(json_data))
            is_data_available = validate_trainingjob_name(trainingjob_name)
            if is_data_available:
                response_code = status.HTTP_409_CONFLICT
                raise TMException("trainingjob name(" + trainingjob_name + ") is already present in database")
            else:
                processed_json_data = request.get_json()
                processed_json_data['training_config'] = json.dumps(request.get_json()["training_config"])
                trainingjob = trainingjob_schema.load(processed_json_data)
                model_info=""
                if  getField(trainingjob.training_config, "is_mme"):
                    pipeline_dict =json.loads(TRAININGMGR_CONFIG_OBJ.pipeline)
                    model_info=get_model_info(TRAININGMGR_CONFIG_OBJ, trainingjob.model_name)
                    s=model_info["meta-info"]["feature-list"]
                    model_type=model_info["meta-info"]["model-type"]
                    try:
                        pipeline_name=pipeline_dict[str(model_type)]
                    except Exception as err:
                        err="Doesn't support the model type"
                        raise TMException(err)
                    pipeline_version=pipeline_name
                    feature_list=','.join(s)
                    result= get_feature_groups_db(PS_DB_OBJ)
                    for res in result:
                        if feature_list==res[1]:
                            featuregroup_name=res[0]
                            break 
                    if featuregroup_name =="":
                        return {"Exception":"The no feature group with mentioned feature list, create a feature group"}, status.HTTP_406_NOT_ACCEPTABLE
                add_update_trainingjob(trainingjob, True)
                api_response =  {"result": "Information stored in database."}                 
                response_code = status.HTTP_201_CREATED
        elif(request.method == 'PUT'):
            LOGGER.debug("Update request json : " + json.dumps(json_data))
            is_data_available = validate_trainingjob_name(trainingjob_name)
            if not is_data_available:
                response_code = status.HTTP_404_NOT_FOUND
                raise TMException("Trainingjob name(" + trainingjob_name + ") is not  present in database")
            else:
                processed_json_data = request.get_json()
                processed_json_data['training_config'] = json.dumps(request.get_json()["training_config"])
                trainingjob = trainingjob_schema.load(processed_json_data)
                trainingjob_info = get_trainingjob_info_by_name(trainingjob_name)
                if trainingjob_info:
                    if trainingjob_info.deletion_in_progress:
                        raise TMException("Failed to process request for trainingjob(" + trainingjob_name + ") " + \
                                        " deletion in progress")
                    if (get_one_word_status(json.loads(trainingjob_info.steps_state))
                            not in [States.FAILED.name, States.FINISHED.name]):
                        raise TMException("Trainingjob(" + trainingjob_name + ") is not in finished or failed status")

                add_update_trainingjob(trainingjob, False)
                api_response = {"result": "Information updated in database."}
                response_code = status.HTTP_200_OK
    except Exception as err:
        LOGGER.error("Failed to create/update training job, " + str(err) )
        api_response =  {"Exception": str(err)}

    return APP.response_class(response= json.dumps(api_response),
                    status= response_code,
                    mimetype=MIMETYPE_JSON)

# Training-Config Handled (No Change) ..
@APP.route('/trainingjobs/retraining', methods=['POST'])
def retraining():
    """
    Function handling rest endpoint to retrain trainingjobs in request json. trainingjob's
    overall_status should be failed or finished and its deletion_in_progress should be False
    otherwise retraining of that trainingjob is counted in failure.
    Args in function: none
    Required Args in json:
        trainingjobs_list: list
                       list containing dictionaries
                           dictionary contains
                               usecase_name: str
                                   name of trainingjob
                               notification_url(optional): str
                                   url for notification
                               feature_filter(optional): str
                                   feature filter
    Returns:
        json:
            success count: int
                successful retraining count
            failure count: int
                failure retraining count
        status: HTTP status code 200
    Exceptions:
        all exception are provided with exception message and HTTP status code.
    """
    LOGGER.debug('request comes for retraining, ' + json.dumps(request.json))
    try:
        check_key_in_dictionary(["trainingjobs_list"], request.json)
    except Exception as err:
        raise APIException(status.HTTP_400_BAD_REQUEST, str(err)) from None

    trainingjobs_list = request.json['trainingjobs_list']
    if not isinstance(trainingjobs_list, list):
        raise APIException(status.HTTP_400_BAD_REQUEST, NOT_LIST)

    for obj in trainingjobs_list:
        try:
            check_key_in_dictionary(["trainingjob_name"], obj)
        except Exception as err:
            raise APIException(status.HTTP_400_BAD_REQUEST, str(err)) from None

    not_possible_to_retrain = []
    possible_to_retrain = []

    for obj in trainingjobs_list:
        trainingjob_name = obj['trainingjob_name']
        results = None
        try:
            trainingjob = get_info_of_latest_version(trainingjob_name)
        except Exception as err:
            not_possible_to_retrain.append(trainingjob_name)
            LOGGER.debug(str(err) + "(trainingjob_name is " + trainingjob_name + ")")
            continue
        
        if trainingjob:
            if trainingjob.deletion_in_progress:
                not_possible_to_retrain.append(trainingjob_name)
                LOGGER.debug("Failed to retrain because deletion in progress" + \
                             "(trainingjob_name is " + trainingjob_name + ")")
                continue

            if (get_one_word_status(json.loads(trainingjob.steps_state))
                    not in [States.FINISHED.name, States.FAILED.name]):
                not_possible_to_retrain.append(trainingjob_name)
                LOGGER.debug("Not finished or not failed status" + \
                             "(trainingjob_name is " + trainingjob_name + ")")
                continue

            try:
                add_update_trainingjob(trainingjob, False)
            except Exception as err:
                not_possible_to_retrain.append(trainingjob_name)
                LOGGER.debug(str(err) + "(training job is " + trainingjob_name + ")")
                continue

            url = 'http://' + str(TRAININGMGR_CONFIG_OBJ.my_ip) + \
                  ':' + str(TRAININGMGR_CONFIG_OBJ.my_port) + \
                  '/trainingjobs/' +trainingjob_name + '/training'
            response = requests.post(url)

            if response.status_code == status.HTTP_200_OK:
                possible_to_retrain.append(trainingjob_name)
            else:
                LOGGER.debug("not 200 response" + "(trainingjob_name is " + trainingjob_name + ")")
                not_possible_to_retrain.append(trainingjob_name)

        else:
            LOGGER.debug("not present in postgres db" + "(trainingjob_name is " + trainingjob_name + ")")
            not_possible_to_retrain.append(trainingjob_name)

        LOGGER.debug('success list: ' + str(possible_to_retrain))
        LOGGER.debug('failure list: ' + str(not_possible_to_retrain))

    return APP.response_class(response=json.dumps( \
        {
            "success count": len(possible_to_retrain),
            "failure count": len(not_possible_to_retrain)
        }),
        status=status.HTTP_200_OK,
        mimetype='application/json')

# Training-Config Handled (No Change) ..
@APP.route('/trainingjobs', methods=['DELETE'])
def delete_list_of_trainingjob_version():
    """
    Function handling rest endpoint to delete latest version of trainingjob_name trainingjobs which is
    given in request json. trainingjob's overall_status should be failed or finished and its
    deletion_in_progress should be False otherwise deletion of that trainingjobs is counted in failure.
    Args in function: none
    Required Args in json:
        list: list
              list containing dictionaries.
                  dictionary contains
                      trainingjob_name: str
                          trainingjob name
                      version: int
                          version of trainingjob
    Returns:
        json:
            success count: int
                successful deletion count
            failure count: int
                failure deletion count
        status:
            HTTP status code 200
    Exceptions:
        all exception are provided with exception message and HTTP status code.
    """
    LOGGER.debug('request comes for deleting:' + json.dumps(request.json))
    if not check_key_in_dictionary(["list"], request.json):
        raise APIException(status.HTTP_400_BAD_REQUEST, "Wrong Request syntax") from None

    list_of_trainingjob_version = request.json['list']
    if not isinstance(list_of_trainingjob_version, list):
        raise APIException(status.HTTP_400_BAD_REQUEST, NOT_LIST)

    not_possible_to_delete = []
    possible_to_delete = []

    for my_dict in list_of_trainingjob_version:

        if not isinstance(my_dict, dict):
            not_possible_to_delete.append(my_dict)
            LOGGER.debug(str(my_dict) + "did not pass dictionary")
            continue

        if not check_key_in_dictionary(["trainingjob_name", "version"], my_dict):
            not_possible_to_delete.append(my_dict)
            LOGGER.debug("key trainingjob_name or version not in the request")
            continue

        trainingjob_name = my_dict['trainingjob_name']
        version = my_dict['version']

        try:
            trainingjob = get_info_by_version(trainingjob_name, version)
        except Exception as err:
            not_possible_to_delete.append(my_dict)
            LOGGER.debug(str(err) + "(trainingjob_name is " + trainingjob_name + ", version is " + str(
                version) + ")")
            continue

        if trainingjob:

            if trainingjob.deletion_in_progress:
                not_possible_to_delete.append(my_dict)
                LOGGER.debug("Failed to process deletion request because deletion is " + \
                             "already in progress" + \
                             "(trainingjob_name is " + trainingjob_name + ", version is " + str(
                    version) + ")")
                continue

            if (get_one_word_status(json.loads(trainingjob.steps_state))
                    not in [States.FINISHED.name, States.FAILED.name]):
                not_possible_to_delete.append(my_dict)
                LOGGER.debug("Not finished or not failed status" + \
                             "(usecase_name is " + trainingjob_name + ", version is " + str(
                    version) + ")")
                continue

            try:
                change_field_value_by_version(trainingjob_name, version,
                                              "deletion_in_progress", True)
            except Exception as err:
                not_possible_to_delete.append(my_dict)
                LOGGER.debug(str(err) + "(usecase_name is " + trainingjob_name + \
                             ", version is " + str(version) + ")")
                continue

            try:
                deleted = True
                if MM_SDK.is_bucket_present(trainingjob_name):
                    deleted = MM_SDK.delete_model_metric(trainingjob_name, version)
            except Exception as err:
                not_possible_to_delete.append(my_dict)
                LOGGER.debug(str(err) + "(trainingjob_name is " + trainingjob_name + \
                             ", version is " + str(version) + ")")
                continue

            if not deleted:
                not_possible_to_delete.append(my_dict)
                continue

            try:
                delete_trainingjob_version(trainingjob_name, version)
            except Exception as err:
                not_possible_to_delete.append(my_dict)
                LOGGER.debug(str(err) + "(trainingjob_name is " + \
                             trainingjob_name + ", version is " + str(version) + ")")
                continue

            possible_to_delete.append(my_dict)

        else:
            not_possible_to_delete.append(my_dict)
            LOGGER.debug("not find in postgres db" + "(trainingjob_name is " + \
                         trainingjob_name + ", version is " + str(version) + ")")

        LOGGER.debug('success list: ' + str(possible_to_delete))
        LOGGER.debug('failure list: ' + str(not_possible_to_delete))

    return APP.response_class(response=json.dumps( \
        {
            "success count": len(possible_to_delete),
            "failure count": len(not_possible_to_delete)
        }),
        status=status.HTTP_200_OK,
        mimetype='application/json')

# Training-Config Handled (No Change)
@APP.route('/trainingjobs/metadata/<trainingjob_name>')
def get_metadata(trainingjob_name):
    """
    Function handling rest endpoint to get accuracy, version and model download url for all
    versions of given trainingjob_name which has overall_state FINISHED and
    deletion_in_progress is False

    Args in function:
        trainingjob_name: str
            name of trainingjob.

    Args in json:
        No json required

    Returns:
        json:
            Successed metadata : list
                                 list containes dictionaries.
                                     dictionary containts
                                         accuracy: dict
                                             metrics of model
                                         version: int
                                             version of trainingjob
                                         url: str
                                             url for downloading model
        status:
            HTTP status code 200

    Exceptions:
        all exception are provided with exception message and HTTP status code.
    """
    response_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    api_response = {}
    if not check_trainingjob_name_or_featuregroup_name(trainingjob_name):
        return {"Exception":"The trainingjob_name is not correct"}, status.HTTP_400_BAD_REQUEST

    LOGGER.debug("Request metadata for trainingjob(name of trainingjob is %s) ", trainingjob_name)
    try:
        results = get_all_versions_info_by_name(trainingjob_name)
        if results:
            info_list = []
            for trainingjob_info in results:
                if (get_one_word_status(json.loads(trainingjob_info.steps_state)) == States.FINISHED.name and
                        not trainingjob_info.deletion_in_progress):                   
                    LOGGER.debug("Downloading metric for " +trainingjob_name )
                    data = get_metrics(trainingjob_name, trainingjob_info[11], MM_SDK)
                    url = "http://" + str(TRAININGMGR_CONFIG_OBJ.my_ip) + ":" + \
                        str(TRAININGMGR_CONFIG_OBJ.my_port) + "/model/" + \
                        trainingjob_name + "/" + str(trainingjob_info[11]) + "/Model.zip"
                    dict_data = {
                        "accuracy": data,
                        "version": trainingjob_info.version,
                        "url": url
                    }
                    info_list.append(dict_data)
            #info_list built        
            api_response = {"Successed metadata": info_list}
            response_code = status.HTTP_200_OK
        else :
            err_msg = "Not found given trainingjob name-" + trainingjob_name
            LOGGER.error(err_msg)
            response_code = status.HTTP_404_NOT_FOUND
            api_response = {"Exception":err_msg}
    except Exception as err:
        LOGGER.error(str(err))
        api_response = {"Exception":str(err)}
    return APP.response_class(response=json.dumps(api_response),
                                        status=response_code,
                                        mimetype=MIMETYPE_JSON)

@APP.route('/featureGroup/<featuregroup_name>', methods=['GET', 'PUT'])
def feature_group_by_name(featuregroup_name):
    """
    Rest endpoint to get or update feature group
    Precondtion for update : not really necessary.

    Args in function:
        featuregroup_name: str
            name of featuregroup_name.

    Args in json:
        if get/put request is called
            json with below fields are given:
                featureGroupName: str
                    description
                feature_list: str
                    feature names
                datalake: str
                    name of datalake
                bucket: str
                    bucket name
                host: str
                    db host
                port: str
                    db port
                token: str
                    token for the bucket
                db org: str
                    db org name
                measurement: str
                    measurement of the influxdb
                enable_Dme: boolean
                    whether to enable dme
                source_name: str
                    name of source
                DmePort: str
                    DME port
                measured_obj_class: str
                    obj class for dme.
                datalake_source: str
                    string indicating datalake source

    Returns:
        1. For get request
            json:
                api response : str
                    response message
                status code:
                    HTTP status code 200
        2. For put request
            json:
                api response : str
                    response message
                status code:
                    HTTP status code 200

    Exceptions:
        All exception are provided with exception message and HTTP status code.
        The individual exceptions for put and get are handled within each internal function
    """
    api_response = {}
    response_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    LOGGER.debug("Feature Group read/update request(featuregroup name) %s", featuregroup_name)

    try:
        if (request.method == 'GET'):
            api_response, response_code = get_feature_group_by_name(featuregroup_name, LOGGER)
            return api_response, response_code
        elif (request.method == 'PUT'):
            featuregroup = FeatureGroupSchema().load(request.get_json())
            feature_group_name = featuregroup.featuregroup_name
            api_response , response_code = edit_feature_group_by_name(feature_group_name, featuregroup, LOGGER, TRAININGMGR_CONFIG_OBJ)
    except Exception as err:
        LOGGER.error("Failed to read/update featuregroup, " + str(err) )
        api_response =  {"Exception": str(err)}

    return APP.response_class(response= json.dumps(api_response),
                    status= response_code,
                    mimetype=MIMETYPE_JSON)

@APP.route('/featureGroup', methods=['POST'])
def create_feature_group():
    """
    Rest endpoint to create feature group

    Args in function:
                NONE

    Args in json:
            json with below fields are given:
                featureGroupName: str
                    description
                feature_list: str
                    feature names
                datalake: str
                    name of datalake
                bucket: str
                    bucket name
                host: str
                    db host
                port: str
                    db port
                token: str
                    token for the bucket
                db org: str
                    db org name
                measurement: str
                    measurement of the influxdb
                enable_Dme: boolean
                    whether to enable dme
                source_name: str
                    name of source
                DmePort: str
                    DME port
                measured_obj_class: str
                    obj class for dme.
                datalake_source: str
                    string indicating datalake source

    Returns:
        1. For post request
            json:
                result : str
                    result message
                status code:
                    HTTP status code 201
        2. For put request
            json:
                result : str
                    result message
                status code:
                    HTTP status code 200

    Exceptions:
        All exception are provided with exception message and HTTP status code."""
    
    api_response = {}
    response_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    LOGGER.debug('feature Group Create request, ' + json.dumps(request.json))

    try:
        featuregroup = FeatureGroupSchema().load(request.get_json())
        feature_group_name = featuregroup.featuregroup_name
        # check the data conformance
        # LOGGER.debug("the db info is : ", get_feature_group_by_name_db(PS_DB_OBJ, feature_group_name))
        if (not check_trainingjob_name_or_featuregroup_name(feature_group_name) or
            len(feature_group_name) < 3 or len(feature_group_name) > 63):
            api_response = {"Exception": "Failed to create the feature group since feature group not valid"}
            response_code = status.HTTP_400_BAD_REQUEST
        else:
            # the features are stored in string format in the db, and has to be passed as list of feature to the dme. Hence the conversion.
            add_featuregroup(featuregroup)
            api_response={"result": "Feature Group Created"}
            response_code =status.HTTP_200_OK
            if featuregroup.enable_dme == True :
                response= create_dme_filtered_data_job(TRAININGMGR_CONFIG_OBJ, featuregroup)
                if response.status_code != 201:
                    api_response={"Exception": "Cannot create dme job"}
                    delete_feature_group_by_name(featuregroup)
                    response_code=status.HTTP_400_BAD_REQUEST
    except ValidationError as err:
        return {"Exception": str(err)}, 400
    except DBException as err:
        return {"Exception": str(err)}, 400
    except Exception as e:
        err_msg = "Failed to create the feature Group "
        api_response = {"Exception":str(e)}
        LOGGER.error(str(e))
    
    return APP.response_class(response=json.dumps(api_response),
                                        status=response_code,
                                        mimetype=MIMETYPE_JSON)

@APP.route('/featureGroup', methods=['GET'])
def get_feature_group():
    """
    Rest endpoint to fetch all the feature groups

    Args in function: none
    Required Args in json:
        no json required 
    
    Returns:
        json:
            FeatureGroups: list
                list of dictionaries.
                    dictionaries contains:
                        featuregroup_name: str
                            name of feature group
                        features: str
                            name of features
                        datalake: str
                            datalake
                        dme: boolean
                            whether to enable dme
                        
    """
    LOGGER.debug("Request for getting all feature groups")
    api_response={}
    response_code=status.HTTP_500_INTERNAL_SERVER_ERROR
    try:
        result= get_feature_groups_db()
        feature_groups=[]
        for res in result:
            dict_data={
                "featuregroup_name": res.featuregroup_name,
                "features": res.feature_list,
                "datalake": res.datalake_source,
                "dme": res.enable_dme
                }
            feature_groups.append(dict_data)
        api_response={"featuregroups":feature_groups}
        response_code=status.HTTP_200_OK

    except Exception as err:
        api_response =   {"Exception": str(err)}
        LOGGER.error(str(err))
    return APP.response_class(response=json.dumps(api_response),
                        status=response_code,
                        mimetype=MIMETYPE_JSON)

@APP.route('/featureGroup', methods=['DELETE'])
def delete_list_of_feature_group():
    """
    Function handling rest endpoint to delete featureGroup which is
    given in request json. 

    Args in function: none
    Required Args in json:
        list: list
              list containing dictionaries.
                  dictionary contains
                      featuregroup_name: str
                          featuregroup name

    Returns:
        json:
            success count: int
                successful deletion count
            failure count: int
                failure deletion count
        status:
            HTTP status code 200
    Exceptions:
        all exception are provided with exception message and HTTP status code.
    """
    LOGGER.debug('request comes for deleting:' + json.dumps(request.json))
    if not check_key_in_dictionary(["featuregroups_list"], request.json):
        LOGGER.debug("exception in check_key_in_dictionary")
        raise APIException(status.HTTP_400_BAD_REQUEST, "Wrong Request syntax") from None

    list_of_feature_groups = request.json['featuregroups_list']
    if not isinstance(list_of_feature_groups, list):
        LOGGER.debug("exception in not instance")
        raise APIException(status.HTTP_400_BAD_REQUEST, NOT_LIST)

    not_possible_to_delete = []
    possible_to_delete = []

    for my_dict in list_of_feature_groups:
        if not isinstance(my_dict, dict):
            not_possible_to_delete.append(my_dict)
            LOGGER.debug(str(my_dict) + "did not pass dictionary")
            continue
        
        if not check_key_in_dictionary(["featureGroup_name"], my_dict):
            not_possible_to_delete.append(my_dict)
            LOGGER.debug("key featureGroup_name is not present in the request")
            continue

        featuregroup_name = my_dict['featureGroup_name']
        results = None
        try:
            results = get_feature_group_by_name_db(featuregroup_name)
        except Exception as err:
            not_possible_to_delete.append(my_dict)
            LOGGER.debug(str(err) + "(featureGroup_name is " + featuregroup_name)
            continue

        if results:
            dme= results.enable_dme
            try:
                delete_feature_group_by_name(featuregroup_name)
                if dme :
                    dme_host= results.host
                    dme_port = results.dme_port
                    resp=delete_dme_filtered_data_job(TRAININGMGR_CONFIG_OBJ, featuregroup_name, dme_host, dme_port)
                    if(resp.status_code !=status.HTTP_204_NO_CONTENT):
                        not_possible_to_delete.append(my_dict)  
                        LOGGER.debug("Cannot delete the dme_data_job"+ featuregroup_name)
                        continue
                possible_to_delete.append(my_dict)
            except Exception as err:
                not_possible_to_delete.append(my_dict)
                LOGGER.debug(str(err) + "(featuregroup_name is "+ featuregroup_name + ")")
                continue
        else:
             not_possible_to_delete.append(my_dict)
             LOGGER.debug("cannot find in postgres db" + "(featuregroup_name is " + \
                          featuregroup_name + ")")

    LOGGER.debug('success list: ' + str(possible_to_delete))
    LOGGER.debug('failure list: ' + str(not_possible_to_delete))

    return APP.response_class(response=json.dumps( \
        {
            "success count": len(possible_to_delete),
            "failure count": len(not_possible_to_delete)
        }),
        status=status.HTTP_200_OK,
        mimetype='application/json')

# Training-Config Handled (No Change)
def async_feature_engineering_status():
    """
    This function takes trainingjobs from DATAEXTRACTION_JOBS_CACHE and checks data extraction status
    (using data extraction api) for those trainingjobs, if status is Completed then it calls
    /trainingjob/dataExtractionNotification route for those trainingjobs.
    """
    url_pipeline_run = "http://" + str(TRAININGMGR_CONFIG_OBJ.my_ip) + \
                       ":" + str(TRAININGMGR_CONFIG_OBJ.my_port) + \
                       "/trainingjob/dataExtractionNotification"
    while True:
        with LOCK:
            fjc = list(DATAEXTRACTION_JOBS_CACHE)
        for trainingjob_name in fjc:
            LOGGER.debug("Current DATAEXTRACTION_JOBS_CACHE :" + str(DATAEXTRACTION_JOBS_CACHE))
            try:
                response = data_extraction_status(trainingjob_name, TRAININGMGR_CONFIG_OBJ)
                if (response.headers['content-type'] != MIMETYPE_JSON or 
                        response.status_code != status.HTTP_200_OK ):
                    raise TMException("Data extraction responsed with error status code or invalid content type" + \
                                         "doesn't send json type response (trainingjob " + trainingjob_name + ")")
                response = response.json()
                LOGGER.debug("Data extraction status response for " + \
                            trainingjob_name + " " + json.dumps(response))

                if response["task_status"] == "Completed":
                    with APP.app_context():
                        change_steps_state_of_latest_version(trainingjob_name,
                                                                Steps.DATA_EXTRACTION.name,
                                                                States.FINISHED.name)
                        change_steps_state_of_latest_version(trainingjob_name,
                                                                Steps.DATA_EXTRACTION_AND_TRAINING.name,
                                                                States.IN_PROGRESS.name)
                    kf_response = requests.post(url_pipeline_run,
                                                data=json.dumps({"trainingjob_name": trainingjob_name}),
                                                headers={
                                                    'content-type': MIMETYPE_JSON,
                                                    'Accept-Charset': 'UTF-8'
                                                })
                    if (kf_response.headers['content-type'] != MIMETYPE_JSON or 
                            kf_response.status_code != status.HTTP_200_OK ):
                        raise TMException("KF adapter responsed with error status code or invalid content type" + \
                                         "doesn't send json type response (trainingjob " + trainingjob_name + ")")
                    with LOCK:
                        DATAEXTRACTION_JOBS_CACHE.pop(trainingjob_name)        
                elif response["task_status"] == "Error":
                    raise TMException("Data extraction has failed for " + trainingjob_name)
            except Exception as err:
                LOGGER.error("Failure during procesing of DATAEXTRACTION_JOBS_CACHE," + str(err))
                """ Job will be removed from DATAEXTRACTION_JOBS_CACHE in  handle_async
                    There might be some further error during handling of exception
                """
                handle_async_feature_engineering_status_exception_case(LOCK,
                                                    DATAEXTRACTION_JOBS_CACHE,
                                                    status.HTTP_500_INTERNAL_SERVER_ERROR,
                                                    str(err) + "(trainingjob name is " + trainingjob_name + ")",
                                                    LOGGER, False, trainingjob_name, MM_SDK)

        #Wait and fetch latest list of trainingjobs
        time.sleep(10)

if __name__ == "__main__":
    TRAININGMGR_CONFIG_OBJ = TrainingMgrConfig()
    try:
        if TRAININGMGR_CONFIG_OBJ.is_config_loaded_properly() is False:
            raise TMException("Not all configuration loaded.")
        LOGGER = TRAININGMGR_CONFIG_OBJ.logger
        PS_DB_OBJ = PSDB(TRAININGMGR_CONFIG_OBJ)
        APP.config['SQLALCHEMY_DATABASE_URI']=f'postgresql+psycopg2://{TRAININGMGR_CONFIG_OBJ.ps_user}:{TRAININGMGR_CONFIG_OBJ.ps_password}@{TRAININGMGR_CONFIG_OBJ.ps_ip}:{TRAININGMGR_CONFIG_OBJ.ps_port}/training_manager_database'
        db.init_app(APP)
        # Todo add flask db upgrade in the docker file  
        migrate = Migrate(APP, db) 
        with APP.app_context():
            db.create_all()
        LOCK = Lock()
        DATAEXTRACTION_JOBS_CACHE = get_data_extraction_in_progress_trainingjobs(PS_DB_OBJ)
        threading.Thread(target=async_feature_engineering_status, daemon=True).start()
        MM_SDK = ModelMetricsSdk()
        list_allow_control_access_origin = TRAININGMGR_CONFIG_OBJ.allow_control_access_origin.split(',')
        CORS(APP, resources={r"/*": {"origins": list_allow_control_access_origin}})
        LOGGER.debug("Starting AIML-WF training manager .....")
        APP.run(debug=True, port=int(TRAININGMGR_CONFIG_OBJ.my_port), host='0.0.0.0')
    except TMException as err:
        print("Startup failure" + str(err))
