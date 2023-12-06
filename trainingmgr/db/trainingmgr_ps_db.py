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
This file contains code for creation of database, table if they are not created
and sending connection of postgres db.
"""
import pg8000.dbapi
from trainingmgr.common.exceptions_utls import DBException

PG_DB_ACCESS_ERROR = "Problem of connection with postgres db"

class PSDB():
    """
    Database interface for training manager
    """

    def __init__(self, config_hdl):
        """
        In this constructor we are passing configration handler to  private instance variable
        and create database,table if it is not created.
        """
        #Create database
        self.__config_hdl = config_hdl
        conn1 = None
        try:
            conn1 = pg8000.dbapi.connect(user=config_hdl.ps_user,
                                        password=config_hdl.ps_password,
                                        host=config_hdl.ps_ip,
                                        port=int(config_hdl.ps_port))
        except pg8000.dbapi.Error:
            self.__config_hdl.logger.error("Problem of connection with postgres db")
            raise DBException(PG_DB_ACCESS_ERROR) from None
        conn1.autocommit = True
        cur1 = conn1.cursor()
        present = False
        try:
            cur1.execute("SELECT datname FROM pg_database")
            for x in cur1.fetchall():
                if x[0] == 'training_manager_database':
                    present = True
            if not present:
                cur1.execute("create database training_manager_database")
            conn1.commit()
            cur1.close()
        except pg8000.dbapi.Error:
            conn1.rollback()
            self.__config_hdl.logger.error("Can't create database.")
            raise DBException(PG_DB_ACCESS_ERROR) from None
        finally:
            if conn1 is not None:
                conn1.close()

        #Create table
        conn2 = None
        try:
            conn2 = pg8000.dbapi.connect(user=config_hdl.ps_user,
                                        password=config_hdl.ps_password,
                                        host=config_hdl.ps_ip,
                                        port=int(config_hdl.ps_port),
                                        database="training_manager_database")
        except pg8000.dbapi.Error:
            self.__config_hdl.logger.error("Problem of connection with postgres db")
            raise DBException(PG_DB_ACCESS_ERROR) from None
        cur2 = conn2.cursor()
        try:
            cur2.execute("create table if not exists trainingjob_info(" + \
                        "trainingjob_name varchar(128) NOT NULL," + \
                        "description varchar(2000) NOT NULL," + \
                        "feature_list varchar(2000) NOT NULL," + \
                        "pipeline_name varchar(128) NOT NULL," + \
                        "experiment_name varchar(128) NOT NULL," + \
                        "arguments varchar(2000) NOT NULL," + \
                        "query_filter varchar(2000) NOT NULL," + \
                        "creation_time TIMESTAMP NOT NULL," + \
                        "run_id varchar(1000) NOT NULL," + \
                        "steps_state varchar(1000) NOT NULL," + \
                        "updation_time TIMESTAMP NOT NULL," + \
                        "version INTEGER  NOT NULL," + \
                        "enable_versioning BOOLEAN NOT NULL," + \
                        "pipeline_version varchar(128) NOT NULL," + \
                        "datalake_source varchar(2000) NOT NULL," + \
                        "model_url varchar(100) NOT NULL," + \
                        "notification_url varchar(1000) NOT NULL," + \
                        "_measurement varchar(100) NOT NULL," + \
                        "bucket varchar(50) NOT NULL," + \
                        "deletion_in_progress BOOLEAN NOT NULL," + \
                        "is_mme BOOLEAN NOT NULL," + \
                        "model_name varchar(128) NOT NULL," + \
                        "model_info varchar(1000) NOT NULL," \
                        "PRIMARY KEY (trainingjob_name,version)" + \
                        ")")
            conn2.commit()
            cur2.close()            
        except pg8000.dbapi.Error:
            conn2.rollback()
            self.__config_hdl.logger.error("Can't create trainingjob_info table.")
            raise DBException("Can't create trainingjob_info table.") from None
        finally:
            if conn2 is not None:
                conn2.close()
        
        # Create Table
        conn3 =None
        try:
            conn3 = pg8000.dbapi.connect(user=config_hdl.ps_user,
                                        password=config_hdl.ps_password,
                                        host=config_hdl.ps_ip,
                                        port=int(config_hdl.ps_port),
                                        database="training_manager_database")
        except pg8000.dbapi.Error:
            self.__config_hdl.logger.error("Problem of connection with postgres db")
            raise DBException(PG_DB_ACCESS_ERROR) from None
        cur3= conn3.cursor()
        try:
            cur3.execute("create table if not exists featuregroup_info(" + \
                        "featureGroup_name varchar(128) NOT NULL," + \
                        "feature_list varchar(2000) NOT NULL," + \
                        "datalake_source varchar(2000) NOT NULL," + \
                        "host varchar(128) NOT NULL," + \
                        "port varchar(128) NOT NULL," + \
                        "bucket varchar(128) NOT NULL," + \
                        "token varchar(2000) NOT NULL," + \
                        "db_org varchar(128) NOT NULL," + \
                        "enable_dme BOOLEAN NOT NULL," + \
                        "measured_obj_class varchar(128) NOT NULL," + \
                        "dme_port varchar(128) NOT NULL," + \
                        "source_name varchar(2000) NOT NULL," + \
                        "PRIMARY KEY (featureGroup_name)" + \
                        ")")
            conn3.commit()
            cur3.close()
        except pg8000.dbapi.Error as err:
            conn2.rollback()
            self.__config_hdl.logger.error("Can't create featuregroup_info table.")
            raise DBException("Can't create featuregroup_info table.", str(err)) from None
        finally:
            if conn3 is not None:
                conn3.close()

    def get_new_conn(self):
        """
        This function makes one new connection to postgres db
        using fields in configaration handler and returns that connection.
        """
        conn = None
        try:
            conn = pg8000.dbapi.connect(user=self.__config_hdl.ps_user,
                                        password=self.__config_hdl.ps_password,
                                        host=self.__config_hdl.ps_ip,
                                        port=int(self.__config_hdl.ps_port),
                                        database="training_manager_database")
            conn.autocommit = False
        except Exception as err :
            raise DBException("Failed to get new db connection," + str(err))
        return conn
