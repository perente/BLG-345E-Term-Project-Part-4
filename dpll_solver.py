import sys
import os

from structures import State, Clause, load_initial_state, load_initial_cnf, pick_branching_variable
from io_manager import (
    IOManager, TraceLogger,STATUS_SAT, STATUS_UNSAT, STATUS_CONFLICT,BCP_OUTPUT_FILE
)
import backtracker


class DPLLSolver:
    """
    DPLL SAT Solver 
    
    1) Read BCP output produced by Inference Engine
    2) Check the status, if status:
       - SAT: model found, return success
       - CONFLICT/UNSAT: return failure, trigger backtracking
       - CONTINUE: Choose variable to branch
    3) Use MOM heuristic for decision 
    4) Try both polarities recursively
    """
    
    # Initialize the DPLL solver
    def __init__(self, initial_state_path: str = None):
        self.io = IOManager()
        self.logger = TraceLogger()
        
        # Load initial state from the given path or default
        if initial_state_path is None:
            initial_state_path = self.io.get_initial_state_path()
        
        # Load file depending on its extension
        if initial_state_path.endswith(".cnf"):
            self.state = load_initial_cnf(initial_state_path)
        else:
            self.state = load_initial_state(initial_state_path)
        
        self.initial_state_path = initial_state_path
        
        print(f"Initial state loaded: {initial_state_path}")
        print(f"Variables: {self.state.num_vars}, Clauses: {len(self.state.clauses)}")
    
    def solve(self):
        # Start at decision level 0
        # Read BCP output for initial unit propagation
        
        result, model = self._dpll_recursive(dl=0)
        
        return result, model
    
    # Main recursive DPLL function
    def _dpll_recursive(self, dl: int):
        # Read BCP output
        try:
            result = self.io.read_bcp_output()
        except FileNotFoundError as e:
            print(f"[DL {dl}] HATA: {e}")
            return False, None
        
        # Save output from P3 to master trace
        self.logger.append_full_output(result.full_log, dl)
        
        status = result.status
        
        print(f"\n[DL {dl}] Status: {status}")
        if result.assignments:
            print(f"[DL {dl}] Assignments: {result.assignments}")
        if result.unassigned_vars:
            print(f"[DL {dl}] Unassigned: {result.unassigned_vars}")
        
        # Check the status
        if status == STATUS_SAT:
            print(f"[DL {dl}] *** SATISFIABLE ***")
            model = {var: val for var, val in result.assignments.items()}
            return True, model
        
        if status in (STATUS_UNSAT, STATUS_CONFLICT):
            print(f"[DL {dl}] Conflict detected, do backtrack")
            return False, None
        
        # IF status CONTINUE - Make decision
        for var in result.unassigned_vars:
            self.state.assignments[var] = None
        for var, val in result.assignments.items():
            self.state.assignments[var] = val
        
        # Choose literal using MOM
        chosen_literal = pick_branching_variable(self.state, self.logger, dl)
        
        if chosen_literal is None:
            # No unassigned variable left
            print(f"[DL {dl}] All variables assigned - SAT")
            model = {var: val for var, val in result.assignments.items()}
            return True, model
        
        # Recursion - try both polarities
        next_dl = dl + 1
        chosen_var = abs(chosen_literal)
        # positive literal -> True, negative literal -> False
        chosen_value = chosen_literal > 0  
        
        # Heuristic-chosen polarity
        print(f"[DL {dl}] Branch: variable {chosen_var} -> "
              f"{'TRUE' if chosen_value else 'FALSE'} (L={chosen_literal}) DL {next_dl}'de")
        
        # Update state and write trigger
        self.state.assign(chosen_var, chosen_value, next_dl)
        self.io.write_trigger(chosen_literal, next_dl)

        
        # Recurse
        success, model = self._dpll_recursive(next_dl)
        if success:
            return True, model
        
        # Branch failed, do backtrack
        print(f"[DL {dl}] Branch failed - Backtracking from DL {next_dl}")
        backtracker.undo_level(self.state, next_dl)
        self.logger.log_backtrack(next_dl)
        
        # New branch with opposite polarity
        negated_literal = -chosen_literal
        negated_value = not chosen_value
        
        print(f"[DL {dl}] Branch: variable {chosen_var} -> "
              f"{'TRUE' if negated_value else 'FALSE'} (L={negated_literal}) at DL {next_dl}")
        
        # Update state and write trigger
        self.state.assign(chosen_var, negated_value, next_dl)
        self.io.write_trigger(negated_literal, next_dl)
        
        # Recurse
        success, model = self._dpll_recursive(next_dl)
        if success:
            return True, model
        
        # Both branches failed, backtrack further
        print(f"[DL {dl}] Both branches failed - Backtracking")
        backtracker.undo_level(self.state, next_dl)
        
        return False, None


class DPLLSolverAutomatic(DPLLSolver):
    """
    Automatic-mode DPLL solver
    
    Simulates P3 by using mock files
    """
    
    def __init__(self, initial_state_path: str = None):
        super().__init__(initial_state_path)
        self.decision_count = 0
    
    def _copy_mock_response(self, dl: int):
        import shutil
        
        base_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Try different file namings
        patterns = [
            f"dl{dl}.txt",
            f"dl{dl}_response.txt",
            f"bcp_output_dl{dl}.txt",
        ]
        
        for pattern in patterns:
            src = os.path.join(base_dir, pattern)
            if os.path.exists(src):
                shutil.copy(src, BCP_OUTPUT_FILE)
                return True
        
        return False
    
    def _dpll_recursive(self, dl: int):
        """
        Otomatik mod icin recursive DPLL.
        Mock dosyalar kullanir.
        """
        # Copy mock response 
        self._copy_mock_response(dl)
        
        # Read BCP output
        try:
            result = self.io.read_bcp_output()
        except FileNotFoundError as e:
            print(f"[DL {dl}] HATA: {e}")
            return False, None
        
        # Store full output from P3 into the master trace
        self.logger.append_full_output(result.full_log, dl)
        
        status = result.status
        
        print(f"\n[DL {dl}] Status: {status}")
        
        # Base cases
        if status == STATUS_SAT:
            print(f"[DL {dl}] *** SATISFIABLE ***")
            model = {var: val for var, val in result.assignments.items()}
            return True, model
        
        if status in (STATUS_UNSAT, STATUS_CONFLICT):
            print(f"[DL {dl}] Conflict - Backtracking")
            return False, None
        
        # Update state for heuristic
        for var in result.unassigned_vars:
            self.state.assignments[var] = None
        for var, val in result.assignments.items():
            self.state.assignments[var] = val
        
        # Pick literal via MOM heuristic
        chosen_literal = pick_branching_variable(self.state, self.logger, dl)
        
        if chosen_literal is None:
            print(f"[DL {dl}] All variables assigned - SAT")
            model = {var: val for var, val in result.assignments.items()}
            return True, model
        
        # Branching
        next_dl = dl + 1
        chosen_var = abs(chosen_literal)
        chosen_value = chosen_literal > 0
        
        print(f"[DL {dl}] Branching: var {chosen_var} = {'T' if chosen_value else 'F'} (L={chosen_literal})")
        
        # Log decision
        self.logger.log_decision(chosen_literal, next_dl)
        
        self.state.assign(chosen_var, chosen_value, next_dl)
        self.io.write_trigger(chosen_literal, next_dl)
        
        # Recurse
        success, model = self._dpll_recursive(next_dl)
        if success:
            return True, model
        
        # Backtrack and try opposite polarity
        print(f"[DL {dl}] Backtracking from DL {next_dl}")
        backtracker.undo_level(self.state, next_dl)
        self.logger.log_backtrack(next_dl)
        
        negated_literal = -chosen_literal
        negated_value = not chosen_value
        
        print(f"[DL {dl}] Trying opposite: var {chosen_var} = {'T' if negated_value else 'F'} (L={negated_literal})")
        
        self.logger.log_decision(negated_literal, next_dl)
        
        self.state.assign(chosen_var, negated_value, next_dl)
        self.io.write_trigger(negated_literal, next_dl)
        
        success, model = self._dpll_recursive(next_dl)
        if success:
            return True, model
        
        backtracker.undo_level(self.state, next_dl)
        return False, None

def main():
    initial_state_path = None
    auto_mode = False
    args = sys.argv[1:]
    
    i = 0
    while i < len(args):
        if args[i] == "--initial" and i + 1 < len(args):
            initial_state_path = args[i + 1]
            i += 2
        elif args[i] == "--auto":
            auto_mode = True
            i += 1
        else:
            i += 1
    
    # Start solver
    try:
        if auto_mode:
            print("Automatic mode - mock files will be used")
            solver = DPLLSolverAutomatic(initial_state_path)
        else:
            print("Interactive mode - waiting for P3 at each step")
            solver = DPLLSolver(initial_state_path)
        
        success, model = solver.solve()
        
        # Print final result
        if success:
            print(">>> RESULT: SATISFIABLE <<<")
            print("\nFinal Assignment:")
            if model:
                for var in sorted(model.keys()):
                    val = model[var]
                    print(f"  Variable {var}: {'TRUE' if val else 'FALSE'}")
        else:
            print(">>> RESULT: UNSATISFIABLE <<<")
        
        # Write final model
        solver.io.write_final_model(
            model if model else {},
            solver.state.num_vars,
            success
        )
        
        # Trace output
        print(f"\nMaster Trace: {solver.logger.get_trace_path()}")
        print("\n--- MASTER TRACE CONTENT ---")
        print(solver.logger.read_trace())
        
    except FileNotFoundError as e:
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
