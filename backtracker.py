def undo_level(state, target_dl: int):
    """
    Verilen decision level'da (ve üstünde) yapılan tüm atamaları geri alır.

    Örneğin target_dl = 2 ise:
      - DL=2'de yapılan tüm karar ve propagasyon atamaları UNASSIGNED yapılır.
      - Daha düşük level'lardaki (0,1) atamalar korunur.
    """
    while state.trail and state.trail[-1][1] >= target_dl:
        var_id, dl = state.trail.pop()

        # Bu değişkeni geri al (UNASSIGNED yap)
        state.assignments[var_id] = None
        state.levels[var_id] = 0

        # İstersen trace'e log ekleyebilirsin:
        # state.trace.append(f"[DL{dl}] UNASSIGN var={var_id}")
