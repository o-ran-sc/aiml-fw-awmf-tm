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
import os
from mock import patch
from trainingmgr.db.trainingmgr_ps_db import PSDB
from dotenv import load_dotenv

class dummpy_test:
       api = "APITest"
       def logger(self):
        return cred_handle()
    
       def error(self):
        raise Exception('Connection Failed To Exist')

class cred_handle:
    def __init__(self):
        self.ps_user = "gdgdgd"
        self.ps_password = "hdhd"
        self.ps_ip = 12345
        self.ps_port = 1000
    
    def logger(self):
        return cred_handle()
    
    def error(self):
        raise Exception('Connection Failed To Exist')

class Cursor:
    def __init__(self, db_name):
        self.db_name = db_name

    def execute(self, query):
        pass

    def fetchall(self):
        return [self.db_name]
    
    def close(self):
        pass

class connection:
    def __init__(self, db_name):
        self.autocommit = False
        self.db_name = db_name
    
    def cursor(self):
        return Cursor(self.db_name)
    
    def rollback(self):
        pass

    def commit(self):
        pass

    def close(self):
        pass

class Test_PSDB:
    @patch('trainingmgr.db.trainingmgr_ps_db.pg8000.dbapi.connect', return_value = connection('usecase_manager_database'))
    def setup_method(self,mock1,mock2):
        self.obj = PSDB(cred_handle())

    def test_init_psdb(self):
        assert self.obj != None, 'PSDB Object Creation Failed'
    
    @patch('trainingmgr.db.trainingmgr_ps_db.pg8000.dbapi.connect', return_value = "HTTP_500_INTERNAL_SERVER_ERROR")
    def test_negative_init_psdb(self,mock1):
      config_hdl = dummpy_test()
      try:
        obj1 = PSDB(config_hdl)
        response = obj1.__init__(config_hdl)
        assert response == 200
      except:
         pass

    @patch('trainingmgr.db.trainingmgr_ps_db.pg8000.dbapi.connect', return_value = connection('usecase_manager_database'))
    def test_get_new_conn(self, mock1):
        out =  self.obj.get_new_conn()
        assert out != None, 'New Connection Failed'

    def test_negative_get_new_conn(self):
        try:
            out =  self.obj.get_new_conn()
            assert out != None, 'New Connection Failed'
            assert False
        except Exception:
            assert True