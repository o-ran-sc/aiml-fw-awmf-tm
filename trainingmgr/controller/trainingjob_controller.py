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
from flask import Blueprint, jsonify, request
from flask_api import status
from marshmallow import ValidationError
from trainingmgr.common.exceptions_utls import TMException
from trainingmgr.common.trainingmgr_config import TrainingMgrConfig
from trainingmgr.schemas.trainingjob_schema import TrainingJobSchema
from trainingmgr.service.training_job_service import delete_training_job, create_training_job, get_training_job, get_trainingjob_by_modelId, get_trainining_jobs,\
get_steps_state
from trainingmgr.common.trainingmgr_util import check_key_in_dictionary
from trainingmgr.common.trainingConfig_parser import validateTrainingConfig

training_job_controller = Blueprint('training_job_controller', __name__)
LOGGER = TrainingMgrConfig().logger

trainingjob_schema = TrainingJobSchema()
trainingjobs_schema = TrainingJobSchema(many=True)

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

@training_job_controller.route('/retraining-jobs', methods=['POST'])
def create_retrainingjob():
    try:
        request_json = request.get_json()

        # Check if 'modelLocation' field is present in the request
        model_location = request_json.get('modelLocation', None)

        if model_location:
            #check if the field modelLocation was populated the in POST request 
            return jsonify({"Message": f"Retraining job initiated for model at {model_location}"}), 200

        if check_key_in_dictionary(["training_config"], request_json):
            request_json['training_config'] = json.dumps(request_json["training_config"])
        else:
            return jsonify({'Exception': 'The training_config is missing'}), status.HTTP_400_BAD_REQUEST
 
        trainingjob = trainingjob_schema.load(request_json)
        model_id = trainingjob.modelId
        trainingConfig = trainingjob.training_config

        if not validateTrainingConfig(trainingConfig):
            return jsonify({'Exception': 'The TrainingConfig is not correct'}), status.HTTP_400_BAD_REQUEST

        trainingjob_db = get_trainingjob_by_modelId(model_id)

        create_training_job(trainingjob)
        return jsonify({"Retrainingjob": trainingjob_schema.dump(trainingjob)}), 201

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