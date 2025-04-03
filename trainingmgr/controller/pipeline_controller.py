# ==================================================================================
#
#       Copyright (c) 2025 Samsung Electronics Co., Ltd. All Rights Reserved.
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

from flask import Blueprint, request, jsonify
from flask_api import status
from trainingmgr.common.exceptions_utls import TMException
from trainingmgr.service.pipeline_service import (
    get_single_pipeline, get_all_pipeline_versions, get_all_pipelines,
    upload_pipeline_service, list_experiments_service
)
from trainingmgr.schemas.problemdetail_schema import ProblemDetails
from trainingmgr.common.trainingmgr_config import TrainingMgrConfig
from trainingmgr.schemas.problemdetail_schema import ProblemDetails
import traceback
import re

pipeline_controller = Blueprint('pipeline_controller', __name__)
LOGGER = TrainingMgrConfig().logger

@pipeline_controller.route('/pipelines/<pipeline_name>', methods=['GET'])
def get_pipeline_info_by_name(pipeline_name):
    LOGGER.debug(f"Request to get information for pipeline: {pipeline_name}")
    try:
        pipeline_info = get_single_pipeline(pipeline_name)
        if pipeline_info:
            return jsonify({"pipeline_info": pipeline_info}), status.HTTP_200_OK
        else:
            return ProblemDetails(404, "Not Found", f"Pipeline '{pipeline_name}' not found.").to_json()
    except TMException as err:
        LOGGER.error(f"TrainingManager exception: {str(err)}")
        return ProblemDetails(404, "Not Found", str(err)).to_json()
    except Exception as err:
        LOGGER.error(f"Unexpected error in get_pipeline_info_by_name: {str(err)}")
        return ProblemDetails(500, "Internal Server Error", f"Error communicating with KFAdapter : {str(err)}").to_json()

@pipeline_controller.route("/pipelines/<pipeline_name>/versions", methods=['GET'])
def get_versions_for_pipeline(pipeline_name):
    LOGGER.debug(f"Request to get all versions for pipeline: {pipeline_name}")
    try:
        version_list = get_all_pipeline_versions(pipeline_name)
        if version_list is None:
            return ProblemDetails(404, "Not Found", f"Pipeline '{pipeline_name}' not found.").to_json()
        return jsonify(version_list), status.HTTP_200_OK
    except Exception as err:
        LOGGER.error(str(err))
        return ProblemDetails(500, "Internal Server Error", str(err)).to_json()

@pipeline_controller.route('/pipelines', methods=['GET'])
def get_pipelines():
    LOGGER.debug("Request to get all pipeline names.")
    try:
        pipelines = get_all_pipelines()
        return jsonify(pipelines), status.HTTP_200_OK
    except Exception as err:
        LOGGER.error(str(err))
        return ProblemDetails(500, "Internal Server Error", str(err)).to_json()

@pipeline_controller.route("/pipelines/<pipeline_name>/upload", methods=['POST'])
def upload_pipeline(pipeline_name):
    LOGGER.debug(f"Request to upload pipeline: {pipeline_name}")
    try:
        PATTERN = re.compile(r"\w+")
        if not re.fullmatch(PATTERN, pipeline_name):
            LOGGER.error(f"Pipeline name '{pipeline_name}' is not correct")
            return ProblemDetails(400, "Bad Request", f"Pipeline name '{pipeline_name}' is not valid.").to_json()
        if 'file' not in request.files:
            LOGGER.error("File not found in request")
            return ProblemDetails(400, "Bad Request", "File not found in request.").to_json()
        uploaded_file = request.files['file']
        if uploaded_file.filename == '':
            LOGGER.error("Filename is missing in request.")
            return ProblemDetails(400, "Bad Request", "Filename is missing in request.").to_json()
        description = request.form.get('description', '')
        upload_pipeline_service(pipeline_name, uploaded_file, description)
        return jsonify({'result': f"Pipeline '{pipeline_name}' uploaded successfully!"}), status.HTTP_200_OK
    except TMException as err:
        return ProblemDetails(500, "Internal Server Error", err.message).to_json()
    except Exception as err:
        LOGGER.error(f"Error in uploading pipeline: {str(err)}")
        return ProblemDetails(500, "Internal Server Error", f"Error in uploading pipeline: {str(err)}").to_json()

@pipeline_controller.route("/pipelines/experiments", methods=['GET'])
def get_all_experiment_names():
    LOGGER.debug("Request to get all experiment names.")
    try:
        experiment_names = list_experiments_service()
        return jsonify(experiment_names), status.HTTP_200_OK
    except Exception as err:
        LOGGER.error(f"Unexpected error in get_experiments: {str(err)}")
        return ProblemDetails(500, "Internal Server Error", f"Unexpected error in get_experiments: {str(err)}").to_json()
