from dataclasses import dataclass
from typing import List, Optional

@dataclass
class Clause:
    """
    CNF clause representation
    - id: Clause ID for tracking
    - literals: List of integers representing literals (positive for true, negative for false)
    """
    id: int
    literals: List[int]

class State:
    """
    - clauses: CNF formülü
    - num_vars: Number of variables
    - assignments[i]: Value of ith variable (True/False/None)
    - levels[i]: Decision level which i is assigned
    - trail: Assignment logs
    """
    def __init__(self, clauses, num_vars):
        self.clauses = clauses
        self.num_vars = num_vars

        # Initially assign None to all variables in range 1-num_vars
        self.assignments = [None] * (num_vars + 1)
        # At which decision level a variable assigned with value, initially zero
        self.levels = [0] * (num_vars + 1)

        # All assignment logs will be held there in format: (var_id, decision_level)
        self.trail = []
        self.last_status = None
        self.last_conflict_id = None
        self.last_dl = None

        # For P3/P5 (arbitrary)
        # self.trace = []

    def assign(self, var_id, value, dl):
        """ 
        Assign a value to related variable and record it in trail
        """
        # Value assignment
        self.assignments[var_id] = value
        # The decision level when the value assigned
        self.levels[var_id] = dl
        # Add to logs
        self.trail.append((var_id, dl))

# Entry point for the decision heuristic
def pick_branching_variable(state):
    
    return mom_heuristic(state)

def mom_heuristic(state):
    """
    MOM implementation.
    
    Fundamental Algorithm:
    1. Find all unsatisfied clauses
    2. Find unsatisfied clauses with minimum size(using unassigned literal count)
    3. Count literal occurrences in minimum-sized clauses
    4. Return the variable with maximum occurrence
    
    Returns:
    --------
    int/None: Either returns selected variable ID or None if no unassigned variable exists
    """
    
    # Find unsatisfied clauses
    unsatisfied_clauses = []
    for clause in state.clauses:
        if not is_clause_satisfied(clause, state):
            unsatisfied_clauses.append(clause)
    
    # If all clauses are satisfied 
    if not unsatisfied_clauses:
        return None
    
    # Find unsatisfied clauses with minimum size (using unassigned literal count)
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
    literal_counts = {}
    
    for clause in min_clauses:
        for literal in clause.literals:
            var_id = abs(literal)
            
            # Only count if variable is unassigned
            if state.assignments[var_id] is None:
                if literal not in literal_counts:
                    literal_counts[literal] = 0
                literal_counts[literal] += 1
    
    # If no unassigned literals
    if not literal_counts:
        return None
    
    # Select variable with maximum occurrence
    # Prefer polarity that appears more frequently when tied
    best_var = None
    best_score = -1
    best_polarity_score = -1
    
    # Follow which variables are already processed
    seen_vars = set()
    
    for literal in literal_counts:
        var_id = abs(literal)
        
        if var_id in seen_vars:
            continue
        seen_vars.add(var_id)
        
        # Count occurrences of both polarities
        pos_count = literal_counts.get(var_id, 0)
        neg_count = literal_counts.get(-var_id, 0)
        
        # Total MOM score
        total_score = pos_count + neg_count
        
        # Prefer the polarity which appears more
        max_polarity = max(pos_count, neg_count)
        
        # Select variable with highest total score
        # Select the one with higher polarity count if it is tied
        if (total_score > best_score or 
            (total_score == best_score and max_polarity > best_polarity_score)):
            best_score = total_score
            best_polarity_score = max_polarity
            best_var = var_id
    
    return best_var


def is_clause_satisfied(clause, state):
    """
    Check if a clause is satisfied under current assignment
    A clause is satisfied if at least one of its literals is TRUE
    
    Parameters:
    -----------
    clause : Clause to check   
    state : Current state with variable assignments
         
    Returns:
    --------
    bool: True if clause satisfied, False otherwise
    """
    for literal in clause.literals:
        var_id = abs(literal)

        var_value = state.assignments[var_id]
        
        # The literal can not satisfy clause if not assigned
        if var_value is None:
            continue
        
        # Check if current assignment matches literal's polarity
        if (literal > 0 and var_value is True) or (literal < 0 and var_value is False):
             return True
    
    return False


def count_unassigned_literals(clause, state):
    """
    Count unassigned literals
    
    Parameters:
    -----------
    clause : Clause to count
    state : Current state with variable assignments
    
    Returns:
    --------
    int: Number of unassigned literals
    """
    count = 0
    for literal in clause.literals:
        var_id = abs(literal)
        if state.assignments[var_id] is None:
            count += 1
    return count

# Parse DIMACS CNF file and return State
def load_initial_cnf(path: str) -> State:
    clauses = []
    num_vars = None
    num_clauses = None
    cid = 1

    with open(path, "r", encoding ="utf-8") as f:
        for line in f:
            # Remove leading or trailing whitespace
            line = line.strip() 
            if not line or line.startswith(("c", "#")): # Skip comments
                continue

            # # Parse the header: p cnf x y
            if line.startswith("p"): 
                parts = line.split()
                num_vars = int(parts[2]) # number of variables (x)
                num_clauses = int(parts[3]) # number of clauses (y)
                continue

            # Parse clause and stop at clause terminator used in DIMACS
            lits = [] 
            for tok in line.split(): 
                # Clause terminator
                if tok == "0":
                    break
                lits.append(int(tok))
            
            clauses.append(Clause(cid, lits))
            cid += 1

    return State(clauses, num_vars)