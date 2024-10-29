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
# ==============================================================================

import datetime
import json
from trainingmgr.common.exceptions_utls import DBException
from trainingmgr.models import db, TrainingJob
from trainingmgr.constants.steps import Steps
from trainingmgr.constants.states import States



DB_QUERY_EXEC_ERROR = "Failed to execute query in "


def get_all_versions_info_by_name(trainingjob_name):
    """
    This function returns information of given trainingjob_name for all version.
    """   
    return TrainingJob.query.filter_by(trainingjob_name=trainingjob_name).all()

def add_update_trainingjob(trainingjob, adding):
    """
    This function add the new row or update existing row with given information
    """

    try:
        # arguments_string = json.dumps({"arguments": trainingjob.arguments})
        datalake_source_dic = {}
        datalake_source_dic[trainingjob.datalake_source] = {}
        trainingjob.datalake_source = json.dumps({"datalake_source": datalake_source_dic})
        trainingjob.creation_time = datetime.datetime.utcnow()
        trainingjob.updation_time = trainingjob.creation_time
        run_id = "No data available"
        steps_state = {
            Steps.DATA_EXTRACTION.name: States.NOT_STARTED.name,
            Steps.DATA_EXTRACTION_AND_TRAINING.name: States.NOT_STARTED.name,
            Steps.TRAINING.name: States.NOT_STARTED.name,
            Steps.TRAINING_AND_TRAINED_MODEL.name: States.NOT_STARTED.name,
            Steps.TRAINED_MODEL.name: States.NOT_STARTED.name
        }
        trainingjob.steps_state=json.dumps(steps_state)
        trainingjob.model_url = "No data available."
        trainingjob.deletion_in_progress = False
        trainingjob.version = 1
        if not adding:

            trainingjob_max_version = db.session.query(TrainingJob).filter(TrainingJob.trainingjob_name == trainingjob.trainingjob_name).order_by(TrainingJob.version.desc()).first()
            
            if trainingjob.enable_versioning:
                trainingjob.version = trainingjob_max_version.version + 1
                db.session.add(trainingjob)
            else:

                for key, value in trainingjob.items():
                    if(key == 'id'):
                        continue
                    setattr(trainingjob_max_version, key, value)

        else:
            db.session.add(trainingjob)
        db.session.commit()

    except Exception as err:
        raise DBException(DB_QUERY_EXEC_ERROR + \
            "add_update_trainingjob"  + str(err))

def get_trainingjob_info_by_name(trainingjob):
    """
    This function returns information of training job by name and 
    by default latest version
    """

    try:
        trainingjob_max_version = TrainingJob.query().filter(TrainingJob.trainingjob_name == trainingjob.trainingjob_name).order_by(TrainingJob.version.desc()).first()
    except Exception as err:
        raise DBException(DB_QUERY_EXEC_ERROR + \
            "get_trainingjob_info_by_name"  + str(err))
    return trainingjob_max_version

def get_info_by_version(trainingjob_name, version):
    """
    This function returns information for given <trainingjob_name, version> trainingjob.
    """

    try:
        trainingjob = TrainingJob.query().filter(TrainingJob.trainingjob_name == trainingjob.trainingjob_name).first()
    except Exception as err:
        raise DBException(DB_QUERY_EXEC_ERROR + \
            "get_info_by_version"  + str(err))
    return trainingjob

def get_steps_state_db(trainingjob_name, version):
    """
    This function returns steps_state value of <trainingjob_name, version> trainingjob as tuple of list.
    """

    try:
        steps_state = TrainingJob.query().filter(TrainingJob.trainingjob_name == trainingjob_name, TrainingJob.version == version).first().steps_state
    except Exception as err:
        raise DBException("Failed to execute query in get_field_of_given_version" + str(err))

    return steps_state