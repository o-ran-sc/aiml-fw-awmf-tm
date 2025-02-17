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
from trainingmgr.service.training_job_service import delete_training_job, create_training_job, get_training_job, get_trainining_jobs, \
get_steps_state
from trainingmgr.common.trainingmgr_util import check_key_in_dictionary
from trainingmgr.common.trainingConfig_parser import validateTrainingConfig
from trainingmgr.service.mme_service import get_modelinfo_by_modelId_service
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
        if delete_training_job(int(training_job_id)):
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
        LOGGER.debug(f"request for training with json {request.get_json()}")
        request_json = request.get_json()

        if check_key_in_dictionary(["training_config"], request_json):
            request_json['training_config'] = json.dumps(request_json["training_config"])
        else:
            return jsonify({'Exception': 'The training_config is missing'}), status.HTTP_400_BAD_REQUEST
        
        trainingjob = trainingjob_schema.load(request_json)

        trainingConfig = trainingjob.training_config
        if(not validateTrainingConfig(trainingConfig)):
            return jsonify({'Exception': 'The TrainingConfig is not correct'}), status.HTTP_400_BAD_REQUEST
        
        model_id = trainingjob.modelId
        registered_model_list = get_modelinfo_by_modelId_service(model_id.modelname, model_id.modelversion)
        # Verify if the modelId is registered over mme or not
        if registered_model_list is None:
            return jsonify({"Exception":f"Model name = {model_id.modelname} and Model version = {model_id.modelversion} is not registered at MME, Please first register at MME and then continue"}), status.HTTP_400_BAD_REQUEST

        registered_model_dict = registered_model_list[0]
        if registered_model_dict["modelLocation"] != trainingjob.model_location:
            return jsonify({"Exception":f"Model name = {model_id.modelname} and Model version = {model_id.modelversion} and trainingjob created does not have same modelLocation, Please first register at MME properly and then continue"}), status.HTTP_400_BAD_REQUEST
        
        return create_training_job(trainingjob=trainingjob, registered_model_dict= registered_model_dict)
        
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
        resp = trainingjobs_schema.dump(get_trainining_jobs())
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
