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
from trainingmgr.models import db, TrainingJob, TrainingJobStatus, ModelID
from trainingmgr.constants.steps import Steps
from trainingmgr.constants.states import States
from sqlalchemy.exc import NoResultFound
from sqlalchemy import desc


DB_QUERY_EXEC_ERROR = "Failed to execute query in "
PATTERN = re.compile(r"\w+")

# with current_app.app_context():
#     engine = db.engine
#     SessionFactory = sessionmaker(bind=engine)
#     db_session = scoped_session(SessionFactory)



def change_field_value(trainingjob_id, field, value):
    """
    This function updates field's value to field_value of trainingjob.
    """
    try:
        trainingjob = TrainingJob.query.filter(TrainingJob.id==trainingjob_id).one()
        setattr(trainingjob, field, value)
        db.session.commit()
    except NoResultFound as err:
        raise DBException(f"Failed to execute change_field_value for id: {trainingjob_id}, because id doesn't exist in db")
    except Exception as err:
        raise DBException("Failed to execute query in change_field_value," + str(err))

def get_field_value(trainingjob_id, field):
    """
    This function get field's value to field_value of trainingjob.
    """
    try:
        trainingjob = TrainingJob.query.filter(TrainingJob.id==trainingjob_id).one()
        return getattr(trainingjob, field)
    except NoResultFound as err:
        raise DBException(f"Failed to execute get_field_value for id: {trainingjob_id}, because id doesn't exist in db")
    except Exception as err:
        raise DBException("Failed to execute query in get_field_value," + str(err))

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
    try:
        if id is not None:
            return TrainingJob.query.filter(TrainingJob.id==id).one()
        else:
            tjs = TrainingJob.query.all()
            return tjs
    except NoResultFound:
        # id is not present
        return None
    except Exception as e:
        raise DBException(f'{DB_QUERY_EXEC_ERROR} : {str(e)}' )
        

def change_field_value_by_version(trainingjob_name, version, field, field_value):
    """
    This function updates field's value to field_value of <trainingjob_name, version> trainingjob.
    """
    try:
        if field == "deletion_in_progress":
            trainingjob = TrainingJob.query.filter(TrainingJob.trainingjob_name == trainingjob_name).filter(TrainingJob.version == version).first()
            trainingjob.deletion_in_progress = field_value
            trainingjob.updation_time = datetime.datetime.utcnow()
            db.session.commit()
    except Exception as err:
        raise DBException("Failed to execute query in change_field_value_by_version," + str(err))


def get_trainingjobs_by_model_id_db(model_name, model_version):
    try:
        trainingjobs = (
            db.session.query(TrainingJob)
            .join(ModelID)
            .filter(
                ModelID.modelname == model_name,
                ModelID.modelversion == model_version
            )
            .all()
        )
        return trainingjobs
    except NoResultFound:
        return None
    except Exception as e:
        raise DBException(f'{DB_QUERY_EXEC_ERROR} in the get_trainingjobs_by_model_id_db : {str(e)}')


def change_steps_state(trainingjob_id, step: Steps, state:States):

    try:
        trainingjob = TrainingJob.query.filter(TrainingJob.id==trainingjob_id).one()
        steps_state = json.loads(trainingjob.steps_state.states)
        steps_state[step] = state
        trainingjob.steps_state.states=json.dumps(steps_state)
        db.session.add(trainingjob)
        db.session.commit()
    except Exception as e:
        raise DBException(f'{DB_QUERY_EXEC_ERROR} the change_steps_state : {str(e)}')


def change_state_to_failed(trainingjob_id):

    try:
        trainingjob = TrainingJob.query.filter(TrainingJob.id==trainingjob_id).one()
        steps_state = json.loads(trainingjob.steps_state.states)
        for step in steps_state:
            if steps_state[step] == States.IN_PROGRESS.name:
                steps_state[step] = States.FAILED.name
        trainingjob.steps_state.states=json.dumps(steps_state)
        db.session.add(trainingjob)
        db.session.commit()
    except Exception as e:
        raise DBException(f'{DB_QUERY_EXEC_ERROR} the change_steps_state to failed : {str(e)}')

def change_steps_state_df(trainingjob_id, step: Steps, state:States):
    try:

        trainingjob = TrainingJob.query.filter(TrainingJob.id==trainingjob_id).one()
        steps_state = json.loads(trainingjob.steps_state.states)
        steps_state[step] = state
        trainingjob.steps_state.states=json.dumps(steps_state)
        db.session.add(trainingjob)
        db.session.commit()
    except Exception as e:
        raise DBException(f'{DB_QUERY_EXEC_ERROR} the change_steps_state : {str(e)}')
    
def changeartifact(trainingjob_id, new_artifact_version):
    try:
        trainingjob = TrainingJob.query.filter(TrainingJob.id==trainingjob_id).one()
        trainingjob.modelId.artifactversion = new_artifact_version
        db.session.commit()
    except Exception as err:
        raise DBException(f'{DB_QUERY_EXEC_ERROR} the changeartifact : {str(err)}')
