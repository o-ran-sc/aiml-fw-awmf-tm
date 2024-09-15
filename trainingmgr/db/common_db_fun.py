# ==================================================================================
#
#       Copyright (c) 2022 Samsung Electronics Co., Ltd. All Rights Reserved.
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

"""
This file contains useful database related functions.
"""
import json
import datetime
from trainingmgr.constants.steps import Steps
from trainingmgr.constants.states import States
from trainingmgr.common.exceptions_utls import DBException

tm_table_name = "trainingjob_info" # Table used by 'Training Manager' for training jobs
fg_table_name = "featuregroup_info"  # Table used by 'Training Manager' for Feature Groups
DB_QUERY_EXEC_ERROR = "Failed to execute query in "

def get_data_extraction_in_progress_trainingjobs(ps_db_obj):
    """
    This function returns dictionary with (<trainingjob_name>, Scheduled) key-value pairs,
    <trainingjob_name> is trainingjob name whose data extraction is in progress
    """
    conn = None
    result = {}
    try:
        conn = ps_db_obj.get_new_conn()
        cursor = conn.cursor()
        cursor.execute('''select trainingjob_name, steps_state from {}'''.format(tm_table_name))
        results = cursor.fetchall()
        if results:
            for row in results:
                steps_state = json.loads(row[1])
                if steps_state[Steps.DATA_EXTRACTION.name] == States.IN_PROGRESS.name:
                    result[row[0]] = "Scheduled"
        cursor.close()
    except Exception as err:
        if conn is not None:
            conn.rollback()
        raise DBException(DB_QUERY_EXEC_ERROR + \
            "get_data_extraction_in_progress_trainingjobs," + str(err))
    finally:
        if conn is not None:
                conn.close()
    return result


def change_field_of_latest_version(trainingjob_name, ps_db_obj, field, field_value):
    """
    This function updates the field's value for given trainingjob.
    """
    conn = None
    try:
        conn = ps_db_obj.get_new_conn()
        cursor = conn.cursor()
        cursor.execute('''select nt.mv from (select max(version) mv,trainingjob_name from ''' + \
                       '''{} group by trainingjob_name) nt where nt.trainingjob_name = %s'''.format(tm_table_name),
                       (trainingjob_name,))
        version = int(cursor.fetchall()[0][0])
        if field == "notification_url":
            cursor.execute('''update {} set notification_url=%s,updation_time=%s '''.format(tm_table_name) + \
                           '''where trainingjob_name = %s and version = %s''',
                           (field_value, datetime.datetime.utcnow(), trainingjob_name, version))
        if field == "run_id":
            cursor.execute('''update {} set run_id =%s,updation_time=%s '''.format(tm_table_name) + \
                           '''where trainingjob_name  = %s and version = %s''',
                           (field_value, datetime.datetime.utcnow(), trainingjob_name, version))
        conn.commit()
        cursor.close()
    except Exception as err:
        if conn is not None:
            conn.rollback()
        raise DBException("Failed to execute query in change_field_of_latest_version,"  + str(err))
    finally:
        if conn is not None:
            conn.close()


def change_field_value_by_version(trainingjob_name, version, ps_db_obj, field, field_value):
    """
    This function updates field's value to field_value of <trainingjob_name, version> trainingjob.
    """
    conn = None
    try:
        conn = ps_db_obj.get_new_conn()
        cursor = conn.cursor()
        if field == "deletion_in_progress":
            cursor.execute('''update {} set deletion_in_progress =%s,'''.format(tm_table_name) + \
                           '''updation_time=%s where trainingjob_name  = %s and version = %s''',
                           (field_value, datetime.datetime.utcnow(), trainingjob_name, version))
        conn.commit()
        cursor.close()
    except Exception as err:
        if conn is not None:
            conn.rollback()
        raise DBException("Failed to execute query in change_field_value_by_version," + str(err))
    finally:
        if conn is not None:
            conn.close()


def get_field_by_latest_version(trainingjob_name, ps_db_obj, field):
    """
    This function returns field's value of <trainingjob_name, trainingjob_name trainingjob's latest version>
    trainingjob as tuple of list.
    """
    conn = ps_db_obj.get_new_conn()
    cursor = conn.cursor()
    results = None
    try:
        cursor.execute('''select nt.mv from (select max(version) mv,trainingjob_name from ''' + \
                       '''{} group by trainingjob_name) nt where nt.trainingjob_name = %s'''.format(tm_table_name),
                       (trainingjob_name,))
        version = int(cursor.fetchall()[0][0])
        if field == "notification_url":
            cursor.execute('''select notification_url from {} where '''.format(tm_table_name) + \
                           '''trainingjob_name = %s and version = %s''',
                           (trainingjob_name, version))
        elif field == "model_url":
            cursor.execute('''select model_url from {} where '''.format(tm_table_name) + \
                           '''trainingjob_name = %s and version = %s''',
                           (trainingjob_name, version))
        results = cursor.fetchall() 
        conn.commit()
        cursor.close()                       
    except Exception as err:
        if conn is not None:
            conn.rollback()
        raise DBException("Failed to execute query in get_field_by_latest_version,"  + str(err))
    finally:
        if conn is not None:
            conn.close()
    return results


def get_field_of_given_version(trainingjob_name, version, ps_db_obj, field):
    """
    This function returns field's value of <trainingjob_name, version> trainingjob as tuple of list.
    """
    conn = None
    results = None
    try:
        conn = ps_db_obj.get_new_conn()
        cursor = conn.cursor()
        if field == "steps_state":
            cursor.execute('''select steps_state from {} where '''.format(tm_table_name) + \
                           '''trainingjob_name = %s and version = %s''',
                           (trainingjob_name, version))
        results = cursor.fetchall()
        conn.commit()
        cursor.close()  
    except Exception as err:
        if conn is not None:
            conn.rollback()
        raise DBException("Failed to execute query in get_field_of_given_version" + str(err))
    finally:
        if conn is not None:
            conn.close()
    return results


def change_in_progress_to_failed_by_latest_version(trainingjob_name, ps_db_obj):
    """
    This function changes steps_state's key's value to FAILED which is currently
    IN_PROGRESS of <trainingjob_name, trainingjob_name trainingjob's latest version> trainingjob.
    """
    status_changed = False
    conn = None
    try:
        conn = ps_db_obj.get_new_conn()
        cursor = conn.cursor()
        cursor.execute('''select nt.mv from (select max(version) mv,trainingjob_name from ''' + \
                       '''{} group by trainingjob_name) nt where nt.trainingjob_name = %s'''.format(tm_table_name),
                       (trainingjob_name,))
        version = int(cursor.fetchall()[0][0])
        cursor.execute("select steps_state from {} where trainingjob_name = %s and ".format(tm_table_name) + \
                       "version = %s", (trainingjob_name, version))
        steps_state = json.loads(cursor.fetchall()[0][0])
        for step in steps_state:
            if steps_state[step] == States.IN_PROGRESS.name:
                steps_state[step] = States.FAILED.name
        cursor.execute("update {} set steps_state = %s where trainingjob_name = %s and ".format(tm_table_name) + \
                       "version= %s", (json.dumps(steps_state), trainingjob_name, version))
        status_changed = True
        conn.commit()
        cursor.close() 
    except Exception as err:
        if conn is not None:
            conn.rollback()
        raise DBException(DB_QUERY_EXEC_ERROR + \
             "change_in_progress_to_failed_by_latest_version" + str(err))
    finally:
        if conn is not None:
            conn.close()
    return status_changed


def change_steps_state_of_latest_version(trainingjob_name, ps_db_obj, key, value):
    """
    This function changes steps_state of trainingjob latest version
    """
    conn = None
    try:
        conn = ps_db_obj.get_new_conn()
        cursor = conn.cursor()
        cursor.execute('''select nt.mv from (select max(version) mv,trainingjob_name from ''' + \
                       '''{} group by trainingjob_name) nt where nt.trainingjob_name = %s'''.format(tm_table_name),
                       (trainingjob_name,))
        version = int(cursor.fetchall()[0][0])
        cursor.execute("select steps_state from {} where trainingjob_name = %s and ".format(tm_table_name) + \
                       "version = %s", (trainingjob_name, version))
        steps_state = json.loads(cursor.fetchall()[0][0])
        steps_state[key] = value
        cursor.execute("update {} set steps_state = %s where trainingjob_name = %s and ".format(tm_table_name) + \
                       "version= %s",  (json.dumps(steps_state), trainingjob_name, version))   
        conn.commit()
        cursor.close() 
    except Exception as err:
        if conn is not None:
            conn.rollback()
        raise DBException(DB_QUERY_EXEC_ERROR + \
            "change_steps_state_of_latest_version"  + str(err))
    finally:
        if conn is not None:
            conn.close()


def change_steps_state_by_version(trainingjob_name, version, ps_db_obj, key, value):
    """
    This function change steps_state of given <trainingjob_name, version> trainingjob.
    """
    conn = None
    try:
        conn = ps_db_obj.get_new_conn()
        cursor = conn.cursor()
        cursor.execute("select steps_state from {} where trainingjob_name = %s and ".format(tm_table_name) + \
                       "version = %s", (trainingjob_name, version))
        steps_state = json.loads(cursor.fetchall()[0][0])
        steps_state[key] = value
        cursor.execute("update {} set steps_state = %s where trainingjob_name = %s ".format(tm_table_name) + \
                       "and version= %s", (json.dumps(steps_state), trainingjob_name, version))
        conn.commit()
        cursor.close()
    except Exception as err:
        if conn is not None:
            conn.rollback()
        raise DBException(DB_QUERY_EXEC_ERROR + \
            "change_steps_state_by_version"  + str(err))
    finally:
        if conn is not None:
            conn.close()


def delete_trainingjob_version(trainingjob_name, version, ps_db_obj):
    """
    This function deletes the trainingjob entry by <trainingjob_name, version> .
    """
    conn = None
    try:
        conn = ps_db_obj.get_new_conn()
        cursor = conn.cursor()
        cursor.execute('''delete from {} where trainingjob_name = %s and version = %s'''.format(tm_table_name),
                       (trainingjob_name, version))
        conn.commit()
        cursor.close()
    except Exception as err:
        if conn is not None:
            conn.rollback()
        raise DBException(DB_QUERY_EXEC_ERROR + \
            "delete_trainingjob_version" + str(err))
    finally:
        if conn is not None:
            conn.close()


def get_info_by_version(trainingjob_name, version, ps_db_obj):
    """
    This function returns information for given <trainingjob_name, version> trainingjob.
    """
    conn = None
    results = None
    try:
        conn = ps_db_obj.get_new_conn()
        cursor = conn.cursor()
        cursor.execute(''' select * from {} where trainingjob_name=%s and version=%s'''.format(tm_table_name),
                       (trainingjob_name, version))
        results = cursor.fetchall()
        conn.commit()
        cursor.close()
    except Exception as err:
        if conn is not None:
            conn.rollback()
        raise DBException(DB_QUERY_EXEC_ERROR + \
            "get_info_by_version"  + str(err))
    finally:
        if conn is not None:
            conn.close()
    return results


def get_trainingjob_info_by_name(trainingjob_name, ps_db_obj):
    """
    This function returns information of training job by name and 
    by default latest version
    """
    conn = None
    results = None
    try:
        conn = ps_db_obj.get_new_conn()
        cursor = conn.cursor()
        cursor.execute('''select nt.mv from (select max(version) mv,trainingjob_name ''' + \
                       '''from {} group by trainingjob_name) nt where nt.trainingjob_name=%s'''.format(tm_table_name),
                       (trainingjob_name,))
        version = int(cursor.fetchall()[0][0])
        cursor.execute(''' select * from {} where trainingjob_name=%s and version = %s'''.format(tm_table_name),
                       (trainingjob_name, version))
        results = cursor.fetchall()
        conn.commit()
        cursor.close()
    except Exception as err:
        if conn is not None:
            conn.rollback()
        raise DBException(DB_QUERY_EXEC_ERROR + \
            "get_trainingjob_info_by_name"  + str(err))
    finally:
        if conn is not None:
            conn.close()
    return results

def get_latest_version_trainingjob_name(trainingjob_name, ps_db_obj):
    """
    This function returns latest version of given trainingjob_name.
    """
    conn = None
    version = None
    try:
        conn = ps_db_obj.get_new_conn()
        cursor = conn.cursor()
        cursor.execute('''select nt.mv from (select max(version) mv,trainingjob_name ''' + \
                       '''from {} group by trainingjob_name) nt where nt.trainingjob_name=%s'''.format(tm_table_name),
                       (trainingjob_name,))
        version = int(cursor.fetchall()[0][0])
        conn.commit()
        cursor.close()
    except Exception as err:
        if conn is not None:
            conn.rollback()
        raise DBException(DB_QUERY_EXEC_ERROR + \
            "get_latest_version_trainingjob_name"  + str(err))
    finally:
        if conn is not None:
            conn.close()
    return version


def get_all_versions_info_by_name(trainingjob_name, ps_db_obj):
    """
    This function returns information of given trainingjob_name for all version.
    """   
    conn = None
    results = None
    try:
        conn = ps_db_obj.get_new_conn()
        cursor = conn.cursor()
        cursor.execute(''' select * from  {} where trainingjob_name=%s '''.format(tm_table_name),
                       (trainingjob_name, ))
        results = cursor.fetchall()
        conn.commit()
        cursor.close()
    except Exception as err:
        if conn is not None:
            conn.rollback()
        raise DBException(DB_QUERY_EXEC_ERROR + \
            "get_all_versions_info_by_name"  + str(err))
    finally:
        if conn is not None:
            conn.close()
    return results


def get_all_distinct_trainingjobs(ps_db_obj):
    """
    This function returns all distinct trainingjob_names.
    """
    conn = None
    trainingjobs = []
    try:
        conn = ps_db_obj.get_new_conn()
        cursor = conn.cursor()
        cursor.execute(''' select distinct trainingjob_name from {} '''.format(tm_table_name))
        results = cursor.fetchall()
        for result in results:
            trainingjobs.append(result[0])
        conn.commit()
        cursor.close()
    except Exception as err:
        if conn is not None:
            conn.rollback()
        raise DBException(DB_QUERY_EXEC_ERROR + \
            "get_all_distinct_trainingjobs"  + str(err))
    finally:
        if conn is not None:
            conn.close()

    return trainingjobs


def get_all_version_num_by_trainingjob_name(trainingjob_name, ps_db_obj):
    """
    This function returns all versions of given trainingjob_name.
    """
    conn = None
    versions = []
    try:
        conn = ps_db_obj.get_new_conn()
        cursor = conn.cursor()
        cursor.execute(''' select version from {} where trainingjob_name=%s'''.format(tm_table_name),
                       (trainingjob_name))
        results = cursor.fetchall()
        for result in results:
            versions.append(result[0])
        conn.commit()
        cursor.close()
    except Exception as err:
        if conn is not None:
            conn.rollback()
        raise DBException(DB_QUERY_EXEC_ERROR + \
            "get_all_version_num_by_trainingjob_name"  + str(err))
    finally:
        if conn is not None:
            conn.close()
    
    return versions


def update_model_download_url(trainingjob_name, version, url, ps_db_obj):
    """
    This function updates model download url for given <trainingjob_name, version>.
    """
    conn = None
    try:
        conn = ps_db_obj.get_new_conn()
        cursor = conn.cursor()
        cursor.execute('''update {} set model_url=%s,updation_time=%s '''.format(tm_table_name) + \
                       '''where trainingjob_name=%s and version=%s''',
                       (url, datetime.datetime.utcnow(),
                        trainingjob_name, version))
        conn.commit()
        cursor.close()
    except Exception as err:
        if conn is not None:
            conn.rollback()
        raise DBException(DB_QUERY_EXEC_ERROR + \
            "update_model_download_url"  + str(err))
    finally:
        if conn is not None:
            conn.close()


def add_update_trainingjob(description, pipeline_name, experiment_name, featuregroup_name, arguments,
                          query_filter, adding, enable_versioning,
                          pipeline_version, datalake_source, trainingjob_name, ps_db_obj, notification_url="",
                          is_mme="", model_name="", model_info=""):
    """
    This function add the new row or update existing row with given information
    """


    conn = None
    try:
        arguments_string = json.dumps({"arguments": arguments})
        datalake_source_dic = {}
        datalake_source_dic[datalake_source] = {}
        datalake_source_string = json.dumps({"datalake_source": datalake_source_dic})
        creation_time = datetime.datetime.utcnow()
        updation_time = creation_time
        run_id = "No data available"
        steps_state = {
            Steps.DATA_EXTRACTION.name: States.NOT_STARTED.name,
            Steps.DATA_EXTRACTION_AND_TRAINING.name: States.NOT_STARTED.name,
            Steps.TRAINING.name: States.NOT_STARTED.name,
            Steps.TRAINING_AND_TRAINED_MODEL.name: States.NOT_STARTED.name,
            Steps.TRAINED_MODEL.name: States.NOT_STARTED.name
        }

        model_url = "No data available."
        deletion_in_progress = False
        version = 1
        conn = ps_db_obj.get_new_conn()
        cursor = conn.cursor()
        if not adding:
            cursor.execute('''select nt.mv from (select max(version) mv,trainingjob_name from ''' + \
                       '''{} group by trainingjob_name) nt where nt.trainingjob_name = %s'''.format(tm_table_name),
                       (trainingjob_name,))
            version = int(cursor.fetchall()[0][0])
            
            if enable_versioning:
                version = version + 1
                cursor.execute('''INSERT INTO {} VALUES '''.format(tm_table_name) + \
                               '''(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,''' + \
                               ''' %s,%s,%s,%s,%s,%s,%s,%s)''',
                               (trainingjob_name, description, featuregroup_name, pipeline_name,
                                experiment_name, arguments_string, query_filter,
                                creation_time, run_id, json.dumps(steps_state),
                                updation_time, version,
                                enable_versioning, pipeline_version,
                                datalake_source_string, model_url, notification_url,
                                deletion_in_progress, is_mme, model_name, model_info))
            else:
                cursor.execute('''update {} set description=%s, feature_list=%s, '''.format(tm_table_name) + \
                               '''pipeline_name=%s,experiment_name=%s,arguments=%s,''' + \
                               '''query_filter=%s,creation_time=%s, run_id=%s,''' + \
                               '''steps_state=%s,''' + \
                               '''pipeline_version=%s,updation_time=%s,enable_versioning=%s,''' + \
                               '''datalake_source=%s,''' + \
                               '''model_url=%s, notification_url=%s, ''' + \
                               '''deletion_in_progress=%s, is_mme=%s, model_name=%s , model_info=%s where ''' + \
                               '''trainingjob_name=%s and version=%s''',
                               (description, featuregroup_name, pipeline_name, experiment_name,
                                arguments_string, query_filter, creation_time, run_id,
                                json.dumps(steps_state),
                                pipeline_version, updation_time, enable_versioning,
                                datalake_source_string, model_url, notification_url,
                                deletion_in_progress, is_mme, model_name, model_info, trainingjob_name, version))

        else:
            cursor.execute(''' INSERT INTO {} VALUES '''.format(tm_table_name) + \
                           '''(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,''' + \
                           '''%s,%s,%s,%s,%s,%s,%s,%s, %s)''',
                           (trainingjob_name, description, featuregroup_name, pipeline_name,
                            experiment_name, arguments_string, query_filter, creation_time,
                            run_id, json.dumps(steps_state),
                            updation_time, version, enable_versioning,
                            pipeline_version, datalake_source_string,
                            model_url, notification_url,
                            deletion_in_progress, is_mme, model_name, model_info))
        conn.commit()
        cursor.close()
    except Exception as err:
        if conn is not None:
            conn.rollback()
        raise DBException(DB_QUERY_EXEC_ERROR + \
            "add_update_trainingjob"  + str(err))
    finally:
        if conn is not None:
            conn.close()

def add_featuregroup(feature_group_name, feature_list, datalake_source , host, port, bucket, token, db_org,_measurement, enable_dme, ps_db_obj, measured_obj_class="", dme_port="", source_name=""):
    """
    This function add the new row or update existing row with given information
    """

    conn = None
    conn = ps_db_obj.get_new_conn()
    cursor = conn.cursor()
    
    try:
        cursor.execute(''' INSERT INTO {} VALUES '''.format(fg_table_name) +
                       '''(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s, %s, %s,%s)''',
                       (feature_group_name, feature_list, datalake_source , host, port, bucket, token, db_org,_measurement,enable_dme, measured_obj_class, dme_port, source_name))
        conn.commit()
        cursor.close()
    except Exception as err:
        if conn is not None:
            conn.rollback()
        raise DBException(DB_QUERY_EXEC_ERROR +
                          "add_featuregroup" + str(err))
    finally:
        if conn is not None:
            conn.close()

def edit_featuregroup(feature_group_name, feature_list, datalake_source , host, port, bucket, token, db_org,_measurement, enable_dme, ps_db_obj, measured_obj_class="", dme_port="", source_name=""):
    """
    This function update existing row with given information
    """

    conn = None
    conn = ps_db_obj.get_new_conn()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''update {} set feature_list = %s, datalake_source = %s,
                        host = %s, port = %s, bucket = %s, token = %s, db_org = %s, _measurement = %s,
                        enable_dme = %s, measured_obj_class = %s, dme_port = %s, source_name = %s
                        where featuregroup_name = %s'''.format(fg_table_name),
                    (feature_list, datalake_source, host, port, bucket, token, db_org,
                        _measurement, enable_dme, measured_obj_class, dme_port, source_name, feature_group_name))
        conn.commit()
        cursor.close()
    except Exception as err:
        if conn is not None:
            conn.rollback()
        raise DBException(DB_QUERY_EXEC_ERROR + "update_featuregroup" + str(err))
    finally:
        if conn is not None:
            conn.close()

def get_feature_groups_db(ps_db_obj):
    """
    This function returns feature_groups
    """
    conn=None
    result=()
    try:
        conn=ps_db_obj.get_new_conn()
        cursor=conn.cursor()
        query = '''select * from {}'''.format(fg_table_name)
        cursor.execute(query)
        result=cursor.fetchall()
        conn.commit()
        cursor.close()
    except Exception as err:
        if conn is not None:
            conn.rollback()
        raise DBException(DB_QUERY_EXEC_ERROR + \
            "get_feature_groups"  + str(err))
    finally:
        if conn is not None:
            conn.close()
    return result

def get_feature_group_by_name_db(ps_db_obj, featuregroup_name):
    """
    This Function return a feature group with name "featuregroup_name"
    """
    conn=None
    result=None
    try:
        conn=ps_db_obj.get_new_conn()
        cursor=conn.cursor()
        cursor.execute(''' select * from  {} where featuregroup_name = %s '''.format(fg_table_name),
                       (featuregroup_name, ))
        result=cursor.fetchall()
        conn.commit()
        cursor.close()
    except Exception as err:
        if conn is not None:
            conn.rollback()
        raise DBException(DB_QUERY_EXEC_ERROR + \
            "get_feature_groups"  + str(err))
    finally:
        if conn is not None:
            conn.close()
    return result 

def delete_feature_group_by_name(ps_db_obj, featuregroup_name):
    """
    This function is used to delete the feature group from db
    """
    conn=None
    try:
        conn=ps_db_obj.get_new_conn()
        cursor=conn.cursor()
        cursor.execute('''delete from {} where featuregroup_name =%s'''.format(fg_table_name),(featuregroup_name, ))
        conn.commit()
        cursor.close()
    except Exception as err:
        if conn is not None:
            conn.rollback()
        raise DBException(DB_QUERY_EXEC_ERROR + \
            "delete_feature_group"  + str(err))
    finally:
        if conn is not None:
            conn.close()
     
def get_all_jobs_latest_status_version(ps_db_obj):
    """
    This function returns True if given trainingjob_name exists in db otherwise
    it returns False.
    """
    conn = None
    results = ()
    try:
        conn = ps_db_obj.get_new_conn()
        cursor = conn.cursor()
        query = '''select uf.trainingjob_name, uf.version, uf.steps_state ''' + \
                '''from trainingjob_info uf inner join ''' + \
                '''(select trainingjob_name,max(version) max_version from trainingjob_info group by ''' + \
                '''trainingjob_name ) uf2 on uf.trainingjob_name = uf2.trainingjob_name ''' + \
                '''and uf.version = uf2.max_version order by uf.trainingjob_name'''

        cursor.execute(query)
        results = cursor.fetchall()
        conn.commit()
        cursor.close()
    except Exception as err:
        if conn is not None:
            conn.rollback()
        raise DBException(DB_QUERY_EXEC_ERROR + \
            "get_all_jobs_latest_status_version"  + str(err))
    finally:
        if conn is not None:
            conn.close()
    return results

def get_info_of_latest_version(trainingjob_name, ps_db_obj):
    """
    This function returns information of <trainingjob_name, trainingjob_name trainingjob's latest version>
    usecase.
    """

    conn = ps_db_obj.get_new_conn()
    cursor = conn.cursor()
    try:
        cursor.execute('''select nt.mv from (select max(version) mv,trainingjob_name ''' + \
                       '''from trainingjob_info group by trainingjob_name) nt where nt.trainingjob_name=%s''',
                       (trainingjob_name,))
        version = int(cursor.fetchall()[0][0])
        cursor.execute(''' select * from trainingjob_info where trainingjob_name=%s and version = %s''',
                       (trainingjob_name, version))
    except Exception as err:
        conn.rollback()
        conn.close()
        raise err
    results = cursor.fetchall()
    conn.commit()
    conn.close()
    return results
