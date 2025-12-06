# DPLL algoritmasının basit bir taslağını oluşturmaya çalıştım.
# İngilizce commentler kodu açıklamak için
# Türkçe commentler yaptığımız işleri nasıl birbirine bağlayacağımızla alakalı

import sys 

import structures               # Data & Heuristics (Person 2)
import io_manager               # I/O & Integration (Person 3)
import backtracker              # Backtracking (Person 5)

def dpll_solve(state):
    """
    Main function of Search Engine

    Parameters
    ----------
    state : object
        Tüm SAT durumunu tutan veri yapısı (structures modülünde tanımlanacak).

    Returns
    -------
    bool
        True  -> formül SAT (bir model bulundu)
        False -> formül UNSAT (hiçbir atama tüm formülü sağlayamıyor)
    """
    dl_zero = 0
    result = dpll_solver(state, dl_zero)

    # GPT YAZDI BU COMMENTLER SILINECEk
    # İsteğe bağlı: Kök seviyede UNSAT durumunda bütün atamaları temizlemek için
    # backtracker.undo_level(state, dl_zero) çağrısı ekleyebilirsin.
    # (Person 5 ile konuşup, DL=0 için nasıl davranmak istediklerine göre karar verirsiniz.)

    return result


def dpll_solver(state, decision_level):
    """
    Recursive DPLL function
    Parameters:
        state: The main data object holding variables and clauses.

        decision_level: Current depth in the decision tree.
                        DL = 0  : root level

    Return:
        True if SAT 
        False if UNSAT
    """

    # Calls project 3 to update state object
    status = io_manager.run_inference(state)    # run_inference() fonksiyonu -> 3.kişiden alınacak   
    print(f"[DL {decision_level}] Inference Status: {status}")

    # Checking the status

    # The branch we have taken led to a conflict
    # Signals False to caller and caller function will undo the current level using backtracker.undo_level()
    if status == 'CONFLICT':
        return False

    # If all clauses are satisfied, then we found a model (an interpretation that makes the formula TRUE)
    if status == 'SAT':
        return True

    # If status is not equal to 'CONFLICT' or 'SAT'
    # 'CONTINUE' and we branch on a new variable

    # Getting the variable to check from Heuristic approach
    var_id = structures.pick_branching_variable(state) # pick_branching_variable() fonksiyonu -> 2.kişiden alınacak

    # If var_id is None, it means there are no variables left to try for satisfiability
    # Since there is no conflict so far, the current assignment satisfies all clauses
    if var_id is None:
        print(f"[DL {decision_level}] No unassigned variable left. Result: SAT")
        return True

    # We still have variables to try, we are going to new decision level
    next_dl = decision_level + 1

    # Try assigning TRUE value on variable at next decision level 
    print(f"[DL {decision_level}] Branching on variable {var_id} -> Try TRUE at DL {next_dl}")
    state.assign(var_id, True, next_dl) # state objesi -> 2.kişiden alınacak

    # Call 'dpll_solver()' recursively for TRUE value of new variable on next level
    if dpll_solver(state, next_dl):
        return True

    # TRUE branch failed, then backtrack this level
    print(f"[DL {decision_level}] Backtracking... Undoing level {next_dl}")
    backtracker.undo_level(state, next_dl) # undo_level() fonksiyonu -> 5.kişiden alınacak
    
    # Trying FALSE value on variable 
    print(f"[DL {decision_level}] Branching on Variable {var_id} -> Try FALSE at DL {next_dl}")
    state.assign(var_id, False, next_dl) # state objesi -> 2.kişiden alınacak

    # Call 'dpll_solver()' recursively for FALSE value of new variable on next level
    if dpll_solver(state, next_dl):
        return True

    # FALSE value is not SAT too, then backtrack again
    print(f"[DL {decision_level}] Both TRUE and FALSE branches failed. Backtracking level {next_dl}")
    backtracker.undo_level(state, next_dl)  # undo_level() fonksiyonu -> 5.kişiden alınacak

    # Caller will continue to backtrack since this branch is UNSAT (leads to a conflict)
    return False

    
