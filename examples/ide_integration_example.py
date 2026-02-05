#!/usr/bin/env python3
"""
Example: IDE integration using waza's JSON streaming

This demonstrates how an IDE extension can:
1. Spawn waza as subprocess  
2. Parse line-delimited JSON events
3. Update UI in real-time

Usage:
    python ide_integration_example.py examples/code-explainer/eval.yaml
"""

import json
import subprocess
import sys
from datetime import datetime

def run_eval_with_progress(eval_path: str):
    """Run waza eval and display progress from JSON events."""
    
    print(f"Starting evaluation: {eval_path}")
    print("-" * 60)
    
    # Spawn waza with JSON streaming
    proc = subprocess.Popen(
        ["waza", "run", eval_path, "--stream-json", "--executor", "mock"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1  # Line buffered
    )
    
    tasks_status = {}
    eval_info = {}
    
    try:
        # Read line-delimited JSON events
        for line in proc.stdout:
            if not line.strip():
                continue
                
            try:
                event = json.loads(line)
                handle_event(event, eval_info, tasks_status)
            except json.JSONDecodeError:
                print(f"Warning: Could not parse line: {line[:50]}...")
                
        # Wait for process to complete
        return_code = proc.wait()
        
        if return_code == 0:
            print("\n" + "=" * 60)
            print("Evaluation completed successfully!")
            print_summary(eval_info, tasks_status)
        else:
            stderr = proc.stderr.read()
            print(f"\nError: Process exited with code {return_code}")
            if stderr:
                print(f"stderr: {stderr}")
                
        return return_code
        
    except KeyboardInterrupt:
        proc.terminate()
        proc.wait()
        print("\nEvaluation cancelled by user")
        return 1

def handle_event(event: dict, eval_info: dict, tasks_status: dict):
    """Handle a single JSON event from waza."""
    
    event_type = event.get("type")
    timestamp = datetime.fromtimestamp(event.get("timestamp", 0))
    time_str = timestamp.strftime("%H:%M:%S")
    
    if event_type == "eval_start":
        eval_info.update({
            "name": event.get("eval"),
            "skill": event.get("skill"),
            "total_tasks": event.get("tasks"),
            "started_at": timestamp
        })
        print(f"[{time_str}] Starting eval: {event.get('eval')}")
        print(f"            Skill: {event.get('skill')}")
        print(f"            Tasks: {event.get('tasks')}")
        print()
        
    elif event_type == "task_start":
        task_name = event.get("task")
        idx = event.get("idx")
        total = event.get("total")
        print(f"[{time_str}] [{idx}/{total}] Task started: {task_name}")
        tasks_status[task_name] = {"status": "running", "started_at": timestamp}
        
    elif event_type == "task_complete":
        task_name = event.get("task")
        status = event.get("status")
        took_ms = event.get("took_ms", 0)
        score = event.get("score", 0)
        
        # Status indicator
        indicator = "✓" if status == "passed" else "✗"
        color = "\033[92m" if status == "passed" else "\033[91m"  # Green/Red
        reset = "\033[0m"
        
        print(f"[{time_str}]       {color}{indicator}{reset} {status} ({took_ms}ms, score: {score:.2f})")
        
        tasks_status[task_name] = {
            "status": status,
            "duration_ms": took_ms,
            "score": score,
            "completed_at": timestamp
        }
        
    elif event_type == "eval_complete":
        eval_info.update({
            "passed": event.get("passed"),
            "failed": event.get("failed"),
            "total": event.get("total"),
            "pass_rate": event.get("rate"),
            "completed_at": timestamp
        })
        
def print_summary(eval_info: dict, tasks_status: dict):
    """Print final summary."""
    
    passed = eval_info.get("passed", 0)
    failed = eval_info.get("failed", 0)
    total = eval_info.get("total", 0)
    pass_rate = eval_info.get("pass_rate", 0)
    
    print(f"\nResults:")
    print(f"  Passed: {passed}/{total}")
    print(f"  Failed: {failed}/{total}")
    print(f"  Pass Rate: {pass_rate*100:.1f}%")
    
    if eval_info.get("started_at") and eval_info.get("completed_at"):
        duration = eval_info["completed_at"] - eval_info["started_at"]
        print(f"  Duration: {duration.total_seconds():.1f}s")
    
    # Task breakdown
    if tasks_status:
        print(f"\nTask Breakdown:")
        for task_name, status in tasks_status.items():
            if status.get("status") == "passed":
                indicator = "\033[92m✓\033[0m"
            else:
                indicator = "\033[91m✗\033[0m"
            
            duration = status.get("duration_ms", 0)
            score = status.get("score", 0)
            print(f"  {indicator} {task_name[:40]:40} {duration:6}ms  {score:.2f}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python ide_integration_example.py <eval.yaml>")
        print("\nExample:")
        print("  python ide_integration_example.py examples/code-explainer/eval.yaml")
        sys.exit(1)
    
    eval_path = sys.argv[1]
    exit_code = run_eval_with_progress(eval_path)
    sys.exit(exit_code)
