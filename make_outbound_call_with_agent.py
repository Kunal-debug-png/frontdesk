import asyncio
import os
import logging
from dotenv import load_dotenv
from livekit import api

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

load_dotenv()

async def make_outbound_call_with_agent(phone_number: str):
    """
    Make an outbound call with agent dispatch.
    This version explicitly dispatches the agent to the room.
    """
    livekit_url = os.getenv("LIVEKIT_URL")
    api_key = os.getenv("LIVEKIT_API_KEY")
    api_secret = os.getenv("LIVEKIT_API_SECRET")
    sip_trunk_id = os.getenv("LIVEKIT_SIP_TRUNK_ID")
    
    if not all([livekit_url, api_key, api_secret, sip_trunk_id]):
        raise ValueError("Missing required environment variables")
    
    lkapi = api.LiveKitAPI(
        url=livekit_url,
        api_key=api_key,
        api_secret=api_secret
    )
    
    try:
        # Use a unique room name
        import time
        room_name = f"outbound-{phone_number.replace('+', '')}-{int(time.time())}"
        
        print("\n" + "="*60)
        print("OUTBOUND CALL WITH AGENT")
        print("="*60)
        
        # Step 1: Create the room first
        print(f"\n[1/3] Creating room: {room_name}")
        room_request = api.CreateRoomRequest(
            name=room_name,
            empty_timeout=300,
            max_participants=10,
            metadata=f'{{"caller_phone": "{phone_number}"}}'
        )
        room = await lkapi.room.create_room(room_request)
        print(f"✓ Room created: {room.name}")
        
        # Step 2: Dispatch agent to the room
        print(f"\n[2/3] Dispatching agent to room...")
        try:
            # Create agent dispatch request
            dispatch_request = api.CreateAgentDispatchRequest(
                room=room_name,
                agent_name="telephony_agent",  # Must match your agent
            )
            dispatch_response = await lkapi.agent_dispatch.create_dispatch(dispatch_request)
            print(f"✓ Agent dispatched!")
            print(f"  Dispatch ID: {dispatch_response.agent_dispatch.id}")
        except Exception as dispatch_error:
            print(f"⚠️  Agent dispatch failed: {dispatch_error}")
            print("  Continuing anyway - agent may auto-join...")
        
        # Step 3: Make the SIP call
        print(f"\n[3/3] Initiating call to {phone_number}...")
        sip_request = api.CreateSIPParticipantRequest(
            sip_trunk_id=sip_trunk_id,
            sip_call_to=phone_number,
            room_name=room_name,
            participant_identity=f"caller-{phone_number}",
            participant_name=f"Outbound Call",
            play_ringtone=True,
        )
        
        sip_response = await lkapi.sip.create_sip_participant(sip_request)
        print(f"✓ Call initiated!")
        print(f"  Room: {room_name}")
        print(f"  Participant ID: {sip_response.participant_id}")
        print(f"  SIP Call ID: {sip_response.sip_call_id}")
        
        # Wait and monitor
        print(f"\n⏳ Monitoring call for 30 seconds...")
        for i in range(6):
            await asyncio.sleep(5)
            
            # Check participants
            participants = await lkapi.room.list_participants(
                api.ListParticipantsRequest(room=room_name)
            )
            
            print(f"\n  [{(i+1)*5}s] Participants in room:")
            for p in participants.participants:
                state_name = {0: "JOINING", 1: "JOINED", 2: "ACTIVE", 3: "DISCONNECTED"}.get(p.state, "UNKNOWN")
                is_agent = "🤖 AGENT" if "agent" in p.identity.lower() else "📞 CALLER"
                print(f"    {is_agent} {p.identity}: {state_name}")
        
        print("\n" + "="*60)
        print("CALL MONITORING COMPLETE")
        print("="*60)
        print("\nDid you hear the agent?")
        print("If NO, check:")
        print("1. Agent is running: python telephony_agent.py start")
        print("2. Agent name matches: 'telephony_agent'")
        print("3. Check agent terminal for errors")
        print("="*60)
        
        return sip_response
        
    except Exception as e:
        logger.error(f"Call failed: {e}", exc_info=True)
        raise
    finally:
        await lkapi.aclose()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python make_outbound_call_with_agent.py <phone_number>")
        print("Example: python make_outbound_call_with_agent.py +918208153112")
        sys.exit(1)
    
    phone_number = sys.argv[1]
    
    if not phone_number.startswith('+'):
        print("Error: Phone number must be in E.164 format (start with +)")
        sys.exit(1)
    
    asyncio.run(make_outbound_call_with_agent(phone_number))
