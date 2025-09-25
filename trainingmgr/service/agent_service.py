import dspy
import os
from trainingmgr.common.trainingmgr_config import TrainingMgrConfig
from trainingmgr.common.exceptions_utls import TMException, DBException
from trainingmgr.service.agent_tools import create_featuregroup, register_model

LOGGER = TrainingMgrConfig().logger

# Define the agent signature
class AgentSignature(dspy.Signature):
    """A signature for the DSPy agent."""
    query: str = dspy.InputField(desc= "The user's natural language request for creating feature group or registering model")
    final: str = dspy.OutputField(desc= "Message that summarize the process result")

# Global agent instance
agent = None

def initialize_agent():
    """Initialize the DSPy agent with tools."""
    global agent
    
    try:
        agent_model = os.getenv("LLM_AGENT_MODEL_FOR_TM")
        agent_token = os.getenv("LLM_AGENT_TOKEN_FOR_TM")
        if not agent_model:
            LOGGER.error("LLM_AGENT_MODEL_FOR_TM not specified.")
            return False
        elif not agent_token:
            LOGGER.error("LLM_AGENT_TOKEN_FOR_TM not found.")          
            return False
                
        # LM configuration
        lm = dspy.LM(agent_model, api_key=agent_token)
        dspy.configure(lm=lm)
        
        # Agent configuration
        agent = dspy.ReAct(
            AgentSignature,
            tools=[create_featuregroup, register_model],
            max_iters=6
        )
        LOGGER.info("Agent initialized successfully.")
        return True
                  
    except Exception as err:
        raise TMException(f"fail to initialize agent exception : {str(err)}")

def process_user_request(user_text_request):
    """Process user request with agent tools"""

    global agent
    
    if agent is None:
        raise TMException("Agent not initialized")
    
    try:
        result = agent(query=user_text_request)
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