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
from logging import Logger
import os
import traceback
import threading
from threading import Lock
import time
from flask import Flask, request, send_file
from flask_api import status
import requests
from flask_cors import cross_origin
from modelmetricsdk.model_metrics_sdk import ModelMetricsSdk
from trainingmgr.common.trainingmgr_operations import data_extraction_start, training_start, data_extraction_status
from trainingmgr.common.trainingmgr_config import TrainingMgrConfig
from trainingmgr.common.trainingmgr_util import get_one_word_status, check_trainingjob_data, \
    check_key_in_dictionary, get_one_key, \
    response_for_training, get_metrics, \
    handle_async_feature_engineering_status_exception_case, \
    validate_trainingjob_name
from trainingmgr.common.exceptions_utls import APIException,TMException
from trainingmgr.constants.steps import Steps
from trainingmgr.constants.states import States

from trainingmgr.db.trainingmgr_ps_db import PSDB
from trainingmgr.db.common_db_fun import get_data_extraction_in_progress_trainingjobs, \
    change_field_of_latest_version, \
    change_in_progress_to_failed_by_latest_version, change_steps_state_of_latest_version, \
    get_info_by_version, \
    get_trainingjob_info_by_name, get_latest_version_trainingjob_name, get_all_versions_info_by_name, \
    update_model_download_url, add_update_trainingjob, \
    get_field_of_given_version,get_all_jobs_latest_status_version

APP = Flask(__name__)
TRAININGMGR_CONFIG_OBJ = None
PS_DB_OBJ = None
LOGGER = None
MM_SDK = None
LOCK = None
DATAEXTRACTION_JOBS_CACHE = None

@APP.errorhandler(APIException)
def error(err):
    """
    Return response with error message and error status code.
    """
    LOGGER.error(err.message)
    return APP.response_class(response=json.dumps({"Exception": err.message}),
                              status=err.code,
                              mimetype='application/json')


@APP.route('/trainingjobs/<trainingjob_name>/<version>', methods=['GET'])
@cross_origin()
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
                         feature_list: str
                             feature names
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
                        _measurement: str
                             _measurement of influx db datalake
                        bucket: str
                             bucket name of influx db datalake
        status code:
            HTTP status code 200

    Exceptions:
        all exception are provided with exception message and HTTP status code.

    """
    LOGGER.debug("Request to fetch trainingjob by name and version(trainingjob:" + \
                 trainingjob_name + " ,version:" + version + ")")
    response_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    response_data = {}
    try:
        results = get_info_by_version(trainingjob_name, version, PS_DB_OBJ)
        data = get_metrics(trainingjob_name, version, MM_SDK)
        if results:
            trainingjob_info = results[0]
            dict_data = {
                "trainingjob_name": trainingjob_info[0],
                "description": trainingjob_info[1],
                "feature_list": trainingjob_info[2],
                "pipeline_name": trainingjob_info[3],
                "experiment_name": trainingjob_info[4],
                "arguments": json.loads(trainingjob_info[5])['arguments'],
                "query_filter": trainingjob_info[6],
                "creation_time": str(trainingjob_info[7]),
                "run_id": trainingjob_info[8],
                "steps_state": json.loads(trainingjob_info[9]),
                "updation_time": str(trainingjob_info[10]),
                "version": trainingjob_info[11],
                "enable_versioning": bool(trainingjob_info[12]),
                "pipeline_version": trainingjob_info[13],
                "datalake_source": get_one_key(json.loads(trainingjob_info[14])['datalake_source']),
                "model_url": trainingjob_info[15],
                "notification_url": trainingjob_info[16],
                "_measurement": trainingjob_info[17],
                "bucket": trainingjob_info[18],
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
                                        mimetype='application/json')

@APP.route('/trainingjobs/<trainingjob_name>/<version>/steps_state', methods=['GET']) # Handled in GUI
@cross_origin()
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
    LOGGER.debug("Request to get steps_state for (trainingjob:" + \
                 trainingjob_name + " and version: " + version + ")")
    reponse_data = {}
    response_code = status.HTTP_500_INTERNAL_SERVER_ERROR

    try:
        results = get_field_of_given_version(trainingjob_name, version, PS_DB_OBJ, "steps_state")
        LOGGER.debug("get_field_of_given_version:" + str(results))
        if results:
            reponse_data = results[0][0]
            response_code = status.HTTP_200_OK
        else:
             
            response_code = status.HTTP_404_NOT_FOUND
            raise TMException("Not found given trainingjob in database")
    except Exception as err:
        LOGGER.error(str(err))
        reponse_data = {"Exception": str(err)}

    return APP.response_class(response=reponse_data,
                                      status=response_code,
                                      mimetype='application/json')

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
    try:
        return send_file(MM_SDK.get_model_zip(trainingjob_name, version), mimetype='application/zip')
    except Exception:
        return {"Exception": "error while downloading model"}, status.HTTP_500_INTERNAL_SERVER_ERROR


@APP.route('/trainingjobs/<trainingjob_name>/training', methods=['POST']) # Handled in GUI
@cross_origin()
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

    LOGGER.debug("Request for training trainingjob  %s ", trainingjob_name)
    response_data = {}
    response_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    try:
        isDataAvaible = validate_trainingjob_name(trainingjob_name, PS_DB_OBJ)
        if not isDataAvaible:
            response_code = status.HTTP_404_NOT_FOUND
            raise TMException("Given trainingjob name is not present in database" + \
                           "(trainingjob: " + trainingjob_name + ")") from None
        else:

            db_results = get_trainingjob_info_by_name(trainingjob_name, PS_DB_OBJ)
            feature_list = db_results[0][2]
            query_filter = db_results[0][6]
            datalake_source = json.loads(db_results[0][14])['datalake_source']
            _measurement = db_results[0][17]
            bucket = db_results[0][18]

            LOGGER.debug('Starting Data Extraction...')
            de_response = data_extraction_start(TRAININGMGR_CONFIG_OBJ, trainingjob_name,
                                         feature_list, query_filter, datalake_source,
                                         _measurement, bucket)
            if (de_response.status_code == status.HTTP_200_OK ):
                LOGGER.debug("Response from data extraction for " + \
                        trainingjob_name + " : " + json.dumps(de_response.json()))
                change_steps_state_of_latest_version(trainingjob_name, PS_DB_OBJ,
                                                    Steps.DATA_EXTRACTION.name,
                                                    States.IN_PROGRESS.name)
                with LOCK:
                    DATAEXTRACTION_JOBS_CACHE[trainingjob_name] = "Scheduled"
                response_data = de_response.json()
                response_code = status.HTTP_200_OK
            elif( de_response.headers['content-type'] == "application/json" ) :
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
        response_data =  {"Exception": str(err)}
        LOGGER.debug("Error is training, job name:" + trainingjob_name + str(err))         
    return APP.response_class(response=json.dumps(response_data),status=response_code,
                            mimetype='application/json')

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
            Logger.error(err_msg)
            err_response_code = status.HTTP_400_BAD_REQUEST
            raise TMException(err_msg)
 
        trainingjob_name = request.json["trainingjob_name"]
        results = get_trainingjob_info_by_name(trainingjob_name, PS_DB_OBJ)
        arguments = json.loads(results[0][5])['arguments']
        arguments["version"] = results[0][11]
        LOGGER.debug(arguments)

        dict_data = {
            "pipeline_name": results[0][3], "experiment_name": results[0][4],
            "arguments": arguments, "pipeline_version": results[0][13]
        }

        response = training_start(TRAININGMGR_CONFIG_OBJ, dict_data, trainingjob_name)
        if ( response.headers['content-type'] != "application/json" 
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
            change_steps_state_of_latest_version(trainingjob_name, PS_DB_OBJ,
                                                Steps.DATA_EXTRACTION_AND_TRAINING.name,
                                                States.FINISHED.name)
            change_steps_state_of_latest_version(trainingjob_name, PS_DB_OBJ,
                                                Steps.TRAINING.name,
                                                States.IN_PROGRESS.name)
            change_field_of_latest_version(trainingjob_name, PS_DB_OBJ,
                                        "run_id", json_data["run_id"])
        else:
            raise TMException("KF Adapter- run_status in not scheduled")
    except requests.exceptions.ConnectionError as err:
        err_msg = "Failed to connect KF adapter."
        LOGGER.error(err_msg)
        if not change_in_progress_to_failed_by_latest_version(trainingjob_name, PS_DB_OBJ) :
            LOGGER.error("Couldn't update the status as failed in db")
        return response_for_training(err_response_code,
                                        err_msg + str(err) + "(trainingjob name is " + trainingjob_name + ")",
                                        LOGGER, False, trainingjob_name, PS_DB_OBJ, MM_SDK)
    except Exception as err:
        LOGGER.error("Failed to handle dataExtractionNotification. " + str(err))
        if not change_in_progress_to_failed_by_latest_version(trainingjob_name, PS_DB_OBJ) :
            LOGGER.error("Couldn't update the status as failed in db")
        return response_for_training(err_response_code,
                                        str(err) + "(trainingjob name is " + trainingjob_name + ")",
                                        LOGGER, False, trainingjob_name, PS_DB_OBJ, MM_SDK)

    return APP.response_class(response=json.dumps({"result": "pipeline is scheduled"}),
                                    status=status.HTTP_200_OK,
                                    mimetype='application/json')


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

        if run_status == 'Succeeded':
            change_steps_state_of_latest_version(trainingjob_name, PS_DB_OBJ,
                                                    Steps.TRAINING.name,
                                                    States.FINISHED.name)
            change_steps_state_of_latest_version(trainingjob_name, PS_DB_OBJ,
                                                    Steps.TRAINING_AND_TRAINED_MODEL.name,
                                                    States.IN_PROGRESS.name)
                   
            version = get_latest_version_trainingjob_name(trainingjob_name, PS_DB_OBJ)
            change_steps_state_of_latest_version(trainingjob_name, PS_DB_OBJ,
                                                    Steps.TRAINING_AND_TRAINED_MODEL.name,
                                                    States.FINISHED.name)
            change_steps_state_of_latest_version(trainingjob_name, PS_DB_OBJ,
                                                    Steps.TRAINED_MODEL.name,
                                                    States.IN_PROGRESS.name)

            if MM_SDK.check_object(trainingjob_name, version, "Model.zip"):
                model_url = "http://" + str(TRAININGMGR_CONFIG_OBJ.my_ip) + ":" + \
                            str(TRAININGMGR_CONFIG_OBJ.my_port) + "/model/" + \
                            trainingjob_name + "/" + str(version) + "/Model.zip"
                
                update_model_download_url(trainingjob_name, version, model_url, PS_DB_OBJ)

                
                change_steps_state_of_latest_version(trainingjob_name, PS_DB_OBJ,
                                                        Steps.TRAINED_MODEL.name,
                                                        States.FINISHED.name)
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
        if not change_in_progress_to_failed_by_latest_version(trainingjob_name, PS_DB_OBJ) :
            LOGGER.error("Couldn't update the status as failed in db")
        
        return response_for_training(status.HTTP_500_INTERNAL_SERVER_ERROR,
                            str(err) + " (trainingjob " + trainingjob_name + ")",
                            LOGGER, False, trainingjob_name, PS_DB_OBJ, MM_SDK)
    #Training success response
    return response_for_training(status.HTTP_200_OK,
                                            "Pipeline notification success.",
                                            LOGGER, True, trainingjob_name, PS_DB_OBJ, MM_SDK)


@APP.route('/trainingjobs/latest', methods=['GET'])
@cross_origin()
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
        results = get_all_jobs_latest_status_version(PS_DB_OBJ)
        trainingjobs = []
        if results:
            for res in results:
                dict_data = {
                    "trainingjob_name": res[0],
                    "version": res[1],
                    "overall_status": get_one_word_status(json.loads(res[2]))
                }
                trainingjobs.append(dict_data)
            api_response = {"trainingjobs": trainingjobs}
            response_code = status.HTTP_200_OK
        else :
            raise TMException("Failed to fetch training job info from db")
    except Exception as err:
        api_response =   {"Exception": str(err)}
        LOGGER.error(str(err))
    return APP.response_class(response=json.dumps(api_response),
                        status=response_code,
                        mimetype='application/json')

@APP.route("/pipelines/<pipe_name>/upload", methods=['POST'])
@cross_origin()
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

        LOGGER.debug("Uploading received for %s", uploaded_file.filename)
        if uploaded_file.filename != '':
            uploaded_file_path = "/tmp/" + uploaded_file.filename
            uploaded_file.save(uploaded_file_path)
            LOGGER.debug("File uploaded :%s", uploaded_file_path)

            kf_adapter_ip = TRAININGMGR_CONFIG_OBJ.kf_adapter_ip
            kf_adapter_port = TRAININGMGR_CONFIG_OBJ.kf_adapter_port
            url = 'http://' + str(kf_adapter_ip) + ':' + str(kf_adapter_port) + \
                  '/pipelineIds/' + pipe_name

            description = ''
            if 'description' in request.form:
                description = request.form['description']
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
    except Exception:
        tbk = traceback.format_exc()
        LOGGER.error(tbk)
        result_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        result_string = "Error while uploading pipeline"

    if uploaded_file_path and os.path.isfile(uploaded_file_path):
        LOGGER.debug("Deleting %s", uploaded_file_path)
        os.remove(uploaded_file_path)

    LOGGER.debug("Responding to Client with %d %s", result_code, result_string)
    return APP.response_class(response=json.dumps({'result': result_string}),
                                  status=result_code,
                                  mimetype='application/json')


@APP.route("/pipelines/<pipeline_name>/versions", methods=['GET'])
@cross_origin()
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
    LOGGER.debug("Request to get all version for given pipeline(" + pipeline_name + ").")
    api_response = {}
    response_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    try:
        kf_adapter_ip = TRAININGMGR_CONFIG_OBJ.kf_adapter_ip
        kf_adapter_port = TRAININGMGR_CONFIG_OBJ.kf_adapter_port
        
        url = 'http://' + str(kf_adapter_ip) + ':' + str(
            kf_adapter_port) + '/pipelines/' + pipeline_name + \
            '/versions'
        LOGGER.debug("URL:" + url)
        response = requests.get(url)
        if response.headers['content-type'] != "application/json":
            raise TMException("Kf adapter doesn't sends json type response")
        api_response = {"versions_list": response.json()['versions_list']}
        response_code = status.HTTP_200_OK
    except Exception as err:
        api_response =  {"Exception": str(err)}
        LOGGER.error(str(err))
    return APP.response_class(response=json.dumps(api_response),
            status=response_code,
            mimetype='application/json')
     

@APP.route('/pipelines', methods=['GET'])
@cross_origin()
def get_all_pipeline_names():
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
    response = None
    api_response = {}
    response_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    try:
        kf_adapter_ip = TRAININGMGR_CONFIG_OBJ.kf_adapter_ip
        kf_adapter_port = TRAININGMGR_CONFIG_OBJ.kf_adapter_port
        url = 'http://' + str(kf_adapter_ip) + ':' + str(kf_adapter_port) + '/pipelines'
        LOGGER.debug(url)
        response = requests.get(url)
        if response.headers['content-type'] != "application/json":
            err_smg = "Kf adapter doesn't sends json type response"
            LOGGER.error(err_smg)
            raise TMException(err_smg)
        pipeline_names = []
        for pipeline in response.json().keys():
            pipeline_names.append(pipeline)

        api_response = {"pipeline_names": pipeline_names}
        response_code = status.HTTP_200_OK 
    except Exception as err:
        LOGGER.error(str(err))
        api_response =  {"Exception": str(err)}
    return APP.response_class(response=json.dumps(api_response),
                                    status=response_code,
                                    mimetype='application/json')


@APP.route('/experiments', methods=['GET'])
@cross_origin()
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
        url = 'http://' + str(kf_adapter_ip) + ':' + str(kf_adapter_port) + '/experiments'
        LOGGER.debug("url is :" + url)
        response = requests.get(url)
        if response.headers['content-type'] != "application/json":
            err_smg = "Kf adapter doesn't sends json type response"
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
                                  mimetype='application/json')


@APP.route('/trainingjobs/<trainingjob_name>', methods=['POST', 'PUT']) # Handled in GUI
@cross_origin()
def trainingjob_operations(trainingjob_name):
    """
    Rest endpoind to create or update trainingjob
    Precondtion for update : trainingjob's overall_status should be failed
    or finished and deletion processs should not be in progress

    Args in function:
        trainingjob_name: str
            name of trainingjob.

    Args in json:
        if post/put request is called
            json with below fields are given:
                description: str
                    description
                feature_list: str
                    feature names
                pipeline_name: str
                    name of pipeline
                experiment_name: str
                    name of experiment
                arguments: dict
                    key-value pairs related to hyper parameters and
                    "trainingjob":<trainingjob_name> key-value pair
                query_filter: str
                    string indication sql where clause for filtering out features
                enable_versioning: bool
                    flag for trainingjob versioning
                pipeline_version: str
                    pipeline version
                datalake_source: str
                    string indicating datalake source
                _measurement: str
                    _measurement for influx db datalake
                bucket: str
                    bucket name for influx db datalake

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
    api_response = {}
    response_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    LOGGER.debug("Training job create/update request(trainingjob name  %s) ", trainingjob_name )
    try:
        json_data = request.json
        if (request.method == 'POST'):          
            LOGGER.debug("Create request json : " + json.dumps(json_data))
            isDataAvailable = validate_trainingjob_name(trainingjob_name, PS_DB_OBJ)
            if  isDataAvailable:
                response_code = status.HTTP_409_CONFLICT
                raise TMException("trainingjob name(" + trainingjob_name + ") is already present in database")
            else:
                (feature_list, description, pipeline_name, experiment_name,
                arguments, query_filter, enable_versioning, pipeline_version,
                datalake_source, _measurement, bucket) = \
                check_trainingjob_data(trainingjob_name, json_data)
                add_update_trainingjob(description, pipeline_name, experiment_name, feature_list,
                                    arguments, query_filter, True, enable_versioning,
                                    pipeline_version, datalake_source, trainingjob_name, 
                                    PS_DB_OBJ, _measurement=_measurement,
                                    bucket=bucket)
                api_response =  {"result": "Information stored in database."}                 
                response_code = status.HTTP_201_CREATED
        elif(request.method == 'PUT'):
            LOGGER.debug("Update request json : " + json.dumps(json_data))
            isDataAvailable = validate_trainingjob_name(trainingjob_name, PS_DB_OBJ)
            if not isDataAvailable:
                response_code = status.HTTP_404_NOT_FOUND
                raise TMException("Trainingjob name(" + trainingjob_name + ") is not  present in database")
            else:
                results = None
                results = get_trainingjob_info_by_name(trainingjob_name, PS_DB_OBJ)
                if results:
                    if results[0][19]:
                        raise TMException("Failed to process request for trainingjob(" + trainingjob_name + ") " + \
                                        " deletion in progress")
                    if (get_one_word_status(json.loads(results[0][9]))
                            not in [States.FAILED.name, States.FINISHED.name]):
                        raise TMException("Trainingjob(" + trainingjob_name + ") is not in finished or failed status")

                (feature_list, description, pipeline_name, experiment_name,
                arguments, query_filter, enable_versioning, pipeline_version,
                datalake_source, _measurement, bucket) = check_trainingjob_data(trainingjob_name, json_data)

                add_update_trainingjob(description, pipeline_name, experiment_name, feature_list,
                                        arguments, query_filter, False, enable_versioning,
                                        pipeline_version, datalake_source, trainingjob_name, PS_DB_OBJ, _measurement=_measurement,
                                        bucket=bucket)
                api_response = {"result": "Information updated in database."}
                response_code = status.HTTP_200_OK
    except Exception as err:
        LOGGER.error("Failed to create/update training job, " + str(err) )
        api_response =  {"Exception": str(err)}

    return APP.response_class(response= json.dumps(api_response),
                    status= response_code,
                    mimetype='application/json')

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

    LOGGER.debug("Request metadata for trainingjob(name of trainingjob is %s) ", trainingjob_name)
    api_response = {}
    response_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    try:
        results = get_all_versions_info_by_name(trainingjob_name, PS_DB_OBJ)
        if results:
            info_list = []
            for trainingjob_info in results:
                if (get_one_word_status(json.loads(trainingjob_info[9])) == States.FINISHED.name and
                        not trainingjob_info[19]):
           
                    LOGGER.debug("Downloading metric for " +trainingjob_name )
                    data = get_metrics(trainingjob_name, trainingjob_info[11], MM_SDK)
                    url = "http://" + str(TRAININGMGR_CONFIG_OBJ.my_ip) + ":" + \
                        str(TRAININGMGR_CONFIG_OBJ.my_port) + "/model/" + \
                        trainingjob_name + "/" + str(trainingjob_info[11]) + "/Model.zip"
                    dict_data = {
                        "accuracy": data,
                        "version": trainingjob_info[11],
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
                                        mimetype='application/json')

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
                if (response.headers['content-type'] != "application/json" or 
                        response.status_code != status.HTTP_200_OK ):
                    raise TMException("Data extraction responsed with error status code or invalid content type" + \
                                         "doesn't send json type response (trainingjob " + trainingjob_name + ")")
                response = response.json()
                LOGGER.debug("Data extraction status response for " + \
                            trainingjob_name + " " + json.dumps(response))

                if response["task_status"] == "Completed":
                    change_steps_state_of_latest_version(trainingjob_name, PS_DB_OBJ,
                                                            Steps.DATA_EXTRACTION.name,
                                                            States.FINISHED.name)
                    change_steps_state_of_latest_version(trainingjob_name, PS_DB_OBJ,
                                                            Steps.DATA_EXTRACTION_AND_TRAINING.name,
                                                            States.IN_PROGRESS.name)
                    kf_response = requests.post(url_pipeline_run,
                                                data=json.dumps({"trainingjob_name": trainingjob_name}),
                                                headers={
                                                    'content-type': 'application/json',
                                                    'Accept-Charset': 'UTF-8'
                                                })
                    if (kf_response.headers['content-type'] != "application/json" or 
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
                                                    LOGGER, False, trainingjob_name,
                                                    PS_DB_OBJ, MM_SDK)

        #Wait and fetch latest list of trainingjobs
        time.sleep(10)

if __name__ == "__main__":
    TRAININGMGR_CONFIG_OBJ = TrainingMgrConfig()
    try:
        if TRAININGMGR_CONFIG_OBJ.is_config_loaded_properly() is False:
            raise Exception("Not all configuration loaded.")
        LOGGER = TRAININGMGR_CONFIG_OBJ.logger
        PS_DB_OBJ = PSDB(TRAININGMGR_CONFIG_OBJ)
        LOCK = Lock()
        DATAEXTRACTION_JOBS_CACHE = get_data_extraction_in_progress_trainingjobs(PS_DB_OBJ)
        threading.Thread(target=async_feature_engineering_status, daemon=True).start()
        MM_SDK = ModelMetricsSdk()
        LOGGER.debug("Starting AIML-WF training manager .....")
        APP.run(debug=True, port=int(TRAININGMGR_CONFIG_OBJ.my_port), host='0.0.0.0')
    except Exception as err:
        print("Startup failure" + str(err))
