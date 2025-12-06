def undo_level(state, target_dl):
    """
    Undo all assignments made at the target decision level and above

    All variables at the mentioned levels will be assigned to None
    The variables at lower levels will stay same
    """
    while state.trail:

        var_id, last_dl = state.trail[-1]

        # If we have backtracked the target level, exit from the loop
        if last_dl < target_dl:
            break 

        # Remove from trail (stack)
        state.trail.pop()

        # Remove the assigned value by making it None
        state.assignments[var_id] = None

        # Make its decision level zero
        state.levels[var_id] = 0

