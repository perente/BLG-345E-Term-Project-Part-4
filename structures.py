from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
import os

# Representation of a CNF clause
@dataclass
class Clause:
    id: int # Clause ID (used for conflict reporting)
    literals: List[int] # positive = true, negative = false
    watched_indices: List[int] = None # Indices of watched literals
    
    def __post_init__(self):
        if self.watched_indices is None:
            # By default, watch the first two literals
            if len(self.literals) >= 2:
                self.watched_indices = [0, 1]
            elif len(self.literals) == 1:
                self.watched_indices = [0]
            else:
                self.watched_indices = []


class State:
    """
    Main data structure storing SAT solver state
    
    Attributes:
        clauses: List of Clause objects (the CNF formula)
        num_vars: Total number of variables in the formula
        assignments: assignments[i] = True / False / None for variable i
        levels: levels[i] = decision level where variable i was assigned
        trail: Stack of (var_id, decision_level) assignments
        last_status: Last status returned by BCP
        last_conflict_id: Conflict clause ID (if any)
        last_dl: Last decision level
    """
    
    def __init__(self, clauses: List[Clause], num_vars):
        self.clauses = clauses
        self.num_vars = num_vars
        
        # Variable assignments
        # None = unassigned, True = assigned true, False = assigned false
        self.assignments: List[Optional[bool]] = [None] * (num_vars + 1)
        
        # Decision level tracking for each variable
        self.levels: List[int] = [0] * (num_vars + 1)
        
        # Trail: chronological assignment record (var_id, decision_level)
        self.trail: List[Tuple[int, int]] = []
        
        # Track BCP result
        self.last_status: Optional[str] = None
        self.last_conflict_id: Optional[int] = None
        self.last_dl: Optional[int] = None

    # Assign a value to a variable and record it in trail
    def assign(self, var_id, value, dl):
        self.assignments[var_id] = value
        self.levels[var_id] = dl
        self.trail.append((var_id, dl))

    # Return assignments as a dictionary
    def get_assignments_dict(self) -> Dict[int, Optional[bool]]:
        return {i: self.assignments[i] for i in range(1, self.num_vars + 1)}

def pick_branching_variable(state: State, trace_logger=None, dl: int = 0) -> Optional[int]:
    """
    Select a decision variable using the MOM heuristic
    Polarity-based tie-breaking is applied
    """
    chosen_literal = mom_heuristic(state)
    
    # Log the selection to master_trace.txt
    if trace_logger is not None and chosen_literal is not None:
        trace_logger.log_pick_branching(chosen_literal, dl)
    
    return chosen_literal


def mom_heuristic(state: State) -> Optional[int]:
    """
    MOM (Maximum Occurrences in Minimum-sized Clauses) heuristic
    with polarity-based tie-breaking
    
    Algorithm:
    1) Find all unsatisfied clauses
    2) Find clauses with minimum number of unassigned literals among them
    3) Count literal occurrences in these minimum-sized clauses
    4. Return the literal with the highest occurrence count (including polarity)
    
    Prioritize variables that appear frequently in smallest clauses,
    to trigger unit propagation or early conflict detection.
    """
    
    # Find unsatisfied clauses
    unsatisfied_clauses = []
    for clause in state.clauses:
        if not is_clause_satisfied(clause, state):
            unsatisfied_clauses.append(clause)
    
    # If there are no unsatisfied clauses, no variable needs to be selected
    if not unsatisfied_clauses:
        return None
    
    # Find minimum size among unsatisfied clauses
    min_size = float('inf')
    min_clauses = []
    
    for clause in unsatisfied_clauses:
        unassigned_count = count_unassigned_literals(clause, state)
        
        if unassigned_count < min_size:
            min_size = unassigned_count
            min_clauses = [clause]
        elif unassigned_count == min_size:
            min_clauses.append(clause)
    
    # Count literal occurrences in minimum-sized clauses
    # Polarity-based counting - positive and negative literals are counted separately
    literal_counts: Dict[int, int] = {}
    
    for clause in min_clauses:
        for literal in clause.literals:
            var_id = abs(literal)
            
            # Count only unassigned ones
            if state.assignments[var_id] is None:
                if literal not in literal_counts:
                    literal_counts[literal] = 0
                literal_counts[literal] += 1
    
    # If no unassigned literals are found
    if not literal_counts:
        return None
    
    # Select the literal with the highest occurrence count
    best_literal = None
    best_score = -1
    
    for literal, count in literal_counts.items():
        # Tie-breaking:
        # Higher count wins
        # If equal, smaller absolute variable ID is chosen
        if count > best_score or (count == best_score and (best_literal is None or abs(literal) < abs(best_literal))):
            best_score = count
            best_literal = literal
    
    return best_literal

# Check whether a clause is satisfied under the current assignment
def is_clause_satisfied(clause: Clause, state: State):
    for literal in clause.literals:
        var_id = abs(literal)
        var_value = state.assignments[var_id]
        
        if var_value is None:
            continue
    
        if (literal > 0 and var_value is True) or (literal < 0 and var_value is False):
            return True
    
    return False

# Count the number of unassigned literals in a clause
def count_unassigned_literals(clause: Clause, state: State):
    count = 0
    for literal in clause.literals:
        var_id = abs(literal)
        if state.assignments[var_id] is None:
            count += 1
    return count

# Load the initial state file in Project #2 format
def load_initial_state(path: str) -> State:
    """
    Format:
    --- HEADER AND METADATA ---
    V: <num_vars>
    C: <num_clauses>
    
    --- VARIABLE ASSIGNMENTS ---
    1    | UNASSIGNED
    ...
    
    --- CLAUSE LIST ---
    C1    | [-1, 2, 3]    | [0, 1]
    ...
    """
    clauses = []
    num_vars = 0
    num_clauses_expected = 0
    assignments = {}
    
    section = None
    
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            
            # Skip empty lines
            if not line:
                continue
            
            # Detect section headers
            if line.startswith("---"):
                if "HEADER" in line or "METADATA" in line:
                    section = "HEADER"
                elif "VARIABLE ASSIGNMENTS" in line:
                    section = "VARS"
                elif "CLAUSE LIST" in line:
                    section = "CLAUSES"
                elif "2-WATCHED" in line:
                    section = "WATCH"  # This section is ignored
                continue
            
            # Parse based on current section
            if section == "HEADER":
                if line.startswith("V:"):
                    num_vars = int(line.split(":")[1].strip())
                elif line.startswith("C:"):
                    num_clauses_expected = int(line.split(":")[1].strip())
            
            elif section == "VARS":
                # Format: 1    | UNASSIGNED  veya  2    | TRUE
                if "|" in line:
                    parts = line.split("|")
                    try:
                        var_id = int(parts[0].strip())
                        val_str = parts[1].strip()
                        if val_str == "TRUE":
                            assignments[var_id] = True
                        elif val_str == "FALSE":
                            assignments[var_id] = False
                        # If UNASSIGNED remains as None
                    except ValueError:
                        pass
            
            elif section == "CLAUSES":
                # Format: C1    | [-1, 2, 3]    | [0, 1]
                if "|" in line:
                    parts = line.split("|")
                    if len(parts) >= 2:
                        # Load clause ID
                        cid_str = parts[0].strip()
                        if cid_str.startswith("C"):
                            cid = int(cid_str[1:])
                        else:
                            continue
                        
                        # Load literals: [-1, 2, 3]
                        lits_str = parts[1].strip()
                        lits_str = lits_str.strip("[]")
                        if lits_str:
                            lits = [int(x.strip()) for x in lits_str.split(",")]
                        else:
                            lits = []
                        
                        # Load watched indices if exist
                        watched = None
                        if len(parts) >= 3:
                            watch_str = parts[2].strip().strip("[]")
                            if watch_str:
                                watched = [int(x.strip()) for x in watch_str.split(",")]
                        
                        clauses.append(Clause(cid, lits, watched))
    
    # Create State
    state = State(clauses, num_vars)
    
    # Apply loaded assignments
    for var_id, val in assignments.items():
        if val is not None:
            state.assign(var_id, val, 0)
    
    return state

# Load a State from a DIMACS CNF file
def load_initial_cnf(path: str) -> State:
    clauses = []
    num_vars = 0
    clause_id = 1

    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            
            # Skip empty lines and comments
            if not line or line.startswith(("c", "#")):
                continue

            # Header: p cnf <num_vars> <num_clauses>
            if line.startswith("p"):
                parts = line.split()
                num_vars = int(parts[2])
                continue

            # Clause: literals followed by 0
            lits = []
            for tok in line.split():
                if tok == "0":
                    break
                lits.append(int(tok))
            
            if lits:
                clauses.append(Clause(clause_id, lits))
                clause_id += 1

    return State(clauses, num_vars)