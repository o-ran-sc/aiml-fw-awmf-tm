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
import dspy
import os
from trainingmgr.common.trainingmgr_config import TrainingMgrConfig
from trainingmgr.common.exceptions_utls import TMException

LOGGER = TrainingMgrConfig().logger

class AgentSignature(dspy.Signature):
    """A signature for the DSPy agent."""
    query: str = dspy.InputField(desc= "The user's natural language request for creating feature group or registering model")
    final: str = dspy.OutputField(desc= "Message that summarize the process result")


class AgentClient:
    """Encapsulates the DSPy agent. Implements Singleton pattern if desired."""

    _instance = None
    _initialized = False
    _agent = None

    def __new__(cls, *args, **kwargs):
        """Singleton: ensure only one instance is created."""
        if cls._instance is None:
            cls._instance = super().__new__(cls, *args, **kwargs)
        return cls._instance

    def initialize_agent(self) -> bool:
        """Initialize the DSPy agent with tools."""
        if AgentClient._initialized:
            return True
        try:
            agent_model = os.getenv("LLM_AGENT_MODEL_FOR_TM")
            agent_token = os.getenv("LLM_AGENT_MODEL_TOKEN_FOR_TM")

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
            AgentClient._agent = dspy.ReAct(
                AgentSignature,
                tools=[],
                max_iters=6
            )
            AgentClient._initialized = True
            LOGGER.info("Agent initialized successfully.")
            return True
        except Exception as err:
            raise TMException(f"fail to initialize agent exception : {str(err)}")

    def process_user_request(self, user_text_request):
        """Process user request with agent tools."""
        if not AgentClient._initialized or AgentClient._agent is None:
            raise TMException("Agent not initialized")

        try:
            result = AgentClient._agent(query=user_text_request)
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