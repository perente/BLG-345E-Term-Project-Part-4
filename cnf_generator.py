import random
import sys
import os
import argparse

def generate_cnf(num_vars, num_clauses, run_id=None, output_dir=None):
    """
    Generates a random 3-SAT problem.
    """
    
    # 1. Generate Clauses
    clauses = []
    for _ in range(num_clauses):
        k = min(3, num_vars)
        vars_in_clause = random.sample(range(1, num_vars + 1), k)
        clause = []
        for var in vars_in_clause:
            sign = random.choice([-1, 1])
            clause.append(var * sign)
        clauses.append(clause)

    # 2. Determine Output Paths
    
    if output_dir:
        base_dir = output_dir
        if not os.path.exists(base_dir):
            os.makedirs(base_dir)
            
        # Naming pattern: input_cnf_{run_id}.cnf / initial_state_{run_id}.txt
        # User requested: input_*_test_ID.txt/cnf
        suffix = f"_{run_id}" if run_id else ""
        cnf_filename = os.path.join(base_dir, f"input_cnf{suffix}.cnf")
        state_filename = os.path.join(base_dir, f"initial_state{suffix}.txt")
        
    elif run_id:
        base_dir = os.path.join("..", "Sample Runs", str(run_id))
        if not os.path.exists(base_dir):
            os.makedirs(base_dir)
        
        cnf_filename = os.path.join(base_dir, f"input_cnf_{run_id}.cnf")
        state_filename = os.path.join(base_dir, f"initial_state_{run_id}.txt")
    
    else:
        cnf_filename = "initial_cnf.txt"
        state_filename = None

    # 3. Write CNF File
    with open(cnf_filename, "w") as f:
        f.write(f"p cnf {num_vars} {num_clauses}\n")
        for clause in clauses:
            f.write(f"{' '.join(map(str, clause))} 0\n")
    
    print(f"Generated CNF: {cnf_filename}")

    # 4. Write Initial State File
    if state_filename:
        with open(state_filename, "w") as f:
            f.write("--- HEADER AND METADATA ---\n")
            f.write(f"V: {num_vars}\n")
            f.write(f"C: {num_clauses}\n")
            f.write("\n")
            
            f.write("--- VARIABLE ASSIGNMENTS ---\n")
            for i in range(1, num_vars + 1):
                f.write(f"{i}    | UNASSIGNED\n")
            f.write("\n")
            
            f.write("--- CLAUSE LIST ---\n")
            for i, clause in enumerate(clauses):
                cid = i + 1
                lits_str = str(clause)
                if len(clause) >= 2:
                    watched = "[0, 1]"
                elif len(clause) == 1:
                    watched = "[0]"
                else:
                    watched = "[]"
                f.write(f"C{cid}    | {lits_str}     | {watched}\n")
            f.write("\n")
            
            f.write("--- 2-WATCHED LITERALS MAPPING ---\n")
            watch_map = {}
            for i, clause in enumerate(clauses):
                cid = f"C{i+1}"
                if len(clause) >= 1:
                    l1 = clause[0]
                    if l1 not in watch_map: watch_map[l1] = []
                    watch_map[l1].append(cid)
                if len(clause) >= 2:
                    l2 = clause[1]
                    if l2 not in watch_map: watch_map[l2] = []
                    watch_map[l2].append(cid)
            
            sorted_lits = []
            for v in range(1, num_vars + 1):
                sorted_lits.append(v)
                sorted_lits.append(-v)
            
            for lit in sorted_lits:
                if lit in watch_map:
                    formatted_list = "[" + ", ".join(watch_map[lit]) + "]"
                    f.write(f"{lit:<5} | {formatted_list}\n")
        
        print(f"Generated State: {state_filename}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate 3-SAT DIMACS CNF files.")
    parser.add_argument("vars", type=int, help="Number of variables")
    parser.add_argument("clauses", type=int, help="Number of clauses")
    parser.add_argument("run_id", nargs="?", help="Optional Run ID/Name")
    parser.add_argument("--dir", help="Specific output directory (overrides default 'Sample Runs' structure)")
    
    args = parser.parse_args()
    
    print(f"Generating: {args.vars} vars, {args.clauses} clauses...")
    generate_cnf(args.vars, args.clauses, args.run_id, args.dir)

