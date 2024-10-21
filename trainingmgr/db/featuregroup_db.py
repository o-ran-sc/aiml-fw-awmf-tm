from trainingmgr.common.exceptions_utls import DBException
from psycopg2.errorcodes import UNIQUE_VIOLATION
from psycopg2 import errors
from trainingmgr.models import db, FeatureGroup

DB_QUERY_EXEC_ERROR = "Failed to execute query in "

def add_featuregroup(featuregroup):
    """
    This function add the new row or update existing row with given information
    """
    try:
        db.session.add(featuregroup)
        db.session.commit()
    except errors.lookup(UNIQUE_VIOLATION) as e:
        raise DBException(DB_QUERY_EXEC_ERROR + " "+ str(e))
    except Exception as err:
        db.session.rollback()
        raise DBException(DB_QUERY_EXEC_ERROR + " failed to add feature group")

def edit_featuregroup(featuregroup_name, featuregroup):
    """
    This function update existing row with given information
    """
    
    featuregroup_info = FeatureGroup.query.filter_by(featuregroup_name=featuregroup_name).first()
    for key, value in featuregroup.items():
        if(key == 'id'):
            continue
        setattr(featuregroup_info, key, value)

    try:
        db.session.commit()
    except Exception as err:
        raise DBException(DB_QUERY_EXEC_ERROR+"failed to update the "+ featuregroup_name+ str(err))
    
    return

def get_feature_groups_db():
    """
    This function returns feature_groups
    """
    featureGroups = FeatureGroup.query.all()
    return featureGroups

def get_feature_group_by_name_db(featuregroup_name):
    """
    This Function return a feature group with name "featuregroup_name"
    """
    return FeatureGroup.query.filter_by(featuregroup_name=featuregroup_name).first()

def delete_feature_group_by_name(featuregroup_name):
    """
    This function is used to delete the feature group from db
    """
    featuregroup = FeatureGroup.query.filter_by(featuregroup_name = featuregroup_name).first()
    if featuregroup:
        db.session.delete(featuregroup)
        db.session.commit()
    return

