import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MASTER_TRACE_FILE = os.path.join(BASE_DIR, "master_trace.txt")


class TraceLogger:
    """
    Manages the Master Execution Trace file.
    
    The trace is a chronological record of every event in the DPLL search:
    - DECIDE: Variable assignments made by the search engine
    - UNIT/ASSIGN: Propagations made by the inference engine
    - CONFLICT: Conflicts detected during BCP
    - BACKTRACK: Backtracking events
    """
    
    def __init__(self):
        """
        Initialize the logger and clear any existing trace file.
        """
        # Clear the trace file at the start of a new run
        if os.path.exists(MASTER_TRACE_FILE):
            os.remove(MASTER_TRACE_FILE)
    
    def log_decision(self, literal: int, dl: int):
        """
        Log a decision made by the search engine.
        
        Args:
            literal: The literal that was decided (positive or negative)
            dl: Decision level
        """
        log_entry = f"[DL{dl}] DECIDE      L={literal}   |\n"
        self._append(log_entry)
    
    def log_backtrack(self, from_dl: int, to_dl: int):
        """
        Log a backtrack event.
        
        Args:
            from_dl: Decision level we're backtracking from
            to_dl: Decision level we're backtracking to
        """
        log_entry = f"[DL{from_dl}] BACKTRACK   -> DL{to_dl}\n"
        self._append(log_entry)
    
    def log_step(self, dl: int, event_type: str, details: str):
        """
        Log a general step with custom format.
        
        Args:
            dl: Decision level
            event_type: Type of event (e.g., 'UNIT', 'ASSIGN', 'CONFLICT')
            details: Additional details about the event
        """
        log_entry = f"[DL{dl}] {event_type}: {details}\n"
        self._append(log_entry)
    
    def append_raw_content(self, content: str):
        """
        Append raw BCP Execution Log content from the Inference Engine.
        
        This is called after each inference engine run to record
        all propagation and conflict events.
        
        Args:
            content: Raw log content from BCP output file
        """
        if content and content.strip():
            self._append(content)
            if not content.endswith("\n"):
                self._append("\n")
    
    def _append(self, text: str):
        """
        Append text to the master trace file.
        
        Args:
            text: Text to append
        """
        with open(MASTER_TRACE_FILE, "a", encoding="utf-8") as f:
            f.write(text)
    
    def log_pick_branching(self, chosen_literal: int, dl: int):
        """
        Log the pick_branching_variable decision.
        
        Args:
            chosen_literal: The literal chosen by MOM heuristic
            dl: Current decision level
        """
        log_entry = f"\n--- PICK BRANCHING VARIABLE ---\nCHOSEN_LITERAL: {chosen_literal}\nDECISION_LEVEL: {dl}\n"
        self._append(log_entry)
    
    def get_trace_path(self) -> str:
        """
        Get the path to the master trace file.
        
        Returns:
            Absolute path to the trace file
        """
        return MASTER_TRACE_FILE
    
    def read_trace(self) -> str:
        """
        Read and return the entire trace content.
        
        Returns:
            Complete trace content as string
        """
        if os.path.exists(MASTER_TRACE_FILE):
            with open(MASTER_TRACE_FILE, "r", encoding="utf-8") as f:
                return f.read()
        return "(No trace file found)"
