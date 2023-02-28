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
   
import pytest
import sys
from dotenv import load_dotenv
import json
from trainingmgr.db.common_db_fun import get_data_extraction_in_progress_trainingjobs, \
     change_field_of_latest_version, change_field_value_by_version, \
     get_field_by_latest_version, get_field_of_given_version, \
     change_in_progress_to_failed_by_latest_version, change_steps_state_of_latest_version, \
     change_steps_state_by_version, delete_trainingjob_version, get_info_by_version, \
     get_trainingjob_info_by_name, get_latest_version_trainingjob_name, \
     get_all_versions_info_by_name, get_all_distinct_trainingjobs, \
     get_all_version_num_by_trainingjob_name, update_model_download_url, \
     add_update_trainingjob, get_all_jobs_latest_status_version, get_info_of_latest_version

mimic_db = {
            "usecase_name": "Tester",
            "description": "Current UseCase Is For Testing Only",
            "feature_list": "*",
            "pipeline_name": "qoe-pipeline",
            "experiment_name": "default",
            "arguments": "{epoches : 1}",
            "query_filter": "",
            "creation_time": "29-09-2022",
            "run_id": 1729,
            "steps_state": json.dumps({"DATA_EXTRACTION" : "IN_PROGRESS"}),
            "updation_time": "29-09-2022",
            "version": 1,
            "enable_versioning": True,
            "target_deployment": "Near RT Ric",
            "pipeline_version": 1,
            "datalake_source": "InfluxSource",
            "incremental_training": False,
            "model": "",
            "model_version": "",
            "model_url":"",
            "notification_url": "",
            "_measurement": "liveCell",
            "bucket": "UEdata",
            "accuracy": 70
        }

class db_helper:
    '''Mimics as a Db'''
    def __init__(self, req_cols, raise_exception = False, check_success_obj = None):
        self.cols = req_cols
        self.raise_exception = raise_exception
        self.check_success_obj = check_success_obj
        self.counter = 0
        
    def get_new_conn(self):
        return db_helper(self.cols, self.raise_exception, self.check_success_obj)
    
    def cursor(self):
        return db_helper(self.cols, self.raise_exception, self.check_success_obj)

    def execute(self, query, values = None):
        if self.raise_exception:
            raise Exception("DB Error")

    def fetchall(self):
        out = []
        if(len(self.cols) > 0):
            if(self.cols[self.counter][0] == "*"):
               for (col, value) in mimic_db.items():
                    out.append(value)
            elif(self.cols[self.counter][0] == None):
                self.counter += 1
                return None
            else:
                for col in self.cols[self.counter]:
                    out.append(mimic_db[col])
        self.counter += 1
        return [out]

    def close(self):
        ''' For checking success in fxn not returning anything, If you call close, then It means query as exceuted as expected '''
        if self.check_success_obj:
            self.check_success_obj.setwin()
        
    def rollback(self):
        pass

    def commit(self):
        pass

class Check:
    def __init__(self):
        self.finished = False

    def setwin(self):
         self.finished = True

class Test_Common_Db_Fun:
    def setup_method(self):
        pass

    def test_get_data_extraction_in_progress_trainingjobs(self):
        db_obj = db_helper([["usecase_name", "steps_state"]])
        out = get_data_extraction_in_progress_trainingjobs(db_obj)
        
        assert out != None, 'Function get_data_extraction_in_progress_trainingjobs has failed'
    
    def test_negative_get_data_extraction_in_progress_trainingjobs(self):
        checker = Check()
        try:
            db_obj = db_helper([["usecase_name", "steps_state"]], raise_exception=True, check_success_obj=checker)
            out = get_data_extraction_in_progress_trainingjobs(db_obj)
            assert out != None, 'Fxn get_usecases_which_has_data_extraction_in_progress Failed'
        except Exception as err:
            assert str(err) == "Failed to execute query in get_data_extraction_in_progress_trainingjobs,DB Error", 'Negative test get_usecases_which_has_data_extraction_in_progress FAILED, Doesnt returned required error'
            assert checker.finished, 'Cursor Not Closed Properly for fxn test_negative_get_usecases_which_has_data_extraction_in_progress'

    def test_change_field_of_latest_version(self):
        for field in ["notification_url", "run_id"]:
            checker = Check()
            db_obj = db_helper([["version", "usecase_name"]], check_success_obj=checker)
            change_field_of_latest_version("Tester", db_obj, field, "a_dummy_value")

            assert checker.finished, 'change_field_of_latest_version Failed For Usecame {} and Field {} '.format("Tester", field)
    
    def test_negative_change_field_of_latest_version(self):
        for field in ["notification_url", "run_id"]:
            checker = Check()
            db_obj = db_helper([["version", "usecase_name"]],raise_exception=True ,check_success_obj=checker)
            try:    
                change_field_of_latest_version("Tester", db_obj, field, "a_dummy_value")
                assert checker.finished, 'change_field_of_latest_version Failed For Usecame {} and Field {} '.format("Tester", field)
                assert False
            except Exception:
                assert True

    def test_change_field_value_by_version_2(self):
        checker = Check()
        db_obj = db_helper([[None]], check_success_obj=checker)
        change_field_value_by_version("Tester", 1, db_obj, "deletion_in_progress", "a_dummy_value")
        assert checker.finished, 'change_field_of_given_version FAILED'
    
    def test_negative_change_field_value_by_version_2(self):
        checker = Check()
        db_obj = db_helper([[None]], raise_exception=True, check_success_obj=checker)
        try:
            change_field_value_by_version("Tester", 1, db_obj, "deletion_in_progress", "a_dummy_value")
            assert checker.finished, 'change_field_value_by_version FAILED'
            assert False
        except Exception:
            assert True
          
    def test_get_field_by_latest_version(self):
        for field in ["notification_url", "model_url", "target_deployment"]:
            db_obj = db_helper([["version"], [field]])
            out = get_field_by_latest_version("Tester", db_obj, field)
            assert out != None, 'get_field_by_latest_version FAILED at field = {}'.format(field)
    
    def test_negative_get_field_by_latest_version(self):
        for field in ["notification_url", "model_url", "target_deployment"]:
            checker = Check()
            try:
                db_obj = db_helper([["version"], [field]], raise_exception=True, check_success_obj=checker)
                out = get_field_by_latest_version("Tester", db_obj, field)
                assert out != None, 'get_field_by_latest_version FAILED at field = {}'.format(field)
                assert False
            except Exception:
                assert True

    def test_get_field_of_given_version(self):
        db_obj = db_helper([["steps_state"]])
        out = get_field_of_given_version("Tester", 1, db_obj, "steps_state")
        assert out != None, ' test_get_field_of_given_version FAILED'
    
    def test_negative_get_field_of_given_version(self):
        checker = Check()
        try:
            db_obj = db_helper([["steps_state"]], raise_exception=True, check_success_obj=checker)
            out = get_field_of_given_version("Tester", 1, db_obj, "steps_state")
            assert out != None, ' test_get_field_of_given_version FAILED'
            assert False
        except Exception:
            assert True

    def test_change_in_progress_to_failed_by_latest_version(self):
        checker = Check()
        db_obj = db_helper([["version"], ["steps_state"]], check_success_obj=checker)
        change_in_progress_to_failed_by_latest_version("Tester", db_obj)
        assert checker.finished, 'change_in_progress_to_failed_by_latest_version FAILED'

    def test_negative_change_in_progress_state_to_failed_of_latest_version(self):
        checker = Check()
        try:
            db_obj = db_helper([["version"], ["steps_state"]], raise_exception=True,check_success_obj=checker)
            change_in_progress_to_failed_by_latest_version("Tester", db_obj)
            assert checker.finished, 'change_in_progress_to_failed_by_latest_version FAILED'
        except Exception as err:
                fxn_name = "change_in_progress_to_failed_by_latest_version("
                assert str(err) == "Failed to execute query in change_in_progress_to_failed_by_latest_versionDB Error", 'Negative test {} FAILED, Doesnt returned required error'.format(fxn_name)
                assert checker.finished, 'Cursor Not Closed Properly for fxn {} | Negative Test'.format(fxn_name)

    def test_change_steps_state_of_latest_version(self):
        checker = Check()
        db_obj = db_helper([["version"], ["steps_state"], [None]],  check_success_obj=checker)
        change_steps_state_of_latest_version("Tester", db_obj, 1, 2) # Dummy Key and Values
        assert checker.finished, 'change_steps_state_of_latest_version FAILED'
    
    def test_negative_change_steps_state_of_latest_version(self):
        checker = Check()
        try:
            db_obj = db_helper([["version"], ["steps_state"], [None]], raise_exception=True ,check_success_obj=checker)
            change_steps_state_of_latest_version("Tester", db_obj, 1, 2) # Dummy Key and Values
            assert checker.finished, 'change_steps_state_of_latest_version FAILED'
        except Exception as err:
                fxn_name = "change_steps_state_of_latest_version"
                assert str(err) == "Failed to execute query in change_steps_state_of_latest_versionDB Error", 'Negative test {} FAILED, Doesnt returned required error'.format(fxn_name)
                assert checker.finished, 'Cursor Not Closed Properly for fxn {} | Negative Test'.format(fxn_name)

    def test_change_steps_state_by_version(self):
        checker = Check()
        db_obj = db_helper([["steps_state"], [None]]  , check_success_obj=checker)
        change_steps_state_by_version("Tester", 1, db_obj, 1, 2) # Dummy Key and Values
        assert checker.finished, 'change_steps_state_by_version FAILED'

    def test_negative_change_steps_state_by_version(self):
        checker = Check()
        try:
            db_obj = db_helper([["steps_state"], [None]]  , raise_exception=True,check_success_obj=checker)
            change_steps_state_by_version("Tester", 1, db_obj, 1, 2) # Dummy Key and Values
            assert checker.finished, 'change_steps_state_by_version FAILED'
        except Exception as err:
                fxn_name = "change_steps_state_by_version"
                assert str(err) == "Failed to execute query in change_steps_state_by_versionDB Error", 'Negative test {} FAILED, Doesnt returned required error'.format(fxn_name)
                assert checker.finished, 'Cursor Not Closed Properly for fxn {} | Negative Test'.format(fxn_name)

    def test_delete_trainingjob_version(self):
        checker = Check()
        db_obj = db_helper([[None]], check_success_obj=checker)
        delete_trainingjob_version("Tester", 1, db_obj)
        assert checker.finished, 'delete_trainingjob_version FAILED'

    def test_negative_delete_trainingjob_version(self):
        checker = Check()
        try:
            db_obj = db_helper([[None]], raise_exception=True,check_success_obj=checker)
            delete_trainingjob_version("Tester", 1, db_obj)
            assert checker.finished, 'delete_trainingjob_version FAILED'
        except Exception as err:
            fxn_name = "delete_trainingjob_version"
            assert str(err) == "Failed to execute query in delete_trainingjob_versionDB Error", 'Negative test {} FAILED, Doesnt returned required error'.format(fxn_name)
            assert checker.finished, 'Cursor Not Closed Properly for fxn {} | Negative Test'.format(fxn_name)
        
    def test_get_info_by_version(self):
        db_obj = db_helper([["*"]])
        out = get_info_by_version("Tester", 1, db_obj)
        assert out != None, 'get_info_by_version FAILED'
    
    def test_negative_get_info_by_version(self):
        checker = Check()
        try:
            db_obj = db_helper([["*"]], raise_exception=True,check_success_obj=checker)
            out = get_info_by_version("Tester", 1, db_obj)
            assert out != None, 'get_info_by_version FAILED'
        except Exception as err:
            fxn_name = "get_info_by_version"
            assert str(err) == "Failed to execute query in get_info_by_versionDB Error", 'Negative test {} FAILED, Doesnt returned required error'.format(fxn_name)
            assert checker.finished, 'Cursor Not Closed Properly for fxn {} | Negative Test'.format(fxn_name)

    def test_get_trainingjob_info_by_name(self):
        db_obj = db_helper([["version"], ["*"]])
        out = get_trainingjob_info_by_name("Tester", db_obj)
        assert out != None, 'get_trainingjob_info_by_name FAILED'

    def test_negative_get_trainingjob_info_by_name(self):
        checker = Check()
        try:
            db_obj = db_helper([["version"], ["*"]], raise_exception=True,check_success_obj=checker)
            out = get_trainingjob_info_by_name("Tester", db_obj)
            assert out != None, 'get_trainingjob_info_by_name FAILED'
        except Exception as err:
            fxn_name = "get_trainingjob_info_by_name"
            assert str(err) == "Failed to execute query in get_trainingjob_info_by_nameDB Error", 'Negative test {} FAILED, Doesnt returned required error'.format(fxn_name)
            assert checker.finished, 'Cursor Not Closed Properly for fxn {} | Negative Test'.format(fxn_name)

    def test_get_latest_version_trainingjob_name(self):
        db_obj = db_helper([["version"]])
        out = get_latest_version_trainingjob_name("Tester", db_obj)
        assert type(out) == int, 'get_latest_version_trainingjob_name FAILED' 

    def test_negative_get_latest_version_trainingjob_name(self):
        checker = Check()
        try:
            db_obj = db_helper([["version"]], raise_exception=True,check_success_obj=checker)
            out = get_latest_version_trainingjob_name("Tester", db_obj)
            assert type(out) == int, 'get_latest_version FAILED'
        except Exception as err:
            fxn_name = "get_latest_version"
            assert str(err) == "Failed to execute query in get_latest_version_trainingjob_nameDB Error", 'Negative test {} FAILED, Doesnt returned required error'.format(fxn_name)
            assert checker.finished, 'Cursor Not Closed Properly for fxn {} | Negative Test'.format(fxn_name)

    def test_get_all_distinct_trainingjobs(self):
        db_obj = db_helper([["usecase_name"]])
        out = get_all_distinct_trainingjobs(db_obj)
        assert type(out) == list, 'get_all_distinct_trainingjobs FAILED'
    
    def test_negative_get_all_distinct_trainingjobs(self):
        checker = Check()
        try:
            db_obj = db_helper([["usecase_name"]],  raise_exception=True,check_success_obj=checker)
            out = get_all_distinct_trainingjobs(db_obj)
            assert type(out) == list, 'get_all_distinct_trainingjobs FAILED'
        except Exception as err:
            fxn_name = "get_all_distinct_trainingjobs"
            assert str(err) == "Failed to execute query in get_all_distinct_trainingjobsDB Error", 'Negative test {} FAILED, Doesnt returned required error'.format(fxn_name)
            assert checker.finished, 'Cursor Not Closed Properly for fxn {} | Negative Test'.format(fxn_name)


    def test_get_all_version_num_by_trainingjob_name(self):
        db_obj = db_helper([["version"]])
        out = get_all_version_num_by_trainingjob_name("Tester", db_obj)
        assert type(out) == list, 'get_all_version_num_by_trainingjob_name FAILED'
    
    def test_negative_get_all_version_num_by_trainingjob_name(self):
        checker = Check()
        try:
            db_obj = db_helper([["version"]], raise_exception=True,check_success_obj=checker)
            out = get_all_version_num_by_trainingjob_name("Tester", db_obj)
            assert type(out) == list, 'get_all_version_num_by_trainingjob_name FAILED'
        except Exception as err:
            fxn_name = "get_all_version_num_by_trainingjob_name"
            assert str(err) == "Failed to execute query in get_all_version_num_by_trainingjob_nameDB Error", 'Negative test {} FAILED, Doesnt returned required error'.format(fxn_name)
            assert checker.finished, 'Cursor Not Closed Properly for fxn {} | Negative Test'.format(fxn_name)

    def test_update_model_download_url(self):
        checker = Check()
        db_obj = db_helper([[None]], check_success_obj=checker)
        update_model_download_url("Tester", 1, "http/dummy/url", db_obj)
        assert checker.finished, 'update_model_download_url FAILED'

    def test_negative_update_model_download_url(self):
        checker = Check()
        try:
            db_obj = db_helper([[None]], raise_exception=True ,check_success_obj=checker)
            update_model_download_url("Tester", 1, "http/dummy/url", db_obj)
            assert checker.finished, 'update_model_download_url FAILED'
        except Exception as err:
            fxn_name = "update_model_download_url"
            assert str(err) == "Failed to execute query in update_model_download_urlDB Error", 'Negative test {} FAILED, Doesnt returned required error'.format(fxn_name)
            assert checker.finished, 'Cursor Not Closed Properly for fxn {} | Negative Test'.format(fxn_name)

    def test_add_update_trainingjob(self):
        checker = Check()
        db_obj = db_helper([[None]], check_success_obj=checker)
        add_update_trainingjob('Testing', 'qoe-pipeline', 'Default', '*', '{epoches : 1}', '', True, True, 1, 'InfluxSource', 'Tester',db_obj)
        assert checker.finished, 'add_update_trainingjob FAILED, When adding = True'
    
    def test_negative_add_update_trainingjob_2(self):
        checker = Check()
        db_obj = db_helper([[None]], check_success_obj=checker)
        add_update_trainingjob('Testing', 'qoe-pipeline', 'Default', '*', '{epoches : 1}', '', True, False, 1, 'InfluxSource', 'Tester',db_obj)
        assert checker.finished, 'add_update_trainingjob FAILED, When adding = True'
    
    def test_negative_add_update_trainingjob_3(self):
        checker = Check()
        db_obj = db_helper([[None]], check_success_obj=checker)
        try:
            add_update_trainingjob('Testing', 'qoe-pipeline', 'Default', '*', '{epoches : 1}', '', False, True, 1, 'InfluxSource', 'Tester',db_obj)
            assert checker.finished, 'add_update_trainingjob FAILED, When adding = True'
            assert False
        except Exception:
            assert True

    def test_negative_add_update_trainingjob_4(self):
        checker = Check()
        db_obj = db_helper([[None]], check_success_obj=checker)
        try:
            add_update_trainingjob('Testing', 'qoe-pipeline', 'Default', '*', '{epoches : 1}', '', False, False, 1, 'InfluxSource', 'Tester',db_obj)
            assert checker.finished, 'add_update_trainingjob FAILED, When adding = True'
            assert False
        except Exception:
            assert True

    def test_negative_add_update_trainingjob_5(self):
        checker = Check()
        try:
            db_obj = db_helper([[None]], raise_exception=True, check_success_obj=checker)
            add_update_trainingjob('Testing ', 'qoe-pipeline', 'Default', '*', '{epoches : 1}', '', True, True, 'Near RT-RIC', 1, 'InfluxSource', 'Tester'
            ,True, '', '', db_obj, '', 'liveCell', 'UEData')
            assert checker.finished, 'add_update_trainingjob FAILED, When adding = True'
        except Exception as err:
            fxn_name = "add_update_trainingjob"
            assert str(err) == "add_update_trainingjob() takes from 12 to 15 positional arguments but 19 were given", 'Negative test {} FAILED when  adding = True , Doesnt returned required error'.format(fxn_name)
    
    def test_get_all_jobs_latest_status_version(self):
        db_obj = db_helper([["usecase_name"]])
        out = get_all_jobs_latest_status_version(db_obj)
        assert out == [['Tester']], 'get_all_distinct_trainingjobs FAILED'
    
    def test_negative_get_all_jobs_latest_status_version(self):
        checker = Check()
        try:
            db_obj = db_helper([["usecase_name"]],  raise_exception=True,check_success_obj=checker)
            out = get_all_jobs_latest_status_version(db_obj)
            assert type(out) == list, 'get_all_jobs_latest_status_version FAILED'
        except Exception as err:
            fxn_name = "get_all_jobs_latest_status_version"
            assert str(err) == "Failed to execute query in get_all_jobs_latest_status_versionDB Error", 'Negative test {} FAILED, Doesnt returned required error'.format(fxn_name)
            assert checker.finished, 'Cursor Not Closed Properly for fxn {} | Negative Test'.format(fxn_name)
    
    def test_get_all_versions_info_by_name(self):
        trainingjob_name = "usecase556"
        db_obj = db_helper([["usecase_name"]])
        out = get_all_versions_info_by_name(trainingjob_name,db_obj)
        assert out == [['Tester']], 'get_all_versions_info_by_name FAILED'
    
    def test_negative_get_all_versions_info_by_name(self):
        checker = Check()
        trainingjob_name = "usecase556"
        my_dict = dict([(1,'apple'), (2,'ball')])
        db_obj = db_helper([["usecase_name"]])
        try:
            db_obj = db_helper([["usecase_name"]],  raise_exception=True,check_success_obj=checker)
            out = get_all_versions_info_by_name(trainingjob_name,db_obj)
            assert type(out) == list, 'get_all_jobs_latest_status_version FAILED'
        except Exception as err:
            fxn_name = "get_all_versions_info_by_name"
            assert str(err) == "Failed to execute query in get_all_versions_info_by_nameDB Error", 'Negative test {} FAILED, Doesnt returned required error'.format(fxn_name)
            assert checker.finished, 'Cursor Not Closed Properly for fxn {} | Negative Test'.format(fxn_name)

    def test_get_info_of_latest_version(self):
        db_obj = db_helper([["version"], ["*"]])
        out = get_info_of_latest_version("Tester", db_obj)
        assert out != None, 'get_info_of_latest_version FAILED'


    def test_negative_get_info_of_latest_version(self):
        checker = Check()
        try:
            db_obj = db_helper([["version"], ["*"]], raise_exception=True,check_success_obj=checker)
            out = get_info_of_latest_version("Tester", db_obj)
            assert out != None, 'get_info_of_latest_version FAILED'
        except Exception as err:
            fxn_name = "get_info_by_version"
            assert str(err) == "DB Error", 'Negative test {} FAILED, Doesnt returned required error'.format(fxn_name)
            assert checker.finished, 'Cursor Not Closed Properly for fxn {} | Negative Test'.format(fxn_name)