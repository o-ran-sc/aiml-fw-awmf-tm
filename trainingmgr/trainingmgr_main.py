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
import ast
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
    handle_async_feature_engineering_status_exception_case, check_feature_group_data, check_trainingjob_name_and_version, check_trainingjob_name_or_featuregroup_name, \
    get_feature_group_by_name, edit_feature_group_by_name
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
from trainingmgr.controller.trainingjob_controller import training_job_controller
from trainingmgr.controller.pipeline_controller import pipeline_controller
from trainingmgr.common.trainingConfig_parser import validateTrainingConfig, getField
from trainingmgr.handler.async_handler import start_async_handler
from trainingmgr.service.training_job_service import change_status_tj, change_update_field_value, get_training_job, update_artifact_version
from trainingmgr.service.pipeline_service import start_training_service

APP = Flask(__name__)
TRAININGMGR_CONFIG_OBJ = TrainingMgrConfig()
from middleware.loggingMiddleware import LoggingMiddleware
APP.wsgi_app = LoggingMiddleware(APP.wsgi_app)
APP.register_blueprint(training_job_controller)
APP.register_blueprint(pipeline_controller)

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



@APP.route('/model/<trainingjob_id>/Model.zip', methods=['GET'])
def get_model(trainingjob_id):
    """
    Function handling rest endpoint to download model zip file of <trainingjob_name, version> trainingjob.

    Args in function:
        trainingjob_id: str
            id of trainingjob.

    Args in json:
        not required json

    Returns:
        zip file of model of <trainingjob id> trainingjob.

    Exceptions:
        all exception are provided with exception message and HTTP status code.
    """
    if not trainingjob_id.isnumeric():
        return {"Exception":"trainingjob id is not correct must be a numerical"}, status.HTTP_400_BAD_REQUEST

    try:
        traininigjob = get_training_job(training_job_id=trainingjob_id)
        
        return send_file(MM_SDK.get_model_zip(traininigjob.modelId.modelname,traininigjob.modelId.modelversion,traininigjob.modelId.artifactversion), mimetype='application/zip')
    except Exception as err:
        LOGGER.error(f"error while downloading model as {str(err)}")
        # for no trainingjob with trainingjob_id
        if "No row was found when one was required" in str(err):
            return {"Exception": f"error while downloading model as no trainingjob with id {trainingjob_id} was found"}, status.HTTP_404_NOT_FOUND
        
        # for no model present in leofs
        if "An error occurred (404) when calling the HeadObject operation: Not Found" in str(err):
            return {"Exception": f"error while downloading model as no model with trainingjob with id {trainingjob_id} was found"}, status.HTTP_404_NOT_FOUND
        
        return {"Exception": "error while downloading model"}, status.HTTP_500_INTERNAL_SERVER_ERROR



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
        if not check_key_in_dictionary(["trainingjob_id"], request.json) :
            err_msg = "featuregroup_name or trainingjob_id key not available in request"
            LOGGER.error(err_msg)
            return {"Exception":err_msg}, status.HTTP_400_BAD_REQUEST
            
        trainingjob_id = request.json["trainingjob_id"]
        trainingjob = get_training_job(trainingjob_id)
        featuregroup_name = getField(trainingjob.training_config, "feature_group_name")
        arguments = getField(trainingjob.training_config, "arguments")

        argument_dict = ast.literal_eval(arguments)

        argument_dict["trainingjob_id"] = trainingjob_id
        argument_dict["featuregroup_name"] = featuregroup_name
        argument_dict["modelName"] = trainingjob.modelId.modelname
        argument_dict["modelVersion"] = trainingjob.modelId.modelversion
        argument_dict["artifactVersion"] = trainingjob.modelId.artifactversion

        # Arguments values must be of type string
        for key, val in argument_dict.items():
            if not isinstance(val, str):
                argument_dict[key] = str(val)
        LOGGER.debug(argument_dict)
        # Experiment name is harded to be Default
        training_details = {
            "pipeline_name": getField(trainingjob.training_config, "pipeline_name"), "experiment_name": 'Default',
            "arguments": argument_dict, "pipeline_version": getField(trainingjob.training_config, "pipeline_name")
        }
        response = training_start(TRAININGMGR_CONFIG_OBJ, training_details, trainingjob_id)
        if ( response.headers['content-type'] != MIMETYPE_JSON 
                or response.status_code != status.HTTP_200_OK ):
            err_msg = "Kf adapter invalid content-type or status_code for " + str(trainingjob_id)
            raise TMException(err_msg)
        
        LOGGER.debug("response from kf_adapter for " + \
                    str(trainingjob_id) + " : " + json.dumps(response.json()))
        json_data = response.json()
        
        if not check_key_in_dictionary(["run_status", "run_id"], json_data):
            err_msg = "Kf adapter invalid response from , key not present ,run_status or  run_id for " + str(trainingjob_id)
            Logger.error(err_msg)
            err_response_code = status.HTTP_400_BAD_REQUEST
            raise TMException(err_msg)

        if json_data["run_status"] == 'scheduled':
            change_status_tj(trainingjob.id,
                            Steps.DATA_EXTRACTION_AND_TRAINING.name,
                            States.FINISHED.name)
            LOGGER.debug("DATA_EXTRACTION_AND_TRAINING step set to FINISHED for training job " + trainingjob.id)
            change_status_tj(trainingjob.id,
                            Steps.TRAINING.name,
                            States.IN_PROGRESS.name)
            LOGGER.debug("TRAINING step set to IN_PROGRESS for training job " + trainingjob.id)
            change_update_field_value(trainingjob.id,
                                     "run_id", 
                                     json_data["run_id"])
            # notification_rapp(trainingjob, TRAININGMGR_CONFIG_OBJ)
        else:
            raise TMException("KF Adapter- run_status in not scheduled")
    except requests.exceptions.ConnectionError as err:
        # err_msg = "Failed to connect KF adapter."
        # LOGGER.error(err_msg)
        # if not change_in_progress_to_failed_by_latest_version(trainingjob_name) :
        #     LOGGER.error(ERROR_TYPE_DB_STATUS)
        # return response_for_training(err_response_code,
        #                                 err_msg + str(err) + "(trainingjob name is " + trainingjob_name + ")",
        #                                 LOGGER, False, trainingjob_name, MM_SDK)
        pass

    except Exception as err:
        # LOGGER.error("Failed to handle dataExtractionNotification. " + str(err))
        # if not change_in_progress_to_failed_by_latest_version(trainingjob_name) :
        #     LOGGER.error(ERROR_TYPE_DB_STATUS)
        # return response_for_training(err_response_code,
        #                                 str(err) + "(trainingjob name is " + trainingjob_name + ")",
        #                                 LOGGER, False, trainingjob_name, MM_SDK)
        pass

    return APP.response_class(response=json.dumps({"result": "pipeline is scheduled"}),
                                    status=status.HTTP_200_OK,
                                    mimetype=MIMETYPE_JSON)


# Will be migrated to pipline Mgr in next iteration
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
        check_key_in_dictionary(["trainingjob_id", "run_status"], request.json)
        trainingjob_id = request.json["trainingjob_id"]
        run_status = request.json["run_status"]

        if run_status == 'SUCCEEDED':

            trainingjob=get_training_job(trainingjob_id)

            change_status_tj(trainingjob_id,
                            Steps.TRAINING.name,
                            States.FINISHED.name)
            
            change_status_tj(trainingjob_id,
                            Steps.TRAINING_AND_TRAINED_MODEL.name,
                            States.IN_PROGRESS.name)
            
            # notification_rapp(trainingjob_info, TRAININGMGR_CONFIG_OBJ)

            # version = get_latest_version_trainingjob_name(trainingjob_name)

            change_status_tj(trainingjob_id,
                            Steps.TRAINING_AND_TRAINED_MODEL.name,
                            States.FINISHED.name)
            change_status_tj(trainingjob_id,
                            Steps.TRAINED_MODEL.name,
                            States.IN_PROGRESS.name)
            
            # notification_rapp(trainingjob_info, TRAININGMGR_CONFIG_OBJ)
            model_name= trainingjob.modelId.modelname
            model_version= trainingjob.modelId.modelversion
            artifact_version= trainingjob.modelId.artifactversion
            artifact_version= update_artifact_version(trainingjob_id , artifact_version, "major")

            if MM_SDK.check_object(model_name, model_version, artifact_version, "Model.zip"):
                model_url = "http://" + str(TRAININGMGR_CONFIG_OBJ.my_ip) + ":" + \
                            str(TRAININGMGR_CONFIG_OBJ.my_port) + "/model/" + \
                            model_name + "/" + str(model_version) + "/" + str(artifact_version) + "/Model.zip"

                change_update_field_value(trainingjob_id, "model_url" , model_url)
                
                change_status_tj(trainingjob_id,
                                Steps.TRAINED_MODEL.name,
                                States.FINISHED.name)
                # notification_rapp(trainingjob_info, TRAININGMGR_CONFIG_OBJ)
            else:
                errMsg = "Trained model is not available  "
                LOGGER.error(errMsg + trainingjob_id)
                raise TMException(errMsg + trainingjob_id)
        else:
            LOGGER.error("Pipeline notification -Training failed " + trainingjob_id)    
            raise TMException("Pipeline not successful for " + \
                                        trainingjob_id + \
                                        ",request json from kf adapter is: " + json.dumps(request.json))      
    except Exception as err:
        #Training failure response
        LOGGER.error("Pipeline notification failed" + str(err))
        # if not change_in_progress_to_failed_by_latest_version(trainingjob_id) :
        #     LOGGER.error(ERROR_TYPE_DB_STATUS)
        
        # return response_for_training(status.HTTP_500_INTERNAL_SERVER_ERROR,
        #                     str(err) + " (trainingjob " + trainingjob_id + ")",
        #                     LOGGER, False, trainingjob_id, MM_SDK)
        return "", 500
    #Training success response
    # return response_for_training(status.HTTP_200_OK,
    #                                         "Pipeline notification success.",
    #                                         LOGGER, True, trainingjob_id, MM_SDK)
    return "", 200




# Moved to pipelineMgr (to be deleted in future)
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



# @APP.route('/trainingjobs/retraining', methods=['POST'])
# def retraining():
#     """
#     Function handling rest endpoint to retrain trainingjobs in request json. trainingjob's
#     overall_status should be failed or finished and its deletion_in_progress should be False
#     otherwise retraining of that trainingjob is counted in failure.
#     Args in function: none
#     Required Args in json:
#         trainingjobs_list: list
#                        list containing dictionaries
#                            dictionary contains
#                                usecase_name: str
#                                    name of trainingjob
#                                notification_url(optional): str
#                                    url for notification
#                                feature_filter(optional): str
#                                    feature filter
#     Returns:
#         json:
#             success count: int
#                 successful retraining count
#             failure count: int
#                 failure retraining count
#         status: HTTP status code 200
#     Exceptions:
#         all exception are provided with exception message and HTTP status code.
#     """
#     LOGGER.debug('request comes for retraining, ' + json.dumps(request.json))
#     try:
#         check_key_in_dictionary(["trainingjobs_list"], request.json)
#     except Exception as err:
#         raise APIException(status.HTTP_400_BAD_REQUEST, str(err)) from None

#     trainingjobs_list = request.json['trainingjobs_list']
#     if not isinstance(trainingjobs_list, list):
#         raise APIException(status.HTTP_400_BAD_REQUEST, NOT_LIST)

#     for obj in trainingjobs_list:
#         try:
#             check_key_in_dictionary(["trainingjob_name"], obj)
#         except Exception as err:
#             raise APIException(status.HTTP_400_BAD_REQUEST, str(err)) from None

#     not_possible_to_retrain = []
#     possible_to_retrain = []

#     for obj in trainingjobs_list:
#         trainingjob_name = obj['trainingjob_name']
#         results = None
#         try:
#             trainingjob = get_info_of_latest_version(trainingjob_name)
#         except Exception as err:
#             not_possible_to_retrain.append(trainingjob_name)
#             LOGGER.debug(str(err) + "(trainingjob_name is " + trainingjob_name + ")")
#             continue
        
#         if trainingjob:
#             if trainingjob.deletion_in_progress:
#                 not_possible_to_retrain.append(trainingjob_name)
#                 LOGGER.debug("Failed to retrain because deletion in progress" + \
#                              "(trainingjob_name is " + trainingjob_name + ")")
#                 continue

#             if (get_one_word_status(json.loads(trainingjob.steps_state))
#                     not in [States.FINISHED.name, States.FAILED.name]):
#                 not_possible_to_retrain.append(trainingjob_name)
#                 LOGGER.debug("Not finished or not failed status" + \
#                              "(trainingjob_name is " + trainingjob_name + ")")
#                 continue

#             try:
#                 add_update_trainingjob(trainingjob, False)
#             except Exception as err:
#                 not_possible_to_retrain.append(trainingjob_name)
#                 LOGGER.debug(str(err) + "(training job is " + trainingjob_name + ")")
#                 continue

#             url = 'http://' + str(TRAININGMGR_CONFIG_OBJ.my_ip) + \
#                   ':' + str(TRAININGMGR_CONFIG_OBJ.my_port) + \
#                   '/trainingjobs/' +trainingjob_name + '/training'
#             response = requests.post(url)

#             if response.status_code == status.HTTP_200_OK:
#                 possible_to_retrain.append(trainingjob_name)
#             else:
#                 LOGGER.debug("not 200 response" + "(trainingjob_name is " + trainingjob_name + ")")
#                 not_possible_to_retrain.append(trainingjob_name)

#         else:
#             LOGGER.debug("not present in postgres db" + "(trainingjob_name is " + trainingjob_name + ")")
#             not_possible_to_retrain.append(trainingjob_name)

#         LOGGER.debug('success list: ' + str(possible_to_retrain))
#         LOGGER.debug('failure list: ' + str(not_possible_to_retrain))

#     return APP.response_class(response=json.dumps( \
#         {
#             "success count": len(possible_to_retrain),
#             "failure count": len(not_possible_to_retrain)
#         }),
#         status=status.HTTP_200_OK,
#         mimetype='application/json')




# @APP.route('/trainingjobs/metadata/<trainingjob_name>')
# def get_metadata(trainingjob_name):
#     """
#     Function handling rest endpoint to get accuracy, version and model download url for all
#     versions of given trainingjob_name which has overall_state FINISHED and
#     deletion_in_progress is False

#     Args in function:
#         trainingjob_name: str
#             name of trainingjob.

#     Args in json:
#         No json required

#     Returns:
#         json:
#             Successed metadata : list
#                                  list containes dictionaries.
#                                      dictionary containts
#                                          accuracy: dict
#                                              metrics of model
#                                          version: int
#                                              version of trainingjob
#                                          url: str
#                                              url for downloading model
#         status:
#             HTTP status code 200

#     Exceptions:
#         all exception are provided with exception message and HTTP status code.
#     """
#     response_code = status.HTTP_500_INTERNAL_SERVER_ERROR
#     api_response = {}
#     if not check_trainingjob_name_or_featuregroup_name(trainingjob_name):
#         return {"Exception":"The trainingjob_name is not correct"}, status.HTTP_400_BAD_REQUEST

#     LOGGER.debug("Request metadata for trainingjob(name of trainingjob is %s) ", trainingjob_name)
#     try:
#         results = get_all_versions_info_by_name(trainingjob_name)
#         if results:
#             info_list = []
#             for trainingjob_info in results:
#                 if (get_one_word_status(json.loads(trainingjob_info.steps_state)) == States.FINISHED.name and
#                         not trainingjob_info.deletion_in_progress):                   
#                     LOGGER.debug("Downloading metric for " +trainingjob_name )
#                     data = get_metrics(trainingjob_name, trainingjob_info[11], MM_SDK)
#                     url = "http://" + str(TRAININGMGR_CONFIG_OBJ.my_ip) + ":" + \
#                         str(TRAININGMGR_CONFIG_OBJ.my_port) + "/model/" + \
#                         trainingjob_name + "/" + str(trainingjob_info[11]) + "/Model.zip"
#                     dict_data = {
#                         "accuracy": data,
#                         "version": trainingjob_info.version,
#                         "url": url
#                     }
#                     info_list.append(dict_data)
#             #info_list built        
#             api_response = {"Successed metadata": info_list}
#             response_code = status.HTTP_200_OK
#         else :
#             err_msg = "Not found given trainingjob name-" + trainingjob_name
#             LOGGER.error(err_msg)
#             response_code = status.HTTP_404_NOT_FOUND
#             api_response = {"Exception":err_msg}
#     except Exception as err:
#         LOGGER.error(str(err))
#         api_response = {"Exception":str(err)}
#     return APP.response_class(response=json.dumps(api_response),
#                                         status=response_code,
#                                         mimetype=MIMETYPE_JSON)

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


# def async_feature_engineering_status():
#     """
#     This function takes trainingjobs from DATAEXTRACTION_JOBS_CACHE and checks data extraction status
#     (using data extraction api) for those trainingjobs, if status is Completed then it calls
#     /trainingjob/dataExtractionNotification route for those trainingjobs.
#     """
#     url_pipeline_run = "http://" + str(TRAININGMGR_CONFIG_OBJ.my_ip) + \
#                        ":" + str(TRAININGMGR_CONFIG_OBJ.my_port) + \
#                        "/trainingjob/dataExtractionNotification"
#     while True:
#         with LOCK:
#             fjc = list(DATAEXTRACTION_JOBS_CACHE)
#         for trainingjob_name in fjc:
#             LOGGER.debug("Current DATAEXTRACTION_JOBS_CACHE :" + str(DATAEXTRACTION_JOBS_CACHE))
#             try:
#                 response = data_extraction_status(trainingjob_name, TRAININGMGR_CONFIG_OBJ)
#                 if (response.headers['content-type'] != MIMETYPE_JSON or 
#                         response.status_code != status.HTTP_200_OK ):
#                     raise TMException("Data extraction responsed with error status code or invalid content type" + \
#                                          "doesn't send json type response (trainingjob " + trainingjob_name + ")")
#                 response = response.json()
#                 LOGGER.debug("Data extraction status response for " + \
#                             trainingjob_name + " " + json.dumps(response))

#                 if response["task_status"] == "Completed":
#                     with APP.app_context():
#                         change_steps_state_of_latest_version(trainingjob_name,
#                                                                 Steps.DATA_EXTRACTION.name,
#                                                                 States.FINISHED.name)
#                         change_steps_state_of_latest_version(trainingjob_name,
#                                                                 Steps.DATA_EXTRACTION_AND_TRAINING.name,
#                                                                 States.IN_PROGRESS.name)
#                     kf_response = requests.post(url_pipeline_run,
#                                                 data=json.dumps({"trainingjob_name": trainingjob_name}),
#                                                 headers={
#                                                     'content-type': MIMETYPE_JSON,
#                                                     'Accept-Charset': 'UTF-8'
#                                                 })
#                     if (kf_response.headers['content-type'] != MIMETYPE_JSON or 
#                             kf_response.status_code != status.HTTP_200_OK ):
#                         raise TMException("KF adapter responsed with error status code or invalid content type" + \
#                                          "doesn't send json type response (trainingjob " + trainingjob_name + ")")
#                     with LOCK:
#                         DATAEXTRACTION_JOBS_CACHE.pop(trainingjob_name)        
#                 elif response["task_status"] == "Error":
#                     raise TMException("Data extraction has failed for " + trainingjob_name)
#             except Exception as err:
#                 LOGGER.error("Failure during procesing of DATAEXTRACTION_JOBS_CACHE," + str(err))
#                 """ Job will be removed from DATAEXTRACTION_JOBS_CACHE in  handle_async
#                     There might be some further error during handling of exception
#                 """
#                 handle_async_feature_engineering_status_exception_case(LOCK,
#                                                     DATAEXTRACTION_JOBS_CACHE,
#                                                     status.HTTP_500_INTERNAL_SERVER_ERROR,
#                                                     str(err) + "(trainingjob name is " + trainingjob_name + ")",
#                                                     LOGGER, False, trainingjob_name, MM_SDK)

#         #Wait and fetch latest list of trainingjobs
#         time.sleep(10)

if __name__ == "__main__":
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
        start_async_handler(APP,db)
        # LOCK = Lock()
        # DATAEXTRACTION_JOBS_CACHE = get_data_extraction_in_progress_trainingjobs(PS_DB_OBJ)
        # threading.Thread(target=try2, daemon=True).start()
        MM_SDK = ModelMetricsSdk()
        list_allow_control_access_origin = TRAININGMGR_CONFIG_OBJ.allow_control_access_origin.split(',')
        CORS(APP, resources={r"/*": {"origins": list_allow_control_access_origin}})
        LOGGER.debug("Starting AIML-WF training manager .....")
        APP.run(debug=True, port=int(TRAININGMGR_CONFIG_OBJ.my_port), host='0.0.0.0')
    except TMException as err:
        print("Startup failure" + str(err))
