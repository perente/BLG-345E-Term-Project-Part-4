"""
dpll_solver.py - DPLL SAT Solver Search Engine (Project #4)

Bu dosya DPLL tabanli SAT solver'in ana giris noktasidir.
Sistematik olarak degisken atama uzayini arastiran temel DPLL
recursive arama algoritmasini uygular.

Ana Bilesenler:
- DPLLSolver: Recursive DPLL algoritmasi ile ana solver sinifi
- MOM Heuristic: Karar degiskeni secimi (structures.py'de)
- TraceLogger: Project #5 entegrasyonu icin master execution trace
- IOManager: Inference Engine (Project #3) ile dosya tabanli iletisim

Kullanim:
    python dpll_solver.py                    # Varsayilan dosyalarla calistir
    python dpll_solver.py --initial <path>   # Ozel initial state dosyasi ile calistir
"""

import sys
import os

# Proje modullerini import et
from structures import State, Clause, load_initial_state, load_initial_cnf, pick_branching_variable
from io_manager import (
    IOManager, TraceLogger, BCPResult,
    STATUS_SAT, STATUS_UNSAT, STATUS_CONFLICT, STATUS_CONTINUE,
    BCP_OUTPUT_FILE
)
import backtracker


class DPLLSolver:
    """
    DPLL SAT Solver - Davis-Putnam-Logemann-Loveland algoritmasini uygular.
    
    Solver su sekilde calisir:
    1. Inference Engine'i calistirarak BCP (Boolean Constraint Propagation) yap
    2. Sonucu kontrol et:
       - SAT: Basari ile model dondur
       - CONFLICT/UNSAT: Basarisizlik dondur (backtracking tetiklenir)
       - CONTINUE: Bir degisken sec ve dallan
    3. MOM heuristic kullanarak karar yap
    4. Her iki polarity icin recursive olarak dene (once tercih edilen, sonra tersi)
    
    Attributes:
        io: Inference Engine ile dosya I/O icin IOManager
        logger: Execution trace kaydi icin TraceLogger
        state: Atamalar ve clause'larla mevcut solver durumu
    """
    
    def __init__(self, initial_state_path: str = None):
        """
        DPLL solver'i baslat.
        
        Args:
            initial_state_path: Initial state dosyasinin yolu. 
                               None ise varsayilan konum kullanilir.
        """
        self.io = IOManager()
        self.logger = TraceLogger()
        
        # Belirtilen yoldan veya varsayilandan initial state yukle
        if initial_state_path is None:
            initial_state_path = self.io.get_initial_state_path()
        
        # Dosya uzantisina gore yukle
        if initial_state_path.endswith(".cnf"):
            self.state = load_initial_cnf(initial_state_path)
        else:
            self.state = load_initial_state(initial_state_path)
        
        self.initial_state_path = initial_state_path
        
        print(f"[DPLLSolver] Initial state yuklendi: {initial_state_path}")
        print(f"[DPLLSolver] Degiskenler: {self.state.num_vars}, Clause'lar: {len(self.state.clauses)}")
    
    def solve(self):
        """
        Public giris noktasi. Decision Level 0'dan DPLL recursion'u baslatir.
        
        Returns:
            Tuple[bool, dict]: (success, model)
            - success: SAT ise True, UNSAT ise False
            - model: SAT ise degisken atamalari dict'i, UNSAT ise None
        """
        print("\n" + "=" * 60)
        print("  DPLL ARAMA BASLIYOR")
        print("=" * 60)
        
        # Decision Level 0'da baslat
        # Oncelikle DL 0 icin BCP output'u oku (initial unit propagation)
        # Not: P3 zaten DL 0 icin bcp_output.txt olusturmus olmali
        
        result, model = self._dpll_recursive(dl=0)
        
        return result, model
    
    def _dpll_recursive(self, dl: int):
        """
        Ana recursive DPLL fonksiyonu.
        
        Algoritma akisi:
        1. Inference Engine'den BCP sonucunu oku
        2. Status'u kontrol et:
           - SAT: Model ile basari dondur
           - CONFLICT/UNSAT: Basarisizlik dondur (backtracking tetiklenir)
           - CONTINUE: Degisken sec ve dallan
        3. MOM heuristic kullanarak karar yap
        4. Her iki polarity icin recursive dene
        
        Args:
            dl: Mevcut decision level
            
        Returns:
            Tuple[bool, dict]: (success, model)
        """
        # Adim 1: BCP output'u oku
        try:
            result = self.io.read_bcp_output()
        except FileNotFoundError as e:
            print(f"[DL {dl}] HATA: {e}")
            return False, None
        
        # P3'ten gelen tam output'u master trace'e kaydet
        self.logger.append_full_output(result.full_log, dl)
        
        status = result.status
        
        print(f"\n[DL {dl}] Status: {status}")
        if result.assignments:
            print(f"[DL {dl}] Atamalar: {result.assignments}")
        if result.unassigned_vars:
            print(f"[DL {dl}] Atanmamis: {result.unassigned_vars}")
        
        # Adim 2: Status kontrol et (Base Cases)
        if status == STATUS_SAT:
            print(f"[DL {dl}] *** SATISFIABLE - Cozum bulundu! ***")
            model = {var: val for var, val in result.assignments.items()}
            return True, model
        
        if status in (STATUS_UNSAT, STATUS_CONFLICT):
            print(f"[DL {dl}] Conflict tespit edildi - Backtracking")
            return False, None
        
        # Adim 3: Status CONTINUE - Karar yap
        # Heuristic icin state'i guncelle
        for var in result.unassigned_vars:
            self.state.assignments[var] = None
        for var, val in result.assignments.items():
            self.state.assignments[var] = val
        
        # MOM heuristic kullanarak branching literali sec
        # Bu artik polarity ile birlikte literal donduruyor
        chosen_literal = pick_branching_variable(self.state)
        
        if chosen_literal is None:
            # Atanmamis degisken kalmadi ama status SAT degildi
            # Bu tum clause'larin tatmin edildigi anlamina gelir
            print(f"[DL {dl}] Tum degiskenler atandi - SAT")
            model = {var: val for var, val in result.assignments.items()}
            return True, model
        
        # Adim 4: Recursion - Her iki polarity'yi dene
        next_dl = dl + 1
        chosen_var = abs(chosen_literal)
        chosen_value = chosen_literal > 0  # Pozitif literal -> True, Negatif -> False
        
        # Dallanma 1: Heuristic'in sectigi polarity
        print(f"[DL {dl}] Dallanma: degisken {chosen_var} -> "
              f"{'TRUE' if chosen_value else 'FALSE'} (L={chosen_literal}) DL {next_dl}'de")
        
        # State'i guncelle ve trigger yaz
        self.state.assign(chosen_var, chosen_value, next_dl)
        self.io.write_trigger(chosen_literal, next_dl)
        
        # SIMDI P3'UN CALISMASI BEKLENIYOR
        # Test icin kullanici burada mock bcp_output.txt hazirlamali
        print(f"[BEKLE] P3 calistirildiktan sonra devam etmek icin bcp_output.txt'yi guncelleyin...")
        
        input(">>> P3 calistiktan sonra Enter'a basin...")
        
        # Recursive cagri
        success, model = self._dpll_recursive(next_dl)
        if success:
            return True, model
        
        # Dallanma 1 basarisiz - Backtrack
        print(f"[DL {dl}] Dallanma 1 basarisiz - Backtracking DL {next_dl}'den")
        backtracker.undo_level(self.state, next_dl)
        self.logger.log_backtrack(next_dl)
        
        # Dallanma 2: Ters polarity
        negated_literal = -chosen_literal
        negated_value = not chosen_value
        
        print(f"[DL {dl}] Dallanma: degisken {chosen_var} -> "
              f"{'TRUE' if negated_value else 'FALSE'} (L={negated_literal}) DL {next_dl}'de")
        
        # State'i guncelle ve trigger yaz
        self.state.assign(chosen_var, negated_value, next_dl)
        self.io.write_trigger(negated_literal, next_dl)
        
        # SIMDI P3'UN CALISMASI BEKLENIYOR
        print(f"[BEKLE] P3 calistirildiktan sonra devam etmek icin bcp_output.txt'yi guncelleyin...")
        
        input(">>> P3 calistiktan sonra Enter'a basin...")
        
        # Recursive cagri
        success, model = self._dpll_recursive(next_dl)
        if success:
            return True, model
        
        # Her iki dallanma da basarisiz - Daha fazla backtrack
        print(f"[DL {dl}] Her iki dallanma da basarisiz - Backtracking")
        backtracker.undo_level(self.state, next_dl)
        
        return False, None


class DPLLSolverAutomatic(DPLLSolver):
    """
    Otomatik modda calisan DPLL Solver.
    
    Mock dosyalar kullanarak P3 simulasyonu yapar.
    Her decision level icin dl<N>.txt dosyasini bcp_output.txt'ye kopyalar.
    """
    
    def __init__(self, initial_state_path: str = None):
        super().__init__(initial_state_path)
        self.decision_count = 0
    
    def _copy_mock_response(self, dl: int):
        """Mock response dosyasini bcp_output.txt'ye kopyala."""
        import shutil
        
        base_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Farkli dosya isim kaliplarini dene
        patterns = [
            f"dl{dl}.txt",
            f"dl{dl}_response.txt",
            f"bcp_output_dl{dl}.txt",
        ]
        
        for pattern in patterns:
            src = os.path.join(base_dir, pattern)
            if os.path.exists(src):
                shutil.copy(src, BCP_OUTPUT_FILE)
                print(f"[Mock] {pattern} -> bcp_output.txt kopyalandi")
                return True
        
        print(f"[Mock] UYARI: DL {dl} icin response dosyasi bulunamadi")
        return False
    
    def _dpll_recursive(self, dl: int):
        """
        Otomatik mod icin recursive DPLL.
        Mock dosyalar kullanir.
        """
        # Mock response'u kopyala
        self._copy_mock_response(dl)
        
        # BCP output'u oku
        try:
            result = self.io.read_bcp_output()
        except FileNotFoundError as e:
            print(f"[DL {dl}] HATA: {e}")
            return False, None
        
        # P3'ten gelen tam output'u master trace'e kaydet
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
        
        # Heuristic icin state guncelle
        for var in result.unassigned_vars:
            self.state.assignments[var] = None
        for var, val in result.assignments.items():
            self.state.assignments[var] = val
        
        # MOM ile literal sec
        chosen_literal = pick_branching_variable(self.state)
        
        if chosen_literal is None:
            print(f"[DL {dl}] Tum degiskenler atandi - SAT")
            model = {var: val for var, val in result.assignments.items()}
            return True, model
        
        # Dallanma
        next_dl = dl + 1
        chosen_var = abs(chosen_literal)
        chosen_value = chosen_literal > 0
        
        print(f"[DL {dl}] Branching: var {chosen_var} = {'T' if chosen_value else 'F'} (L={chosen_literal})")
        
        # P4 kararini logla
        self.logger.log_decision(chosen_literal, next_dl)
        
        self.state.assign(chosen_var, chosen_value, next_dl)
        self.io.write_trigger(chosen_literal, next_dl)
        
        # Recursive
        success, model = self._dpll_recursive(next_dl)
        if success:
            return True, model
        
        # Backtrack ve ters polarity dene
        print(f"[DL {dl}] Backtracking from DL {next_dl}")
        backtracker.undo_level(self.state, next_dl)
        self.logger.log_backtrack(next_dl)
        
        negated_literal = -chosen_literal
        negated_value = not chosen_value
        
        print(f"[DL {dl}] Trying opposite: var {chosen_var} = {'T' if negated_value else 'F'} (L={negated_literal})")
        
        # P4 kararini logla
        self.logger.log_decision(negated_literal, next_dl)
        
        self.state.assign(chosen_var, negated_value, next_dl)
        self.io.write_trigger(negated_literal, next_dl)
        
        success, model = self._dpll_recursive(next_dl)
        if success:
            return True, model
        
        backtracker.undo_level(self.state, next_dl)
        return False, None


# ==============================================================================
# ANA CALISTIRMA
# ==============================================================================

def main():
    """
    DPLL SAT Solver icin ana giris noktasi.
    
    Kullanim:
        python dpll_solver.py                    # Interactive mod (P3 bekler)
        python dpll_solver.py --auto             # Otomatik mod (mock dosyalar)
        python dpll_solver.py --initial <path>   # Ozel initial state
    """
    print("=" * 70)
    print("  DPLL SAT Solver - Search Engine (Project #4)")
    print("  MOM Heuristic ile (Polarity Bazli Tie-Breaking)")
    print("=" * 70)
    
    # Komut satiri argumanlarini parse et
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
    
    # Solver'i baslat ve calistir
    try:
        if auto_mode:
            print("[Mod] Otomatik mod - Mock dosyalar kullanilacak")
            solver = DPLLSolverAutomatic(initial_state_path)
        else:
            print("[Mod] Interactive mod - Her adimda P3 beklenecek")
            solver = DPLLSolver(initial_state_path)
        
        success, model = solver.solve()
        
        # Final sonucu yazdir
        print("\n" + "=" * 70)
        if success:
            print(">>> SONUC: SATISFIABLE <<<")
            print("\nFinal Atama:")
            if model:
                for var in sorted(model.keys()):
                    val = model[var]
                    print(f"  Degisken {var}: {'TRUE' if val else 'FALSE'}")
        else:
            print(">>> SONUC: UNSATISFIABLE <<<")
        
        # Final modeli dosyaya yaz
        solver.io.write_final_model(
            model if model else {},
            solver.state.num_vars,
            success
        )
        
        # Trace bilgisi
        print(f"\nMaster Trace: {solver.logger.get_trace_path()}")
        print("\n--- MASTER TRACE ICERIGI ---")
        print(solver.logger.read_trace())
        
    except FileNotFoundError as e:
        print(f"[HATA] {e}")
        print("\nAsagidaki dosyalarin mevcut oldugundan emin olun:")
        print("  - initial_state.txt (Initial formula state)")
        print("  - bcp_output.txt (P3'ten gelen BCP output)")
        sys.exit(1)
    except Exception as e:
        print(f"[HATA] Beklenmeyen hata: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
