import os

# Remove existing trace file if it exists
trace_file = os.path.join(os.path.dirname(__file__), "master_trace.txt")
if os.path.exists(trace_file):
    os.remove(trace_file)
    print(f"✓ Existing trace file removed: {trace_file}")

# Run the solver
print("\n--- Running DPLL Solver (auto mode) ---\n")
os.system("python dpll_solver.py --auto")

# Check trace file
print("\n--- master_trace.txt Content ---\n")
if os.path.exists(trace_file):
    with open(trace_file, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Look for PICK BRANCHING VARIABLE sections
    if "--- PICK BRANCHING VARIABLE ---" in content:
        print("TEST PASSED: pick_branching_variable selections were written to the trace!\n")
        
        # Display relevant trace lines
        lines = content.split("\n")
        for line in lines:
            if (
                "PICK BRANCHING VARIABLE" in line
                or "CHOSEN_LITERAL" in line
                or "DECISION_LEVEL" in line
            ):
                print(f"  {line}")
    else:
        print("TEST FAILED: pick_branching_variable selections not found in the trace!")
else:
    print(f"Trace file was not created: {trace_file}")
