# DPLL algoritmasının basit bir taslağını oluşturmaya çalıştım.
# İngilizce commentler kodu açıklamak için
# Türkçe commentler yaptığımız işleri nasıl birbirine bağlayacağımızla alakalı

import sys 

import structures               # Data & Heuristics (Person 2)
import io_manager               # I/O & Integration (Person 3)
import backtracker              # Backtracking (Person 5)

"""
Recusive DPLL function
Arguments:
    state: The main data object holding variables and clauses.
    decision_level: Current depth in the decision tree.
Return:
    True if SAT 
    False if UNSAT
"""

def dpll_solver(state, decision_level):

    # Calls project 3 to update state object
    status = io_manager.run_inference(state)    # run_inference() fonksiyonu -> 3.kişiden alınacak   
    print(f"[DL {decision_level}] Inference Status: {status}")

    # Checking the status
    if status == 'CONFLICT':
        return False

    if status == 'SAT':
        return True

    # If status is not equal to 'CONFLICT' or 'SAT'
    # Then it is 'CONTINUE'

    # Getting the variable to check from Heuristic approach
    var_id = structures.pick_branching_variable(state) # pick_branching_variable() fonksiyonu -> 2.kişiden alınacak

    # If var_id is None, it means there are no variable left to try for satisfiableity
    # and since there is no conflict since now, it is satisfiable
    if var_id is None:
        return True

    # We still have variables to try, we are going to new decision level
    next_dl = decision_level + 1

    # Trying TRUE value on variable 
    print(f"[DL {decision_level}] Branching on Variable {var_id} -> Trying TRUE")
    state.assign(var_id, True, next_dl) # state objesi -> 2.kişiden alınacak

    # Call 'dpll_solver()' recursively for TRUE value of new variable on next level
    if dpll_solver(state, next_dl):
        return True

    # TRUE value is not SAT, then backtrack
    print(f"[DL {decision_level}] Backtracking... Undoing level {next_dl}")
    backtracker.undo_level(state, next_dl) # undo_level() fonksiyonu -> 5.kişiden alınacak
    
    # Trying FALSE value on variable 
    print(f"[DL {decision_level}] Branching on Variable {var_id} -> Trying False")
    state.assign(var_id, False, next_dl) # state objesi -> 2.kişiden alınacak

    # Call 'dpll_solver()' recursively for FALSE value of new variable on next level
    if dpll_solver(state, next_dl):
        return True

    # FALSE value is not SAT too, then backtrack again
    print(f"[DL {decision_level}] Both branches failed. Backtracking level {next_dl}")
    backtracker.undo_level(state, next_dl)  # undo_level() fonksiyonu -> 5.kişiden alınacak

    return False

    
