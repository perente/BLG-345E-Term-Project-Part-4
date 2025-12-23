"""
io_manager.py - DPLL SAT Solver Input/Output Manager

This module handles all file-based communication:
- Writing BCP trigger files to Project #3 (Inference Engine)
- Reading BCP output files from Project #3
- Writing master trace and final model for Project #5

All file paths are configured inline (no separate config.py).
All output files are written to the current working directory.
"""

import os
from typing import Dict, List, Optional
from dataclasses import dataclass

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Input files (files we read from)
BCP_OUTPUT_FILE = os.path.join(BASE_DIR, "bcp_output.txt")
INITIAL_STATE_FILE = os.path.join(BASE_DIR, "initial_state.txt")
INPUT_CNF_FILE = os.path.join(BASE_DIR, "input.cnf")

# Output files (files we write to)
BCP_INPUT_FILE = os.path.join(BASE_DIR, "bcp_input.txt")  # Trigger file for P3
MASTER_TRACE_FILE = os.path.join(BASE_DIR, "master_trace.txt")
FINAL_MODEL_FILE = os.path.join(BASE_DIR, "final_model.txt")

# Status constants
STATUS_SAT = "SAT"
STATUS_UNSAT = "UNSAT"
STATUS_CONFLICT = "CONFLICT"
STATUS_CONTINUE = "CONTINUE"


# ==============================================================================
# DATA CLASSES
# ==============================================================================

@dataclass
class BCPResult:
    """
    Result of BCP (Boolean Constraint Propagation) execution.
    
    Attributes:
        status: One of 'SAT', 'CONTINUE', 'CONFLICT', 'UNSAT'
        dl: Decision level after BCP
        conflict_id: Conflict clause ID (if status is CONFLICT)
        exec_log: Raw execution log lines for master trace
        assignments: Variable ID -> True/False mapping
        unassigned_vars: List of variable IDs still unassigned
        full_log: Complete raw log content
    """
    status: str
    dl: int
    conflict_id: Optional[int]
    exec_log: List[str]
    assignments: Dict[int, bool]
    unassigned_vars: List[int]
    full_log: str


class IOManager:
    """
    Manages all file I/O operations for the DPLL solver.
    
    Handles file-based communication with the Inference Engine:
    - Writes trigger input specifying decision literal and level
    - Reads BCP output containing status and variable states
    """
    
    def __init__(self):
        """Initialize IO Manager."""
        pass
    
    def write_trigger(self, literal: int, decision_level: int):
        """
        Create BCP Input file for the Inference Engine.
        
        Format (as specified in project documentation):
            TRIGGER_LITERAL: <value>
            DL: <value>
        
        Args:
            literal: Decision literal (positive or negative integer)
            decision_level: Current decision level
        """
        content = f"TRIGGER_LITERAL: {literal}\nDL: {decision_level}\n"
        
        with open(BCP_INPUT_FILE, "w", encoding="utf-8") as f:
            f.write(content)
        
        print(f"[IOManager] Wrote trigger: L={literal}, DL={decision_level}")
    
    def read_bcp_output(self) -> BCPResult:
        """
        Parse BCP output file created by the Inference Engine.
        
        Extracts:
        - STATUS section: status, decision level, conflict ID
        - BCP EXECUTION LOG section: raw log lines
        - CURRENT VARIABLE STATE section: variable assignments
        
        Returns:
            BCPResult containing all parsed information
        """
        if not os.path.exists(BCP_OUTPUT_FILE):
            raise FileNotFoundError(
                f"{BCP_OUTPUT_FILE} not found. Was the inference engine executed?"
            )
        
        # Initialize result containers
        status = None
        dl = 0
        conflict_id: Optional[int] = None
        exec_log: List[str] = []
        assignments: Dict[int, bool] = {}
        unassigned_vars: List[int] = []
        
        with open(BCP_OUTPUT_FILE, "r", encoding="utf-8") as f:
            lines = f.readlines()
            full_log = "".join(lines)
        
        # Track current section
        section = None
        
        for line in lines:
            line_stripped = line.strip()
            
            if not line_stripped:
                continue
            
            # Detect section headers
            if line_stripped.startswith("---"):
                if "STATUS" in line_stripped:
                    section = "STATUS"
                elif "BCP EXECUTION LOG" in line_stripped:
                    section = "LOG"
                elif "CURRENT VARIABLE STATE" in line_stripped:
                    section = "STATE"
                continue
            
            # Parse based on current section
            if section == "STATUS":
                if line_stripped.startswith("STATUS:"):
                    status = line_stripped.split(":", 1)[1].strip()
                elif line_stripped.startswith("DL:"):
                    dl = int(line_stripped.split(":", 1)[1].strip())
                elif line_stripped.startswith("CONFLICT_ID:"):
                    val = line_stripped.split(":", 1)[1].strip()
                    conflict_id = None if val == "None" else int(val)
            
            elif section == "LOG":
                # Collect all log lines for master trace
                if line_stripped:
                    exec_log.append(line_stripped)
            
            elif section == "STATE":
                # Parse variable state: "1 | TRUE" or "1    | UNASSIGNED"
                if "|" in line_stripped:
                    parts = line_stripped.split("|")
                    var_str = parts[0].strip()
                    state_str = parts[1].strip()
                    
                    if var_str.isdigit():
                        var = int(var_str)
                        if state_str == "UNASSIGNED":
                            unassigned_vars.append(var)
                        elif state_str == "TRUE":
                            assignments[var] = True
                        elif state_str == "FALSE":
                            assignments[var] = False
        
        print(f"[IOManager] Read BCP output: status={status}, DL={dl}, conflict={conflict_id}")
        
        return BCPResult(
            status=status or STATUS_CONTINUE,
            dl=dl,
            conflict_id=conflict_id,
            exec_log=exec_log,
            assignments=assignments,
            unassigned_vars=unassigned_vars,
            full_log=full_log
        )
    
    def write_final_model(self, assignments: Dict[int, Optional[bool]], 
                          num_vars: int, is_sat: bool):
        """
        Write final results to the model output file.
        
        Format (for Project #5):
            STATUS: SAT
            
            --- FINAL VARIABLE STATE ---
            1    | TRUE
            2    | FALSE
            ...
        
        Args:
            assignments: Dictionary of variable assignments
            num_vars: Total number of variables
            is_sat: Whether the formula is satisfiable
        """
        with open(FINAL_MODEL_FILE, "w", encoding="utf-8") as f:
            f.write(f"STATUS: {'SAT' if is_sat else 'UNSAT'}\n")
            f.write("\n--- FINAL VARIABLE STATE ---\n")
            
            if is_sat:
                for var_id in range(1, num_vars + 1):
                    val = assignments.get(var_id)
                    if val is None:
                        txt = "UNASSIGNED"
                    else:
                        txt = "TRUE" if val else "FALSE"
                    f.write(f"{var_id}    | {txt}\n")
        
        print(f"[IOManager] Wrote final model to {FINAL_MODEL_FILE}")
    
    def get_initial_state_path(self) -> str:
        """Return path to initial state file."""
        return INITIAL_STATE_FILE
    
    def get_input_cnf_path(self) -> str:
        """Return path to input CNF file."""
        return INPUT_CNF_FILE


# ==============================================================================
# MASTER TRACE MANAGEMENT
# ==============================================================================

class TraceLogger:
    """
    Manages the Master Execution Trace file.
    
    The trace is a chronological record of every event in the DPLL search:
    - DECIDE: Assignments made by the search engine
    - UNIT/ASSIGN: Propagations made by the inference engine
    - CONFLICT: Conflicts detected during BCP
    - BACKTRACK: Backtracking events
    
    Full output from P3 is recorded for each decision level.
    """
    
    def __init__(self):
        """Initialize logger and clear any existing trace file."""
        if os.path.exists(MASTER_TRACE_FILE):
            os.remove(MASTER_TRACE_FILE)
    
    def append_full_output(self, full_log: str, dl: int):
        """
        Append full output from P3 to master trace.
        
        Records complete output for each decision level:
        - STATUS section
        - BCP EXECUTION LOG section
        - CURRENT VARIABLE STATE section
        
        Args:
            full_log: Complete BCP output from P3
            dl: Decision level
        """
        if full_log:
            with open(MASTER_TRACE_FILE, "a", encoding="utf-8") as f:
                f.write(f"\n{'='*60}\n")
                f.write(f"DECISION LEVEL {dl}\n")
                f.write(f"{'='*60}\n")
                f.write(full_log)
                if not full_log.endswith("\n"):
                    f.write("\n")
    
    def append_bcp_log(self, exec_log: List[str]):
        """
        Append only BCP Execution Log lines (for backward compatibility).
        
        Args:
            exec_log: Raw log lines from BCP output file
        """
        if exec_log:
            with open(MASTER_TRACE_FILE, "a", encoding="utf-8") as f:
                for line in exec_log:
                    f.write(line + "\n")
    
    def log_decision(self, literal: int, dl: int):
        """
        Log decision made by P4.
        
        Args:
            literal: Decision literal (positive or negative)
            dl: Decision level
        """
        with open(MASTER_TRACE_FILE, "a", encoding="utf-8") as f:
            f.write(f"\n--- P4 DECISION ---\n")
            f.write(f"TRIGGER_LITERAL: {literal}\n")
            f.write(f"DL: {dl}\n")
    
    def log_backtrack(self, from_dl: int):
        """
        Log backtrack event.
        
        Args:
            from_dl: Decision level being backtracked from
        """
        with open(MASTER_TRACE_FILE, "a", encoding="utf-8") as f:
            f.write(f"\n--- BACKTRACK from DL {from_dl} ---\n")
    
    def log_pick_branching(self, chosen_literal: int, dl: int):
        """
        Log pick_branching_variable decision.
        
        Args:
            chosen_literal: Literal selected by MOM heuristic
            dl: Current decision level
        """
        with open(MASTER_TRACE_FILE, "a", encoding="utf-8") as f:
            f.write(f"\n--- PICK BRANCHING VARIABLE ---\n")
            f.write(f"CHOSEN_LITERAL: {chosen_literal}\n")
            f.write(f"DECISION_LEVEL: {dl}\n")
    
    def get_trace_path(self) -> str:
        """Return path to master trace file."""
        return MASTER_TRACE_FILE
    
    def read_trace(self) -> str:
        """Read and return entire trace content."""
        if os.path.exists(MASTER_TRACE_FILE):
            with open(MASTER_TRACE_FILE, "r", encoding="utf-8") as f:
                return f.read()
        return "(No trace file found)"


# ==============================================================================
# STANDALONE FUNCTIONS (for backward compatibility)
# ==============================================================================

def write_bcp_trigger(trigger_lit: int, dl: int):
    """Standalone function to write BCP trigger file."""
    io = IOManager()
    io.write_trigger(trigger_lit, dl)


def read_bcp_output() -> BCPResult:
    """Standalone function to read BCP output."""
    io = IOManager()
    return io.read_bcp_output()