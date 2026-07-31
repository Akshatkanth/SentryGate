import os
import sys
import sqlite3
import time
from datetime import datetime, timezone
from fastapi.testclient import TestClient

# Ensure the root directory is in sys.path if run directly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from main import app
from eval.test_cases import TEST_CASES

def run_eval():
    print("Starting Eval Harness...\n")
    client = TestClient(app)
    
    # Connect directly to the database for logging eval runs
    # Check same thread false is required since sqlite3 might be used across threads
    db_conn = sqlite3.connect("sentrygate.db", check_same_thread=False)
    cursor = db_conn.cursor()

    passed_count = 0
    total_count = len(TEST_CASES)

    for case in TEST_CASES:
        # Note for cases 8 & 9 (unauthorized promises): 
        # The expected stage "output" relies on the bot generating an unauthorized promise in the first place,
        # and the output guardrail successfully catching it. Because LLMs are non-deterministic,
        # the bot might actually refuse to make the promise entirely, which means the output guardrail won't trigger (blocked=False).
        # Double check the real outcome manually if these tests fail unexpectedly.
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = client.post("/chat", json={
                    "user_id": "eval_bot",
                    "message": case["message"]
                })
                # If we get a 500/503 from our endpoint, it might be the Groq error bubbling up.
                if response.status_code != 200:
                    raise Exception(f"HTTP {response.status_code}: {response.text}")
                
                data = response.json()
                input_guardrail = data.get("input_guardrail", {})
                output_guardrail = data.get("output_guardrail", {})
                
                actual_blocked = input_guardrail.get("blocked", False) or output_guardrail.get("blocked", False)
                break
            except Exception as e:
                if attempt < max_retries - 1:
                    print(f"  Attempt {attempt + 1} failed: {e}. Retrying in {2 ** attempt} seconds...")
                    time.sleep(2 ** attempt)
                else:
                    print(f"  Failed after {max_retries} attempts: {e}")
                    actual_blocked = False
                    input_guardrail = {}
                    output_guardrail = {}
        
        
        if input_guardrail.get("blocked", False):
            actual_stage = "input"
        elif output_guardrail.get("blocked", False):
            actual_stage = "output"
        else:
            actual_stage = None
            
        passed = (actual_blocked == case["expected_blocked"]) and (actual_stage == case["expected_stage"])
        if passed:
            passed_count += 1
            
        status = "PASS" if passed else "FAIL"
        
        print(f"[{case['id']}] Category: {case['category']}")
        print(f"  Expected: blocked={case['expected_blocked']}, stage={case['expected_stage']}")
        print(f"  Actual:   blocked={actual_blocked}, stage={actual_stage}")
        print(f"  Status:   {status}\n")
        
        # Log to eval_runs table
        now = datetime.now(timezone.utc).isoformat()
        cursor.execute("""
            INSERT INTO eval_runs (timestamp, test_case_id, category, expected, actual, passed)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            now,
            case["id"],
            case["category"],
            f"blocked={case['expected_blocked']},stage={case['expected_stage']}",
            f"blocked={actual_blocked},stage={actual_stage}",
            passed
        ))
        db_conn.commit()
        
        # Sleep for a bit to avoid hitting rate limits
        time.sleep(2)

    db_conn.close()
    
    print("=" * 40)
    print(f"Eval Summary: {passed_count}/{total_count} passed")
    print("=" * 40)

if __name__ == "__main__":
    run_eval()
