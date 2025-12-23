import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MASTER_TRACE_FILE = os.path.join(BASE_DIR, "master_trace.txt")

class TraceLogger:
    def __init__(self):
        # Clear trace file at new run
        if os.path.exists(MASTER_TRACE_FILE):
            os.remove(MASTER_TRACE_FILE)

    # Log decision made by search engine
    def log_decision(self, literal: int, dl: int):
        log_entry = f"[DL{dl}] DECIDE      L={literal}   |\n"
        self._append(log_entry)
    
    # Log a backtrack
    def log_backtrack(self, from_dl: int, to_dl: int):
        log_entry = f"[DL{from_dl}] BACKTRACK   -> DL{to_dl}\n"
        self._append(log_entry)

    # Log a generic solver event
    def log_step(self, dl: int, event_type: str, details: str):
        log_entry = f"[DL{dl}] {event_type}: {details}\n"
        self._append(log_entry)
    
    # Append raw execution output from inference engine
    def append_raw_content(self, content: str):
        if content and content.strip():
            self._append(content)
            if not content.endswith("\n"):
                self._append("\n")
    
    def _append(self, text: str):
        #  Append text to master trace file
        with open(MASTER_TRACE_FILE, "a", encoding="utf-8") as f:
            f.write(text)
    
    def log_pick_branching(self, chosen_literal: int, dl: int):
        # Log pick_branching_variable decision
        log_entry = f"\n--- PICK BRANCHING VARIABLE ---\nCHOSEN_LITERAL: {chosen_literal}\nDECISION_LEVEL: {dl}\n"
        self._append(log_entry)
    
    def get_trace_path(self) -> str:
        # Get the path to master trace file
        return MASTER_TRACE_FILE
    
    def read_trace(self) -> str:
        # Load and return trace content
        if os.path.exists(MASTER_TRACE_FILE):
            with open(MASTER_TRACE_FILE, "r", encoding="utf-8") as f:
                return f.read()
        return "(No trace file)"
