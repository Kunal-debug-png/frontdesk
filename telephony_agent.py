import asyncio
import logging
import os
import sys
from datetime import datetime
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from livekit.agents import (
    Agent,
    AgentSession,
    JobContext,
    WorkerOptions,
    cli,
    function_tool
)
from livekit.plugins import deepgram, cartesia, silero
from prompts import AGENT_INSTRUCTIONS, get_greeting_instruction

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("telephony-agent")
load_dotenv()

@function_tool
async def get_current_time() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

@function_tool
async def wait_for_answer(question: str, caller_phone: str = "unknown", max_wait_seconds: int = 60) -> str:
    try:
        from knowledge_manager import add_unknown_question, check_for_answer, mark_question_answered
        import asyncio
        
        logger.info(f"Waiting for answer to: {question}")
        add_unknown_question(question, caller_phone)
        
        check_interval = 3
        max_checks = max_wait_seconds // check_interval
        
        for i in range(max_checks):
            answer = check_for_answer(question)
            
            if answer:
                logger.info(f"Answer found: {answer}")
                mark_question_answered(question, answered_on_call=False)
                
                try:
                    from sms_client import send_notification_for_unanswered
                    logger.info("Sending SMS notification...")
                    send_notification_for_unanswered()
                except Exception as e:
                    logger.error(f"Error sending SMS notification: {e}")
                
                return f"Great news! {answer}"
            
            await asyncio.sleep(check_interval)
            
        logger.warning(f"Timeout waiting for answer to: {question}")
        return "I've noted your question. Our team will call you back with the answer shortly. May I have your phone number?"
        
    except Exception as e:
        logger.error(f"Error in wait_for_answer: {e}")
        return "I've noted your question. Our team will follow up with you soon."

async def entrypoint(ctx: JobContext):
    logger.info("Agent starting...")
    logger.info("Entrypoint function called")
    
    import os
    logger.info(f"Current working directory: {os.getcwd()}")
    logger.info(f"Knowledge base path: {os.path.abspath('knowledge_base.csv')}")
    
    kb_path = os.path.abspath('knowledge_base.csv')
    if os.path.exists(kb_path):
        logger.info("Knowledge base file exists")
        with open(kb_path, 'r') as f:
            content = f.read()
            logger.info(f"Knowledge base content:\n{content}")
    else:
        logger.error("Knowledge base file does not exist")
    
    try:
        logger.info("Attempting to import sms_client...")
        from sms_client import send_notification_for_unanswered
        logger.info("Successfully imported sms_client")
        logger.info("Checking for questions to notify...")
        import os
        logger.info(f"Current working directory: {os.getcwd()}")
        logger.info(f"Knowledge base path: {os.path.abspath('knowledge_base.csv')}")
        
        result = send_notification_for_unanswered()
        logger.info(f"SMS notification function returned: {result}")
    except ImportError as e:
        logger.error(f"Failed to import sms_client: {e}")
        import traceback
        logger.error(traceback.format_exc())
    except Exception as e:
        logger.error(f"Error in SMS notification: {e}")
        import traceback
        logger.error(traceback.format_exc())
    
    try:
        from knowledge_manager import archive_answered_questions_to_prompt
        import os
        logger.info("Archiving learned knowledge...")
        prompt_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'prompts.py')
        logger.info(f"Archiving to: {prompt_file}")
        archive_answered_questions_to_prompt(prompt_file=prompt_file)
        logger.info("Successfully archived knowledge")
    except Exception as e:
        logger.error(f"Error archiving knowledge: {e}")
        import traceback
        logger.error(traceback.format_exc())
    
    await ctx.connect()
    logger.info(f"Connected to room: {ctx.room.name}")
    
    caller_phone = "unknown"
    try:
        if ctx.room.metadata:
            import json
            metadata = json.loads(ctx.room.metadata)
            caller_phone = metadata.get('caller_phone', 'unknown')
            logger.info(f"Caller's phone number from room metadata: {caller_phone}")
        else:
            logger.warning("No room metadata found, using 'unknown' for caller phone")
    except Exception as e:
        logger.error(f"Error reading room metadata: {e}")
    
    logger.info("Waiting for participant to join...")
    participant = await ctx.wait_for_participant()
    logger.info(f"Phone call connected from participant: {participant.identity}")
    
    agent_context = {
        "caller_phone": caller_phone
    }
    
    from knowledge_manager import load_additional_knowledge
    additional_knowledge = load_additional_knowledge()
    
    full_instructions = AGENT_INSTRUCTIONS + additional_knowledge
    
    @function_tool
    async def wait_for_answer_with_phone(question: str) -> str:
            The answer if provided, or a fallback message
        """
        return await wait_for_answer(question, caller_phone=agent_context["caller_phone"])
    
    agent = Agent(
        instructions=full_instructions,
        tools=[get_current_time, wait_for_answer_with_phone]
    )
    
    # Configure the voice processing pipeline optimized for telephony
    session = AgentSession(
        # Voice Activity Detection
        vad=silero.VAD.load(),
        
        # Speech-to-Text - Deepgram Nova-3
        stt=deepgram.STT(
            model="nova-3",  # Latest model
            language="en-US",
            interim_results=True,
            punctuate=True,
            smart_format=True,
            filler_words=True,
            endpointing_ms=300,  # Wait 300ms of silence before considering user done (adjust as needed)
            sample_rate=16000
        ),
        
        # Large Language Model - Google Gemini
        llm="google/gemini-2.5-pro",
        
        # Text-to-Speech - Cartesia Sonic-2
        tts=cartesia.TTS(
            model="sonic-2",
            voice="a0e99841-438c-4a64-b679-ae501e7d6091",  # Professional female voice
            language="en",
            speed=1.0,
            sample_rate=24000
        )
    )
    
    # Start the agent session
    await session.start(agent=agent, room=ctx.room)
    
    # Generate personalized greeting based on time of day
    import datetime
    hour = datetime.datetime.now().hour
    if hour < 12:
        time_greeting = "Good morning"
    elif hour < 18:
        time_greeting = "Good afternoon"
    else:
        time_greeting = "Good evening"
    
    await session.generate_reply(
        instructions=get_greeting_instruction(time_greeting)
    )

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('telephony_agent.log', mode='w')
        ]
    )
    
    # Run the agent with the name that matches your dispatch rule
    cli.run_app(WorkerOptions(
        entrypoint_fnc=entrypoint,
        agent_name="telephony_agent"  # This must match your dispatch rule
    ))