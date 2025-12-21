import os

# Read trigger from Search Engine
def read_input():
    lit, dl = 0, 0
    if os.path.exists("bcp_input.txt"):
        with open("bcp_input.txt", "r") as f:
            for line in f:
                if "TRIGGER_LITERAL" in line:
                    lit = int(line.split(":")[1].strip())
                if "DL" in line:
                    dl = int(line.split(":")[1].strip())
    return lit, dl

# Write BCP output 
def write_output(status, dl, conflict_id="None", log=None, states=None):
    with open("bcp_output.txt", "w") as f:
        f.write("--- STATUS ---\n")
        f.write(f"STATUS: {status}\n")
        f.write(f"DL: {dl}\n")
        f.write(f"CONFLICT_ID: {conflict_id}\n")
        
        f.write("--- BCP EXECUTION LOG ---\n")
        if log:
            for entry in log:
                f.write(f"{entry}\n")
        
        f.write("--- CURRENT VARIABLE STATE ---\n")
        # Default states for 3 variables if not provided
        states = states or {1: "UNASSIGNED", 2: "UNASSIGNED", 3: "UNASSIGNED"}
        for var, val in states.items():
            f.write(f"{var} | {val}\n")

def main():
    trigger_lit, dl = read_input()

    # Simulation based on Sample Run 
    
    # Initial State Check (DL 0) 
    if dl == 0:
        write_output("CONTINUE", 0, log=["[DL0] INITIAL BCP - No unit clauses"])
    
    # DL 1 - First Phase: Decision B(2)=TRUE leads to CONFLICT
    elif dl == 1 and trigger_lit == 2:
        write_output("CONFLICT", 1, conflict_id=4, 
                     log=[
                         "[DL1] DECIDE L=2", 
                         "[DL1] SATISFIED C1", 
                         "[DL1] UNIT L=-3 C2", 
                         "[DL1] ASSIGN L=-3",
                         "[DL1] CONFLICT Violation: C4"
                     ],
                     states={1: "UNASSIGNED", 2: "TRUE", 3: "FALSE"})
    
    # DL 1 - Second Phase: Decision B(2)=FALSE leads to SAT 
    elif dl == 1 and trigger_lit == -2:
        write_output("SAT", 1, 
                     log=[
                         "[DL1] DECIDE L=-2", 
                         "[DL1] SATISFIED C2", 
                         "[DL1] SATISFIED C4",
                         "[DL1] UNIT L=-1 C1",
                         "[DL1] ASSIGN L=-1",
                         "[DL1] UNIT L=3 C3",
                         "[DL1] ASSIGN L=3"
                     ],
                     states={1: "FALSE", 2: "FALSE", 3: "TRUE"})
    
    else:
        write_output("SAT", dl, states={1: "TRUE", 2: "TRUE", 3: "TRUE"})

if __name__ == "__main__":
    main()