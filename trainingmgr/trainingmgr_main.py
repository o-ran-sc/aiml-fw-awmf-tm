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
from flask import Flask, request, send_file, jsonify
from flask_api import status
from flask_migrate import Migrate
import requests
from flask_cors import CORS
from trainingmgr.db.trainingjob_db import change_state_to_failed
from modelmetricsdk.model_metrics_sdk import ModelMetricsSdk
from trainingmgr.common.trainingmgr_operations import  notification_rapp, training_start, delete_dme_filtered_data_job
from trainingmgr.common.trainingmgr_config import TrainingMgrConfig
from trainingmgr.common.trainingmgr_util import check_key_in_dictionary, \
    get_feature_group_by_name, edit_feature_group_by_name
from trainingmgr.common.exceptions_utls import APIException,TMException
from trainingmgr.constants.steps import Steps
from trainingmgr.constants.states import States
from trainingmgr.db.trainingmgr_ps_db import PSDB
from trainingmgr.models import db
from trainingmgr.schemas import TrainingJobSchema , FeatureGroupSchema
from trainingmgr.db.featuregroup_db import get_feature_group_by_name_db, delete_feature_group_by_name
from trainingmgr.controller import featuregroup_controller, training_job_controller
from trainingmgr.controller.pipeline_controller import pipeline_controller
from trainingmgr.controller.agent_controller import agent_controller
from trainingmgr.common.trainingConfig_parser import getField
from trainingmgr.handler.async_handler import start_async_handler
from trainingmgr.service.mme_service import get_modelinfo_by_modelId_service
from trainingmgr.service.training_job_service import change_status_tj, change_update_field_value, fetch_pipelinename_and_version, get_training_job

APP = Flask(__name__)
TRAININGMGR_CONFIG_OBJ = TrainingMgrConfig()
from middleware.loggingMiddleware import LoggingMiddleware
APP.wsgi_app = LoggingMiddleware(APP.wsgi_app)
APP.register_blueprint(featuregroup_controller, url_prefix='/ai-ml-model-training/v1')
APP.register_blueprint(training_job_controller, url_prefix='/ai-ml-model-training/v1')
APP.register_blueprint(agent_controller, url_prefix="/experiment/agent")
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
featuregroups_schema = FeatureGroupSchema(many=True)

@APP.errorhandler(APIException)
def error(err):
    """
    Return response with error message and error status code.
    """
    LOGGER.error(err.message)
    return APP.response_class(response=json.dumps({"Exception": err.message}),
                              status=err.code,
                              mimetype=MIMETYPE_JSON)


@APP.route('/model/<modelname>/<modelversion>/<artifactversion>/Model.zip', methods=['GET'])
def get_model(modelname, modelversion, artifactversion):
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

    try:
        
        return send_file(MM_SDK.get_model_zip(modelname, modelversion, artifactversion), mimetype='application/zip')
    except Exception as err:
        LOGGER.error(f"error while downloading model as {str(err)}")
        # for no trainingjob with trainingjob_id
        
        # for no model present in leofs
        if "An error occurred (404) when calling the HeadObject operation: Not Found" in str(err):
            err_msg = (
                f"Error while downloading model: "
                f"Model Name = {modelname}, "
                f"Model Version = {modelversion}, "
                f"Artifact Version = {artifactversion}, "
                f"Model not found"
            )
            LOGGER.error(err_msg)  
            return err_msg, status.HTTP_404_NOT_FOUND

        return {"Exception": "error while downloading model"}, status.HTTP_500_INTERNAL_SERVER_ERROR

@APP.route('/trainingjob/dataExtractionNotification', methods=['POST'])
def data_extraction_notification():
    """
    This rest endpoint will be invoked when data extraction is finished.
    It will further invoke kf-adapter for training, if the response from kf-adapter run_status is "scheduled",
    that means request is accepted by kf-adapter for futher processing.

    Args in function:
        None

    Args in json:
        trainingjob_id: str
            id of trainingjob.

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
    try:
        if (not check_key_in_dictionary(["trainingJobId"], request.json)
                and not check_key_in_dictionary(["trainingjob_id"], request.json)):
            err_msg = "featuregroup_name or trainingjob_id key not available in request"
            LOGGER.error(err_msg)
            return {"Exception":err_msg}, status.HTTP_400_BAD_REQUEST
            
        trainingjob_id = request.json.get("trainingJobId") or request.json.get("trainingjob_id")
        trainingjob = get_training_job(trainingjob_id)
        featuregroup_name = getField(trainingjob.training_config, "feature_group_name")
        argument_dict = getField(trainingjob.training_config, "arguments")

        # argument_dict = ast.literal_eval(arguments)

        argument_dict["trainingjob_id"] = trainingjob_id
        argument_dict["featuregroup_name"] = featuregroup_name
        argument_dict["modelName"] = trainingjob.modelId.modelname
        argument_dict["modelVersion"] = trainingjob.modelId.modelversion
        argument_dict["modellocation"] = trainingjob.model_location

        # Arguments values must be of type string
        for key, val in argument_dict.items():
            if not isinstance(val, str):
                argument_dict[key] = str(val)
        LOGGER.debug(argument_dict)
        # Experiment name is harded to be Default

        model_id = trainingjob.modelId
        registered_model_list = get_modelinfo_by_modelId_service(model_id.modelname, model_id.modelversion)

        if registered_model_list is None:
            return jsonify({"Exception":f"Model Name = {model_id.modelname} and Model Version = {model_id.modelversion} is not registered at MME, Please first register at MME and then continue"}), status.HTTP_400_BAD_REQUEST

        registered_model_dict = registered_model_list[0]

        pipeline_name =""
        pipeline_version =""
        if registered_model_dict["modelId"]["artifactVersion"] == "0.0.0":
            if registered_model_dict["modelLocation"] == "":
                pipeline_name, pipeline_version = fetch_pipelinename_and_version("training", trainingjob.training_config)
            else:
                pipeline_name, pipeline_version = fetch_pipelinename_and_version("re-training", trainingjob.training_config)
                if pipeline_name == "" or  pipeline_version =="":
                    return jsonify({"Error": "Provide retraining pipeline name and version"}), 500
        else:
            pipeline_name, pipeline_version = fetch_pipelinename_and_version("re-training", trainingjob.training_config)
            if pipeline_name == "" or  pipeline_version =="":
                return jsonify({"Error": "Provide retraining pipeline name and version"}), 500

        training_details = {
            "pipeline_name": pipeline_name, "experiment_name": 'Default',
            "arguments": argument_dict, "pipeline_version": pipeline_version
        }
        LOGGER.debug("training detail for kf adapter is: "+ str(training_details))
        response = training_start(TRAININGMGR_CONFIG_OBJ, training_details, trainingjob_id)
        if ( response.headers['content-type'] != MIMETYPE_JSON 
                or response.status_code != status.HTTP_200_OK ):
            err_msg = "Kf adapter invalid content-type or status_code for " + str(trainingjob_id)
            raise TMException(err_msg)
        
        LOGGER.debug("response from kf_adapter for " + \
                    str(trainingjob_id) + " : " + json.dumps(response.json()))
        json_data = response.json()
        
        if not check_key_in_dictionary(["run_status", "run_id"], json_data):
            err_msg = "Kf adapter invalid response: missing run_status or run_id for " + str(trainingjob_id)
            LOGGER.error(err_msg)

            raise TMException(err_msg)

        if json_data["run_status"] == 'scheduled':
            change_status_tj(trainingjob.id,
                            Steps.DATA_EXTRACTION_AND_TRAINING.name,
                            States.FINISHED.name)
            LOGGER.debug("DATA_EXTRACTION_AND_TRAINING step set to FINISHED for training job " + str(trainingjob.id))
            change_status_tj(trainingjob.id,
                            Steps.TRAINING.name,
                            States.IN_PROGRESS.name)
            LOGGER.debug("TRAINING step set to IN_PROGRESS for training job " + str(trainingjob.id))
            change_update_field_value(trainingjob.id,
                                     "run_id", 
                                     json_data["run_id"])
            # notification_rapp(trainingjob, TRAININGMGR_CONFIG_OBJ)
        else:
            raise TMException("KF Adapter- run_status in not scheduled")
    except requests.exceptions.ConnectionError as err:
        LOGGER.error(f"DataExtraction Notification failed due to {str(err)}")
        try:
            notification_rapp(trainingjob.id)
            change_state_to_failed(trainingjob.id)
        except Exception as e:
            if "the change_steps_state to failed" in str(e):
                LOGGER.error(f"failed to update the status of trainingjob to FAILED due to {str(err)}")
        return jsonify({"Error":"Failed to connect to KF adapter"}) , 504

    except Exception as err:
        LOGGER.error("error is : "+ str(err))
        try:
            notification_rapp(trainingjob.id)
            change_state_to_failed(trainingjob.id)
        except Exception as e:
            if "the change_steps_state to failed" in str(e):
                LOGGER.error(f"failed to update the status of trainingjob to FAILED due to {str(err)}")
        return jsonify({"failed":"error"}), 500

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
        trainingjob_id: str
            id of trainingjob.

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
        has_tid = (check_key_in_dictionary(["trainingJobId"], request.json)
                   or check_key_in_dictionary(["trainingjob_id"], request.json))
        has_status = (check_key_in_dictionary(["run_status"], request.json)
                      or check_key_in_dictionary(["runStatus"], request.json))
        if not (has_tid and has_status):
            return jsonify({"Exception": "trainingJobId (or trainingjob_id) and run_status are required"}), 400

        trainingjob_id = request.json.get("trainingJobId") or request.json.get("trainingjob_id")
        run_status = request.json.get("run_status") or request.json.get("runStatus")

        if run_status == 'SUCCEEDED':

            trainingjob=get_training_job(trainingjob_id)

            change_status_tj(trainingjob_id,
                            Steps.TRAINING.name,
                            States.FINISHED.name)
            
            change_status_tj(trainingjob_id,
                            Steps.TRAINING_AND_TRAINED_MODEL.name,
                            States.IN_PROGRESS.name)
            
            notification_rapp(trainingjob.id)

            change_status_tj(trainingjob_id,
                            Steps.TRAINING_AND_TRAINED_MODEL.name,
                            States.FINISHED.name)
            change_status_tj(trainingjob_id,
                            Steps.TRAINED_MODEL.name,
                            States.IN_PROGRESS.name)
            
            notification_rapp(trainingjob.id)

            model_name= trainingjob.modelId.modelname
            model_version= trainingjob.modelId.modelversion

            modelinfo = get_modelinfo_by_modelId_service(model_name, model_version)[0]
            artifactversion = modelinfo["modelId"]["artifactVersion"]
            if MM_SDK.check_object(model_name, model_version, artifactversion, "Model.zip"):
                model_url = "http://" + str(TRAININGMGR_CONFIG_OBJ.my_ip) + ":" + \
                            str(TRAININGMGR_CONFIG_OBJ.my_port) + "/model/" + \
                            model_name + "/" + str(model_version) + "/" + str(artifactversion) + "/Model.zip"

                change_update_field_value(trainingjob_id, "model_url" , model_url)
                
                change_status_tj(trainingjob_id,
                                Steps.TRAINED_MODEL.name,
                                States.FINISHED.name)
                notification_rapp(trainingjob.id)
            else:
                errMsg = "Trained model is not available  "
                LOGGER.error(errMsg + str(trainingjob_id))
                change_status_tj(trainingjob_id,
                                Steps.TRAINED_MODEL.name,
                                States.FAILED.name)
                notification_rapp(trainingjob.id)
                raise TMException(errMsg + str(trainingjob_id))
        else:
            LOGGER.error("Pipeline notification -Training failed " + str(trainingjob_id)) 
            change_status_tj(trainingjob_id,
                            Steps.TRAINING.name,
                            States.FAILED.name)
            notification_rapp(trainingjob.id)
            raise TMException("Pipeline not successful for " + str(trainingjob_id) +
                              ", request json from kf adapter is: " + json.dumps(request.json))
    except Exception as err:
        #Training failure response
        LOGGER.error("Pipeline notification failed" + str(err))
        try:
            notification_rapp(trainingjob.id)
            change_state_to_failed(trainingjob.id)
        except Exception as e:
            if "the change_steps_state to failed" in str(e):
                LOGGER.error(f"failed to update the status of trainingjob to FAILED due to {str(err)}")
        return jsonify({"Error":"Training Failed"}), 500

    return jsonify({"Message":"Training successful"}), 200

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
