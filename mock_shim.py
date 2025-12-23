"""
mock_shim.py - Mock Inference Engine for Testing

This script simulates the Inference Engine (Project #3) for testing purposes.
It reads the trigger file, determines the requested decision level,
and copies the appropriate pre-generated response file to bcp_output.txt.

Usage:
    python mock_shim.py

The mock reads bcp_input.txt to determine the decision level,
then copies the corresponding dl<N>.txt file to bcp_output.txt.

All files are read/written in the current working directory.
"""

import os
import shutil
import sys

# Define paths - all in current directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

TRIGGER_FILE = os.path.join(BASE_DIR, "bcp_input.txt")  # Input from P4
OUTPUT_FILE = os.path.join(BASE_DIR, "bcp_output.txt")  # Output for P4


def main():
    """
    Main function for mock inference engine.
    
    1. Read trigger file to determine requested decision level
    2. Find corresponding pre-made response file (dl<N>.txt)
    3. Copy it to bcp_output.txt
    """
    target_dl = 0
    trigger_literal = 0
    
    # Step 1: Parse trigger file to get decision level
    if os.path.exists(TRIGGER_FILE):
        try:
            with open(TRIGGER_FILE, "r", encoding="utf-8") as f:
                content = f.read()
                for line in content.splitlines():
                    line = line.strip()
                    if line.startswith("DL:"):
                        target_dl = int(line.split(":")[1].strip())
                    elif line.startswith("TRIGGER_LITERAL:"):
                        trigger_literal = int(line.split(":")[1].strip())
        except Exception as e:
            print(f"[Mock Shim] Error reading trigger: {e}")
            target_dl = 0
    else:
        # No trigger file means initial state (DL 0)
        print("[Mock Shim] No trigger file found, assuming DL 0")
        target_dl = 0
    
    print(f"[Mock Shim] Requested DL={target_dl}, Literal={trigger_literal}")
    
    # Step 2: Find the source file for this decision level
    # Try different naming patterns in current directory
    source_patterns = [
        f"dl{target_dl}.txt",           # dl0.txt, dl1.txt, ...
        f"dl{target_dl}_4.txt",         # dl0_4.txt, dl1_4.txt, ... (P4 format)
        f"bcp_out_dl{target_dl}.txt",   # Alternative naming
    ]
    
    source_path = None
    for pattern in source_patterns:
        candidate = os.path.join(BASE_DIR, pattern)
        if os.path.exists(candidate):
            source_path = candidate
            break
    
    # Step 3: Copy source to output file
    if source_path:
        print(f"[Mock Shim] Copying {os.path.basename(source_path)} -> bcp_output.txt")
        shutil.copy(source_path, OUTPUT_FILE)
    else:
        # No matching file found - create a generic CONFLICT response
        print(f"[Mock Shim] Warning: No response file found for DL {target_dl}")
        print(f"[Mock Shim] Searched patterns: {source_patterns}")
        print(f"[Mock Shim] Creating default CONFLICT response")
        
        # Create a generic conflict response
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write("--- STATUS ---\n")
            f.write("STATUS: CONFLICT\n")
            f.write(f"DL: {target_dl}\n")
            f.write("CONFLICT_ID: None\n")
            f.write("\n--- BCP EXECUTION LOG ---\n")
            f.write(f"[DL{target_dl}] CONFLICT | No response file\n")
            f.write("\n--- CURRENT VARIABLE STATE ---\n")


if __name__ == "__main__":
    main()
