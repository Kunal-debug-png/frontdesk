"""
Monitor for new questions and show desktop notifications.
Run this in the background to get alerted when customers ask questions.
"""
import time
import os
from knowledge_manager import get_unanswered_questions

def monitor_questions():
    """Monitor for new unanswered questions."""
    print("\n" + "="*60)
    print("📢 QUESTION MONITOR - Watching for new questions...")
    print("="*60)
    print("Keep this running to see questions as they arrive!")
    print("Press Ctrl+C to stop\n")
    
    last_count = 0
    
    try:
        while True:
            unanswered = get_unanswered_questions()
            current_count = len(unanswered)
            
            if current_count > last_count:
                # New question(s) arrived!
                new_questions = unanswered[last_count:]
                
                print("\n" + "🔔 " * 20)
                print("🚨 NEW QUESTION ALERT! 🚨")
                print("🔔 " * 20)
                
                for q in new_questions:
                    print(f"\n❓ Question: {q['question']}")
                    print(f"📞 From: {q['caller_phone']}")
                    print(f"⏰ Time: {q['timestamp']}")
                    print("\n⚡ CUSTOMER IS WAITING! Answer now:")
                    print(f"   python quick_answer.py")
                
                print("\n" + "🔔 " * 20 + "\n")
                
                # Try to play a beep (Windows)
                try:
                    import winsound
                    winsound.Beep(1000, 500)  # 1000 Hz for 500ms
                except:
                    pass
            
            last_count = current_count
            
            # Check every 2 seconds
            time.sleep(2)
            
    except KeyboardInterrupt:
        print("\n\n👋 Monitoring stopped.\n")

if __name__ == "__main__":
    monitor_questions()
