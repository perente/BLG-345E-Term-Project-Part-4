import os
import sys
import shutil

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
sys.path.insert(0, PROJECT_ROOT)

from structures import State, Clause, pick_branching_variable


def verify_mom_decisions():
    clauses = [
        Clause(1, [-1, -2, 3]),   # C1
        Clause(2, [-1, 2, 4]),    # C2
        Clause(3, [-3, -4])       # C3
    ]
    state = State(clauses, 4)
    
    expected_decisions = [
        (0, -3, "var3=FALSE"),   # DL0: L=-3
        (1, -1, "var1=FALSE"),   # DL1: L=-1
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
        
        if actual_literal is not None:
            var_id = abs(actual_literal)
            value = actual_literal > 0
            state.assignments[var_id] = value
    
    # SAT check
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
    files_to_copy = ["initial_state.txt", "dl0.txt", "dl1.txt", "dl2.txt"]
    
    for fname in files_to_copy:
        src = os.path.join(SCRIPT_DIR, fname)
        dst = os.path.join(PROJECT_ROOT, fname)
        if os.path.exists(src):
            shutil.copy(src, dst)
            print(f"    {fname}")
    
    os.chdir(PROJECT_ROOT)
    
    from dpll_solver import DPLLSolverAutomatic
    
    solver = DPLLSolverAutomatic()
    success, model = solver.solve()
    
    if success:
        print("    STATUS: SAT")
        print("    Model:", model)
        
        expected = {1: False, 3: False}
        correct = all(model.get(v) == expected[v] for v in expected)
        
        if correct:
            print("    Model verified")
    else:
        print("    STATUS: UNSAT")
        print("    ERROR")
        return False
    
    return success


if __name__ == "__main__":
    print("\n")
    
    mom_passed = verify_mom_decisions()
    
    try:
        solver_passed = run_solver_test()
    except Exception as e:
        print(f"\nError, solver test failed: {e}")
        import traceback
        traceback.print_exc()
        solver_passed = False
    
    sys.exit(0 if (mom_passed and solver_passed) else 1)
