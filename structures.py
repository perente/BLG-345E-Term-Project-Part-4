"""
structures.py - DPLL SAT Solver Veri Yapilari ve Heuristic

Bu modul asagidaki bilesenleri icerir:
- Clause: CNF clause temsil eden dataclass
- State: Tum SAT solver durumunu tutan ana veri yapisi
- MOM Heuristic: Maximum Occurrences in Minimum-sized Clauses
  (Polarity bazli tie-breaking ile)
"""

from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
import os

# ==============================================================================
# VERI YAPILARI
# ==============================================================================

@dataclass
class Clause:
    """
    CNF clause temsili
    
    Attributes:
        id: Clause ID (conflict reporting icin)
        literals: Integer listesi (pozitif = true, negatif = false)
        watched_indices: Izlenen literal indeksleri [index1, index2]
    """
    id: int
    literals: List[int]
    watched_indices: List[int] = None
    
    def __post_init__(self):
        if self.watched_indices is None:
            # Varsayilan olarak ilk iki literali izle
            if len(self.literals) >= 2:
                self.watched_indices = [0, 1]
            elif len(self.literals) == 1:
                self.watched_indices = [0]
            else:
                self.watched_indices = []


class State:
    """
    SAT solver durumunu tutan ana veri yapisi.
    
    Attributes:
        clauses: Clause nesnelerinin listesi (CNF formul)
        num_vars: Formuldeki toplam degisken sayisi
        assignments: assignments[i] = True/False/None (degisken i icin)
        levels: levels[i] = degisken i'nin atandigi decision level
        trail: (var_id, decision_level) tuple'larinin stack'i
        last_status: BCP'den gelen son status
        last_conflict_id: Conflict clause ID (varsa)
        last_dl: Son decision level
    """
    
    def __init__(self, clauses: List[Clause], num_vars: int):
        self.clauses = clauses
        self.num_vars = num_vars
        
        # Degisken atamalari: index 0 kullanilmaz, 1..num_vars degiskenler icin
        # None = atanmamis, True = true atanmis, False = false atanmis
        self.assignments: List[Optional[bool]] = [None] * (num_vars + 1)
        
        # Decision level takibi: her degiskenin hangi seviyede atandigi
        self.levels: List[int] = [0] * (num_vars + 1)
        
        # Trail: kronolojik atama kaydi (var_id, decision_level)
        self.trail: List[Tuple[int, int]] = []
        
        # BCP sonuc takibi
        self.last_status: Optional[str] = None
        self.last_conflict_id: Optional[int] = None
        self.last_dl: Optional[int] = None

    def assign(self, var_id: int, value: bool, dl: int):
        """
        Bir degiskene deger ata ve trail'e kaydet.
        
        Args:
            var_id: Degisken ID (1-indexed)
            value: Atanacak boolean deger
            dl: Mevcut decision level
        """
        self.assignments[var_id] = value
        self.levels[var_id] = dl
        self.trail.append((var_id, dl))

    def get_assignments_dict(self) -> Dict[int, Optional[bool]]:
        """
        Atamalari dictionary olarak dondur (heuristic fonksiyonlari icin).
        
        Returns:
            Degisken ID -> True/False/None eslemesi
        """
        return {i: self.assignments[i] for i in range(1, self.num_vars + 1)}


# ==============================================================================
# MOM HEURISTIC - Maximum Occurrences in Minimum-sized Clauses
# Polarity bazli tie-breaking ile
# ==============================================================================

def pick_branching_variable(state: State) -> Optional[int]:
    """
    MOM heuristic kullanarak karar degiskeni sec.
    Polarity bazli tie-breaking uygulanir.
    
    Args:
        state: Mevcut solver durumu
        
    Returns:
        Branch yapilacak literal (pozitif veya negatif), veya None
    """
    return mom_heuristic(state)


def mom_heuristic(state: State) -> Optional[int]:
    """
    MOM (Maximum Occurrences in Minimum-sized Clauses) Heuristic
    Polarity bazli tie-breaking ile
    
    Algoritma:
    1. Tum tatmin edilmemis clause'lari bul
    2. Tatmin edilmemis clause'lar arasinda minimum atanmamis literal sayisina sahip olanlari bul
    3. Minimum boyutlu clause'larda literal occurrences'lari say
    4. En yuksek occurrence'a sahip literali dondur (polarity dahil)
    
    Amac: Kritik (en kucuk) clause'larda sik gorulen degiskenlere oncelik vermek,
    boylece unit propagation veya erken conflict detection tetiklemek.
    
    Args:
        state: Mevcut solver durumu
        
    Returns:
        En yuksek MOM skoruna sahip literal (pozitif veya negatif formda)
        Tum clause'lar tatmin edilmisse None
    """
    
    # Adim 1: Tatmin edilmemis clause'lari bul
    unsatisfied_clauses = []
    for clause in state.clauses:
        if not is_clause_satisfied(clause, state):
            unsatisfied_clauses.append(clause)
    
    # Hic tatmin edilmemis clause yoksa, secilecek degisken yok
    if not unsatisfied_clauses:
        return None
    
    # Adim 2: Tatmin edilmemis clause'lar arasinda minimum boyutu bul
    min_size = float('inf')
    min_clauses = []
    
    for clause in unsatisfied_clauses:
        unassigned_count = count_unassigned_literals(clause, state)
        
        if unassigned_count < min_size:
            min_size = unassigned_count
            min_clauses = [clause]
        elif unassigned_count == min_size:
            min_clauses.append(clause)
    
    # Adim 3: Minimum boyutlu clause'larda literal occurrences'lari say
    # ONEMLI: Polarity bazli sayim - hem pozitif hem negatif literaller ayri sayilir
    literal_counts: Dict[int, int] = {}
    
    for clause in min_clauses:
        for literal in clause.literals:
            var_id = abs(literal)
            
            # Sadece atanmamis degiskenleri say
            if state.assignments[var_id] is None:
                if literal not in literal_counts:
                    literal_counts[literal] = 0
                literal_counts[literal] += 1
    
    # Atanmamis literal bulunamazsa
    if not literal_counts:
        return None
    
    # Adim 4: En yuksek occurrence'a sahip literali sec
    # Polarity bazli tie-breaking: Daha sik gorunen polarity tercih edilir
    best_literal = None
    best_score = -1
    
    for literal, count in literal_counts.items():
        # En yuksek skora sahip literali sec
        # Esitlik durumunda, daha dusuk absolute value tercih edilir (deterministic)
        if count > best_score or (count == best_score and (best_literal is None or abs(literal) < abs(best_literal))):
            best_score = count
            best_literal = literal
    
    return best_literal


def is_clause_satisfied(clause: Clause, state: State) -> bool:
    """
    Bir clause'un mevcut atama altinda tatmin edilip edilmedigini kontrol et.
    
    Bir clause, en az bir literali TRUE olarak degerlendirildiginde tatmin edilir:
    - Pozitif literal x, assignments[x] = True ise true'dur
    - Negatif literal -x, assignments[x] = False ise true'dur
    
    Args:
        clause: Kontrol edilecek clause
        state: Mevcut solver durumu
        
    Returns:
        Clause tatmin edilmisse True, degilse False
    """
    for literal in clause.literals:
        var_id = abs(literal)
        var_value = state.assignments[var_id]
        
        # Atanmamis literal clause'u tatmin edemez
        if var_value is None:
            continue
        
        # Literal polaritesine uygun mu kontrol et
        if (literal > 0 and var_value is True) or (literal < 0 and var_value is False):
            return True
    
    return False


def count_unassigned_literals(clause: Clause, state: State) -> int:
    """
    Bir clause'daki atanmamis literal sayisini say.
    
    Args:
        clause: Sayilacak clause
        state: Mevcut solver durumu
        
    Returns:
        Atanmamis literal sayisi
    """
    count = 0
    for literal in clause.literals:
        var_id = abs(literal)
        if state.assignments[var_id] is None:
            count += 1
    return count


# ==============================================================================
# INITIAL STATE PARSING (Project #2 output formatinda)
# ==============================================================================

def load_initial_state(path: str) -> State:
    """
    Project #2 formatindaki initial state dosyasini parse et.
    
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
    
    Args:
        path: Dosya yolu
        
    Returns:
        Yuklenmis State nesnesi
    """
    clauses = []
    num_vars = 0
    num_clauses_expected = 0
    assignments = {}
    
    section = None
    
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            
            # Bos satirlari atla
            if not line:
                continue
            
            # Section header'lari tespit et
            if line.startswith("---"):
                if "HEADER" in line or "METADATA" in line:
                    section = "HEADER"
                elif "VARIABLE ASSIGNMENTS" in line:
                    section = "VARS"
                elif "CLAUSE LIST" in line:
                    section = "CLAUSES"
                elif "2-WATCHED" in line:
                    section = "WATCH"  # Bu kismi okumayiz, sadece atlariz
                continue
            
            # Section'a gore parse et
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
                        # UNASSIGNED ise None olarak kalir
                    except ValueError:
                        pass
            
            elif section == "CLAUSES":
                # Format: C1    | [-1, 2, 3]    | [0, 1]
                if "|" in line:
                    parts = line.split("|")
                    if len(parts) >= 2:
                        # Clause ID parse et
                        cid_str = parts[0].strip()
                        if cid_str.startswith("C"):
                            cid = int(cid_str[1:])
                        else:
                            continue
                        
                        # Literals parse et: [-1, 2, 3]
                        lits_str = parts[1].strip()
                        lits_str = lits_str.strip("[]")
                        if lits_str:
                            lits = [int(x.strip()) for x in lits_str.split(",")]
                        else:
                            lits = []
                        
                        # Watched indices parse et (varsa)
                        watched = None
                        if len(parts) >= 3:
                            watch_str = parts[2].strip().strip("[]")
                            if watch_str:
                                watched = [int(x.strip()) for x in watch_str.split(",")]
                        
                        clauses.append(Clause(cid, lits, watched))
    
    # State olustur
    state = State(clauses, num_vars)
    
    # Yuklenenmis atamalari uygula
    for var_id, val in assignments.items():
        if val is not None:
            state.assign(var_id, val, 0)
    
    return state


def load_initial_cnf(path: str) -> State:
    """
    DIMACS CNF dosyasindan State yukle.
    
    Args:
        path: CNF dosya yolu
        
    Returns:
        Yuklenmis State nesnesi
    """
    clauses = []
    num_vars = 0
    clause_id = 1

    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            
            # Bos satirlari ve yorumlari atla
            if not line or line.startswith(("c", "#")):
                continue

            # Header: p cnf <num_vars> <num_clauses>
            if line.startswith("p"):
                parts = line.split()
                num_vars = int(parts[2])
                continue

            # Clause: literals + 0
            lits = []
            for tok in line.split():
                if tok == "0":
                    break
                lits.append(int(tok))
            
            if lits:
                clauses.append(Clause(clause_id, lits))
                clause_id += 1

    return State(clauses, num_vars)