import sys 

import structures               # Data & Heuristics
import io_manager               # I/O & Integration
import backtracker              # Backtracking

def dpll_solve(state):
    """
    Main function of Search Engine

    Parameters
    ----------
    state : object
        Data structure that holds all SAT status

    Returns
    -------
    bool
        True  -> SAT
        False -> UNSAT
    """
    dl_zero = 0
    result = dpll_solver(state, dl_zero)

    return result


def dpll_solver(state, decision_level):
    """
    Recursive DPLL function
    Parameters:
        state: The main data object holding variables and clauses.

        decision_level: Current depth in the decision tree.
                        DL = 0  : root level

    Return:
        True -> SAT 
        False -> UNSAT
    """

    # Calls project 3 to update state object
    status = io_manager.run_inference(state)       
    print(f"[DL {decision_level}] Inference Status: {status}")

    # Checking the status

    # The branch we have taken led to a conflict
    # Signals False to caller and caller function will undo the current level using backtracker.undo_level()
    if status == 'CONFLICT':
        return False

    # If all clauses are satisfied, then we found a model (an interpretation that makes the formula TRUE)
    if status == 'SAT':
        return True

    # If status is not equal to 'CONFLICT' or 'SAT'
    # 'CONTINUE' and we branch on a new variable

    # Getting the variable to check from Heuristic approach
    var_id = structures.pick_branching_variable(state) # pick_branching_variable() fonksiyonu -> 2.kişiden alınacak

    # If var_id is None, it means there are no variables left to try for satisfiability
    # Since there is no conflict so far, the current assignment satisfies all clauses
    if var_id is None:
        print(f"[DL {decision_level}] No unassigned variable left. Result: SAT")
        return True

    # We still have variables to try, we are going to new decision level
    next_dl = decision_level + 1

    # Try assigning TRUE value on variable at next decision level 
    print(f"[DL {decision_level}] Branching on variable {var_id} -> Try TRUE at DL {next_dl}")
    state.assign(var_id, True, next_dl) # state objesi -> 2.kişiden alınacak

    # Call 'dpll_solver()' recursively for TRUE value of new variable on next level
    if dpll_solver(state, next_dl):
        return True

    # TRUE branch failed, then backtrack this level
    print(f"[DL {decision_level}] Backtracking... Undoing level {next_dl}")
    backtracker.undo_level(state, next_dl) # undo_level() fonksiyonu -> 5.kişiden alınacak
    
    # Trying FALSE value on variable 
    print(f"[DL {decision_level}] Branching on Variable {var_id} -> Try FALSE at DL {next_dl}")
    state.assign(var_id, False, next_dl) # state objesi -> 2.kişiden alınacak

    # Call 'dpll_solver()' recursively for FALSE value of new variable on next level
    if dpll_solver(state, next_dl):
        return True

    # FALSE value is not SAT too, then backtrack again
    print(f"[DL {decision_level}] Both TRUE and FALSE branches failed. Backtracking level {next_dl}")
    backtracker.undo_level(state, next_dl)  # undo_level() fonksiyonu -> 5.kişiden alınacak

    # Caller will continue to backtrack since this branch is UNSAT (leads to a conflict)
    return False

# MAIN EXECUTION BLOCK

if __name__ == "__main__":
    print("--- SAT Solver Started ---")
    
    # Reset Master Trace file.
    try:
        io_manager.initialize_master_trace()
    except AttributeError:
        print("Warning: 'initialize_master_trace' not found!")

    # Read initial CNF file and generate the State
    try:
        initial_state = structures.load_initial_cnf("initial_cnf.txt")
        print(f"Problem Loaded: {initial_state.num_vars} variable loaded.")
    except FileNotFoundError:
        print("Error: 'initial_cnf.txt' not found!")
        sys.exit(1)
    
    # Start the engine
    result = dpll_solve(initial_state)
    
    # Print result
    if result:
        print("\n>>> RESULT: SATISFIABLE <<<")
        print("Final Assignments:", initial_state.assignments)
    else:
        print("\n>>> RESULT: UNSATISFIABLE <<<")

    
