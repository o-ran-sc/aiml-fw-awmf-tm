# ==================================================================================
#
#       Copyright (c) 2025 Taeil Jung <wjdxodlf0123@gmail.com> All Rights Reserved.
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
import os
import requests
import dspy
from trainingmgr.common.trainingmgr_config import TrainingMgrConfig
from trainingmgr.common.exceptions_utls import TMException
from trainingmgr.schemas.agent_schema import FeatureGroupIntent, ModelRegistrationIntent

CONFIG = TrainingMgrConfig()
LOGGER = CONFIG.logger

# Define the DSPy tool
@dspy.Tool
def create_feature_group(
    featuregroup_name: str,
    feature_list: str,
    enable_dme: bool,
    host: str,
    port: str,
    bucket: str,
    token: str,
    measurement: str,
    db_org: str,
    dme_port: str = None,
    source_name: str = None,
    measured_obj_class: str = None,
    datalake_source: str = "InfluxSource"
) -> str:
    """Create a feature group using the Training Manager API."""
    try:
        data = {
            "featuregroup_name": featuregroup_name,
            "feature_list": feature_list,
            "datalake_source": datalake_source,
            "enable_dme": enable_dme,
            "host": host,
            "port": port,
            "bucket": bucket,
            "token": token,
            "measurement": measurement,
            "db_org": db_org,
            "dme_port": dme_port,
            "source_name": source_name,
            "measured_obj_class": measured_obj_class,
        }
        obj = FeatureGroupIntent.model_validate(data)
        json_payload = obj.model_dump(exclude_none=True)

        tm_ip = CONFIG.my_ip
        tm_port = CONFIG.my_port
        if not tm_ip or not tm_port:
            raise TMException("Training manager IP/Port not configured")

        url = f"http://{tm_ip}:{tm_port}/ai-ml-model-training/v1/featureGroup"
        response = requests.post(url, json=json_payload, timeout=15)
        response.raise_for_status()
        return f"Feature group '{obj.featuregroup_name}' created (status={response.status_code})."
    except Exception as err:
        raise TMException(f"Error creating feature group: {str(err)}")

@dspy.Tool
def register_model(
    model_name: str,
    model_version: str,
    description: str,
    author: str,
    owner: str = "",
    input_data_type: str = "",
    output_data_type: str = "",
    model_location: str = "",
    artifact_version: str = ""
) -> str:
    """Register a model in the Model Management Service (MME)."""
    try:
        mme_ip = CONFIG.model_management_service_ip
        mme_port = CONFIG.model_management_service_port
        if not mme_ip or not mme_port:
            raise TMException("Model management service IP/Port not configured")

        obj = ModelRegistrationIntent(
            model_name=model_name,
            model_version=model_version,
            description=description,
            author=author,
            owner=owner or "",
            input_data_type=input_data_type or "",
            output_data_type=output_data_type or "",
            model_location=model_location or None,
            artifact_version=(artifact_version or None),
        )

        payload = {
            "modelId": {
                "modelName": obj.model_name,
                "modelVersion": obj.model_version,
            },
            "description": obj.description,
            "modelInformation": {
                "metadata": {
                    "author": obj.author,
                    "owner": obj.owner or "",
                },
                "inputDataType": obj.input_data_type,
                "outputDataType": obj.output_data_type,
            },
        }
        if obj.model_location:
            payload["modelLocation"] = obj.model_location
        if obj.artifact_version:
            payload["modelId"]["artifactVersion"] = obj.artifact_version

        url = f"http://{mme_ip}:{mme_port}/ai-ml-model-registration/v1/model-registrations"
        response = requests.post(url, json=payload, timeout=15)
        response.raise_for_status()
        return f"Model '{model_name}' version '{model_version}' registered (status={response.status_code})."
    except Exception as err:
        raise TMException(f"Error registering model: {str(err)}")

# Define the agent signature
class AgentSignature(dspy.Signature):
    """A signature for the DSPy agent."""
    query: str = dspy.InputField(desc= "The user's natural language request for creating feature group or registering model")
    final: str = dspy.OutputField(desc= "Message that summarize the process result")


class AgentClient:
    """Encapsulates the DSPy agent. Implements Singleton pattern if desired."""

    _instance = None

    def __new__(cls, *args, **kwargs):
        """Singleton: ensure only one instance is created."""
        if cls._instance is None:
            cls._instance = super().__new__(cls, *args, **kwargs)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized') and self._initialized:
            return
        self._initialized = False
        self._agent = None

    def initialize_agent(self) -> bool:
        """Initialize the DSPy agent with tools."""
        if self._initialized:
            return True

        try:
            agent_model = CONFIG.llm_agent_model_for_tm
            agent_token = CONFIG.llm_agent_model_token_for_tm

            if not agent_model:
                LOGGER.error("LLM_AGENT_MODEL_FOR_TM not specified")
                return False
            elif not agent_token:
                LOGGER.error("LLM_AGENT_MODEL_TOKEN_FOR_TM not found")
                return False 

            # LM configuration
            lm = dspy.LM(agent_model, api_key=agent_token)
            dspy.configure(lm=lm)

            # Agent configuration
            self._agent = dspy.ReAct(
                AgentSignature,
                tools=[create_feature_group, register_model],
                max_iters=6
            )

            self._initialized = True
            LOGGER.info("Agent initialized successfully.")
            return True

        except Exception as err:
            raise TMException(f"fail to initialize agent exception: {str(err)}")

    def process_user_request(self, user_text_request):
        """Process user request with agent tools."""
        if not self._initialized or self._agent is None:
            raise TMException("Agent not initialized")

        try:
            result = self._agent(query=user_text_request)
            response = result.final
            return {
                'success': True,
                'result': response,
            }
        except Exception as err:
            LOGGER.error(f"Error processing user request: {str(err)}")
            return {
                'success': False,
                'error': str(err),
            }
    
def get_agent_model() -> str:
    """
    Return the configured LLM agent model name for TM via TrainingMgrConfig.
    """
    model = CONFIG.llm_agent_model_for_tm
    if not model:
        raise TMException("LLM agent model not configured")
    return model