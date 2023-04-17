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
import validators

def create_url_host_port(protocol, host, port, path=''):
    """
    This function creates and validates URL based on the inputs.
    """
    url = protocol + '://' + host + ':' + port + '/' + path
    if not validators.url(url):
        logger.debug('URL validation error: ',url)
        return None
    return url

def data_extraction_start(training_config_obj, trainingjob_name, feature_list, query_filter,
                          datalake_source, _measurement, bucket):
    """
    This function calls data extraction module for data extraction of trainingjob_name training and
    returns response which we is gotten by calling data extraction module.
    """
    logger = training_config_obj.logger
    logger.debug('training manager is calling data extraction for '+trainingjob_name)
    data_extraction_ip = training_config_obj.data_extraction_ip
    data_extraction_port = training_config_obj.data_extraction_port
    url = 'http://'+str(data_extraction_ip)+':'+str(data_extraction_port)+'/feature-groups' #NOSONAR
    logger.debug(url)

    source = {}
    source['source'] = datalake_source
    if 'InfluxSource' in datalake_source:
        source['source']['InfluxSource']['query']='''from(bucket:"'''+\
                                                  bucket + '''") |> '''+\
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
    transform_inner_dic['FeatureList'] = feature_list
    transform_inner_dic['SQLFilter'] = query_filter
    transform['transform'].append(transform_inner_dic)

    sink = {}
    sink_inner_dic = {}
    sink_inner_dic['CollectionName'] = trainingjob_name
    sink['CassandraSink'] = sink_inner_dic

    dictionary = {}
    dictionary.update(source)
    dictionary.update(transform)
    dictionary['sink'] = sink
   
    logger.debug(json.dumps(dictionary))

    response = requests.post(url,
                             data=json.dumps(dictionary),
                             headers={'content-type': 'application/json',
                                      'Accept-Charset': 'UTF-8'})
    return response

def data_extraction_status(trainingjob_name,training_config_obj):
    """
    This function calls data extraction module for getting data extraction status of
    trainingjob_name training and returns it.
    """
    logger = training_config_obj.logger
    logger.debug('training manager is calling data extraction for '+trainingjob_name)
    data_extraction_ip = training_config_obj.data_extraction_ip
    data_extraction_port = training_config_obj.data_extraction_port
    url = 'http://'+str(data_extraction_ip)+':'+str(data_extraction_port)+'/task-status/'+trainingjob_name #NOSONAR
    logger.debug(url)
    response = requests.get(url)
    return response

def training_start(training_config_obj, dict_data, trainingjob_name):
    """
    This function calls kf_adapter module to start pipeline of trainingjob_name training and returns
    response which is gotten by calling kf adapter module.
    """
    logger = training_config_obj.logger
    logger.debug('training manager is calling kf_adapter for pipeline run for '+trainingjob_name)
    logger.debug('training manager will send to kf_adapter: '+json.dumps(dict_data))
    kf_adapter_ip = training_config_obj.kf_adapter_ip
    kf_adapter_port = training_config_obj.kf_adapter_port
    url = 'http://'+str(kf_adapter_ip)+':'+str(kf_adapter_port)+'/trainingjobs/' + trainingjob_name + '/execution' #NOSONAR
    logger.debug(url)
    response = requests.post(url,
                             data=json.dumps(dict_data),
                             headers={'content-type': 'application/json',
                                      'Accept-Charset': 'UTF-8'})

    return response

def create_dme_filtered_data_job(training_config_obj, source_name, db_org, bucket_name,
                                 token, features, feature_group_name, host, port):
    """
    This function calls Non-RT RIC DME APIs for creating filter PM data jobs.
    """
    logger = training_config_obj.logger

    job_json =  {
        "info_type_id": "json-file-data-from-filestore-to-influx",
        "job_owner": "console",
        "status_notification_uri": "http://callback.nonrtric:80/post",
        "job_definition": { "db-url":"http://influxdb.onap:8086",
        "db-org":db_org,
        "db-bucket":bucket_name,
        "db-token": token,
        "filterType":"pmdata",
        "filter":
            {"sourceNames":[source_name],
            "measTypes":features}}}

    headers = {'Content-type': 'application/json'}

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
