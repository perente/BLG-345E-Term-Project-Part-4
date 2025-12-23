"""
io_manager.py - DPLL SAT Solver Input/Output Manager

Bu modul tum dosya tabanli iletisimi yonetir:
- Project #3'e BCP trigger dosyalari yazma
- Project #3'ten BCP output dosyalari okuma
- Project #5 icin master trace ve final model yazma

Tum dosya yollari inline olarak ayarlanir (ayri config.py yok).
Tum output dosyalari mevcut calisma dizinine yazilir.
"""

import os
from typing import Dict, List, Optional
from dataclasses import dataclass

# ==============================================================================
# DOSYA YOLU KONFIGURASYONU (Inline - config.py yok)
# ==============================================================================

# Base dizin: bu dosyanin bulundugu dizin
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Input dosyalari (okudugumuz dosyalar)
BCP_OUTPUT_FILE = os.path.join(BASE_DIR, "bcp_output.txt")
INITIAL_STATE_FILE = os.path.join(BASE_DIR, "initial_state.txt")
INPUT_CNF_FILE = os.path.join(BASE_DIR, "input.cnf")

# Output dosyalari (yazdigimiz dosyalar) - tumu mevcut dizinde
BCP_INPUT_FILE = os.path.join(BASE_DIR, "bcp_input.txt")  # P3'e trigger dosyasi
MASTER_TRACE_FILE = os.path.join(BASE_DIR, "master_trace.txt")
FINAL_MODEL_FILE = os.path.join(BASE_DIR, "final_model.txt")

# Status sabitleri
STATUS_SAT = "SAT"
STATUS_UNSAT = "UNSAT"
STATUS_CONFLICT = "CONFLICT"
STATUS_CONTINUE = "CONTINUE"


# ==============================================================================
# VERI SINIFLARI
# ==============================================================================

@dataclass
class BCPResult:
    """
    BCP (Boolean Constraint Propagation) calismasinin sonucu.
    
    Attributes:
        status: 'SAT', 'CONTINUE', 'CONFLICT', 'UNSAT' degerlerinden biri
        dl: BCP sonrasi decision level
        conflict_id: Conflict clause ID (status CONFLICT ise)
        exec_log: Master trace icin raw execution log satirlari
        assignments: Degisken ID -> True/False eslemesi
        unassigned_vars: Hala atanmamis degisken ID'lerinin listesi
        full_log: Tum raw log icerigi
    """
    status: str
    dl: int
    conflict_id: Optional[int]
    exec_log: List[str]
    assignments: Dict[int, bool]
    unassigned_vars: List[int]
    full_log: str


# ==============================================================================
# IO MANAGER SINIFI
# ==============================================================================

class IOManager:
    """
    DPLL solver icin tum dosya I/O islemlerini yonetir.
    
    Inference Engine ile dosyalar uzerinden iletisimi yonetir:
    - Decision literal ve level belirten trigger input yazar
    - Status ve degisken durumlarini iceren BCP output okur
    """
    
    def __init__(self):
        """
        IO Manager'i baslat.
        """
        pass
    
    def write_trigger(self, literal: int, decision_level: int):
        """
        Inference Engine icin BCP Input dosyasi olustur.
        
        Format (proje dokumaninda belirtildigi gibi):
            TRIGGER_LITERAL: <value>
            DL: <value>
        
        Args:
            literal: Karar literali (pozitif veya negatif integer)
            decision_level: Mevcut decision level
        """
        content = f"TRIGGER_LITERAL: {literal}\nDL: {decision_level}\n"
        
        with open(BCP_INPUT_FILE, "w", encoding="utf-8") as f:
            f.write(content)
        
        print(f"[IOManager] Wrote trigger: L={literal}, DL={decision_level}")
    
    def read_bcp_output(self) -> BCPResult:
        """
        Inference Engine tarafindan olusturulan BCP output dosyasini parse et.
        
        Cikarir:
        - STATUS section: status, decision level, conflict ID
        - BCP EXECUTION LOG section: raw log satirlari
        - CURRENT VARIABLE STATE section: degisken atamalari
        
        Returns:
            Tum parse edilmis bilgiyi iceren BCPResult
        """
        if not os.path.exists(BCP_OUTPUT_FILE):
            raise FileNotFoundError(
                f"{BCP_OUTPUT_FILE} bulunamadi. Inference engine calistirildi mi?"
            )
        
        # Sonuc konteynerlerini baslat
        status = None
        dl = 0
        conflict_id: Optional[int] = None
        exec_log: List[str] = []
        assignments: Dict[int, bool] = {}
        unassigned_vars: List[int] = []
        
        with open(BCP_OUTPUT_FILE, "r", encoding="utf-8") as f:
            lines = f.readlines()
            full_log = "".join(lines)
        
        # Hangi section'da oldugumuz takip et
        section = None
        
        for line in lines:
            line_stripped = line.strip()
            
            if not line_stripped:
                continue
            
            # Section header'larini tespit et
            if line_stripped.startswith("---"):
                if "STATUS" in line_stripped:
                    section = "STATUS"
                elif "BCP EXECUTION LOG" in line_stripped:
                    section = "LOG"
                elif "CURRENT VARIABLE STATE" in line_stripped:
                    section = "STATE"
                continue
            
            # Mevcut section'a gore parse et
            if section == "STATUS":
                if line_stripped.startswith("STATUS:"):
                    status = line_stripped.split(":", 1)[1].strip()
                elif line_stripped.startswith("DL:"):
                    dl = int(line_stripped.split(":", 1)[1].strip())
                elif line_stripped.startswith("CONFLICT_ID:"):
                    val = line_stripped.split(":", 1)[1].strip()
                    conflict_id = None if val == "None" else int(val)
            
            elif section == "LOG":
                # Master trace icin tum log satirlarini topla
                if line_stripped:
                    exec_log.append(line_stripped)
            
            elif section == "STATE":
                # Degisken durumunu parse et: "1 | TRUE" veya "1    | UNASSIGNED"
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
        Final sonuclardan model output dosyasina yaz.
        
        Format (Project #5 icin):
            STATUS: SAT
            
            --- FINAL VARIABLE STATE ---
            1    | TRUE
            2    | FALSE
            ...
        
        Args:
            assignments: Degisken atamalari dict'i
            num_vars: Toplam degisken sayisi
            is_sat: Formul tatmin edilebilir mi
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
        """Initial state dosyasinin yolunu dondur."""
        return INITIAL_STATE_FILE
    
    def get_input_cnf_path(self) -> str:
        """Input CNF dosyasinin yolunu dondur."""
        return INPUT_CNF_FILE


# ==============================================================================
# MASTER TRACE YONETIMI
# ==============================================================================

class TraceLogger:
    """
    Master Execution Trace dosyasini yonetir.
    
    Trace, DPLL arama surecindeki her olayin kronolojik kaydini tutar:
    - DECIDE: Search engine tarafindan yapilan atamalari
    - UNIT/ASSIGN: Inference engine tarafindan yapilan propagasyonlar
    - CONFLICT: BCP sirasinda tespit edilen conflict'ler
    - BACKTRACK: Backtracking olaylari
    
    Her decision level icin P3'ten gelen tam output kaydedilir.
    """
    
    def __init__(self):
        """
        Logger'i baslat ve mevcut trace dosyasini temizle.
        """
        # Yeni bir calistirmada trace dosyasini temizle
        if os.path.exists(MASTER_TRACE_FILE):
            os.remove(MASTER_TRACE_FILE)
    
    def append_full_output(self, full_log: str, dl: int):
        """
        P3'ten gelen tam output'u master trace'e ekle.
        
        Her decision level icin tam cikti kaydedilir:
        - STATUS section
        - BCP EXECUTION LOG section
        - CURRENT VARIABLE STATE section
        
        Args:
            full_log: P3'ten gelen tam BCP output
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
        Sadece BCP Execution Log satirlarini ekle (geriye uyumluluk icin).
        
        Args:
            exec_log: BCP output dosyasindan raw log satirlari
        """
        if exec_log:
            with open(MASTER_TRACE_FILE, "a", encoding="utf-8") as f:
                for line in exec_log:
                    f.write(line + "\n")
    
    def log_decision(self, literal: int, dl: int):
        """
        P4'un yaptigil karar kaydet.
        
        Args:
            literal: Karar literali (pozitif veya negatif)
            dl: Decision level
        """
        with open(MASTER_TRACE_FILE, "a", encoding="utf-8") as f:
            f.write(f"\n--- P4 DECISION ---\n")
            f.write(f"TRIGGER_LITERAL: {literal}\n")
            f.write(f"DL: {dl}\n")
    
    def log_backtrack(self, from_dl: int):
        """
        Backtrack olayini logla.
        
        Args:
            from_dl: Backtrack yapilan decision level
        """
        with open(MASTER_TRACE_FILE, "a", encoding="utf-8") as f:
            f.write(f"\n--- BACKTRACK from DL {from_dl} ---\n")
    
    def get_trace_path(self) -> str:
        """Master trace dosyasinin yolunu dondur."""
        return MASTER_TRACE_FILE
    
    def read_trace(self) -> str:
        """Tum trace icerigini oku ve dondur."""
        if os.path.exists(MASTER_TRACE_FILE):
            with open(MASTER_TRACE_FILE, "r", encoding="utf-8") as f:
                return f.read()
        return "(Trace dosyasi bulunamadi)"


# ==============================================================================
# BAGIMSIZ FONKSIYONLAR (geriye uyumluluk icin)
# ==============================================================================

def write_bcp_trigger(trigger_lit: int, dl: int):
    """BCP trigger dosyasi yazmak icin bagimsiz fonksiyon."""
    io = IOManager()
    io.write_trigger(trigger_lit, dl)


def read_bcp_output() -> BCPResult:
    """BCP output okumak icin bagimsiz fonksiyon."""
    io = IOManager()
    return io.read_bcp_output()