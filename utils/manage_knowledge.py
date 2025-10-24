"""
Helper script to manage the knowledge base.
Use this to view and answer questions.
"""
import sys
from knowledge_manager import (
    get_unanswered_questions,
    get_answered_questions,
    get_knowledge_stats,
    initialize_knowledge_base
)

def show_stats():
    """Display knowledge base statistics."""
    stats = get_knowledge_stats()
    print("\n" + "="*60)
    print("KNOWLEDGE BASE STATISTICS")
    print("="*60)
    print(f"Total Questions: {stats['total']}")
    print(f"Answered: {stats['answered']}")
    print(f"Unanswered: {stats['unanswered']}")
    print("="*60 + "\n")

def show_unanswered():
    """Display all unanswered questions."""
    questions = get_unanswered_questions()
    
    print("\n" + "="*60)
    print("UNANSWERED QUESTIONS")
    print("="*60)
    
    if not questions:
        print("No unanswered questions! 🎉")
    else:
        for i, q in enumerate(questions, 1):
            print(f"\n{i}. Question: {q['question']}")
            print(f"   Asked by: {q['caller_phone']}")
            print(f"   Time: {q['timestamp']}")
            print("-" * 60)
    
    print()

def show_answered():
    """Display all answered questions."""
    answered = get_answered_questions()
    
    print("\n" + "="*60)
    print("ANSWERED QUESTIONS (Active Knowledge)")
    print("="*60)
    
    if not answered:
        print("No answered questions yet.")
    else:
        for i, (question, answer) in enumerate(answered.items(), 1):
            print(f"\n{i}. Q: {question}")
            print(f"   A: {answer}")
            print("-" * 60)
    
    print()

def main():
    """Main menu."""
    initialize_knowledge_base()
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "stats":
            show_stats()
        elif command == "unanswered":
            show_unanswered()
        elif command == "answered":
            show_answered()
        else:
            print(f"Unknown command: {command}")
            print_usage()
    else:
        # Show everything
        show_stats()
        show_unanswered()
        show_answered()

def print_usage():
    """Print usage instructions."""
    print("\nUsage:")
    print("  python manage_knowledge.py              # Show everything")
    print("  python manage_knowledge.py stats        # Show statistics")
    print("  python manage_knowledge.py unanswered   # Show unanswered questions")
    print("  python manage_knowledge.py answered     # Show answered questions")
    print("\nTo answer questions:")
    print("  1. Open knowledge_base.csv in Excel or any CSV editor")
    print("  2. Fill in the 'answer' column for unanswered questions")
    print("  3. Change 'answered' column from 'no' to 'yes'")
    print("  4. Save the file")
    print("  5. Restart the agent - it will automatically load new answers!")
    print()

if __name__ == "__main__":
    main()
