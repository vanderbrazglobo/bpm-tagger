#!/usr/bin/env python3
"""
bpm_tagger_app.py
App desktop com interface gráfica para detectar BPM, tom musical,
processar subpastas, exportar CSV e suporte a múltiplos formatos de áudio.

Dependências:
    pip install customtkinter librosa mutagen soundfile cffi audioread
"""

import csv
import os
import re
import sys
import types
import threading
from datetime import datetime
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

try:
    import customtkinter as ctk
except ImportError:
    print("CustomTkinter não encontrado. Instale com: pip install customtkinter")
    sys.exit(1)

import tkinter as tk
from tkinter import filedialog, messagebox

# ── Constantes ───────────────────────────────────────────────────────────────
SUPPORTED_FORMATS = {
    "mp3":  "MP3",
    "flac": "FLAC",
    "wav":  "WAV",
    "aiff": "AIFF",
    "aif":  "AIFF",
    "ogg":  "OGG",
    "m4a":  "M4A",
}

KEY_NAMES = ["C", "C#", "D", "D#", "E", "F",
             "F#", "G", "G#", "A", "A#", "B"]

# ── Helpers de áudio ─────────────────────────────────────────────────────────
def safe_filename(name: str) -> str:
    name = name.replace("/", "-").replace("\x00", "")
    name = re.sub(r'[\\:*?"<>|]', "_", name)
    return name.strip(". ") or "unnamed"

def already_processed(stem: str) -> bool:
    return bool(re.search(r'[_\[\s]?\d{2,3}BPM', stem, re.IGNORECASE))

def detect_bpm_and_key(path: Path, detect_key: bool = False):
    import librosa
    import numpy as np
    y, sr = librosa.load(str(path), sr=None, mono=True, duration=60)
    onset_env = librosa.onset.onset_strength(y=y, sr=sr)
    tempo = librosa.feature.tempo(onset_envelope=onset_env, sr=sr)
    bpm = round(float(tempo[0]) if hasattr(tempo, "__len__") else float(tempo))

    key = None
    if detect_key:
        chroma = librosa.feature.chroma_cqt(y=y, sr=sr)
        chroma_mean = np.mean(chroma, axis=1)
        key_idx = int(np.argmax(chroma_mean))
        key = KEY_NAMES[key_idx]

    return bpm, key

def copy_tags(src: Path, dst: Path):
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

def collect_files(folder: Path, formats: set, subfolders: bool) -> list:
    files = []
    pattern = "**/*" if subfolders else "*"
    for ext in formats:
        files += list(folder.glob(f"{pattern}.{ext}"))
        files += list(folder.glob(f"{pattern}.{ext.upper()}"))
    return sorted(set(files))

# ── App ──────────────────────────────────────────────────────────────────────
class BPMTaggerApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.title("BPM Tagger")
        self.geometry("820x740")
        self.minsize(720, 600)
        self.resizable(True, True)

        # Estado
        self.folder_path = tk.StringVar()
        self.dry_run      = tk.BooleanVar(value=True)
        self.opt_key      = tk.BooleanVar(value=False)
        self.opt_sub      = tk.BooleanVar(value=False)
        self.opt_csv      = tk.BooleanVar(value=False)
        self.fmt_mp3      = tk.BooleanVar(value=True)
        self.fmt_flac     = tk.BooleanVar(value=False)
        self.fmt_wav      = tk.BooleanVar(value=False)
        self.fmt_aiff     = tk.BooleanVar(value=False)
        self.fmt_ogg      = tk.BooleanVar(value=False)
        self.fmt_m4a      = tk.BooleanVar(value=False)
        self.is_running   = False
        self._csv_rows    = []

        self._build_ui()

    # ── UI ───────────────────────────────────────────────────────────────────
    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)

        # Header
        header = ctk.CTkFrame(self, fg_color=("#1a1a2e", "#0f0f1a"), corner_radius=0)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(header, text="🎵  BPM Tagger",
            font=ctk.CTkFont(family="Georgia", size=28, weight="bold"),
            text_color="#4f9cf9"
        ).grid(row=0, column=0, padx=30, pady=(20, 4), sticky="w")

        ctk.CTkLabel(header,
            text="Detecta BPM, tom musical e renomeia seus arquivos de áudio",
            font=ctk.CTkFont(size=13), text_color="#8896a5"
        ).grid(row=1, column=0, padx=30, pady=(0, 18), sticky="w")

        # ── Pasta ────────────────────────────────────────────────────────────
        folder_frame = ctk.CTkFrame(self, fg_color=("#1e1e2e", "#16162a"), corner_radius=12)
        folder_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=(16, 6))
        folder_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(folder_frame, text="Pasta de áudio",
            font=ctk.CTkFont(size=13, weight="bold"), text_color="#c0cfe0"
        ).grid(row=0, column=0, columnspan=3, padx=20, pady=(14, 6), sticky="w")

        self.folder_entry = ctk.CTkEntry(folder_frame,
            textvariable=self.folder_path,
            placeholder_text="Selecione ou cole o caminho da pasta...",
            height=40, font=ctk.CTkFont(size=12),
            fg_color=("#12121f","#12121f"), border_color="#2d3a4a", text_color="#e0eaf5"
        )
        self.folder_entry.grid(row=1, column=0, columnspan=2, padx=(20,8), pady=(0,14), sticky="ew")

        ctk.CTkButton(folder_frame, text="📂  Selecionar", width=130, height=40,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#2563eb", hover_color="#1d4ed8",
            command=self._browse_folder
        ).grid(row=1, column=2, padx=(0,20), pady=(0,14))

        # ── Opções ───────────────────────────────────────────────────────────
        opts_frame = ctk.CTkFrame(self, fg_color=("#1e1e2e","#16162a"), corner_radius=12)
        opts_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=(0, 6))
        opts_frame.grid_columnconfigure((0,1), weight=1)

        # Coluna esquerda — Funcionalidades
        left = ctk.CTkFrame(opts_frame, fg_color="transparent")
        left.grid(row=0, column=0, padx=(20,10), pady=14, sticky="nw")

        ctk.CTkLabel(left, text="Funcionalidades",
            font=ctk.CTkFont(size=12, weight="bold"), text_color="#818cf8"
        ).grid(row=0, column=0, sticky="w", pady=(0,8))

        switches = [
            (self.dry_run,  "🔍  Modo simulação (dry-run)",        "#f59e0b", "#d97706"),
            (self.opt_key,  "🎼  Detectar tom musical (key)",       "#a78bfa", "#7c3aed"),
            (self.opt_sub,  "📁  Processar subpastas",              "#34d399", "#059669"),
            (self.opt_csv,  "📊  Exportar relatório CSV",           "#60a5fa", "#2563eb"),
        ]
        for i, (var, label, prog, btn) in enumerate(switches):
            ctk.CTkSwitch(left, text=label, variable=var,
                font=ctk.CTkFont(size=12), text_color="#a0b0c0",
                progress_color=prog, button_color=btn
            ).grid(row=i+1, column=0, sticky="w", pady=4)

        # Separador vertical
        ctk.CTkFrame(opts_frame, width=1, fg_color="#2d3a4a"
        ).grid(row=0, column=0, sticky="nse", padx=(0,0), pady=14)

        # Coluna direita — Formatos
        right = ctk.CTkFrame(opts_frame, fg_color="transparent")
        right.grid(row=0, column=1, padx=(10,20), pady=14, sticky="nw")

        ctk.CTkLabel(right, text="Formatos suportados",
            font=ctk.CTkFont(size=12, weight="bold"), text_color="#818cf8"
        ).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0,8))

        formats = [
            (self.fmt_mp3,  "MP3"),
            (self.fmt_flac, "FLAC"),
            (self.fmt_wav,  "WAV"),
            (self.fmt_aiff, "AIFF"),
            (self.fmt_ogg,  "OGG"),
            (self.fmt_m4a,  "M4A"),
        ]
        for i, (var, label) in enumerate(formats):
            row, col = divmod(i, 2)
            ctk.CTkCheckBox(right, text=label, variable=var,
                font=ctk.CTkFont(size=12), text_color="#a0b0c0",
                fg_color="#2563eb", hover_color="#1d4ed8",
                checkmark_color="#ffffff"
            ).grid(row=row+1, column=col, sticky="w", padx=(0,20), pady=3)

        # Botão Iniciar
        self.run_btn = ctk.CTkButton(opts_frame,
            text="▶  Iniciar Varredura", width=200, height=44,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#059669", hover_color="#047857",
            command=self._start
        )
        self.run_btn.grid(row=1, column=0, columnspan=2, pady=(0,16))

        # ── Log ──────────────────────────────────────────────────────────────
        log_frame = ctk.CTkFrame(self, fg_color=("#1e1e2e","#16162a"), corner_radius=12)
        log_frame.grid(row=3, column=0, sticky="nsew", padx=20, pady=(0,8))
        log_frame.grid_rowconfigure(1, weight=1)
        log_frame.grid_columnconfigure(0, weight=1)

        log_hdr = ctk.CTkFrame(log_frame, fg_color="transparent")
        log_hdr.grid(row=0, column=0, sticky="ew", padx=16, pady=(12,6))
        log_hdr.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(log_hdr, text="Log de execução",
            font=ctk.CTkFont(size=13, weight="bold"), text_color="#c0cfe0"
        ).grid(row=0, column=0, sticky="w")

        ctk.CTkButton(log_hdr, text="Limpar", width=70, height=26,
            font=ctk.CTkFont(size=11), fg_color="#2d3a4a", hover_color="#374151",
            command=self._clear_log
        ).grid(row=0, column=1, sticky="e")

        self.log_box = ctk.CTkTextbox(log_frame,
            font=ctk.CTkFont(family="Courier New", size=12),
            fg_color=("#12121f","#12121f"), text_color="#c8d8e8",
            border_color="#2d3a4a", border_width=1,
            wrap="word", state="disabled"
        )
        self.log_box.grid(row=1, column=0, sticky="nsew", padx=16, pady=(0,12))

        # Status bar
        self.status_bar = ctk.CTkFrame(self, fg_color=("#12121f","#0a0a14"), height=32, corner_radius=0)
        self.status_bar.grid(row=4, column=0, sticky="ew")
        self.status_bar.grid_columnconfigure(0, weight=1)

        self.status_label = ctk.CTkLabel(self.status_bar,
            text="Pronto. Selecione uma pasta para começar.",
            font=ctk.CTkFont(size=11), text_color="#4a5a6a"
        )
        self.status_label.grid(row=0, column=0, padx=16, sticky="w")

        self.stats_label = ctk.CTkLabel(self.status_bar, text="",
            font=ctk.CTkFont(size=11), text_color="#4a5a6a"
        )
        self.stats_label.grid(row=0, column=1, padx=16, sticky="e")

    # ── Ações ────────────────────────────────────────────────────────────────
    def _browse_folder(self):
        path = filedialog.askdirectory(title="Selecione a pasta com os arquivos de áudio")
        if path:
            self.folder_path.set(path)
            self._set_status(f"Pasta: {path}")

    def _clear_log(self):
        self.log_box.configure(state="normal")
        self.log_box.delete("1.0", "end")
        self.log_box.configure(state="disabled")
        self.stats_label.configure(text="")

    def _set_status(self, msg):
        self.status_label.configure(text=msg)

    def _log(self, msg, tag="info"):
        colors = {
            "ok":    "#34d399",
            "error": "#f87171",
            "skip":  "#60a5fa",
            "bpm":   "#fbbf24",
            "key":   "#c084fc",
            "info":  "#c8d8e8",
            "sep":   "#2d3a4a",
            "head":  "#818cf8",
            "csv":   "#34d399",
        }
        self.log_box.configure(state="normal")
        self.log_box.insert("end", msg + "\n")
        line_start = self.log_box.index("end-2l linestart")
        line_end   = self.log_box.index("end-1l lineend")
        self.log_box.tag_add(tag, line_start, line_end)
        self.log_box.tag_config(tag, foreground=colors.get(tag, colors["info"]))
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

        # Pelo menos um formato selecionado
        selected_fmts = self._get_formats()
        if not selected_fmts:
            messagebox.showwarning("Atenção", "Selecione pelo menos um formato de áudio.")
            return

        if self.is_running:
            return

        self.is_running = True
        self._csv_rows = []
        self.run_btn.configure(state="disabled", text="⏳  Processando...")
        self._clear_log()
        threading.Thread(target=self._process, args=(folder,), daemon=True).start()

    def _get_formats(self) -> set:
        fmts = set()
        mapping = [
            (self.fmt_mp3,  {"mp3"}),
            (self.fmt_flac, {"flac"}),
            (self.fmt_wav,  {"wav"}),
            (self.fmt_aiff, {"aiff", "aif"}),
            (self.fmt_ogg,  {"ogg"}),
            (self.fmt_m4a,  {"m4a"}),
        ]
        for var, exts in mapping:
            if var.get():
                fmts |= exts
        return fmts

    def _process(self, folder_str):
        folder      = Path(folder_str)
        dry         = self.dry_run.get()
        do_key      = self.opt_key.get()
        do_sub      = self.opt_sub.get()
        do_csv      = self.opt_csv.get()
        formats     = self._get_formats()
        mode        = "DRY-RUN (simulação)" if dry else "REAL — arquivos serão renomeados"

        self._log("━" * 64, "sep")
        self._log(f"  Pasta    : {folder}", "head")
        self._log(f"  Modo     : {mode}", "head")
        self._log(f"  Formatos : {', '.join(sorted(formats)).upper()}", "head")
        self._log(f"  Tom      : {'Sim' if do_key else 'Não'}  |  "
                  f"Subpastas: {'Sim' if do_sub else 'Não'}  |  "
                  f"CSV: {'Sim' if do_csv else 'Não'}", "head")
        self._log("━" * 64, "sep")

        files = collect_files(folder, formats, do_sub)

        if not files:
            self._log("  Nenhum arquivo encontrado nos formatos selecionados.", "error")
            self._finish(0, 0, 0, dry, folder, do_csv)
            return

        self._log(f"  {len(files)} arquivo(s) encontrado(s)\n", "info")
        self.after(0, lambda: self._set_status(f"Processando {len(files)} arquivo(s)..."))

        ok = skip = error = 0

        for f in files:
            stem = f.stem
            ext  = f.suffix.lower()

            if already_processed(stem):
                self._log(f"⏭  SKIP   {f.name}", "skip")
                skip += 1
                continue

            self._log(f"🔍  {f.name}", "info")
            self.after(0, lambda n=f.name: self._set_status(f"Analisando: {n}"))

            try:
                bpm, key = detect_bpm_and_key(f, detect_key=do_key)
            except Exception as e:
                self._log(f"   ✗ Erro: {e}", "error")
                error += 1
                continue

            self._log(f"   BPM: {bpm}", "bpm")
            if do_key and key:
                self._log(f"   Tom: {key}", "key")

            # Montar novo nome
            suffix = f"_{bpm}BPM"
            if do_key and key:
                suffix += f"_{key}"
            new_stem = safe_filename(f"{stem}{suffix}")
            new_path = f.parent / (new_stem + ext)

            counter = 1
            while new_path.exists() and new_path != f:
                new_path = f.parent / (safe_filename(f"{stem}{suffix}_{counter}") + ext)
                counter += 1

            # CSV row
            if do_csv:
                self._csv_rows.append({
                    "arquivo_original": f.name,
                    "arquivo_novo": new_path.name if not dry else f"{new_stem}{ext} [simulação]",
                    "bpm": bpm,
                    "tom": key or "",
                    "formato": ext.lstrip(".").upper(),
                    "pasta": str(f.parent),
                })

            if dry:
                self._log(f"   → {new_path.name}  [simulação]", "skip")
                ok += 1
                continue

            try:
                f.rename(new_path)
                copy_tags(f, new_path)
                self._log(f"   ✔ Renomeado → {new_path.name}", "ok")
                ok += 1
            except OSError as e:
                self._log(f"   ✗ Falha: {e}", "error")
                error += 1

        self._finish(ok, skip, error, dry, folder, do_csv)

    def _finish(self, ok, skip, error, dry, folder=None, do_csv=False):
        self._log("\n" + "━" * 64, "sep")
        self._log(
            f"  Concluído —  ✔ {ok} {'simulados' if dry else 'renomeados'}  "
            f"⏭ {skip} ignorados  ✗ {error} erros",
            "ok" if error == 0 else "error"
        )
        self._log("━" * 64, "sep")

        self.after(0, lambda: self.run_btn.configure(state="normal", text="▶  Iniciar Varredura"))
        self.after(0, lambda: self._set_status("Pronto."))
        self.after(0, lambda: self.stats_label.configure(text=f"✔ {ok}  ⏭ {skip}  ✗ {error}"))
        self.is_running = False

        # Exportar CSV — abre diálogo na thread principal após liberar botão
        if do_csv and self._csv_rows:
            self.after(200, lambda: self._save_csv(folder))

    def _save_csv(self, folder=None):
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_name = f"bpm_report_{ts}.csv"
        chosen = filedialog.asksaveasfilename(
            title="Salvar relatório CSV",
            initialfile=default_name,
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("Todos os arquivos", "*.*")],
            initialdir=str(folder) if folder else str(Path.home())
        )
        if chosen:
            try:
                with open(chosen, "w", newline="", encoding="utf-8") as fh:
                    writer = csv.DictWriter(fh, fieldnames=[
                        "arquivo_original", "arquivo_novo", "bpm", "tom", "formato", "pasta"
                    ])
                    writer.writeheader()
                    writer.writerows(self._csv_rows)
                self._log(f"  📊 CSV salvo → {chosen}", "csv")
                self._set_status(f"CSV salvo: {chosen}")
            except Exception as e:
                self._log(f"  ✗ Erro ao salvar CSV: {e}", "error")
        else:
            self._log("  ⚠ Exportação CSV cancelada.", "skip")


# ── Main ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = BPMTaggerApp()
    app.mainloop()
