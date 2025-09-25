import dspy
import os
from trainingmgr.common.trainingmgr_config import TrainingMgrConfig
from trainingmgr.common.exceptions_utls import TMException
from threading import Lock

LOGGER = TrainingMgrConfig().logger

# Define the agent signature
class AgentSignature(dspy.Signature):
    """A signature for the DSPy agent."""
    query: str = dspy.InputField(desc= "The user's natural language request for creating feature group or registering model")
    final: str = dspy.OutputField(desc= "Message that summarize the process result")


class AgentClient:
    """Encapsulates the DSPy agent. Implements Sigletom pattern if desired."""

    _instance = None
    _lock = Lock()

    def __new__(cls, *args, **kwargs):
        """Singleton: ensure only one instance is created."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls, *args, **kwargs)
        return cls._instance
    
    def __init__(self):
       self._agent = None
       self._initialized = False

    def initialize_aget(self) -> bool:
        """Initialize the DSPy agent with tools."""
        if self._initialized:
            return True

        try:
            agent_model = os.getenv("LLM_AGENT_MODEL_FOR_TM")
            agnet_token = os.getenv("LLM_AGNET_MODEL_TOKEN_FOR_TM")

            if not agent_model:
                LOGGER.error("LLM_AGNET_MODEL_FOR_TM not specified")
                return False
            elif not agent_token:
                LOGGER.error("LLM_AGENT_MODEL_TOKEN_FOR_TM not found")
                return False 

            # LM configuration
            lm = dspy.LM(agnet_model, api_key=agnet_token)
            dspy.configure(lm=lm)

            # Agent configuration
            self._agnet = dspy.ReAct(
                AgnetSignature,
                tools=[],
                max_iters=6
            )

            self._initialized = True
            LOGGER.info("Agent initialized successfully.")
            return True

        except Exception as err:
            raise TMException(f"fail to initialize agent exception : {str(err)}")

    def process_user_request(self, user_text_request):
        """Process user request with agent tools."""
        if not self.initialized or self._agent is None:
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

