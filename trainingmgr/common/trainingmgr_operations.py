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

""""
Training manager main operations
.
"""

import json
import requests
from trainingmgr.db.trainingjob_db import get_trainingjob
from trainingmgr.common.trainingmgr_config import TrainingMgrConfig
import validators
from trainingmgr.common.exceptions_utls import TMException
from flask_api import status
TRAININGMGR_CONFIG_OBJ = TrainingMgrConfig()
LOGGER = TRAININGMGR_CONFIG_OBJ.logger

MIMETYPE_JSON = "application/json"

def create_url_host_port(protocol, host, port, path=''):
    """
    This function creates and validates URL based on the inputs.
    """
    url = protocol + '://' + host + ':' + port + '/' + path
    if not validators.url(url):
        raise TMException('URL validation error: '+ url)
    return url

def data_extraction_start(training_config_obj, training_job_id, feature_list_str, query_filter,
                          datalake_source, _measurement, influxdb_info_dic, featuregroup_name):
    """
    This function calls data extraction module for data extraction of trainingjob_name training and
    returns response which we is gotten by calling data extraction module.
    """
    logger = training_config_obj.logger
    logger.debug('training manager is calling data extraction for trainingjob_id '+ str(training_job_id))
    data_extraction_ip = training_config_obj.data_extraction_ip
    data_extraction_port = training_config_obj.data_extraction_port
    url = 'http://'+str(data_extraction_ip)+':'+str(data_extraction_port)+'/feature-groups' #NOSONAR
    logger.debug(url)

    source = {}
    source['source'] = datalake_source
    if 'InfluxSource' in datalake_source:
        source['source']['InfluxSource']['query']='''from(bucket:"'''+\
                                                  influxdb_info_dic["bucket"] + '''") |> '''+\
                                                  '''range(start: 0, stop: now()) '''+\
                                                  '''|> filter(fn: (r) => r._measurement == "'''+\
                                                  _measurement + '''") '''+\
                                                  '''|> pivot(rowKey:["_time"], '''+\
                                                  '''columnKey: ["_field"], '''+\
                                                  '''valueColumn: "_value")'''
     
    transform = {}
    transform['transform'] = []
    transform_inner_dic = {}
    transform_inner_dic['operation'] = "SQLTransform"
    transform_inner_dic['FeatureList'] = feature_list_str
    transform_inner_dic['SQLFilter'] = query_filter
    transform['transform'].append(transform_inner_dic)

    sink = {}
    sink_inner_dic = {}
    # sink_inner_dic['CollectionName'] = str(training_job_id)
    sink_inner_dic['CollectionName'] = featuregroup_name + "_" + str(training_job_id)
    sink['CassandraSink'] = sink_inner_dic

    dictionary = {}
    dictionary.update(source)
    dictionary.update(transform)
    dictionary['sink'] = sink
    dictionary['influxdb_info']= influxdb_info_dic
    dictionary["trainingjob_id"] = str(training_job_id)
   
    logger.debug(json.dumps(dictionary))

    response = requests.post(url,
                             data=json.dumps(dictionary),
                             headers={'content-type': MIMETYPE_JSON,
                                      'Accept-Charset': 'UTF-8'})
    return response

def data_extraction_status(featuregroup_name, trainingjob_id, training_config_obj):
    """
    This function calls data extraction module for getting data extraction status of
    trainingjob_name training and returns it.
    """
    LOGGER.debug(f'training manager is calling data extraction for trainingjob_id {str(featuregroup_name)}')
    data_extraction_ip = training_config_obj.data_extraction_ip
    data_extraction_port = training_config_obj.data_extraction_port
    task_id = featuregroup_name + "_" + str(trainingjob_id)
    url = 'http://'+str(data_extraction_ip)+':'+str(data_extraction_port)+'/task-status/'+str(task_id) #NOSONAR
    LOGGER.debug(url)
    response = requests.get(url)
    return response

def training_start(training_config_obj, dict_data, trainingjob_id):
    """
    This function calls kf_adapter module to start pipeline of trainingjob_name training and returns
    response which is gotten by calling kf adapter module.
    """
    try:

        LOGGER.debug('training manager is calling kf_adapter for pipeline run for '+str(trainingjob_id))
        LOGGER.debug('training manager will send to kf_adapter: '+json.dumps(dict_data))
        kf_adapter_ip = training_config_obj.kf_adapter_ip
        kf_adapter_port = training_config_obj.kf_adapter_port
        url = 'http://'+str(kf_adapter_ip)+':'+str(kf_adapter_port)+'/trainingjobs/' + str(trainingjob_id) + '/execution' #NOSONAR
        LOGGER.debug(url)
        response = requests.post(url,
                                data=json.dumps(dict_data),
                                headers={'content-type': MIMETYPE_JSON,
                                        'Accept-Charset': 'UTF-8'})

        return response
    except Exception as err:
        errMsg= f'the training start failed as {str(err)}'
        LOGGER.error(errMsg)
        raise TMException(errMsg)

def create_dme_filtered_data_job(training_config_obj, source_name, features, feature_group_name,host, port ,measured_obj_class):
    """
    This function calls Non-RT RIC DME APIs for creating filter PM data jobs.
    """
    # Converts 'a ,b,  c, d' --> ['a', 'b', 'c', 'd']
    feature_list = [word.strip() for word in features.split(',') if word != '']
    source_list = [word.strip() for word in source_name.split(',') if word != '']
    logger = training_config_obj.logger
    job_json = {
        "info_type_id": "PmData",
        "job_owner": "console",
        "job_definition": {
          "filter":{
              "sourceNames": source_list,
               "measObjInstIds": [],
               "measTypeSpecs": [{
                  "measuredObjClass": measured_obj_class,
                  "measTypes": feature_list
                }],
                "measuredEntityDns": []
          },
          "deliveryInfo": {
             "topic": "pmreports",
             "bootStrapServers": "kafka-1-kafka-bootstrap.nonrtric:9097"
          }

        }
    }


    headers = {'Content-type': MIMETYPE_JSON}
    url = create_url_host_port('http', host, port, 'data-consumer/v1/info-jobs/{}'.format(feature_group_name))
    logger.debug(url)
    logger.debug(json.dumps(job_json))
    response = requests.put(url, data=json.dumps(job_json), headers=headers)
    return response

def delete_dme_filtered_data_job(training_config_obj, feature_group_name, host, port):
    """
    This function calls Non-RT RIC DME APIs for deleting filter PM data jobs.
    """
    logger = training_config_obj.logger

    url = create_url_host_port('http', host, port, 'data-consumer/v1/info-jobs/{}'.format(feature_group_name))
    logger.debug(url)
    response = requests.delete(url)
    return response

def notification_rapp(trainingjob_id):
    try:
        trainingjob = get_trainingjob(trainingjob_id)
        steps_state = trainingjob.steps_state.states
        if trainingjob.notification_url != "" and trainingjob.notification_url is not None:
            response = requests.post(trainingjob.notification_url,
                                    data=json.dumps(steps_state),
                                    headers={
                                        'content-type': MIMETYPE_JSON,
                                        'Accept-Charset': 'UTF-8'
                                    })
            if response.status_code != 200:
                raise TMException("Notification failed: "+response.text)
    except Exception as err:
        LOGGER.error(f"failed to notify rapp due to {str(err)}")