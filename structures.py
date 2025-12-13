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
    Geçici basit heuristic:
    1..num_vars arası ilk UNASSIGNED değişkeni seç.
    İleride MOM / Jeroslow-Wang ile değiştirilecek.
    """
    for var in range(1, state.num_vars + 1):
        if state.assignments[var] is None:
            return var
    return None  # hiç unassigned kalmadıysa

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