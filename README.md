# Telephony Agent with Knowledge Base

A telephony agent system that handles incoming calls, manages a knowledge base of questions and answers, and integrates with Twilio for SMS notifications.

## Design Overview

The system is built around a modular architecture with the following key components:

1. **Telephony Agent** (`telephony_agent.py`):
   - Handles voice interactions with callers
   - Manages call state and session information
   - Integrates with LiveKit for real-time communication

2. **Knowledge Management** (`knowledge_manager.py`):
   - Manages a CSV-based knowledge base of questions and answers
   - Handles question archiving to prompt templates
   - Provides querying capabilities for the agent

3. **SMS Notification System** (`sms_client.py`):
   - Sends SMS notifications when questions are answered
   - Uses Twilio's API for message delivery
   - Tracks notification status to prevent duplicates

4. **Web Interface** (`web_ui.py`):
   - Provides a simple web interface for managing the knowledge base
   - Built with FastAPI for easy API development
   - Serves static files for the admin dashboard

## Implementation Details

### Data Flow
1. When a call is received, the telephony agent processes the audio input
2. Unanswered questions are stored in `knowledge_base.csv`
3. Administrators can view and answer questions through the web interface
4. Once answered, the system can notify the original caller via SMS
5. Answered questions are archived to the prompt template for future reference

### Key Features
- **Real-time Question Handling**: Processes and stores questions during calls
- **SMS Notifications**: Alerts users when their questions are answered
- **Knowledge Archiving**: Moves answered questions to the prompt template
- **Web-based Management**: Simple interface for managing the knowledge base

## Trade-offs and Considerations

### Design Decisions
1. **CSV-based Storage**:
   - Chosen for simplicity and ease of implementation
   - May not scale well for very large knowledge bases
   - Easy to inspect and modify manually if needed

2. **SMS Notifications**:
   - Requires Twilio account and configuration
   - Adds latency to the response cycle
   - Provides better user experience by closing the feedback loop

3. **Prompt Engineering**:
   - Uses a template-based approach for system prompts
   - Balances flexibility with consistency
   - Requires careful tuning for optimal performance

### Performance Considerations
- The system is designed for moderate call volumes
- CSV operations are not thread-safe (handled by serializing access)
- SMS notifications are processed asynchronously to avoid blocking

## Setup and Installation

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Configure environment variables in `.env`:
   ```
   TWILIO_SID=your_twilio_sid
   TWILIO_SECRET=your_twilio_auth_token
   TWILIO_OUTBOUND=your_twilio_phone_number
   ```

3. Start the telephony agent:
   ```bash
   python telephony_agent.py start
   ```

4. Access the web interface at `http://localhost:8000`

## Usage

1. **Handling Calls**:
   - The agent will automatically process incoming calls
   - Unanswered questions are logged for later response

2. **Managing Knowledge**:
   - Use the web interface to view and answer questions
   - Monitor system status and statistics

3. **SMS Notifications**:
   - Configure Twilio credentials in `.env`
   - Notifications are sent automatically when questions are answered

## Future Improvements

- to Implement a proper database backend for better scalability
- to Add user authentication for the web interface
- to Support multiple languages
- to Add analytics and reporting features
- to Implement rate limiting for SMS notifications



API & Service Setup Guide

1. Deepgram (Speech-to-Text)

Sign up at console.deepgram.com
.

Go to API Keys → Create New Key and copy it.

Add to .env as:

DEEPGRAM_API_KEY="your_deepgram_key"

2. Cartesia (Text-to-Speech / Voice Generation)

Create an account at cartesia.ai
.

In the dashboard, open API Access → Create Key.

Add to .env as:

CARTESIA_API_KEY="your_cartesia_key"

4. Twilio (Voice / SMS Integration)

Sign up at twilio.com
.

In Console → Account Info, copy:

Account SID

Auth Token

Buy or configure an outbound phone number in Phone Numbers.

Add to .env:

TWILIO_SID="your_twilio_sid"
TWILIO_SECRET="your_auth_token"
TWILIO_OUTBOUND="+1xxxxxxxxxx"

4. LiveKit (Voice/Video/SIP Bridge)

Sign up at livekit.io
.

Go to Cloud Dashboard → Create Project.

Copy your LiveKit URL, API Key, and API Secret.

To enable SIP:

Open SIP → Create Trunk

Copy the SIP URI and Trunk ID

Add to .env:

LIVEKIT_URL="wss://your-project.livekit.cloud"
LIVEKIT_API_KEY="your_livekit_api_key"
LIVEKIT_API_SECRET="your_livekit_api_secret"
LIVEKIT_SIP_URI="sip:xxxxx.sip.livekit.cloud"
LIVEKIT_SIP_TRUNK_ID="ST_xxxxxxxxxx"