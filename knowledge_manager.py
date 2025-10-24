"""
Knowledge management system for handling unknown questions and learning.
"""
import csv
import os
import logging
from datetime import datetime
from typing import Dict, List, Optional
from twilio.rest import Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def send_sms(to_phone: str, message: str) -> bool:
    """
    Send an SMS using Twilio
    
    Args:
        to_phone: Recipient phone number in E.164 format (e.g., +1234567890)
        message: Message to send
        
    Returns:
        bool: True if message was sent successfully, False otherwise
    """
    try:
        account_sid = os.getenv('TWILIO_SID')
        auth_token = os.getenv('TWILIO_SECRET')
        from_phone = os.getenv('TWILIO_OUTBOUND')
        
        if not all([account_sid, auth_token, from_phone]):
            logger.error("Missing Twilio credentials in environment variables")
            return False
            
        client = Client(account_sid, auth_token)
        
        message = client.messages.create(
            body=message,
            from_=from_phone,
            to=to_phone
        )
        
        logger.info(f"SMS sent to {to_phone}. SID: {message.sid}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send SMS to {to_phone}: {str(e)}")
        return False

KNOWLEDGE_FILE = "knowledge_base.csv"

def initialize_knowledge_base():
    """Create knowledge base CSV if it doesn't exist."""
    if not os.path.exists(KNOWLEDGE_FILE):
        with open(KNOWLEDGE_FILE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['question', 'answer', 'answered', 'timestamp', 'caller_phone', 'answered_on_call'])

def add_unknown_question(question: str, caller_phone: str = "unknown") -> bool:
    """
    Add an unknown question to the knowledge base.
    
    Args:
        question: The question that was asked
        caller_phone: Phone number of the caller
    
    Returns:
        True if added successfully
    """
    try:
        initialize_knowledge_base()
        
        # Check if question already exists
        if question_exists(question):
            return False
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        with open(KNOWLEDGE_FILE, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([question, '', 'no', timestamp, caller_phone, 'false'])
        
        return True
    except Exception as e:
        print(f"Error adding question: {e}")
        return False

def question_exists(question: str) -> bool:
    """Check if a question already exists in the knowledge base."""
    try:
        if not os.path.exists(KNOWLEDGE_FILE):
            return False
        
        with open(KNOWLEDGE_FILE, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['question'].lower().strip() == question.lower().strip():
                    return True
        return False
    except Exception:
        return False

def get_unanswered_questions() -> List[Dict]:
    """Get all unanswered questions."""
    try:
        initialize_knowledge_base()
        
        unanswered = []
        with open(KNOWLEDGE_FILE, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['answered'].lower() == 'no':
                    unanswered.append(row)
        
        return unanswered
    except Exception:
        return []

def get_answered_questions(include_answered_on_call: bool = None) -> Dict[str, str]:
    """
    Get all answered questions as a dictionary.
    
    Args:
        include_answered_on_call: If set, filter by answered_on_call status (True/False)
                                If None, return all answered questions
    
    Returns:
        Dict mapping questions to answers
    """
    try:
        initialize_knowledge_base()
        
        result = {}
        with open(KNOWLEDGE_FILE, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['answered'].lower() == 'yes' and row['answer'].strip():
                    if include_answered_on_call is not None:
                        if row.get('answered_on_call', 'false').lower() == str(include_answered_on_call).lower():
                            result[row['question']] = row['answer']
                    else:
                        result[row['question']] = row['answer']
        
        return result
    except Exception as e:
        print(f"Error getting answered questions: {e}")
        return {}

def check_for_answer(question: str) -> Optional[str]:
    """
    Check if a specific question has been answered in the CSV.
    Used for real-time answer detection.
    
    Args:
        question: The question to check
    
    Returns:
        The answer if found and answered=yes, None otherwise
    """
    try:
        if not os.path.exists(KNOWLEDGE_FILE):
            return None
        
        with open(KNOWLEDGE_FILE, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['question'].lower().strip() == question.lower().strip():
                    if row['answered'].lower() == 'yes' and row['answer'].strip():
                        return row['answer']
        
        return None
    except Exception:
        return None

def mark_question_answered(question: str, answered_on_call: bool = False) -> bool:
    """
    Mark a question as answered after the agent uses it.
    
    Args:
        question: The question to mark as answered
        answered_on_call: Whether the question was answered during a call
    
    Returns:
        True if marked successfully
    """
    try:
        if not os.path.exists(KNOWLEDGE_FILE):
            return False
            
        rows = []
        fieldnames = []
        
        # Read existing data
        with open(KNOWLEDGE_FILE, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames
            
            for row in reader:
                if row['question'] == question:
                    # Store the old answered_on_call value before updating
                    was_answered_on_call = row.get('answered_on_call', 'false').lower() == 'true'
                    
                    # Update the row
                    row['answered'] = 'yes'
                    row['answered_on_call'] = str(answered_on_call).lower()
                    row['timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    
                    # If this question wasn't answered on call and has a valid phone number, send SMS
                    if not was_answered_on_call and row.get('caller_phone') and row.get('answer'):
                        phone = row['caller_phone']
                        # Ensure phone number starts with a '+' for E.164 format
                        if not phone.startswith('+'):
                            phone = f"+{phone}"
                        
                        sms_message = (
                            f"Your question has been answered!\n\n"
                            f"Q: {row['question']}\n"
                            f"A: {row['answer']}\n\n"
                            f"Thank you for your patience!"
                        )
                        
                        # Send SMS in a separate thread to not block the main process
                        import threading
                        threading.Thread(
                            target=send_sms,
                            args=(phone, sms_message),
                            daemon=True
                        ).start()
                
                rows.append(row)
        
        # Write back
        with open(KNOWLEDGE_FILE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        
        return True
    except Exception as e:
        print(f"Error marking question as answered: {e}")
        return False

def load_additional_knowledge() -> str:
    """
    Load all answered questions and format them for the prompt.
    
    Returns:
        Formatted string of additional knowledge
    """
    answered = get_answered_questions()
    
    if not answered:
        return ""
    
    knowledge_text = "\n\nADDITIONAL KNOWLEDGE (Recently Added):\n"
    for question, answer in answered.items():
        knowledge_text += f"\nQ: {question}\nA: {answer}\n"
    
    return knowledge_text

def archive_answered_questions_to_prompt(prompt_file: str = "prompts.py") -> bool:
    """
    Move answered questions from CSV to the prompt file permanently.
    This clears answered questions from CSV and adds them to the agent's knowledge.
    
    Args:
        prompt_file: Path to the prompts.py file
    
    Returns:
        True if successful, False otherwise
    """
    try:
        print("\n" + "="*50)
        print("STARTING KNOWLEDGE ARCHIVE PROCESS")
        print("-"*50)
        
        answered = get_answered_questions()
        print(f"Found {len(answered)} answered questions to process")
        for q, a in answered.items():
            print(f"- Q: {q}\n  A: {a}")
        
        if not answered:
            print("No answered questions to archive.")
            return True
        
        # Read the current prompt file
        with open(prompt_file, 'r', encoding='utf-8') as f:
            prompt_content = f.read()
        
        # Create the new knowledge section
        new_knowledge = "\n# LEARNED KNOWLEDGE FROM PAST INTERACTIONS:\n{LEARNED_QA}"
        
        # Check if we need to add the LEARNED_QA section
        if "LEARNED_QA = " not in prompt_content:
            # Add the LEARNED_QA section before CRITICAL RULES
            prompt_content = prompt_content.replace(
                'CRITICAL RULES:',
                new_knowledge + '\n\nCRITICAL RULES:'
            )
            print("\nAdded LEARNED_QA section to prompts.py")
        
        # Create or update the LEARNED_QA content
        learned_qa_content = ""
        for question, answer in answered.items():
            learned_qa_content += f"Q: {question}\nA: {answer}\n\n"
        
        # Update the LEARNED_QA variable
        if "LEARNED_QA = " in prompt_content:
            # Extract existing content
            import re
            pattern = r'(LEARNED_QA = """)(.*?)(""")'
            existing_learned_qa = re.search(pattern, prompt_content, re.DOTALL)
            
            if existing_learned_qa:
                # Append new Q&A to existing content
                current_content = existing_learned_qa.group(2)
                updated_content = current_content + learned_qa_content
                prompt_content = re.sub(
                    pattern,
                    f'\\1{updated_content}\\3',
                    prompt_content,
                    flags=re.DOTALL
                )
                print("\nUpdated existing LEARNED_QA section with new Q&A pairs")
        
        # Write back to file
        with open(prompt_file, 'w', encoding='utf-8') as f:
            f.write(prompt_content)
        
        # Now clear answered questions from CSV, keep only unanswered
        print("\nProcessing knowledge_base.csv:")
        if not os.path.exists(KNOWLEDGE_FILE):
            print("  knowledge_base.csv not found")
            return True
        
        unanswered_rows = []
        with open(KNOWLEDGE_FILE, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames
            print(f"  Found columns: {', '.join(fieldnames)}")
            
            for row in reader:
                if row['answered'].lower() != 'yes':
                    print(f"  Keeping unanswered question: {row['question']}")
                    unanswered_rows.append(row)
                else:
                    print(f"  Will remove answered question: {row['question']}")
        
        # Rewrite CSV with only unanswered questions
        print(f"\nWriting {len(unanswered_rows)} unanswered questions back to knowledge_base.csv")
        with open(KNOWLEDGE_FILE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(unanswered_rows)
            print("  Successfully updated knowledge_base.csv")
        
        print("\n" + "="*50)
        print(f"✅ ARCHIVE COMPLETE")
        print("-"*50)
        print(f"- Added {len(answered)} answered questions to {prompt_file}")
        print(f"- Kept {len(unanswered_rows)} unanswered questions in knowledge_base.csv")
        print("="*50 + "\n")
        
        return True
        
    except Exception as e:
        print(f"❌ Error archiving questions: {e}")
        import traceback
        traceback.print_exc()
        return False

def get_knowledge_stats() -> Dict:
    """Get statistics about the knowledge base."""
    try:
        initialize_knowledge_base()
        
        total = 0
        answered_count = 0
        unanswered_count = 0
        
        with open(KNOWLEDGE_FILE, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                total += 1
                if row['answered'].lower() == 'yes':
                    answered_count += 1
                else:
                    unanswered_count += 1
        
        return {
            'total': total,
            'answered': answered_count,
            'unanswered': unanswered_count
        }
    except Exception:
        return {'total': 0, 'answered': 0, 'unanswered': 0}

# Example usage and testing
if __name__ == "__main__":
    # Initialize
    initialize_knowledge_base()
    
    # Add a test question
    add_unknown_question("Do you have parking?", "+918208153112")
    
    # Get stats
    stats = get_knowledge_stats()
    print(f"Knowledge Base Stats: {stats}")
    
    # Get unanswered
    unanswered = get_unanswered_questions()
    print(f"\nUnanswered questions: {len(unanswered)}")
    for q in unanswered:
        print(f"  - {q['question']}")
