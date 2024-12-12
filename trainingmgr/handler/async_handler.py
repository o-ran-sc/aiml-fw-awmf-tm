import threading
from threading import Lock
import json
import time
import requests
from trainingmgr.common.trainingConfig_parser import getField
from trainingmgr.common.trainingmgr_config import TrainingMgrConfig
from trainingmgr.common.trainingmgr_operations import data_extraction_status
from trainingmgr.service.training_job_service import get_data_extraction_in_progress_trainingjobs, get_training_job, change_status_tj
# from trainingmgr.common.trainingmgr_util import handle_async_feature_engineering_status_exception_case
from trainingmgr.common.exceptions_utls import TMException
from trainingmgr.constants import Steps, States
from modelmetricsdk.model_metrics_sdk import ModelMetricsSdk
from trainingmgr.db.trainingjob_db import change_state_to_failed




# Global variables
LOCK = Lock()
DATAEXTRACTION_JOBS_CACHE = {}
LOGGER = TrainingMgrConfig().logger
TRAININGMGR_CONFIG_OBJ = TrainingMgrConfig()
Model_Metrics_Sdk = ModelMetricsSdk()



def check_and_notify_feature_engineering_status(APP,db):
    """Asynchronous function to check and notify feature engineering status."""
    LOGGER.debug("in the check_and_notify_feature_engineering_status")
    url_pipeline_run = (
        f"http://{TRAININGMGR_CONFIG_OBJ.my_ip}:"
        f"{TRAININGMGR_CONFIG_OBJ.my_port}/trainingjob/dataExtractionNotification"
    )
    while True:
        with LOCK:
            training_job_ids = list(DATAEXTRACTION_JOBS_CACHE)
        for trainingjob_id in training_job_ids:
            LOGGER.debug(f"Current DATAEXTRACTION_JOBS_CACHE: {DATAEXTRACTION_JOBS_CACHE}")
            try:
                # trainingjob_name = trainingjob.trainingjob_name
                with APP.app_context():
                    trainingjob = get_training_job(trainingjob_id)
                featuregroup_name = getField(trainingjob.training_config, "feature_group_name")
                response = data_extraction_status(featuregroup_name, trainingjob_id, TRAININGMGR_CONFIG_OBJ)
                if (response.headers.get('content-type') != "application/json" or
                        response.status_code != 200):
                    raise TMException(f"Data extraction API returned an error for {featuregroup_name}. for trainingjob_id {trainingjob.id}")

                response_data = response.json()
                LOGGER.debug(f"Data extraction status for {featuregroup_name}: {json.dumps(response_data)} for trainingjob_id {trainingjob.id}")

                if response_data["task_status"] == "Completed":
                    with APP.app_context():
                        
                        change_status_tj(trainingjob.id, Steps.DATA_EXTRACTION.name, States.FINISHED.name)
                        change_status_tj(trainingjob.id, Steps.DATA_EXTRACTION_AND_TRAINING.name, States.IN_PROGRESS.name)
                    kf_response = requests.post(
                        url_pipeline_run,
                        data=json.dumps({"trainingjob_id": trainingjob.id}),
                        headers={'Content-Type': "application/json", 'Accept-Charset': 'UTF-8'}
                    )
                    if (kf_response.headers.get('content-type') != "application/json" or
                            kf_response.status_code != 200):
                        raise TMException(f"KF adapter returned an error for {featuregroup_name}.")

                    with LOCK:
                        DATAEXTRACTION_JOBS_CACHE.pop(trainingjob.id)
                elif response_data["task_status"] == "Error":
                    raise TMException(f"Data extraction failed for {featuregroup_name}.")
            except Exception as err:
                LOGGER.error(f"Error processing DATAEXTRACTION_JOBS_CACHE: {str(err)}")
                with APP.app_context():
                    change_state_to_failed(trainingjob)
                    # notification_rapp(trainingjob.id)
                    with LOCK:
                        try:
                            DATAEXTRACTION_JOBS_CACHE.pop(trainingjob.id)
                        except KeyError as key_err:
                            LOGGER.error("The training job key doesn't exist in DATAEXTRACTION_JOBS_CACHE: " + str(key_err))

        time.sleep(10)  # Sleep before checking again



def start_async_handler(APP,db):
    """Start the asynchronous handler."""

    LOGGER.debug("Initializing the asynchronous handler...")
    with APP.app_context():
        DATAEXTRACTION_JOBS_CACHE = get_data_extraction_in_progress_trainingjobs()
    print("DATAEXTRACTION_JOBS_CACHE in start async is: ", DATAEXTRACTION_JOBS_CACHE)
    # Start the async function in a separate thread
    threading.Thread(target=check_and_notify_feature_engineering_status, args=(APP,db), daemon=True).start()
    LOGGER.debug("Asynchronous handler started.")