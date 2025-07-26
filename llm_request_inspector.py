#!/usr/bin/env python3
"""
LLM Request Inspector - Tool to track and analyze llama.cpp requests.
"""

import sys
import os
import glob
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

def watch_requests():
    """Watch for new request files and display them."""
    print("=== LLM Request Inspector ===")
    print("Watching for new llama.cpp requests...")
    print("Use Ctrl+C to stop\n")
    
    log_dir = "logs/llm_requests"
    os.makedirs(log_dir, exist_ok=True)
    
    seen_files = set()
    
    try:
        while True:
            # Check for new request files
            request_files = glob.glob(f"{log_dir}/request_*.txt")
            response_files = glob.glob(f"{log_dir}/response_*.txt")
            
            new_request_files = [f for f in request_files if f not in seen_files]
            new_response_files = [f for f in response_files if f not in seen_files]
            
            for file_path in sorted(new_request_files):
                print_request_file(file_path)
                seen_files.add(file_path)
            
            for file_path in sorted(new_response_files):
                print_response_file(file_path)
                seen_files.add(file_path)
            
            import time
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nStopping request inspector...")

def print_request_file(file_path):
    """Print request file contents."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        print(f"{'='*60}")
        print(f"🔍 NEW REQUEST: {os.path.basename(file_path)}")
        print(f"{'='*60}")
        
        # Extract key information
        lines = content.split('\n')
        for line in lines:
            if line.startswith('Timestamp:'):
                print(f"⏰ {line}")
            elif line.startswith('URL:'):
                print(f"🌐 {line}")
            elif '"prompt":' in line:
                # Find prompt in payload
                break
        
        # Find and extract prompt
        prompt_start = content.find('=== FULL PROMPT ===')
        prompt_end = content.find('=== END PROMPT ===')
        
        if prompt_start != -1 and prompt_end != -1:
            prompt = content[prompt_start + len('=== FULL PROMPT ==='):prompt_end].strip()
            print(f"\n📝 PROMPT ({len(prompt)} chars):")
            print("-" * 40)
            
            # Show context analysis
            analyze_prompt_context(prompt)
            
            # Show first 300 chars of prompt
            if len(prompt) > 300:
                print(f"{prompt[:300]}...")
                print(f"... (truncated, full prompt {len(prompt)} chars)")
            else:
                print(prompt)
        
        print()
        
    except Exception as e:
        print(f"Error reading request file {file_path}: {e}")

def print_response_file(file_path):
    """Print response file contents."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        print(f"📤 RESPONSE: {os.path.basename(file_path)}")
        
        # Extract generated text
        text_start = content.find('=== GENERATED TEXT ===')
        text_end = content.find('=== FULL RESPONSE ===')
        
        if text_start != -1 and text_end != -1:
            generated_text = content[text_start + len('=== GENERATED TEXT ==='):text_end].strip()
            print(f"✨ Generated ({len(generated_text)} chars): {generated_text[:150]}...")
        
        print()
        
    except Exception as e:
        print(f"Error reading response file {file_path}: {e}")

def analyze_prompt_context(prompt):
    """Analyze the prompt to check what context was included."""
    print("🔍 CONTEXT ANALYSIS:")
    
    # Check for scene context
    if 'current_text' in prompt.lower():
        print("  ✅ Contains current_text variable")
    if 'scene_summary' in prompt.lower():
        print("  ✅ Contains scene_summary variable")
    if 'project_name' in prompt.lower():
        print("  ✅ Contains project_name variable")
    if 'has_selection' in prompt.lower():
        print("  ✅ Contains has_selection variable")
    if 'selected_text' in prompt.lower():
        print("  ✅ Contains selected_text variable")
    
    # Check for actual text content
    maria_count = prompt.lower().count('maria')
    if maria_count > 0:
        print(f"  📝 Contains 'Maria' {maria_count} times")
    
    # Check for Polish text indicators
    polish_chars = ['ą', 'ć', 'ę', 'ł', 'ń', 'ó', 'ś', 'ź', 'ż']
    polish_count = sum(prompt.count(char) for char in polish_chars)
    if polish_count > 0:
        print(f"  🇵🇱 Contains Polish characters ({polish_count} total)")

def list_recent_requests():
    """List recent requests."""
    print("=== Recent LLM Requests ===\n")
    
    log_dir = "logs/llm_requests"
    if not os.path.exists(log_dir):
        print("No requests logged yet.")
        return
    
    # Get all request files, sorted by modification time
    request_files = glob.glob(f"{log_dir}/request_*.txt")
    request_files.sort(key=os.path.getmtime, reverse=True)
    
    if not request_files:
        print("No requests logged yet.")
        return
    
    print(f"Found {len(request_files)} request(s):\n")
    
    for i, file_path in enumerate(request_files[:10]):  # Show last 10
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract timestamp and prompt preview
            timestamp_line = [line for line in content.split('\n') if line.startswith('Timestamp:')]
            timestamp = timestamp_line[0].replace('Timestamp: ', '') if timestamp_line else 'Unknown'
            
            prompt_start = content.find('=== FULL PROMPT ===')
            prompt_end = content.find('=== END PROMPT ===')
            
            if prompt_start != -1 and prompt_end != -1:
                prompt = content[prompt_start + len('=== FULL PROMPT ==='):prompt_end].strip()
                preview = prompt[:100].replace('\n', ' ')
                print(f"{i+1:2d}. {timestamp}")
                print(f"    📝 {preview}...")
                analyze_prompt_context(prompt)
                print()
        
        except Exception as e:
            print(f"Error reading {file_path}: {e}")

def test_context_building():
    """Test context building with different scenarios."""
    print("=== Testing Context Building ===\n")
    
    try:
        from core.llm.service import LLMService
        
        service = LLMService()
        service.initialize('llamacpp')
        
        # Test scenarios
        scenarios = [
            {
                'name': 'Basic scene context',
                'context': {
                    'current_text': 'Maria spojrzała przez okno.',
                    'scene_summary': 'Scena w domu Marii',
                    'project_name': 'Test Project'
                }
            },
            {
                'name': 'With text selection',
                'context': {
                    'current_text': 'Maria spojrzała przez okno.',
                    'scene_summary': 'Scena w domu Marii',
                    'project_name': 'Test Project',
                    'has_selection': True,
                    'selected_text': 'przez okno'
                }
            },
            {
                'name': 'Longer scene text',
                'context': {
                    'current_text': 'Maria spojrzała przez okno na deszczowy krajobraz. Krople deszczu spływały po szybie, tworząc malownicze wzory. Myślała o wszystkim, co się zdarzyło ostatnio.',
                    'scene_summary': 'Scena refleksji Marii w domu podczas deszczu',
                    'project_name': 'Test Project'
                }
            }
        ]
        
        for i, scenario in enumerate(scenarios, 1):
            print(f"{i}. Testing: {scenario['name']}")
            print(f"   Context: {scenario['context']}")
            
            try:
                # Execute task to trigger logging
                response = service.execute_task("continue_scene", scenario['context'])
                print(f"   ✅ Request sent successfully (response: {len(response)} chars)")
            except Exception as e:
                print(f"   ❌ Request failed: {e}")
            
            print()
        
        print("✅ All test scenarios completed. Check logs/llm_requests/ for details.")
        
    except Exception as e:
        print(f"❌ Error testing context building: {e}")

def clean_logs():
    """Clean old log files."""
    log_dir = "logs/llm_requests"
    if not os.path.exists(log_dir):
        print("No log directory found.")
        return
    
    files = glob.glob(f"{log_dir}/*.txt")
    if not files:
        print("No log files found.")
        return
    
    print(f"Found {len(files)} log files. Delete all? (y/N): ", end='')
    response = input().strip().lower()
    
    if response == 'y':
        for file_path in files:
            os.remove(file_path)
        print(f"✅ Deleted {len(files)} log files.")
    else:
        print("Cancelled.")

def main():
    """Main function."""
    if len(sys.argv) < 2:
        print("LLM Request Inspector")
        print("\nUsage:")
        print("  python llm_request_inspector.py watch    # Watch for new requests")
        print("  python llm_request_inspector.py list     # List recent requests")
        print("  python llm_request_inspector.py test     # Test context building")
        print("  python llm_request_inspector.py clean    # Clean log files")
        return
    
    command = sys.argv[1]
    
    if command == 'watch':
        watch_requests()
    elif command == 'list':
        list_recent_requests()
    elif command == 'test':
        test_context_building()
    elif command == 'clean':
        clean_logs()
    else:
        print(f"Unknown command: {command}")

if __name__ == "__main__":
    main()