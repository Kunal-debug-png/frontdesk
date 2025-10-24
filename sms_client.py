import os
import logging
from twilio.rest import Client
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SMSClient:
    def __init__(self):
        self.account_sid = os.getenv('TWILIO_SID')
        self.auth_token = os.getenv('TWILIO_SECRET')
        self.from_phone = os.getenv('TWILIO_OUTBOUND')
        
        if not all([self.account_sid, self.auth_token, self.from_phone]):
            raise ValueError("Missing Twilio credentials in environment variables")
        
        self.client = Client(self.account_sid, self.auth_token)
    
    def send_sms(self, to_phone: str, message: str) -> bool:
        try:
            if not to_phone.startswith('+'):
                to_phone = f"+{to_phone}"
            
            message = self.client.messages.create(
                body=message,
                from_=self.from_phone,
                to=to_phone
            )
            
            logger.info(f"SMS sent to {to_phone}. SID: {message.sid}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send SMS to {to_phone}: {str(e)}")
            return False

def send_notification_for_unanswered():
    import csv
    from datetime import datetime
    
    KNOWLEDGE_FILE = "knowledge_base.csv"
    
    try:
        logger.info(f"Checking {KNOWLEDGE_FILE} for questions to notify...")
        
        if not os.path.exists(KNOWLEDGE_FILE):
            logger.error(f"{KNOWLEDGE_FILE} not found!")
            return
        
        sms_client = SMSClient()
        
        with open(KNOWLEDGE_FILE, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            logger.info(f"Found {len(rows)} rows in {KNOWLEDGE_FILE}")
        
        notifications_sent = 0
        
        for i, row in enumerate(rows, 1):
            logger.info(f"\nChecking row {i}:")
            logger.info(f"  Question: {row.get('question')}")
            logger.info(f"  Answered: {row.get('answered')}")
            logger.info(f"  Answer: {row.get('answer')}")
            logger.info(f"  Phone: {row.get('caller_phone')}")
            logger.info(f"  Answered on call: {row.get('answered_on_call')}")
            
            if (row.get('answered', '').lower() == 'yes' and 
                row.get('answered_on_call', 'false').lower() == 'false' and
                row.get('caller_phone') and 
                row.get('answer')):
                
                try:
                    message = (
                        "Your question has been answered!\n\n"
                        f"Q: {row['question']}\n"
                        f"A: {row['answer']}\n\n"
                        "Thank you for your patience!"
                    )
                    
                    logger.info(f"Sending SMS to {row['caller_phone']}...")
                    success = sms_client.send_sms(row['caller_phone'], message)
                    
                    if success:
                        logger.info("SMS sent successfully!")
                        row['answered_on_call'] = 'true'
                        notifications_sent += 1
                    else:
                        logger.error("Failed to send SMS")
                        
                except Exception as e:
                    logger.error(f"Error sending SMS: {str(e)}")
                    import traceback
                    logger.error(traceback.format_exc())
        
        if notifications_sent > 0:
            try:
                with open(KNOWLEDGE_FILE, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=reader.fieldnames)
                    writer.writeheader()
                    writer.writerows(rows)
                logger.info(f"Updated {KNOWLEDGE_FILE} with {notifications_sent} notification(s)")
            except Exception as e:
                logger.error(f"Error updating {KNOWLEDGE_FILE}: {str(e)}")
        else:
            logger.info("No notifications were sent")
                
    except Exception as e:
        logger.error(f"Error in send_notification_for_unanswered: {str(e)}")

if __name__ == "__main__":
    send_notification_for_unanswered()
