"""
run_test.py - Test Case Runner for DPLL SAT Solver

Bu script belirli bir test case'i calistirir ve MOM heuristic'in
dogru kararlari verip vermedigini dogrular.

Kullanim:
    python tests/test_case_1/run_test.py
"""

import os
import sys
import shutil

# Ana dizini Python path'e ekle
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
sys.path.insert(0, PROJECT_ROOT)

from structures import State, Clause, pick_branching_variable, load_initial_state


def verify_mom_decisions():
    """
    MOM heuristic'in bu test case icin dogru kararlar verdigini dogrula.
    
    Test Case 1:
    - C1: [1, 2]       (x1 v x2)
    - C2: [-1, 3]      (-x1 v x3)
    - C3: [-2, -3]     (-x2 v -x3)
    - C4: [2, 4]       (x2 v x4)
    - C5: [-4, 5]      (-x4 v x5)
    - C6: [-3, -5]     (-x3 v -x5)
    
    Beklenen MOM kararlari:
    - DL0: L=2 (tum clause'lar 2 literal, var 2 en cok gorunen)
    - DL1: L=-3 (C3 ve C6 kaldi, -3 en cok gorunen)
    - DL2: L=-1 (C2 kaldi, -1 secilir)
    - DL3: L=-4 (C5 kaldi, -4 secilir)
    - DL4: SAT (tum clause'lar tatmin edildi)
    """
    
    print("=" * 70)
    print("  TEST CASE 1: MOM Heuristic Dogrulama")
    print("=" * 70)
    
    # Initial state olustur
    clauses = [
        Clause(1, [1, 2]),      # C1
        Clause(2, [-1, 3]),     # C2
        Clause(3, [-2, -3]),    # C3
        Clause(4, [2, 4]),      # C4
        Clause(5, [-4, 5]),     # C5
        Clause(6, [-3, -5])     # C6
    ]
    state = State(clauses, 5)
    
    # Beklenen kararlar
    expected_decisions = [
        (0, 2, "var2=TRUE"),      # DL0: L=2
        (1, -3, "var3=FALSE"),    # DL1: L=-3
        (2, -1, "var1=FALSE"),    # DL2: L=-1
        (3, -4, "var4=FALSE"),    # DL3: L=-4
    ]
    
    all_passed = True
    
    for dl, expected_literal, description in expected_decisions:
        actual_literal = pick_branching_variable(state)
        
        passed = (actual_literal == expected_literal)
        status = "✓ PASSED" if passed else "✗ FAILED"
        
        print(f"\nDL{dl}: {description}")
        print(f"  Beklenen: L={expected_literal}")
        print(f"  Gerceklesen: L={actual_literal}")
        print(f"  {status}")
        
        if not passed:
            all_passed = False
        
        # State'i guncelle (bir sonraki DL icin)
        if actual_literal is not None:
            var_id = abs(actual_literal)
            value = actual_literal > 0
            state.assignments[var_id] = value
    
    # Son kontrol: Tum clause'lar tatmin edilmis olmali
    final_decision = pick_branching_variable(state)
    sat_passed = (final_decision is None)
    
    print(f"\nFinal (SAT Check):")
    print(f"  MOM donusu: {final_decision}")
    print(f"  Beklenen: None (tum clause'lar satisfied)")
    print(f"  {'✓ PASSED' if sat_passed else '✗ FAILED'}")
    
    if not sat_passed:
        all_passed = False
    
    print("\n" + "=" * 70)
    if all_passed:
        print("  TUM TESTLER GECTI! ✓")
    else:
        print("  BAZI TESTLER BASARISIZ! ✗")
    print("=" * 70)
    
    return all_passed


def run_solver_test():
    """
    DPLL solver'i bu test case ile calistir.
    """
    print("\n" + "=" * 70)
    print("  DPLL SOLVER TESTI")
    print("=" * 70)
    
    # Test dosyalarini ana dizine kopyala
    test_dir = SCRIPT_DIR
    
    files_to_copy = [
        ("initial_state.txt", "initial_state.txt"),
        ("dl0.txt", "dl0.txt"),
        ("dl1.txt", "dl1.txt"),
        ("dl2.txt", "dl2.txt"),
        ("dl3.txt", "dl3.txt"),
        ("dl4.txt", "dl4.txt"),
    ]
    
    print("\n[1] Test dosyalari kopyalaniyor...")
    for src_name, dst_name in files_to_copy:
        src = os.path.join(test_dir, src_name)
        dst = os.path.join(PROJECT_ROOT, dst_name)
        if os.path.exists(src):
            shutil.copy(src, dst)
            print(f"    {src_name} -> {dst_name}")
    
    print("\n[2] DPLL Solver calistiriliyor...")
    print("    Komut: python dpll_solver.py --auto")
    
    # Solver'i import et ve calistir
    os.chdir(PROJECT_ROOT)
    
    from dpll_solver import DPLLSolverAutomatic
    
    solver = DPLLSolverAutomatic()
    success, model = solver.solve()
    
    print("\n[3] Sonuc:")
    if success:
        print("    STATUS: SAT ✓")
        print("    Model:", model)
        
        # Modeli dogrula
        expected_model = {1: False, 2: True, 3: False, 4: False}
        model_correct = True
        for var, expected_val in expected_model.items():
            actual_val = model.get(var)
            if actual_val != expected_val:
                print(f"    UYARI: var{var} beklenen={expected_val}, gerceklesen={actual_val}")
                model_correct = False
        
        if model_correct:
            print("    Model dogrulandi! ✓")
    else:
        print("    STATUS: UNSAT ✗")
        print("    HATA: Bu formul SAT olmali!")
        return False
    
    return success


if __name__ == "__main__":
    print("\n")
    
    # Test 1: MOM kararlarini dogrula
    mom_passed = verify_mom_decisions()
    
    # Test 2: Solver'i calistir
    try:
        solver_passed = run_solver_test()
    except Exception as e:
        print(f"\n[HATA] Solver testi basarisiz: {e}")
        import traceback
        traceback.print_exc()
        solver_passed = False
    
    # Ozet
    print("\n" + "=" * 70)
    print("  TEST OZETI")
    print("=" * 70)
    print(f"  MOM Heuristic Testi: {'✓ PASSED' if mom_passed else '✗ FAILED'}")
    print(f"  Solver Testi: {'✓ PASSED' if solver_passed else '✗ FAILED'}")
    print("=" * 70)
    
    sys.exit(0 if (mom_passed and solver_passed) else 1)
