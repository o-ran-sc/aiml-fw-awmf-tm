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

import datetime
import re
import json
from trainingmgr.common.exceptions_utls import DBException
from trainingmgr.common.trainingConfig_parser import getField
from trainingmgr.models import db, TrainingJob, TrainingJobStatus, ModelID
from trainingmgr.constants.steps import Steps
from trainingmgr.constants.states import States
from sqlalchemy.sql import func
from sqlalchemy.exc import NoResultFound




DB_QUERY_EXEC_ERROR = "Failed to execute query in "
PATTERN = re.compile(r"\w+")

def get_all_versions_info_by_name(trainingjob_name):
    """
    This function returns information of given trainingjob_name for all version.
    """   
    return TrainingJob.query.filter_by(trainingjob_name=trainingjob_name).all()


def get_trainingjob_info_by_name(trainingjob_name):
    """
    This function returns information of training job by name and 
    by default latest version
    """

    try:
        trainingjob_max_version = TrainingJob.query.filter(TrainingJob.trainingjob_name == trainingjob_name).order_by(TrainingJob.version.desc()).first()
    except Exception as err:
        raise DBException(DB_QUERY_EXEC_ERROR + \
            "get_trainingjob_info_by_name"  + str(err))
    return trainingjob_max_version

def add_update_trainingjob(trainingjob, adding):
    """
    This function add the new row or update existing row with given information
    """

    try:
        # arguments_string = json.dumps({"arguments": trainingjob.arguments})
        datalake_source_dic = {}
        # Needs to be populated from feature_group
        # datalake_source_dic[trainingjob.datalake_source] = {}
        # trainingjob.datalake_source = json.dumps({"datalake_source": datalake_source_dic}) 
        trainingjob.creation_time = datetime.datetime.utcnow()
        trainingjob.updation_time = trainingjob.creation_time
        steps_state = {
            Steps.DATA_EXTRACTION.name: States.NOT_STARTED.name,
            Steps.DATA_EXTRACTION_AND_TRAINING.name: States.NOT_STARTED.name,
            Steps.TRAINING.name: States.NOT_STARTED.name,
            Steps.TRAINING_AND_TRAINED_MODEL.name: States.NOT_STARTED.name,
            Steps.TRAINED_MODEL.name: States.NOT_STARTED.name
        }
        training_job_status = TrainingJobStatus(states= json.dumps(steps_state))
        db.session.add(training_job_status)
        db.session.commit()     #to get the steps_state id

        trainingjob.deletion_in_progress = False
        trainingjob.version = 1
        
        if not adding:
            trainingjob_max_version = db.session.query(TrainingJob).filter(TrainingJob.trainingjob_name == trainingjob.trainingjob_name).order_by(TrainingJob.version.desc()).first()
            if  getField(trainingjob_max_version.training_config, "enable_versioning"):
                trainingjob.version = trainingjob_max_version.version + 1
                db.session.add(trainingjob)
            else:
                for attr in vars(trainingjob):
                    if(attr == 'id' or attr == '_sa_instance_state'):
                        continue
                    setattr(trainingjob_max_version, attr, getattr(trainingjob, attr))

        else:
            trainingjob.steps_state_id = training_job_status.id
            db.session.add(trainingjob)
        db.session.commit()

    except Exception as err:
        raise DBException(DB_QUERY_EXEC_ERROR + \
            "add_update_trainingjob"  + str(err))
    
def get_info_by_version(trainingjob_name, version):
    """
    This function returns information for given <trainingjob_name, version> trainingjob.
    """

    try:
        trainingjob = TrainingJob.query.filter(TrainingJob.trainingjob_name == trainingjob_name).filter(TrainingJob.version == version).first()
    except Exception as err:
        raise DBException(DB_QUERY_EXEC_ERROR + \
            "get_info_by_version"  + str(err))
    return trainingjob

def get_steps_state_db(trainingjob_name, version):
    """
    This function returns steps_state value of <trainingjob_name, version> trainingjob as tuple of list.
    """

    try:
        steps_state = TrainingJob.query.filter(TrainingJob.trainingjob_name == trainingjob_name).filter(TrainingJob.version == version).first().steps_state.states
    except Exception as err:
        raise DBException("Failed to execute query in get_field_of_given_version" + str(err))

    return steps_state

def get_info_of_latest_version(trainingjob_name):
    """
    This function returns information of <trainingjob_name, trainingjob_name trainingjob's latest version>
    usecase.
    """

    try:
        trainingjob_max_version = TrainingJob.query.filter(TrainingJob.trainingjob_name == trainingjob_name).order_by(TrainingJob.version.desc()).first()
    except Exception as err:
        raise DBException("Failed to execute query in get_info_of_latest_version " + str(err))

    return trainingjob_max_version

def get_all_jobs_latest_status_version():
    """
    This function returns all trainingjobs latest version.
    """

    try:
        subquery = (
            db.session.query(
                TrainingJob.trainingjob_name,
                func.max(TrainingJob.version).label('max_version')
                ).group_by(TrainingJob.trainingjob_name)
                .subquery()
        )
        results = (
            db.session.query(TrainingJob)
            .join(subquery, (TrainingJob.trainingjob_name == subquery.c.trainingjob_name) & 
                            (TrainingJob.version == subquery.c.max_version))
            .all()
        )

    except Exception as err:

        raise DBException(DB_QUERY_EXEC_ERROR + \
            "get_all_jobs_latest_status_version"  + str(err))

    return results

def change_steps_state_of_latest_version(trainingjob_name, key, value):
    """
    This function changes steps_state of trainingjob latest version
    """
    try:
        trainingjob_max_version = TrainingJob.query.filter(TrainingJob.trainingjob_name == trainingjob_name).order_by(TrainingJob.version.desc()).first()
        steps_state = json.loads(trainingjob_max_version.steps_state)
        steps_state[key] = value
        trainingjob_max_version.steps_state = json.dumps(steps_state) 
        db.session.commit()
    except Exception as err:
        raise DBException(DB_QUERY_EXEC_ERROR + \
            "change_steps_state_of_latest_version"  + str(err))

def change_in_progress_to_failed_by_latest_version(trainingjob_name):
    """
    This function changes steps_state's key's value to FAILED which is currently
    IN_PROGRESS of <trainingjob_name, trainingjob_name trainingjob's latest version> trainingjob.
    """
    status_changed = False
    try:
        trainingjob_max_version = TrainingJob.query.filter(TrainingJob.trainingjob_name == trainingjob_name).order_by(TrainingJob.version.desc()).first()
        steps_state = json.loads(trainingjob_max_version.steps_state)
        for step in steps_state:
            if steps_state[step] == States.IN_PROGRESS.name:
                steps_state[step] = States.FAILED.name
        trainingjob_max_version.steps_state = json.dumps(steps_state)
        status_changed = True
        db.session.commit()
    except Exception as err:
        raise DBException(DB_QUERY_EXEC_ERROR + \
             "change_in_progress_to_failed_by_latest_version" + str(err))
    return status_changed

def get_field_by_latest_version(trainingjob_name, field):
    """
    This function returns field's value of <trainingjob_name, trainingjob_name trainingjob's latest version>
    trainingjob as tuple of list.
    """

    try:
        trainingjob_max_version = TrainingJob.query.filter(TrainingJob.trainingjob_name == trainingjob_name).order_by(TrainingJob.version.desc()).first()
        result = None
        if field == "notification_url":
            result = trainingjob_max_version.notification_url
        elif field == "model_url":
            result = trainingjob_max_version.model_url
                    
    except Exception as err:
        raise DBException("Failed to execute query in get_field_by_latest_version,"  + str(err))

    return result

def change_field_of_latest_version(trainingjob_name, field, field_value):
    """
    This function updates the field's value for given trainingjob.
    """
    try:
        trainingjob_max_version = TrainingJob.query.filter(TrainingJob.trainingjob_name == trainingjob_name).order_by(TrainingJob.version.desc()).first()
        if field == "notification_url":
            trainingjob_max_version.notification_url = field_value
            trainingjob_max_version.updation_time = datetime.datetime.utcnow()
        if field == "run_id":
            trainingjob_max_version.run_id = field_value
            trainingjob_max_version.updation_time = datetime.datetime.utcnow()
        db.session.commit()
    except Exception as err:
        raise DBException("Failed to execute query in change_field_of_latest_version,"  + str(err))
    
def get_latest_version_trainingjob_name(trainingjob_name):
    """
    This function returns latest version of given trainingjob_name.
    """
    try:
        trainingjob_max_version = TrainingJob.query.filter(TrainingJob.trainingjob_name == trainingjob_name).order_by(TrainingJob.version.desc()).first()

    except Exception as err:
        raise DBException(DB_QUERY_EXEC_ERROR + \
            "get_latest_version_trainingjob_name"  + str(err))
    
    return trainingjob_max_version.version

def update_model_download_url(trainingjob_name, version, url):
    """
    This function updates model download url for given <trainingjob_name, version>.
    """
    try:

        trainingjob_max_version = TrainingJob.query.filter(TrainingJob.trainingjob_name == trainingjob_name).filter(TrainingJob.version == version).first()
        trainingjob_max_version.model_url = url
        db.session.commit()
    except Exception as err:
        raise DBException(DB_QUERY_EXEC_ERROR + \
            "update_model_download_url"  + str(err))

def change_field_value_by_version(trainingjob_name, version, field, field_value):
    """
    This function updates field's value to field_value of <trainingjob_name, version> trainingjob.
    """
    conn = None
    try:
        if field == "deletion_in_progress":
            trainingjob = TrainingJob.query.filter(TrainingJob.trainingjob_name == trainingjob_name).filter(TrainingJob.version == version).first()
            trainingjob.deletion_in_progress = field_value
            trainingjob.updation_time = datetime.datetime.utcnow()
            db.session.commit()
    except Exception as err:
        raise DBException("Failed to execute query in change_field_value_by_version," + str(err))
     
def change_field_value(traininigjob_id, field, value):
    """
    This function updates field's value to field_value of trainingjob.
    """
    try:
        trainingjob = TrainingJob.query.filter(TrainingJob.id==traininigjob_id).one()
        setattr(trainingjob, field, value)
        db.session.commit()
    except Exception as err:
        raise DBException("Failed to execute query in change_field_value," + str(err))

def delete_trainingjob_version(trainingjob_name, version):
    """
    This function deletes the trainingjob entry by <trainingjob_name, version> .
    """

    try:
        trainingjob = TrainingJob.query.filter(TrainingJob.trainingjob_name == trainingjob_name).filter(TrainingJob.version == version).first()
        if trainingjob:
            db.session.delete(trainingjob)
        db.session.commit()
 
    except Exception as err:
        raise DBException(DB_QUERY_EXEC_ERROR + \
            "delete_trainingjob_version" + str(err))

def create_trainingjob(trainingjob):
        
        steps_state = {
            Steps.DATA_EXTRACTION.name: States.NOT_STARTED.name,
            Steps.DATA_EXTRACTION_AND_TRAINING.name: States.NOT_STARTED.name,
            Steps.TRAINING.name: States.NOT_STARTED.name,
            Steps.TRAINING_AND_TRAINED_MODEL.name: States.NOT_STARTED.name,
            Steps.TRAINED_MODEL.name: States.NOT_STARTED.name
        }

        try:
            training_job_status = TrainingJobStatus(states= json.dumps(steps_state))
            db.session.add(training_job_status)
            db.session.commit()     #to get the steps_state id

            trainingjob.steps_state_id = training_job_status.id
            db.session.add(trainingjob)
            db.session.commit()
        except Exception as err:
            raise DBException(f'{DB_QUERY_EXEC_ERROR} in the create_trainingjob : {str(err)}')

def delete_trainingjob_by_id(id: int):
    """
    This function delets the trainingjob using the id which is PK

    Args:
        id (int): Primary key ID of the trainingjob
    
    Returns:
        bool: True if the trainingjob was not found and dleted, false if not found.
    """
    try:
        tj = db.session.query(TrainingJob).get(id)
        if tj:
            db.session.delete(tj)
            db.session.commit()
            return True
    
    except NoResultFound:
        return False
    except Exception as e:
        db.session.rollback()
        raise DBException(f'{DB_QUERY_EXEC_ERROR} : {str(e)}' )

def get_trainingjob(id: int=None):
    if id is not None:
        try:
            tj = TrainingJob.query.filter(TrainingJob.id==id).one()
            return tj
        except NoResultFound as err:
            raise DBException(f"Failed to get trainingjob by id: {id} due to {str(err)}")
    else:
        tjs = TrainingJob.query.all()
        return tjs

def get_trainingjob_by_modelId_db(model_id):
    try:
        trainingjob = (
            db.session.query(TrainingJob)
            .join(ModelID)
            .filter(
                ModelID.modelname == model_id.modelname,
                ModelID.modelversion == model_id.modelversion
            )
            .one()
        )
        return trainingjob
    except NoResultFound:
        return None
    except Exception as e:
        raise DBException(f'{DB_QUERY_EXEC_ERROR} in the get_trainingjob_by_modelId_db : {str(e)}')
    
def change_steps_state(trainingjob, step: Steps, state:States):
    try:
        steps_state = json.loads(trainingjob.steps_state.states)
        steps_state[step] = state
        trainingjob.steps_state.states=json.dumps(steps_state)
        db.session.add(trainingjob)
        db.session.commit()
    except Exception as e:
        raise DBException(f'{DB_QUERY_EXEC_ERROR} in the change_steps_state : {str(e)}')