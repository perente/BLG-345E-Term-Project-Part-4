# GECICI OLARAK BURADA, IMPLEMENT EDILECEK

#def run_inference(state):

#    return 'CONTINUE'

import subprocess
from dataclasses import dataclass
from typing import Dict, List, Optional

from structures import State


BCP_INPUT = "bcp_input.txt"
BCP_OUTPUT = "bcp_output.txt"
MASTER_TRACE_FILE = "execution_trace.txt" 
P3_COMMAND = ["python", "inference_engine.py"] # P3 runner command


@dataclass
class BCPResult:
    status: str                # 'SAT', 'UNSAT', 'CONFLICT', 'CONTINUE'
    dl: int                    # decision level after BCP
    conflict_id: Optional[int] # conflict clause ID if any
    exec_log: List[str]        # execution
    var_states: Dict[int, str] # var_id -> 'TRUE', 'FALSE', 'UNASSIGNED'

# Program başladığında master trace dosyasını sıfırlar (yeni oluşturur).
def initialize_master_trace():
    with open(MASTER_TRACE_FILE, "w") as f:
        f.write("--- MASTER EXECUTION TRACE START ---\n")
        
#     P3'ten dönen logları ana trace dosyasına ekler.
#     Mod 'a' (append) olduğu için üzerine yazmaz, sonuna ekler.

def append_to_master_trace(exec_log: List[str]):
    with open(MASTER_TRACE_FILE, "a") as f:
        for line in exec_log:
            f.write(line + "\n")
        f.write("--------------------------------------------------\n")

def write_bcp_trigger(trigger_lit: int, dl: int):
    """
    The format of the trigger file:
    TRIGGER_LITERAL: 1
    DL: 1
    """
    with open(BCP_INPUT, "w") as f:
        f.write(f"TRIGGER_LITERAL: {trigger_lit}\n")
        f.write(f"DL: {dl}\n")


def read_bcp_output() -> BCPResult:
    status = None
    dl = 0
    conflict_id: Optional[int] = None
    exec_log: List[str] = []
    var_states: Dict[int, str] = {}

    section = None

    with open(BCP_OUTPUT, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            if line.startswith("---"):
                if "STATUS" in line:
                    section = "STATUS"
                elif "BCP EXECUTION LOG" in line:
                    section = "LOG"
                elif "CURRENT VARIABLE STATE" in line:
                    section = "STATE"
                continue

            if section == "STATUS":
                if line.startswith("STATUS:"):
                    status = line.split(":")[1].strip()
                elif line.startswith("DL:"):
                    dl = int(line.split(":")[1].strip())
                elif line.startswith("CONFLICT_ID:"):
                    txt = line.split(":")[1].strip()
                    conflict_id = None if txt == "None" else int(txt)

            elif section == "LOG":
                exec_log.append(line)

            elif section == "STATE":
                left, right = line.split("|")
                var_id = int(left.strip())
                var_states[var_id] = right.strip()

    return BCPResult(status, dl, conflict_id, exec_log, var_states)


def apply_bcp_result_to_state(state: State, result: BCPResult):
    """
    P3 output state assignments -> State object
    """
    for var_id, val in result.var_states.items():
        if val == "UNASSIGNED":
            continue

        new_val = True if val == "TRUE" else False

        if state.assignments[var_id] is None:
            state.assignments[var_id] = new_val
            state.levels[var_id] = result.dl
            state.trail.append((var_id, result.dl))
        else:
            # Generally this should not happen, unless there is a conflict
            state.assignments[var_id] = new_val


def run_inference(state: State) -> str:
    """
    DPLL → P3 main function to run inference. 
    Steps:
    1. Write trigger file
    2. Run Interference Engine (P3)
    3. Read output
    4. Update State
    5. Return 'SAT' / 'CONFLICT' / 'CONTINUE'
    """

    # Determine trigger literal
    if state.trail:
        var_id, dl = state.trail[-1]
        val = state.assignments[var_id]
        lit = var_id if val else -var_id
    else:
        lit = 0
        dl = 0

    write_bcp_trigger(lit, dl)

    subprocess.run(P3_COMMAND, check=True)

    result = read_bcp_output()
    
    # Okuduğumuz logları ana dosyaya kaydet
    if result.exec_log:
        append_to_master_trace(result.exec_log)

    apply_bcp_result_to_state(state, result)

    if result.status == "SAT":
        return "SAT"
    if result.status in ("UNSAT", "CONFLICT"):
        return "CONFLICT"
    return "CONTINUE"
