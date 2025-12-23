"""
Bagimsiz Dogrulama: MOM Heuristic ve SAT Solver Testi
Bu script, pick_branching_variable fonksiyonunun gercekten calistigini dogrular.
"""
from structures import State, Clause, pick_branching_variable, is_clause_satisfied

# Test Case 3 clauses
clauses = [
    Clause(1, [1, 2]),      # C1: (1 OR 2)
    Clause(2, [-1, 3]),     # C2: (-1 OR 3)
    Clause(3, [-2, -3]),    # C3: (-2 OR -3)
    Clause(4, [1, -4]),     # C4: (1 OR -4)
    Clause(5, [4, 5])       # C5: (4 OR 5)
]
state = State(clauses, 5)

print("=== BAGIMSIZ DOGRULAMA ===\n")
print("CNF Formulu:")
print("  C1: (1 OR 2)")
print("  C2: (-1 OR 3)")
print("  C3: (-2 OR -3)")
print("  C4: (1 OR -4)")
print("  C5: (4 OR 5)")
print()

decisions = []
step = 1

while True:
    lit = pick_branching_variable(state)
    if lit is None:
        print(f"Step {step}: Tum clause'lar satisfied - BITTI\n")
        break
    
    var = abs(lit)
    val = lit > 0
    val_str = "TRUE" if val else "FALSE"
    
    print(f"Step {step}: MOM secti L={lit}")
    print(f"  -> var{var} = {val_str}")
    
    state.assignments[var] = val
    decisions.append((var, val))
    
    # Satisfied clause'lari goster
    satisfied = []
    for c in clauses:
        if is_clause_satisfied(c, state):
            satisfied.append(f"C{c.id}")
    print(f"  -> Satisfied: {satisfied}")
    print(f"  -> State: {[state.assignments[i] for i in range(1,6)]}")
    print()
    step += 1

# Final model dogrulamasi
print("=== FINAL MODEL DOGRULAMASI ===\n")
print(f"Model: var1={state.assignments[1]}, var2={state.assignments[2]}, var3={state.assignments[3]}, var4={state.assignments[4]}, var5={state.assignments[5]}")
print()

all_satisfied = True
for c in clauses:
    sat = is_clause_satisfied(c, state)
    status = "OK" if sat else "FAIL"
    print(f"C{c.id} {c.literals}: {status}")
    if not sat:
        all_satisfied = False

print()
if all_satisfied:
    print("SONUC: Tum clause'lar satisfied - SAT DOGRULANDI!")
else:
    print("SONUC: Bazi clause'lar satisfied degil - HATA!")
