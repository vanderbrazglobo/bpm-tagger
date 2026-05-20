#!/usr/bin/env python3
"""
bpm_tagger.py
Detecta BPM de arquivos MP3 com librosa e renomeia adicionando o BPM ao nome.
Preserva metadados ID3, ignora arquivos já processados e usa nomes seguros.

Uso:
    python bpm_tagger.py <pasta>          # processa pasta
    python bpm_tagger.py <pasta> --dry-run  # apenas simula, sem renomear

Dependências:
    pip install librosa mutagen soundfile
"""

import argparse
import logging
import os
import re
import sys
import types
from pathlib import Path

# ---------------------------------------------------------------------------
# Bloqueia numba antes de qualquer import do librosa.
# O librosa tenta importar numba para JIT; sem ele instalado, lança erro.
# Injetamos um módulo falso que satisfaz o import sem fazer nada.
# ---------------------------------------------------------------------------
def _mock_numba() -> None:
    fake = types.ModuleType("numba")
    fake.__version__ = "0.0.0"  # type: ignore[attr-defined]

    def _noop(*args, **kwargs):
        def decorator(fn):
            return fn
        return decorator

    fake.jit = _noop          # type: ignore[attr-defined]
    fake.njit = _noop         # type: ignore[attr-defined]
    fake.vectorize = _noop    # type: ignore[attr-defined]
    fake.guvectorize = _noop  # type: ignore[attr-defined]
    fake.stencil = _noop      # type: ignore[attr-defined]
    fake.extending = types.ModuleType("numba.extending")
    fake.core = types.ModuleType("numba.core")
    sys.modules["numba"] = fake
    sys.modules["numba.extending"] = fake.extending
    sys.modules["numba.core"] = fake.core
    os.environ["NUMBA_DISABLE_JIT"] = "1"

_mock_numba()

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("bpm_tagger")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def safe_filename(name: str) -> str:
    """Remove/substitui caracteres inválidos em nomes de arquivo (macOS/Linux)."""
    name = name.replace("/", "-").replace("\x00", "")
    name = re.sub(r'[\\:*?"<>|]', "_", name)
    name = name.strip(". ")
    return name or "unnamed"


def already_has_bpm(stem: str) -> bool:
    """Retorna True se o nome já contiver um padrão como _123BPM ou [123BPM]."""
    return bool(re.search(r'[_\[\s]?\d{2,3}BPM', stem, re.IGNORECASE))


def detect_bpm(path: Path) -> float | None:
    """Usa librosa para estimar o BPM do arquivo de áudio."""
    try:
        import librosa
        y, sr = librosa.load(str(path), sr=None, mono=True, duration=60)

        # librosa 0.11+ usa beat.beat_track com API atualizada;
        # usamos tempo_estimator direto para evitar dependência do numba mock
        onset_env = librosa.onset.onset_strength(y=y, sr=sr)
        tempo = librosa.feature.tempo(onset_envelope=onset_env, sr=sr)
        bpm = float(tempo[0]) if hasattr(tempo, "__len__") else float(tempo)
        return round(bpm)
    except Exception as exc:
        log.error("  ✗ Erro ao analisar %s: %s", path.name, exc)
        return None


def copy_id3_tags(src: Path, dst: Path) -> None:
    """Copia tags ID3 do arquivo original para o renomeado."""
    try:
        from mutagen import File as MutagenFile
        audio = MutagenFile(str(src), easy=False)
        if audio is None:
            return
        tags = audio.tags
        if tags is None:
            return
        dst_audio = MutagenFile(str(dst), easy=False)
        if dst_audio is None:
            return
        if dst_audio.tags is None:
            dst_audio.add_tags()
        dst_audio.tags.update(tags)
        dst_audio.save()
    except Exception as exc:
        log.warning("  ⚠ Não foi possível copiar tags de %s: %s", src.name, exc)


# ---------------------------------------------------------------------------
# Core
# ---------------------------------------------------------------------------

def process_folder(folder: Path, dry_run: bool = False) -> None:
    mp3_files = sorted(folder.glob("*.mp3")) + sorted(folder.glob("*.MP3"))
    # Deduplicar (case-insensitive em sistemas case-sensitive)
    seen: set[Path] = set()
    unique_files: list[Path] = []
    for f in mp3_files:
        if f not in seen:
            seen.add(f)
            unique_files.append(f)

    if not unique_files:
        log.warning("Nenhum arquivo MP3 encontrado em: %s", folder)
        return

    log.info("=" * 60)
    log.info("Pasta : %s", folder)
    log.info("Arquivos MP3 encontrados: %d", len(unique_files))
    log.info("Modo   : %s", "DRY-RUN (simulação)" if dry_run else "REAL")
    log.info("=" * 60)

    stats = {"ok": 0, "skip": 0, "error": 0}

    for mp3 in unique_files:
        stem = mp3.stem

        # --- Já processado? ---
        if already_has_bpm(stem):
            log.info("⏭  SKIP  %s  (BPM já no nome)", mp3.name)
            stats["skip"] += 1
            continue

        log.info("🔍  Analisando  %s …", mp3.name)
        bpm = detect_bpm(mp3)

        if bpm is None:
            stats["error"] += 1
            continue

        log.info("   BPM detectado: %d", bpm)

        # --- Montar novo nome ---
        new_stem = safe_filename(f"{stem}_{bpm}BPM")
        new_name = new_stem + ".mp3"
        new_path = mp3.parent / new_name

        # Evitar colisão
        counter = 1
        while new_path.exists() and new_path != mp3:
            new_stem_c = safe_filename(f"{stem}_{bpm}BPM_{counter}")
            new_path = mp3.parent / (new_stem_c + ".mp3")
            counter += 1

        if dry_run:
            log.info("   [DRY-RUN] %s  →  %s", mp3.name, new_path.name)
            stats["ok"] += 1
            continue

        # --- Renomear ---
        try:
            mp3.rename(new_path)
            log.info("   ✔ Renomeado: %s  →  %s", mp3.name, new_path.name)
            stats["ok"] += 1
        except OSError as exc:
            log.error("   ✗ Falha ao renomear %s: %s", mp3.name, exc)
            stats["error"] += 1

    log.info("=" * 60)
    log.info(
        "Concluído — ✔ %d renomeados | ⏭ %d ignorados | ✗ %d erros",
        stats["ok"], stats["skip"], stats["error"],
    )
    log.info("=" * 60)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Detecta BPM de MP3s e renomeia adicionando _<BPM>BPM ao nome.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("folder", help="Pasta com arquivos MP3")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simula a operação sem renomear nenhum arquivo",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Ativa log detalhado (DEBUG)",
    )
    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    folder = Path(args.folder).expanduser().resolve()
    if not folder.is_dir():
        log.error("Pasta não encontrada: %s", folder)
        sys.exit(1)

    # Verificar dependências
    missing = []
    for pkg in ("librosa", "mutagen"):
        try:
            __import__(pkg)
        except ImportError:
            missing.append(pkg)
    if missing:
        log.error(
            "Dependências ausentes: %s\n"
            "Instale com:  pip install %s",
            ", ".join(missing),
            " ".join(missing),
        )
        sys.exit(1)

    process_folder(folder, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
