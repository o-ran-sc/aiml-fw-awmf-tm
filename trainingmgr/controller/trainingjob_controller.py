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
from trainingmgr.schemas.problemdetail_schema import ProblemDetails
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
    LOGGER.debug(f'Delete training job : {training_job_id}')
    try:
        if delete_training_job(int(training_job_id)):
            LOGGER.debug(f'Training job {training_job_id} deleted successfully.')
            return '', 204
        else:
            LOGGER.debug(f'Training job {training_job_id} not found.')
            return ProblemDetails(404, "Not Found", f"Training job with ID {training_job_id} does not exist.").to_json()
    except Exception as e:
        LOGGER.error(f"Error deleting training job {training_job_id}: {str(e)}")
        return ProblemDetails(500, "Internal Server Error", str(e)).to_json()

@training_job_controller.route('/training-jobs', methods=['POST'])
def create_trainingjob():
    try:
        LOGGER.debug(f"Request for training job with JSON: {request.get_json()}")
        request_json = request.get_json()
        if not check_key_in_dictionary(["training_config"], request_json):
            return ProblemDetails(400, "Bad Request", "The 'training_config' field is missing.").to_json()
        request_json['training_config'] = json.dumps(request_json["training_config"])
        trainingjob = trainingjob_schema.load(request_json)
        trainingConfig = trainingjob.training_config
        if not validateTrainingConfig(trainingConfig):
            return ProblemDetails(400, "Bad Request", "The provided 'training_config' is not valid.").to_json()
        model_id = trainingjob.modelId
        registered_model_list = get_modelinfo_by_modelId_service(model_id.modelname, model_id.modelversion)
        if registered_model_list is None:
            return ProblemDetails(400, "Bad Request", f"Model '{model_id.modelname}' version '{model_id.modelversion}' is not registered at MME. Please register at MME first.").to_json()
        registered_model_dict = registered_model_list[0]
        if registered_model_dict["modelLocation"] != trainingjob.model_location:
            return ProblemDetails(400, "Bad Request", f"Model '{model_id.modelname}' version '{model_id.modelversion}' does not match the registered model location.").to_json()
        return create_training_job(trainingjob=trainingjob, registered_model_dict=registered_model_dict)
    except ValidationError as error:
        return ProblemDetails(400, "Validation Error", str(error.messages)).to_json()
    except Exception as e:
        LOGGER.error(f"Error creating training job: {str(e)}")
        return ProblemDetails(500, "Internal Server Error", str(e)).to_json()

@training_job_controller.route('/training-jobs/', methods=['GET'])
def get_trainingjobs():
    LOGGER.debug(f'Fetching all training jobs')
    try:
        resp = trainingjobs_schema.dump(get_trainining_jobs())
        return jsonify(resp), 200
    except TMException as err:
        return ProblemDetails(400, "Bad Request", str(err)).to_json()
    except Exception as e:
        LOGGER.error(f"Error fetching training jobs: {str(e)}")
        return ProblemDetails(500, "Internal Server Error", str(e)).to_json()

@training_job_controller.route('/training-jobs/<int:training_job_id>', methods=['GET'])
def get_trainingjob(training_job_id):
    LOGGER.debug(f'Fetching training job {training_job_id}')
    try:
        return jsonify(trainingjob_schema.dump(get_training_job(training_job_id))), 200
    except TMException as err:
        return ProblemDetails(400, "Bad Request", str(err)).to_json()
    except Exception as e:
        LOGGER.error(f"Error fetching training job {training_job_id}: {str(e)}")
        return ProblemDetails(500, "Internal Server Error", str(e)).to_json()


@training_job_controller.route('/training-jobs/<int:training_job_id>/status', methods=['GET'])
def get_trainingjob_status(training_job_id):
    LOGGER.debug(f'Requesting status for training job {training_job_id}')
    try:
        status = get_steps_state(training_job_id)
        return jsonify(json.loads(status)), 200
    except Exception as err:
        LOGGER.error(f"Error fetching status for training job {training_job_id}: {str(err)}")
        return ProblemDetails(500, "Internal Server Error", str(err)).to_json()
