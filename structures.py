from dataclasses import dataclass
from typing import List, Optional

@dataclass
class Clause:
    """
    CNF clause representation.
    - id: Clause ID for tracking
    - literals: List of integers representing literals (positive for true, negative for false)
    """
    id: int
    literals: List[int]

class State:
    """

    KESIN DEGIL STATE ICINE DEFINE EDECEGIMIZ SEYLERE GORE DEGISECEK BURA 

    Global SAT durumu.
    Project 4 açısından:
      - clauses: CNF formülü
      - num_vars: değişken sayısı
      - assignments[i]: i. değişkenin değeri (True/False/None)
      - levels[i]: i. değişken hangi decision level'da atanmış
      - trail: atamaların sırası (backtrack için)
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

        # İleride P3/P5 için istersen:
        # self.trace = []

    def assign(self, var_id, value, dl):
        """ 
        Assign a value to the related variable at the given decision level
        """
        # Value assignment
        self.assignments[var_id] = value
        # The decision level when the value assigned
        self.levels[var_id] = dl
        # Add to logs
        self.trail.append((var_id, dl))


def pick_branching_variable(state):
    """
    MOM (Maximum Occurrences in Minimum-Sized Clauses) Heuristic
    
    Selects the next variable to branch on using MOM heuristic:
    1. Find all unsatisfied clauses
    2. Among those, find the ones with minimum size (unassigned literals)
    3. Count literal occurrences in those minimum clauses
    4. Select the variable that appears most frequently
    5. Return variable with preferred polarity
    
    Parameters:
    -----------
    state : State
        Current SAT solver state with clauses and assignments
    
    Returns:
    --------
    int or None: Variable ID to branch on (1 to num_vars), or None if all assigned
    """
    
    # Geçici basit heuristic - 1..num_vars arası ilk UNASSIGNED değişkeni seç
    # for var in range(1, state.num_vars + 1):
    #     if state.assignments[var] is None:
    #         return var
    # return None
    
    # ACTIVE HEURISTIC: MOM
    return mom_heuristic(state)

def mom_heuristic(state):
    """
    MOM (Maximum Occurrences in Minimum-Sized Clauses) implementation.
    
    Core Algorithm:
    1. Filter unsatisfied clauses
    2. Find minimum-sized unsatisfied clauses (by unassigned literal count)
    3. Count literal occurrences in those clauses
    4. Return the variable with maximum occurrence
    
    Returns:
    --------
    int or None: Selected variable ID, or None if no unassigned variable exists
    """
    
    # Step 1: Find unsatisfied clauses
    unsatisfied_clauses = []
    for clause in state.clauses:
        if not is_clause_satisfied(clause, state):
            unsatisfied_clauses.append(clause)
    
    # If all clauses satisfied (SAT)
    if not unsatisfied_clauses:
        return None
    
    # Step 2: Find minimum-sized clauses (by unassigned literal count)
    min_size = float('inf')
    min_clauses = []
    
    for clause in unsatisfied_clauses:
        unassigned_count = count_unassigned_literals(clause, state)
        
        if unassigned_count < min_size:
            min_size = unassigned_count
            min_clauses = [clause]
        elif unassigned_count == min_size:
            min_clauses.append(clause)
    
    # Step 3: Count literal occurrences in minimum clauses
    literal_counts = {}
    
    for clause in min_clauses:
        for literal in clause.literals:
            var_id = abs(literal)
            
            # Only count if variable is unassigned
            if state.assignments[var_id] is None:
                if literal not in literal_counts:
                    literal_counts[literal] = 0
                literal_counts[literal] += 1
    
    # If no unassigned literals (all variables assigned)
    if not literal_counts:
        return None
    
    # Step 4: Select variable with maximum occurrence
    # MOM heuristic: prioritize variables appearing most in minimum clauses
    # When tied, prefer the polarity that appears more frequently
    best_var = None
    best_score = -1
    best_polarity_score = -1
    
    # Track which variables we've already processed
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
        
        # For tie-breaking: prefer whichever polarity appears more
        max_polarity = max(pos_count, neg_count)
        
        # Select variable with highest total score
        # If tied, select the one with higher single polarity count
        if (total_score > best_score or 
            (total_score == best_score and max_polarity > best_polarity_score)):
            best_score = total_score
            best_polarity_score = max_polarity
            best_var = var_id
    
    return best_var


def is_clause_satisfied(clause, state):
    """
    Check if a clause is satisfied under current assignment.
    
    A clause is satisfied if at least one of its literals evaluates to TRUE.
    
    Parameters:
    -----------
    clause : Clause
        The clause to check
    state : State
        Current state with variable assignments
    
    Returns:
    --------
    bool: True if clause is satisfied, False otherwise
    """
    for literal in clause.literals:
        var_id = abs(literal)
        is_positive = (literal > 0)
        
        var_value = state.assignments[var_id]
        
        # If unassigned, this literal can't satisfy the clause
        if var_value is None:
            continue
        
        # Calculate literal value
        literal_value = var_value if is_positive else not var_value
        
        # If any literal is TRUE, clause is satisfied
        if literal_value:
            return True
    
    return False


def count_unassigned_literals(clause, state):
    """
    Count how many literals in a clause have unassigned variables.
    
    Parameters:
    -----------
    clause : Clause
        The clause to count
    state : State
        Current state with variable assignments
    
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

def load_initial_cnf(path: str) -> State:
    """
    DIMACS CNF parser - input_nf_4.cnf formatına göre okur ve State objesi döner.
    """

    clauses = []
    num_vars = None
    num_clauses = None
    cid = 1

    with open(path, "r", encoding = "utf-8") as f:
        for line in f:
            line = line.strip() # remove leading/trailing whitespace
            if not line or line.startswith(("c", "#")): # skip comments
                continue

            if line.startswith("p"): # problem line (e.g., "p cnf x y")
                parts = line.split()
                num_vars = int(parts[2]) # number of variables (x)
                num_clauses = int(parts[3]) # number of clauses (y)
                continue

            # Parse clause
            lits = [] 
            for tok in line.split(): 
                if tok == "0": # clause terminator
                    break
                lits.append(int(tok))
            
            clauses.append(Clause(cid, lits))
            cid += 1

    return State(clauses, num_vars)