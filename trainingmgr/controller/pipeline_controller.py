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
from trainingmgr.common.exceptions_utls import TMException
from trainingmgr.service.pipeline_service import get_single_pipeline
from trainingmgr.common.trainingmgr_config import TrainingMgrConfig

pipeline_controller = Blueprint('pipeline_controller', __name__)
LOGGER = TrainingMgrConfig().logger

@pipeline_controller.route('/pipelines/<pipeline_name>', methods=['GET'])
def get_pipeline_info_by_name(pipeline_name):
    LOGGER.debug(f"Your Controller: Request to get information for pipeline: {pipeline_name}")
    api_response = {}
    response_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    try:
        pipeline_info = get_single_pipeline(pipeline_name)
        if pipeline_info:
            api_response = {"pipeline_info": pipeline_info}
            response_code = status.HTTP_200_OK
        else:
            api_response = {"error": f"Pipeline '{pipeline_name}' not found"}
            response_code = status.HTTP_404_NOT_FOUND
    except TMException as err:
        api_response = {"error": str(err)}
        response_code = status.HTTP_404_NOT_FOUND
        LOGGER.error(f"TrainingManager exception: {str(err)}")
    except Exception as err:
        api_response = {"error": "An unexpected error occurred"}
        LOGGER.error(f"Unexpected error in get_pipeline_info_by_name: {str(err)}")

    return api_response, response_code