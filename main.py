import structures
import dpll_solver

def main():
    # Input file
    cnf_file = "input.cnf" 
    
    # Load initial CNF
    state = structures.load_initial_cnf(cnf_file)
    
    # Start DPLL solver
    is_sat = dpll_solver.dpll_solve(state)
    
    # Final Output
    if is_sat:
        with open("final_model.txt", "w") as f:
            f.write("STATUS: SAT\nFINAL VARIABLE STATE\n")
            for var in range(1, state.num_vars + 1):
                val = state.assignments[var]
                status = "TRUE" if val is True else "FALSE" if val is False else "UNASSIGNED"
                f.write(f"{var} | {status}\n")
    else:
        with open("final_model.txt", "w") as f:
            f.write("STATUS: UNSAT\n")

if __name__ == "__main__":
    main()