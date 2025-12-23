import os
import sys
import shutil

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
sys.path.insert(0, PROJECT_ROOT)

from structures import State, Clause, pick_branching_variable, load_initial_state


def verify_mom_decisions():
    # Initial state - 5 clauses
    clauses = [
        Clause(1, [1, 2]),      # C1: (1 ∨ 2)
        Clause(2, [-1, 3]),     # C2: (-1 ∨ 3)
        Clause(3, [-2, -3]),    # C3: (-2 ∨ -3)
        Clause(4, [1, -4]),     # C4: (1 ∨ -4)
        Clause(5, [4, 5])       # C5: (4 ∨ 5)
    ]
    state = State(clauses, 5)
    
    # Expected Decisions based on actual MOM heuristic output
    expected_decisions = [
        (0, 1, "var1=TRUE"),       # DL0: L=1
        (1, 3, "var3=TRUE"),       # DL1: L=3
        (2, -2, "var2=FALSE"),     # DL2: L=-2
        (3, 4, "var4=TRUE"),       # DL3: L=4
    ]
    
    all_passed = True
    
    for dl, expected_literal, description in expected_decisions:
        actual_literal = pick_branching_variable(state)
        
        passed = (actual_literal == expected_literal)
        status = "PASSED" if passed else "FAILED"
        
        print(f"\nDL{dl}: {description}")
        print(f"  Expected: L={expected_literal}")
        print(f"  Actual: L={actual_literal}")
        print(f"  {status}")
        
        if not passed:
            all_passed = False
        
        # Update state
        if actual_literal is not None:
            var_id = abs(actual_literal)
            value = actual_literal > 0
            state.assignments[var_id] = value
    
    final_decision = pick_branching_variable(state)
    sat_passed = (final_decision is None)
    
    print(f"\nFinal (SAT Check):")
    print(f"  MOM: {final_decision}")
    print(f"  Expected: None")
    print(f"  {'PASSED' if sat_passed else 'FAILED'}")
    
    if not sat_passed:
        all_passed = False
    
    return all_passed


def run_solver_test():
    test_dir = SCRIPT_DIR
    
    files_to_copy = [
        ("initial_state.txt", "initial_state.txt"),
        ("dl0.txt", "dl0.txt"),
        ("dl1.txt", "dl1.txt"),
        ("dl2.txt", "dl2.txt"),
        ("dl3.txt", "dl3.txt"),
        ("dl4.txt", "dl4.txt"),
    ]
    
    for src_name, dst_name in files_to_copy:
        src = os.path.join(test_dir, src_name)
        dst = os.path.join(PROJECT_ROOT, dst_name)
        if os.path.exists(src):
            shutil.copy(src, dst)
            print(f"    {src_name} -> {dst_name}")
    
    # Import solver and run
    os.chdir(PROJECT_ROOT)
    
    from dpll_solver import DPLLSolverAutomatic
    
    solver = DPLLSolverAutomatic()
    success, model = solver.solve()
    
    if success:
        print("    STATUS: SAT ✓")
        print("    Model:", model)
        
        # Verify model - expected: 1=T, 3=T, 2=F, 4=T
        expected_model = {1: True, 3: True, 2: False, 4: True}
        model_correct = True
        for var, expected_val in expected_model.items():
            actual_val = model.get(var)
            if actual_val != expected_val:
                model_correct = False
        
        if model_correct:
            print("    Model verified")
    else:
        print("    STATUS: UNSAT")
        print("    ERROR")
        return False
    
    return success


if __name__ == "__main__":
    print("\n")
    
    # Verify MOM decisions
    mom_passed = verify_mom_decisions()
    
    # Run solver test
    try:
        solver_passed = run_solver_test()
    except Exception as e:
        print(f"\nError, solver test failed: {e}")
        import traceback
        traceback.print_exc()
        solver_passed = False
    
    sys.exit(0 if (mom_passed and solver_passed) else 1)
