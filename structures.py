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
