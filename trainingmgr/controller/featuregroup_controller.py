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
from trainingmgr.db.featuregroup_db import add_featuregroup, delete_feature_group_by_name
from trainingmgr.common.trainingmgr_config import TrainingMgrConfig
from trainingmgr.schemas import FeatureGroupSchema



featuregroup_controller = Blueprint('featuregroup_controller', __name__)
TRAININGMGR_CONFIG_OBJ = TrainingMgrConfig()
LOGGER = TRAININGMGR_CONFIG_OBJ.logger

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
    response_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    LOGGER.debug('feature Group Create request, ' + json.dumps(request.json))

    try:
        featuregroup = FeatureGroupSchema().load(request.get_json())

            # the features are stored in string format in the db, and has to be passed as list of feature to the dme. Hence the conversion.
        add_featuregroup(featuregroup)
        api_response={"result": "Feature Group Created"}
        response_code =status.HTTP_200_OK
        if featuregroup.enable_dme == True :
            response= create_dme_filtered_data_job(TRAININGMGR_CONFIG_OBJ, featuregroup)
            if response.status_code != 201:
                api_response={"Exception": "Cannot create dme job"}
                delete_feature_group_by_name(featuregroup)
                response_code=status.HTTP_400_BAD_REQUEST
    except ValidationError as err:
        LOGGER.error(f"Failed to create the feature Group {str(err)}")
        return {"Exception": str(err)}, 400
    except DBException as err:
        LOGGER.error(f"Failed to create the feature Group {str(err)}")
        return {"Exception": str(err)}, 400
    except Exception as e:
        api_response = {"Exception":str(e)}
        LOGGER.error(f"Failed to create the feature Group {str(err)}")
        jsonify(json.dumps(api_response)), 500
    
    return jsonify(api_response), 201