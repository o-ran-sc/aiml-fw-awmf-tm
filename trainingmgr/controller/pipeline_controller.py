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

from flask import Blueprint, jsonify, request
from flask_api import status
from trainingmgr.common.exceptions_utls import TMException
from trainingmgr.service.pipeline_service import get_single_pipeline, get_all_pipeline_versions, get_all_pipelines, \
    upload_pipeline_service
from trainingmgr.common.trainingmgr_config import TrainingMgrConfig
import traceback
import re

pipeline_controller = Blueprint('pipeline_controller', __name__)
LOGGER = TrainingMgrConfig().logger

@pipeline_controller.route('/pipelines/<pipeline_name>', methods=['GET'])
def get_pipeline_info_by_name(pipeline_name):
    LOGGER.debug(f"Your Controller: Request to get information for pipeline: {pipeline_name}")
    try:
        pipeline_info = get_single_pipeline(pipeline_name)
        if pipeline_info:
            return jsonify({"pipeline_info": pipeline_info}), status.HTTP_200_OK
        else:
            return jsonify({"error": f"Pipeline '{pipeline_name}' not found"}), status.HTTP_404_NOT_FOUND
    except TMException as err:
        LOGGER.error(f"TrainingManager exception: {str(err)}")
        return jsonify({"error": str(err)}), status.HTTP_404_NOT_FOUND
    except Exception as err:
        LOGGER.error(f"Unexpected error in get_pipeline_info_by_name: {str(err)}")
        return jsonify({"error": "An unexpected error occurred"}), status.HTTP_500_INTERNAL_SERVER_ERROR
    
    
@pipeline_controller.route("/pipelines/<pipeline_name>/versions", methods=['GET'])
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
    try:
        version_list = get_all_pipeline_versions(pipeline_name)
        if version_list is None:
            # Signifies Pipeline doesn't exist
            return jsonify({"error": f"Pipeline '{pipeline_name}' not found"}), status.HTTP_404_NOT_FOUND
        
        return jsonify(version_list), status.HTTP_200_OK
        
    except Exception as err:
        LOGGER.error(str(err))
        return jsonify({"Exception": str(err)}), status.HTTP_500_INTERNAL_SERVER_ERROR

    
@pipeline_controller.route('/pipelines', methods=['GET'])
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
    try:
        pipelines = get_all_pipelines()
        return jsonify(pipelines), status.HTTP_200_OK
    except Exception as err:
        LOGGER.error(str(err))
        return jsonify({"Exception": str(err)}, status.HTTP_500_INTERNAL_SERVER_ERROR)
    
@pipeline_controller.route("/pipelines/<pipeline_name>/upload", methods=['POST'])
def upload_pipeline(pipeline_name):
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
    LOGGER.debug("Your Controller: Request to upload pipeline.")
    try:
        LOGGER.debug(str(request))
        LOGGER.debug(str(request.files))
        # Validate Pipeline_name
        PATTERN = re.compile(r"\w+")
        if not re.fullmatch(PATTERN, pipeline_name):
            LOGGER.error(f"Pipeline name {pipeline_name} is not correct")
            return jsonify({'result': f"Pipeline name {pipeline_name} is not correct"}), status.HTTP_500_INTERNAL_SERVER_ERROR
            
        # Check if file is uploaded and name of file is correct
        if 'file' in request.files:
            uploaded_file = request.files['file']
        else:
            tbk = traceback.format_exc()
            LOGGER.error(tbk)
            return jsonify({'result': "Error while uploading pipeline| File not found in request.files"}), status.HTTP_500_INTERNAL_SERVER_ERROR
        
        LOGGER.debug("Uploading received for %s", uploaded_file.filename)
        
        if uploaded_file.filename == '':
            tbk = traceback.format_exc()
            LOGGER.error(tbk)
            return jsonify({'result': "Error while uploading pipeline| Filename is not found in request.files"}), status.HTTP_500_INTERNAL_SERVER_ERROR
        description = ''
        if 'description' in request.form:
            description = request.form['description']
        
        # If the below fxn doesn't fails, It means the file is uploaded successfully
        upload_pipeline_service(pipeline_name, uploaded_file, description)
        return jsonify({'result': f"Pipeline uploaded {pipeline_name} Sucessfully!"}), status.HTTP_200_OK
    except TMException as err:
        return jsonify({'result': err.message}), status.HTTP_500_INTERNAL_SERVER_ERROR
    except Exception as err:
        return jsonify({'result': "Error in uploading Pipeline| Error : " + str(err)}), status.HTTP_500_INTERNAL_SERVER_ERROR
