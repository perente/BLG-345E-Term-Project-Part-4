class StateSolver:
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

        # 1..num_vars için: None / True / False
        self.assignments = [None] * (num_vars + 1)
        # her değişkenin decision level'ı
        self.levels = [0] * (num_vars + 1)

        # Atamaların "sırasını" tutan stack (trail)
        # Her eleman: (var_id, decision_level)
        self.trail = []

        # İleride P3/P5 için istersen:
        # self.trace = []

    def assign(self, var_id: int, value: bool, dl: int):
        """
        Bir değişkeni (var_id) verilen decision level'da ata.
        DPLL her dalda bunu kullanacak.
        """
        self.assignments[var_id] = value
        self.levels[var_id] = dl
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
