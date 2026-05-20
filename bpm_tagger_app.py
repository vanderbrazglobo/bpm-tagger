#!/usr/bin/env python3
"""
bpm_tagger_app.py
App desktop com interface gráfica para detectar BPM e renomear arquivos MP3.

Dependências:
    pip install customtkinter librosa mutagen soundfile cffi audioread
"""

import os
import re
import sys
import types
import threading
from pathlib import Path

# ── Bloqueia numba antes do librosa ─────────────────────────────────────────
def _mock_numba():
    fake = types.ModuleType("numba")
    fake.__version__ = "0.0.0"
    def _noop(*a, **k):
        def decorator(fn): return fn
        return decorator
    fake.jit = _noop
    fake.njit = _noop
    fake.vectorize = _noop
    fake.guvectorize = _noop
    fake.stencil = _noop
    fake.extending = types.ModuleType("numba.extending")
    fake.core = types.ModuleType("numba.core")
    sys.modules["numba"] = fake
    sys.modules["numba.extending"] = fake.extending
    sys.modules["numba.core"] = fake.core
    os.environ["NUMBA_DISABLE_JIT"] = "1"

_mock_numba()

# ── Imports principais ───────────────────────────────────────────────────────
try:
    import customtkinter as ctk
except ImportError:
    print("CustomTkinter não encontrado. Instale com: pip install customtkinter")
    sys.exit(1)

import tkinter as tk
from tkinter import filedialog, messagebox

# ── Helpers de BPM ──────────────────────────────────────────────────────────
def safe_filename(name: str) -> str:
    name = name.replace("/", "-").replace("\x00", "")
    name = re.sub(r'[\\:*?"<>|]', "_", name)
    return name.strip(". ") or "unnamed"

def already_has_bpm(stem: str) -> bool:
    return bool(re.search(r'[_\[\s]?\d{2,3}BPM', stem, re.IGNORECASE))

def detect_bpm(path: Path):
    import librosa
    y, sr = librosa.load(str(path), sr=None, mono=True, duration=60)
    onset_env = librosa.onset.onset_strength(y=y, sr=sr)
    tempo = librosa.feature.tempo(onset_envelope=onset_env, sr=sr)
    bpm = float(tempo[0]) if hasattr(tempo, "__len__") else float(tempo)
    return round(bpm)

def copy_id3_tags(src: Path, dst: Path):
    try:
        from mutagen import File as MutagenFile
        audio = MutagenFile(str(src), easy=False)
        if not audio or not audio.tags:
            return
        dst_audio = MutagenFile(str(dst), easy=False)
        if not dst_audio:
            return
        if not dst_audio.tags:
            dst_audio.add_tags()
        dst_audio.tags.update(audio.tags)
        dst_audio.save()
    except Exception:
        pass

# ── App ──────────────────────────────────────────────────────────────────────
class BPMTaggerApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Aparência
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.title("BPM Tagger")
        self.geometry("780x620")
        self.minsize(680, 520)
        self.resizable(True, True)

        # Estado
        self.folder_path = tk.StringVar()
        self.dry_run = tk.BooleanVar(value=True)
        self.is_running = False

        self._build_ui()

    # ── UI ───────────────────────────────────────────────────────────────────
    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # ── Header ──────────────────────────────────────────────────────────
        header = ctk.CTkFrame(self, fg_color=("#1a1a2e", "#0f0f1a"), corner_radius=0)
        header.grid(row=0, column=0, sticky="ew", padx=0, pady=0)
        header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            header,
            text="🎵  BPM Tagger",
            font=ctk.CTkFont(family="Georgia", size=28, weight="bold"),
            text_color="#4f9cf9"
        ).grid(row=0, column=0, padx=30, pady=(20, 4), sticky="w")

        ctk.CTkLabel(
            header,
            text="Detecta BPM e renomeia seus arquivos MP3 automaticamente",
            font=ctk.CTkFont(size=13),
            text_color="#8896a5"
        ).grid(row=1, column=0, padx=30, pady=(0, 18), sticky="w")

        # ── Painel de controles ──────────────────────────────────────────────
        controls = ctk.CTkFrame(self, fg_color=("#1e1e2e", "#16162a"), corner_radius=12)
        controls.grid(row=1, column=0, sticky="ew", padx=20, pady=(16, 8))
        controls.grid_columnconfigure(1, weight=1)

        # Seleção de pasta
        ctk.CTkLabel(
            controls,
            text="Pasta com MP3s",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#c0cfe0"
        ).grid(row=0, column=0, columnspan=3, padx=20, pady=(16, 6), sticky="w")

        self.folder_entry = ctk.CTkEntry(
            controls,
            textvariable=self.folder_path,
            placeholder_text="Clique em 'Selecionar Pasta' ou cole o caminho aqui...",
            height=40,
            font=ctk.CTkFont(size=12),
            fg_color=("#12121f", "#12121f"),
            border_color="#2d3a4a",
            text_color="#e0eaf5"
        )
        self.folder_entry.grid(row=1, column=0, columnspan=2, padx=(20, 8), pady=(0, 16), sticky="ew")

        ctk.CTkButton(
            controls,
            text="📂  Selecionar",
            width=130,
            height=40,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#2563eb",
            hover_color="#1d4ed8",
            command=self._browse_folder
        ).grid(row=1, column=2, padx=(0, 20), pady=(0, 16))

        # Separador
        sep = ctk.CTkFrame(controls, height=1, fg_color="#2d3a4a")
        sep.grid(row=2, column=0, columnspan=3, sticky="ew", padx=20, pady=(0, 12))

        # Opções
        opts_frame = ctk.CTkFrame(controls, fg_color="transparent")
        opts_frame.grid(row=3, column=0, columnspan=3, padx=20, pady=(0, 16), sticky="ew")
        opts_frame.grid_columnconfigure(1, weight=1)

        self.dry_run_switch = ctk.CTkSwitch(
            opts_frame,
            text="Modo simulação  (dry-run — não renomeia, só mostra o preview)",
            variable=self.dry_run,
            font=ctk.CTkFont(size=12),
            text_color="#8896a5",
            progress_color="#f59e0b",
            button_color="#d97706",
        )
        self.dry_run_switch.grid(row=0, column=0, sticky="w")

        self.run_btn = ctk.CTkButton(
            opts_frame,
            text="▶  Iniciar Varredura",
            width=180,
            height=40,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#059669",
            hover_color="#047857",
            command=self._start
        )
        self.run_btn.grid(row=0, column=1, sticky="e")

        # ── Log ──────────────────────────────────────────────────────────────
        log_frame = ctk.CTkFrame(self, fg_color=("#1e1e2e", "#16162a"), corner_radius=12)
        log_frame.grid(row=2, column=0, sticky="nsew", padx=20, pady=(0, 8))
        log_frame.grid_rowconfigure(1, weight=1)
        log_frame.grid_columnconfigure(0, weight=1)

        log_header = ctk.CTkFrame(log_frame, fg_color="transparent")
        log_header.grid(row=0, column=0, sticky="ew", padx=16, pady=(12, 6))
        log_header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            log_header,
            text="Log de execução",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#c0cfe0"
        ).grid(row=0, column=0, sticky="w")

        ctk.CTkButton(
            log_header,
            text="Limpar",
            width=70,
            height=26,
            font=ctk.CTkFont(size=11),
            fg_color="#2d3a4a",
            hover_color="#374151",
            command=self._clear_log
        ).grid(row=0, column=1, sticky="e")

        self.log_box = ctk.CTkTextbox(
            log_frame,
            font=ctk.CTkFont(family="Courier New", size=12),
            fg_color=("#12121f", "#12121f"),
            text_color="#c8d8e8",
            border_color="#2d3a4a",
            border_width=1,
            wrap="word",
            state="disabled"
        )
        self.log_box.grid(row=1, column=0, sticky="nsew", padx=16, pady=(0, 12))

        # ── Status bar ───────────────────────────────────────────────────────
        self.status_bar = ctk.CTkFrame(self, fg_color=("#12121f", "#0a0a14"), height=32, corner_radius=0)
        self.status_bar.grid(row=3, column=0, sticky="ew")
        self.status_bar.grid_columnconfigure(0, weight=1)

        self.status_label = ctk.CTkLabel(
            self.status_bar,
            text="Pronto. Selecione uma pasta para começar.",
            font=ctk.CTkFont(size=11),
            text_color="#4a5a6a"
        )
        self.status_label.grid(row=0, column=0, padx=16, sticky="w")

        self.stats_label = ctk.CTkLabel(
            self.status_bar,
            text="",
            font=ctk.CTkFont(size=11),
            text_color="#4a5a6a"
        )
        self.stats_label.grid(row=0, column=1, padx=16, sticky="e")

    # ── Ações ────────────────────────────────────────────────────────────────
    def _browse_folder(self):
        path = filedialog.askdirectory(title="Selecione a pasta com os arquivos MP3")
        if path:
            self.folder_path.set(path)
            self._set_status(f"Pasta selecionada: {path}")

    def _clear_log(self):
        self.log_box.configure(state="normal")
        self.log_box.delete("1.0", "end")
        self.log_box.configure(state="disabled")
        self.stats_label.configure(text="")

    def _set_status(self, msg):
        self.status_label.configure(text=msg)

    def _log(self, msg, tag=None):
        colors = {
            "ok":    "#34d399",
            "error": "#f87171",
            "skip":  "#60a5fa",
            "bpm":   "#fbbf24",
            "info":  "#c8d8e8",
            "sep":   "#2d3a4a",
            "head":  "#818cf8",
        }
        self.log_box.configure(state="normal")
        self.log_box.insert("end", msg + "\n")

        # Colorir última linha
        line_start = self.log_box.index("end-2l linestart")
        line_end   = self.log_box.index("end-1l lineend")
        color = colors.get(tag, colors["info"])
        self.log_box.tag_add(tag or "info", line_start, line_end)
        self.log_box.tag_config(tag or "info", foreground=color)

        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    def _start(self):
        folder = self.folder_path.get().strip()
        if not folder:
            messagebox.showwarning("Atenção", "Selecione uma pasta primeiro.")
            return
        if not Path(folder).is_dir():
            messagebox.showerror("Erro", f"Pasta não encontrada:\n{folder}")
            return
        if self.is_running:
            return

        self.is_running = True
        self.run_btn.configure(state="disabled", text="⏳  Processando...")
        self._clear_log()
        threading.Thread(target=self._process, args=(folder,), daemon=True).start()

    def _process(self, folder_str):
        folder = Path(folder_str)
        dry = self.dry_run.get()
        mode = "DRY-RUN (simulação)" if dry else "REAL — arquivos serão renomeados"

        self._log("━" * 62, "sep")
        self._log(f"  Pasta  : {folder}", "head")
        self._log(f"  Modo   : {mode}", "head")
        self._log("━" * 62, "sep")

        mp3_files = sorted(set(list(folder.glob("*.mp3")) + list(folder.glob("*.MP3"))))

        if not mp3_files:
            self._log("  Nenhum arquivo MP3 encontrado.", "error")
            self._finish(0, 0, 0)
            return

        self._log(f"  {len(mp3_files)} arquivo(s) encontrado(s)\n", "info")
        self.after(0, lambda: self._set_status(f"Processando {len(mp3_files)} arquivo(s)..."))

        ok = skip = error = 0

        for mp3 in mp3_files:
            stem = mp3.stem

            if already_has_bpm(stem):
                self._log(f"⏭  SKIP   {mp3.name}", "skip")
                skip += 1
                continue

            self._log(f"🔍  {mp3.name}", "info")
            self.after(0, lambda n=mp3.name: self._set_status(f"Analisando: {n}"))

            try:
                bpm = detect_bpm(mp3)
            except Exception as e:
                self._log(f"   ✗ Erro: {e}", "error")
                error += 1
                continue

            self._log(f"   BPM detectado: {bpm}", "bpm")

            new_stem = safe_filename(f"{stem}_{bpm}BPM")
            new_path = mp3.parent / (new_stem + ".mp3")

            counter = 1
            while new_path.exists() and new_path != mp3:
                new_path = mp3.parent / (safe_filename(f"{stem}_{bpm}BPM_{counter}") + ".mp3")
                counter += 1

            if dry:
                self._log(f"   → {new_path.name}  [simulação]", "skip")
                ok += 1
                continue

            try:
                mp3.rename(new_path)
                copy_id3_tags(mp3, new_path)
                self._log(f"   ✔ Renomeado → {new_path.name}", "ok")
                ok += 1
            except OSError as e:
                self._log(f"   ✗ Falha: {e}", "error")
                error += 1

        self._finish(ok, skip, error, dry)

    def _finish(self, ok, skip, error, dry=False):
        self._log("\n" + "━" * 62, "sep")
        self._log(
            f"  Concluído —  ✔ {ok} {'simulados' if dry else 'renomeados'}  "
            f"⏭ {skip} ignorados  ✗ {error} erros",
            "ok" if error == 0 else "error"
        )
        self._log("━" * 62, "sep")

        self.after(0, lambda: self.run_btn.configure(state="normal", text="▶  Iniciar Varredura"))
        self.after(0, lambda: self._set_status("Pronto."))
        self.after(0, lambda: self.stats_label.configure(
            text=f"✔ {ok}  ⏭ {skip}  ✗ {error}"
        ))
        self.is_running = False


# ── Main ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = BPMTaggerApp()
    app.mainloop()
