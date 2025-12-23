"""
backtracker.py - DPLL Solver icin State Backtracking

Bu modul DPLL arama icin backtracking mekanizmasini saglar.
Bir conflict tespit edildiginde, solver hedef decision level'dan
itibaren yapilmis tum atamalari geri almalidir.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from structures import State


def undo_level(state: "State", target_dl: int):
    """
    Hedef decision level ve uzerinde yapilmis tum atamalari geri al.
    
    Bu fonksiyon conflict sonrasi backtracking yaparken cagirilir.
    target_dl ve uzerinde atanmis tum degiskenler unassigned (None) yapilir.
    Trail, target_dl'den hemen onceki duruma geri sarilir.
    
    Args:
        state: Degistirilecek solver state'i
        target_dl: Backtrack yapilacak decision level
                   target_dl ve daha yuksek seviyelerdeki tum atamalar geri alinir
    """
    while state.trail:
        # En son atamaliya bak
        var_id, last_dl = state.trail[-1]
        
        # Bu atama hedef seviyeden once yapildiysa dur
        if last_dl < target_dl:
            break
        
        # Trail'den cikar (stack pop)
        state.trail.pop()
        
        # Degiskeni unassigned yap
        state.assignments[var_id] = None
        
        # Decision level'ini sifirla
        state.levels[var_id] = 0


def get_current_dl(state: "State") -> int:
    """
    Trail'den mevcut decision level'i al.
    
    Returns:
        En son atamanin decision level'i,
        veya trail bossa 0.
    """
    if state.trail:
        return state.trail[-1][1]
    return 0
