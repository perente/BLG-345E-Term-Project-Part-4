from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from structures import State


def undo_level(state: "State", target_dl: int):
    """
    Undo all assignments made at and above the target decision level
    
    - Called during backtracking after a conflict
    - All variables assigned at decision levels >= target_dl are
      set to unassigned (None)
    """
    while state.trail:
        # Look at most recent assignment
        var_id, last_dl = state.trail[-1]
        
        # Stop if this assignment was made before target_dl
        if last_dl < target_dl:
            break
        
        # Stack pop-Remove from trail 
        state.trail.pop()
        
        # Unassign variable
        state.assignments[var_id] = None
        
        # Reset its decision level
        state.levels[var_id] = 0

# Get current decision level from trail
def get_current_dl(state: "State"):
    if state.trail:
        return state.trail[-1][1]
    return 0
