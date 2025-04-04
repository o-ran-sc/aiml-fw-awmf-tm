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
from flask_api import status
from flask import Blueprint, jsonify, request
from marshmallow import ValidationError
from trainingmgr.common.exceptions_utls import DBException
from trainingmgr.common.trainingmgr_operations import create_dme_filtered_data_job
from trainingmgr.common.trainingmgr_util import check_trainingjob_name_or_featuregroup_name
from trainingmgr.db.featuregroup_db import add_featuregroup, delete_feature_group_by_name
from trainingmgr.common.trainingmgr_config import TrainingMgrConfig
from trainingmgr.schemas import FeatureGroupSchema
from trainingmgr.service.featuregroup_service import get_all_featuregroups
from trainingmgr.schemas.problemdetail_schema import ProblemDetails


featuregroup_controller = Blueprint('featuregroup_controller', __name__)
TRAININGMGR_CONFIG_OBJ = TrainingMgrConfig()
LOGGER = TRAININGMGR_CONFIG_OBJ.logger
MIMETYPE_JSON = "application/json"
featuregroups_schema = FeatureGroupSchema(many=True)

@featuregroup_controller.route('/featureGroup', methods=['POST'])
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
    LOGGER.debug('feature Group Create request, ' + json.dumps(request.json))
    try:
        featuregroup = FeatureGroupSchema().load(request.get_json())
        feature_group_name = featuregroup.featuregroup_name
        if (not check_trainingjob_name_or_featuregroup_name(feature_group_name) or
            len(feature_group_name) < 3 or len(feature_group_name) > 63):
            return ProblemDetails(400, "Bad Request", "Failed to create the feature group since feature group not valid").to_json()
        add_featuregroup(featuregroup)
        api_response = FeatureGroupSchema().dump(featuregroup)
        if featuregroup.enable_dme:
            response = create_dme_filtered_data_job(
                TRAININGMGR_CONFIG_OBJ,
                featuregroup.source_name,
                featuregroup.feature_list,
                featuregroup.featuregroup_name,
                featuregroup.host,
                featuregroup.dme_port,
                featuregroup.measured_obj_class
            )
            if response.status_code != 201:
                delete_feature_group_by_name(featuregroup.featuregroup_name)
                return ProblemDetails(
                    400,
                    "Bad Request",
                    "Cannot create dme job | DME Error : " + str(response.json().get("detail", "Unknown error"))
                ).to_json()
        return jsonify(api_response), 201
    except ValidationError as err:
        LOGGER.error(f"ValidationError: {str(err)}")
        return ProblemDetails(400, "Validation Error", str(err)).to_json()
    except DBException as err:
        LOGGER.error(f"DBException: {str(err)}")
        if "already exist" in str(err):
            return ProblemDetails(409, "Conflict", str(err)).to_json()
        return ProblemDetails(400, "Bad Request", str(err)).to_json()
    except Exception as err:
        LOGGER.error(f"Unexpected Error: {str(err)}")
        return ProblemDetails(500, "Internal Server Error", str(err)).to_json()

@featuregroup_controller.route('/featureGroup', methods=['GET'])
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
    try:
        api_response = featuregroups_schema.dump(get_all_featuregroups())
        return jsonify({"FeatureGroups": api_response}), 200
    except Exception as err:
        LOGGER.error(f"Failed to get featuregroups: {str(err)}")
        return ProblemDetails(500, "Internal Server Error", "Failed to get featuregroups").to_json()
