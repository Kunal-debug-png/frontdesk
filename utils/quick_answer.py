"""
Quick answer tool - Use this to answer questions in real-time while customer is on hold.
"""
import csv
import sys
import os

KNOWLEDGE_FILE = "knowledge_base.csv"

def show_waiting_questions():
    """Show questions waiting for answers."""
    if not os.path.exists(KNOWLEDGE_FILE):
        print("No questions yet!")
        return []
    
    waiting = []
    with open(KNOWLEDGE_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['answered'].lower() == 'no':
                waiting.append(row)
    
    return waiting

def answer_question(question: str, answer: str):
    """Answer a specific question."""
    if not os.path.exists(KNOWLEDGE_FILE):
        print("Knowledge base not found!")
        return False
    
    # Read all rows
    rows = []
    found = False
    with open(KNOWLEDGE_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        for row in reader:
            if row['question'].lower().strip() == question.lower().strip():
                row['answer'] = answer
                row['answered'] = 'yes'
                found = True
                print(f"\n✅ Answered: {question}")
                print(f"   Answer: {answer}\n")
            rows.append(row)
    
    if not found:
        print(f"\n❌ Question not found: {question}\n")
        return False
    
    # Write back
    with open(KNOWLEDGE_FILE, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    
    return True

def interactive_mode():
    """Interactive mode to answer questions."""
    print("\n" + "="*60)
    print("QUICK ANSWER TOOL - Real-time Question Answering")
    print("="*60)
    print("This tool helps you answer questions while customers wait!")
    print("="*60 + "\n")
    
    while True:
        waiting = show_waiting_questions()
        
        if not waiting:
            print("✅ No questions waiting for answers!")
            print("\nWaiting for new questions... (Press Ctrl+C to exit)")
            import time
            time.sleep(3)
            continue
        
        print(f"📋 {len(waiting)} question(s) waiting:\n")
        for i, q in enumerate(waiting, 1):
            print(f"{i}. {q['question']}")
            print(f"   From: {q['caller_phone']} at {q['timestamp']}")
            print()
        
        try:
            choice = input("Enter question number to answer (or 'r' to refresh): ").strip()
            
            if choice.lower() == 'r':
                print("\n🔄 Refreshing...\n")
                continue
            
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(waiting):
                    question = waiting[idx]['question']
                    print(f"\n❓ Question: {question}")
                    answer = input("💬 Your answer: ").strip()
                    
                    if answer:
                        answer_question(question, answer)
                        print("✅ Answer saved! Customer will receive it immediately.\n")
                    else:
                        print("❌ Answer cannot be empty!\n")
                else:
                    print("❌ Invalid number!\n")
            except ValueError:
                print("❌ Please enter a valid number!\n")
                
        except KeyboardInterrupt:
            print("\n\n👋 Exiting...\n")
            break

def quick_answer_mode():
    """Quick mode - answer the most recent question."""
    waiting = show_waiting_questions()
    
    if not waiting:
        print("✅ No questions waiting!")
        return
    
    # Get most recent question
    question = waiting[-1]['question']
    caller = waiting[-1]['caller_phone']
    
    print("\n" + "="*60)
    print("QUICK ANSWER - Most Recent Question")
    print("="*60)
    print(f"\n❓ Question: {question}")
    print(f"📞 From: {caller}\n")
    
    answer = input("💬 Your answer: ").strip()
    
    if answer:
        answer_question(question, answer)
        print("\n✅ Answer saved! Customer will receive it immediately.\n")
    else:
        print("\n❌ Answer cannot be empty!\n")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "quick":
        quick_answer_mode()
    else:
        interactive_mode()
