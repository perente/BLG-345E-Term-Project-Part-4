import os
import sys

# Constants
BCP_INPUT = "bcp_input.txt"
BCP_OUTPUT = "bcp_output.txt"
INITIAL_CNF = "initial_cnf.txt"
TRACE_FILE = "execution_trace.txt"

class Clause:
    def __init__(self, cid, literals):
        self.id = cid
        self.literals = literals

class InferenceEngine:
    def __init__(self):
        self.num_vars = 0
        self.clauses = []
        self.assignments = {} # var_id -> bool
        self.dl = 0
        self.log = []
        self.conflict_id = None
        self.trigger_lit = 0
        self.trigger_dl = 0

    def load_cnf(self):
        if not os.path.exists(INITIAL_CNF):
            print(f"Error: {INITIAL_CNF} not found.")
            sys.exit(1)
        
        cid = 1
        with open(INITIAL_CNF, "r") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("c") or line.startswith("%") or line.startswith("0") or line == "":
                    continue
                
                if line.startswith("p"):
                    parts = line.split()
                    self.num_vars = int(parts[2])
                    continue
                
                # Parse clause
                lits = []
                for tok in line.split():
                    if tok == "0": break
                    lits.append(int(tok))
                
                if lits:
                    self.clauses.append(Clause(cid, lits))
                    cid += 1

    def load_trigger(self):
        if os.path.exists(BCP_INPUT):
            with open(BCP_INPUT, "r") as f:
                for line in f:
                    if "TRIGGER_LITERAL" in line:
                        self.trigger_lit = int(line.split(":")[1].strip())
                    if "DL" in line:
                        self.trigger_dl = int(line.split(":")[1].strip())
        self.dl = self.trigger_dl

    def reconstruct_state(self):
        # Reconstruct state from execution_trace.txt
        if not os.path.exists(TRACE_FILE):
            return

        with open(TRACE_FILE, "r") as f:
            for line in f:
                line = line.strip()
                # Parse DECIDE or ASSIGN lines to rebuild assignments
                # Formats: 
                # [DLx] DECIDE      L=y   |
                # [DLx] ASSIGN    L=y    | 
                # (Note: The stub produced "[DL1] ASSIGN L=-3", but io_manager might format it differently or we just need to parse what we write)
                # Let's match typical patterns.
                
                parts = line.split()
                lit = None
                
                # Look for L=... part
                for part in parts:
                    if part.startswith("L="):
                        try:
                            lit_str = part.split("=")[1]
                            # Clean potential trailing chars like |
                            lit = int(''.join(c for c in lit_str if c in "-0123456789"))
                        except:
                            pass
                        break
                
                if lit is not None:
                    if "DECIDE" in line or "ASSIGN" in line:
                        var = abs(lit)
                        val = (lit > 0)
                        self.assignments[var] = val

    def get_val(self, lit):
        var = abs(lit)
        if var not in self.assignments:
            return None
        val = self.assignments[var]
        return val if lit > 0 else not val

    def is_satisfied(self, clause):
        for lit in clause.literals:
            if self.get_val(lit) is True:
                return True
        return False

    def is_conflicting(self, clause):
        # All literals false
        for lit in clause.literals:
            if self.get_val(lit) is not False:
                return False
        return True

    def get_unit_literal(self, clause):
        # Returns (literal, True) if unit, else (None, False)
        unassigned = []
        for lit in clause.literals:
            val = self.get_val(lit)
            if val is True:
                return None # Satisfied
            if val is None:
                unassigned.append(lit)
        
        if len(unassigned) == 1:
            return unassigned[0]
        return None

    def run_bcp(self):
        queue = []
        
        # If trigger is a decision (non-zero), assign it
        if self.trigger_lit != 0:
            var = abs(self.trigger_lit)
            val = (self.trigger_lit > 0)
            
            # Check if already assigned (should generally not happen for DECIDE unless reconstructing)
            # For DECIDE trigger, it's the new assignment driving this BCP
            if var not in self.assignments:
                self.assignments[var] = val
                # Log happens in search engine for DECIDE, but we might want to log it if it's the trigger?
                # The stub logged: "[DL1] DECIDE L=2"
                # But typically search engine logs DECIDE. 
                # However, io_manager calls run_inference AFTER writing trigger.
                # If trigger is DECIDE, we assume it's already in trace? 
                # Actually io_manager.append_decision_to_master_trace is called BEFORE run_inference.
                # So we assume it's assigned. 
                # Wait, io_manager writes trigger THEN calls run_inference.
                pass
            
            queue.append(self.trigger_lit)

            # If trigger is DECIDE, we confirm it's logged in reconstruction?
            # io_manager:
            #   append_decision_to_master_trace(var_id, next_dl)
            #   state.assign(var_id, True, next_dl) 
            #   run_inference(...)
            # So trace has the DECIDE line. reconstruct_state will pick it up.
            
            # However, if this is an implied trigger (e.g. from previous level?), 
            # usually BCP starts with the queue containing the decision literal.
            
        else:
            # DL0 case or no trigger
            pass

        # If DL=0, we should check for initial unit clauses even without trigger
        if self.dl == 0 and self.trigger_lit == 0:
            # Add all items to queue check? Or just loop clauses?
            # Standard: loop clauses to find initial units
            pass

        # Main propagation loop
        # We need to iterate until fixpoint or conflict
        
        # Optimization: We can just loop repeatedly over clauses finding units until no new units or conflict
        # Since this is a simple python implementation, O(N^2) or similar is acceptable for samples.
        
        while True:
            progress = False
            
            # Check all clauses
            for clause in self.clauses:
                if self.is_satisfied(clause):
                    # Optional: Log satisfied? Stub did: [DL1] SATISFIED C1
                    # To avoid excessive logs, maybe only log once per step? 
                    # But verifying satisfied clauses every time is expensive for logs.
                    # We'll skip logging "SATISFIED" for every clause every loop to avoid spam, 
                    # unless it just became satisfied?
                    continue

                if self.is_conflicting(clause):
                    self.conflict_id = clause.id
                    self.log.append(f"[DL{self.dl}] CONFLICT Violation: C{clause.id}")
                    return "CONFLICT"

                unit_lit = self.get_unit_literal(clause)
                if unit_lit is not None:
                    # Found unit
                    var = abs(unit_lit)
                    val = (unit_lit > 0)
                    
                    if var not in self.assignments:
                        self.assignments[var] = val
                        progress = True
                        
                        self.log.append(f"[DL{self.dl}] UNIT      L={unit_lit}    | C{clause.id}")
                        self.log.append(f"[DL{self.dl}] ASSIGN    L={unit_lit}    |")
                        # Add to queue logic if we were using watched literals
            
            if not progress:
                break
        
        return "SAT" if self.all_clauses_satisfied() else "CONTINUE"  
        # Note: If no conflict, we return SAT if all satisfied, else CONTINUE (meaning stable but partial)
        # But wait, the stub/io_manager expects: SAT, CONFLICT, or CONTINUE?
        # dpll_solver check:
        # if status == 'SAT': return True
        # if input var_id is None (no unassigned) -> SAT
        
        # If we have unassigned variables but no conflict -> CONTINUE
    
    def all_clauses_satisfied(self):
        for clause in self.clauses:
            if not self.is_satisfied(clause):
                return False
        return True

    def write_result(self, status):
        # We need to output all variables, including unassigned ones
        # Project validation requires STATUS: SAT/UNSAT/CONFLICT
        # But for intermediate BCP, "SAT" usually means "All clauses satisfied" (Solution found)
        # "CONFLICT" means conflict found.
        # "CONTINUE" means consistent so far but not complete.
        
        if status == "SAT":
            # Double check if really all variables assigned?
            # DPLL logic: "If status == 'SAT': return True" (Solution found)
            pass
            
        with open(BCP_OUTPUT, "w") as f:
            f.write("--- STATUS ---\n")
            f.write(f"STATUS: {status}\n")
            f.write(f"DL: {self.dl}\n")
            f.write(f"CONFLICT_ID: {self.conflict_id}\n")
            
            f.write("--- BCP EXECUTION LOG ---\n")
            for line in self.log:
                f.write(line + "\n")
            
            f.write("--- CURRENT VARIABLE STATE ---\n")
            for i in range(1, self.num_vars + 1):
                if i in self.assignments:
                    val_str = "TRUE" if self.assignments[i] else "FALSE"
                else:
                    val_str = "UNASSIGNED"
                f.write(f"{i} | {val_str}\n")


def main():
    engine = InferenceEngine()
    engine.load_cnf()
    engine.load_trigger()
    engine.reconstruct_state()
    
    status = engine.run_bcp()
    
    # Check if complete (SAT typically implies all variables assigned and clauses satisfied)
    # If run_bcp returns SAT, it means valid full model or empty clause set?
    # run_bcp above returns SAT if all clauses satisfied.
    # If not all satisfied (partial assignment) but no conflict -> CONTINUE
    if status == "SAT" and not engine.all_clauses_satisfied():
        status = "CONTINUE"
        
    engine.write_result(status)

if __name__ == "__main__":
    main()