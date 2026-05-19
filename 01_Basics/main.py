"""
AI Study Assistant / Quiz Generator
Run: python main.py
"""

import json
import sys
from pathlib import Path

# Allow imports from project root
sys.path.insert(0, str(Path(__file__).resolve().parent))

import config
from src.answer_checker import check_answers, format_results_report
from src.notes_generator import format_notes_for_display, generate_notes
from src.quiz_generator import generate_quiz
from src.weakness_analyzer import analyze_weak_areas, format_weakness_report


def clear_screen():
    print("\n" * 2)


def banner():
    print(r"""
   ___   ____    ____ _            _   
  / _ \ / ___|  / ___| |_ ___  ___| |_ 
 | | | |\___ \  \___ \ __/ _ \/ __| __|
 | |_| | ___) |  ___) | ||  __/\__ \ |_ 
  \___/ |____/  |____/ \__\___||___/\__|
        Study Assistant & Quiz Generator
    """)


def get_topic() -> str:
    print("Enter a chapter or topic (e.g. 'Photosynthesis', 'Python loops'):")
    topic = input("> ").strip()
    while not topic:
        topic = input("Topic cannot be empty. Try again:\n> ").strip()
    return topic


def ask_int(prompt: str, default: int, min_v: int, max_v: int) -> int:
    raw = input(f"{prompt} [{default}]: ").strip()
    if not raw:
        return default
    try:
        n = int(raw)
        return max(min_v, min(max_v, n))
    except ValueError:
        return default


def run_quiz(questions: list[dict]) -> dict[int, str]:
    user_answers = {}
    print(f"\n--- Quiz: {len(questions)} questions ---")
    print("Answer with A, B, C, or D (or press Enter to skip)\n")

    for q in questions:
        print(f"\nQ{q['id']}. {q['question']}\n")
        for letter, text in sorted(q["options"].items()):
            print(f"   {letter}) {text}")
        while True:
            ans = input("\nYour answer (A/B/C/D): ").strip().upper()
            if ans == "":
                user_answers[q["id"]] = ""
                break
            if ans in q["options"]:
                user_answers[q["id"]] = ans
                break
            print("  Invalid — choose A, B, C, or D (or Enter to skip).")

    return user_answers


def save_session(topic: str, notes: dict, check: dict, analysis: dict):
    """Optional: save last session to data/ folder."""
    data_dir = Path(__file__).parent / "data"
    data_dir.mkdir(exist_ok=True)
    path = data_dir / "last_session.json"
    payload = {
        "topic": topic,
        "notes": notes,
        "score": check["score"],
        "total": check["total"],
        "percentage": check["percentage"],
        "weak_subtopics": analysis.get("weak_subtopics", []),
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"\nSession saved to: {path}")


def main():
    banner()

    if config.DEMO_MODE:
        print("  [DEMO MODE] No API key — using sample content.")
        print("  Free AI: add GROQ_API_KEY in .env (https://console.groq.com)\n")
    else:
        print(f"  [AI MODE] Using {config.PROVIDER.upper()} — model: {config.MODEL}\n")

    topic = get_topic()
    num_q = ask_int("How many MCQs?", default=5, min_v=3, max_v=10)

    print("\nGenerating study notes... (this may take a few seconds)")
    notes = generate_notes(topic)
    print(format_notes_for_display(notes))

    input("Press Enter when ready for the quiz...")

    notes_text = notes["summary"] + "\n" + "\n".join(notes["key_points"])
    print("\nGenerating quiz questions...")
    questions = generate_quiz(topic, num_questions=num_q, notes_context=notes_text)

    if not questions:
        print("Could not generate questions. Try again or check your API key.")
        return

    user_answers = run_quiz(questions)
    check = check_answers(questions, user_answers)
    print(format_results_report(check))

    analysis = analyze_weak_areas(topic, check)
    print(format_weakness_report(analysis))

    save = input("\nSave this session to data/last_session.json? (y/n): ").strip().lower()
    if save == "y":
        save_session(topic, notes, check, analysis)

    again = input("\nStudy another topic? (y/n): ").strip().lower()
    if again == "y":
        clear_screen()
        main()
    else:
        print("\nGood luck with your studies!")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nBye!")
    except Exception as e:
        print(f"\nError: {e}")
        if config.DEMO_MODE:
            print("Tip: For full AI features, copy .env.example to .env and add your API key.")
