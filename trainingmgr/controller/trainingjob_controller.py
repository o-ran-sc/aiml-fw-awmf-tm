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

import json
from threading import Lock
from flask import Blueprint, jsonify, request
from flask_api import status
from marshmallow import ValidationError
from trainingmgr.common.exceptions_utls import TMException
from trainingmgr.common.trainingmgr_config import TrainingMgrConfig
from trainingmgr.schemas.trainingjob_schema import TrainingJobSchema
from trainingmgr.service.training_job_service import delete_training_job, create_training_job, get_training_job, get_trainingjob_by_modelId, get_trainining_jobs, \
get_steps_state, change_status_tj, get_data_extraction_in_progress_trainingjobs
from trainingmgr.common.trainingmgr_util import check_key_in_dictionary
from trainingmgr.common.trainingmgr_operations import data_extraction_start
from trainingmgr.common.trainingConfig_parser import validateTrainingConfig, getField
from trainingmgr.service.featuregroup_service import get_featuregroup_by_name
from trainingmgr.constants.steps import Steps
from trainingmgr.constants.states import States
from trainingmgr.handler.async_handler import DATAEXTRACTION_JOBS_CACHE

training_job_controller = Blueprint('training_job_controller', __name__)
LOGGER = TrainingMgrConfig().logger
TRAININGMGR_CONFIG_OBJ = TrainingMgrConfig()
LOCK = Lock()

trainingjob_schema = TrainingJobSchema()
trainingjobs_schema = TrainingJobSchema(many=True)
MIMETYPE_JSON = "application/json"

@training_job_controller.route('/training-jobs/<int:training_job_id>', methods=['DELETE'])
def delete_trainingjob(training_job_id):
    LOGGER.debug(f'delete training job : {training_job_id}')
    try:
        if delete_training_job(str(training_job_id)):
            LOGGER.debug(f'training job with {training_job_id} is deleted successfully.')
            return '', 204
        else:
            LOGGER.debug(f'training job with {training_job_id} does not exist.')
            return jsonify({
                'message': 'training job with given id is not found'
            }), 500 
         
    except Exception as e:
        return jsonify({
            'message': str(e)
        }), 500
    
    
@training_job_controller.route('/training-jobs', methods=['POST'])
def create_trainingjob():

    try:

        request_json = request.get_json()

        if check_key_in_dictionary(["training_config"], request_json):
            request_json['training_config'] = json.dumps(request_json["training_config"])
        else:
            return jsonify({'Exception': 'The training_config is missing'}), status.HTTP_400_BAD_REQUEST
        
        trainingjob = trainingjob_schema.load(request_json)

        model_id = trainingjob.modelId
        
        trainingConfig = trainingjob.training_config
        if(not validateTrainingConfig(trainingConfig)):
            return jsonify({'Exception': 'The TrainingConfig is not correct'}), status.HTTP_400_BAD_REQUEST
        
        #check if trainingjob is already present with name
        trainingjob_db = get_trainingjob_by_modelId(model_id)

        if trainingjob_db != None:
            return jsonify({"Exception":f"modelId {model_id.modelname} and {model_id.modelversion} is already present in database"}), status.HTTP_409_CONFLICT

        create_training_job(trainingjob)

        return jsonify({"Trainingjob": trainingjob_schema.dump(trainingjob)}), 201
        
    except ValidationError as error:
        return jsonify(error.messages), status.HTTP_400_BAD_REQUEST
    except Exception as e:
        return jsonify({
            'message': str(e)
        }), 500

@training_job_controller.route('/training-jobs/', methods=['GET'])
def get_trainingjobs():
    LOGGER.debug(f'get the trainingjobs')
    try:
        resp = trainingjob_schema.dump(get_trainining_jobs())
        return jsonify(resp), 200
    except TMException as err:
        return jsonify({
            'message': str(err)
        }), 400
    except Exception as e:
        return jsonify({
            'message': str(e)
        }), 500

@training_job_controller.route('/training-jobs/<int:training_job_id>', methods=['GET'])
def get_trainingjob(training_job_id):
    LOGGER.debug(f'get the trainingjob correspoinding to id: {training_job_id}')
    try:
        return jsonify(trainingjob_schema.dump(get_training_job(training_job_id))), 200
    except TMException as err:
        return jsonify({
            'message': str(err)
        }), 400
    except Exception as e:
        return jsonify({
            'message': str(e)
        }), 500

@training_job_controller.route('/training-jobs/<int:training_job_id>/status', methods=['GET'])
def get_trainingjob_status(training_job_id):
    LOGGER.debug(f'request to get the training_job status of {training_job_id}')
    try:
        status = get_steps_state(training_job_id)
        return jsonify(json.loads(status)), 200
    except Exception as err:
        return jsonify({
            'message': str(err)
        }), 500

@training_job_controller.route('/training-jobs/<int:training_job_id>/training', methods=['POST'])
def training(training_job_id):
    """
    Rest end point to start training job.
    It calls data extraction module for data extraction and other training steps

    Args in function:
        training_job_id: str
            id of trainingjob.

    Args in json:
        not required json

    Returns:
        json:
            training_job_id: str
                name of trainingjob
            result: str
                route of data extraction module for getting data extraction status of
                given training_job_id .
        status code:
            HTTP status code 200

    Exceptions:
        all exception are provided with exception message and HTTP status code.
    """

    LOGGER.debug("Request for training trainingjob  %s ", training_job_id)
    try:
        trainingjob = get_training_job(training_job_id)
        trainingjob_name = trainingjob.trainingjob_name
        featuregroup= get_featuregroup_by_name(getField(trainingjob.training_config, "feature_group_name"))
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
        de_response = data_extraction_start(TRAININGMGR_CONFIG_OBJ, featuregroup.featuregroup_name,
                                        feature_list_string, query_filter, datalake_source,
                                        _measurement, influxdb_info_dic, training_job_id)
        if (de_response.status_code == status.HTTP_200_OK ):
            LOGGER.debug("Response from data extraction for " + \
                    trainingjob_name + " : " + json.dumps(de_response.json()))
            change_status_tj(trainingjob,
                                Steps.DATA_EXTRACTION.name,
                                States.IN_PROGRESS.name)
            with LOCK:
                DATAEXTRACTION_JOBS_CACHE[trainingjob] = "Scheduled"
        elif( de_response.headers['content-type'] == MIMETYPE_JSON ) :
            errMsg = "Data extraction responded with error code."
            LOGGER.error(errMsg)
            json_data = de_response.json()
            LOGGER.debug(str(json_data))
            if check_key_in_dictionary(["result"], json_data):
                return jsonify({
                    "message": json.dumps({"Failed":errMsg + json_data["result"]})
                }), 500
            else:
                return jsonify({
                    "message": errMsg
                }), 500
        else:
                return jsonify({
                    "message": "failed data extraction"
                }), 500
    except TMException as err:
        if "No row was found when one was required" in str(err):
            return jsonify({
                    'message': str(err)
                }), 404 
    except Exception as e:
        # print(traceback.format_exc())
        # response_data =  {"Exception": str(err)}
        LOGGER.debug("Error is training, job id: " + str(training_job_id)+" " + str(e))   
        return jsonify({
            'message': str(e)
        }), 500      
    return '', 200