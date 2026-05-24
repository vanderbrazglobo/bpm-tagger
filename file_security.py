"""
file_security.py
Módulo de validação e segurança de arquivos para o BPM Tagger.

Responsabilidades:
    - Bloquear extensões perigosas (.exe, .bat, .sh, .msi, etc.)
    - Detectar ZIPs suspeitos (com executáveis dentro)
    - Limitar tamanho máximo de arquivo (padrão: 300 MB)
    - Validar magic bytes (o arquivo é realmente áudio?)

Uso:
    from file_security import SecurityValidator, SecurityError

    validator = SecurityValidator()
    ok, reason = validator.validate(path)
    if not ok:
        raise SecurityError(reason)
"""

import struct
import zipfile
from pathlib import Path

# ── Configuração ─────────────────────────────────────────────────────────────
MAX_FILE_SIZE_MB = 300
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

# Extensões bloqueadas por serem executáveis ou potencialmente maliciosas
BLOCKED_EXTENSIONS = {
    ".exe", ".bat", ".cmd", ".com", ".msi", ".dll",
    ".sh",  ".ps1", ".vbs", ".js",  ".jar", ".py",
    ".scr", ".pif", ".reg", ".lnk", ".hta", ".wsf",
}

# Extensões de arquivo comprimido que serão inspecionadas internamente
ARCHIVE_EXTENSIONS = {".zip", ".7z", ".rar", ".tar", ".gz", ".bz2"}

# Magic bytes dos formatos de áudio suportados
# Formato: {extensão: [(offset, bytes_esperados), ...]}
AUDIO_MAGIC = {
    ".mp3":  [(0, b"\xff\xfb"), (0, b"\xff\xf3"), (0, b"\xff\xf2"),
              (0, b"ID3")],
    ".flac": [(0, b"fLaC")],
    ".wav":  [(0, b"RIFF")],
    ".aiff": [(0, b"FORM")],
    ".aif":  [(0, b"FORM")],
    ".ogg":  [(0, b"OggS")],
    ".m4a":  [(4, b"ftyp")],
}


class SecurityError(Exception):
    """Levantada quando um arquivo falha na validação de segurança."""
    pass


class SecurityValidator:
    """
    Valida arquivos antes de processamento.
    Instancie uma vez e reutilize para todos os arquivos da sessão.
    """

    def __init__(
        self,
        max_size_mb: int = MAX_FILE_SIZE_MB,
        check_magic: bool = True,
        check_zip_content: bool = True,
    ):
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.check_magic = check_magic
        self.check_zip_content = check_zip_content

    # ── API pública ──────────────────────────────────────────────────────────

    def validate(self, path: Path) -> tuple[bool, str]:
        """
        Valida um arquivo. Retorna (True, "") se seguro,
        ou (False, motivo) se bloqueado.
        """
        checks = [
            self._check_extension,
            self._check_size,
            self._check_zip_content_fn,
            self._check_magic_bytes,
        ]
        for check in checks:
            ok, reason = check(path)
            if not ok:
                return False, reason
        return True, ""

    # ── Verificações internas ────────────────────────────────────────────────

    def _check_extension(self, path: Path) -> tuple[bool, str]:
        """Bloqueia extensões perigosas."""
        ext = path.suffix.lower()
        if ext in BLOCKED_EXTENSIONS:
            return False, f"Extensão bloqueada por segurança: {ext}"
        return True, ""

    def _check_size(self, path: Path) -> tuple[bool, str]:
        """Bloqueia arquivos acima do limite de tamanho."""
        try:
            size = path.stat().st_size
        except OSError:
            return False, "Não foi possível verificar o tamanho do arquivo."
        if size > self.max_size_bytes:
            size_mb = size / (1024 * 1024)
            return False, (
                f"Arquivo muito grande: {size_mb:.1f} MB "
                f"(limite: {self.max_size_bytes // (1024*1024)} MB)"
            )
        return True, ""

    def _check_zip_content_fn(self, path: Path) -> tuple[bool, str]:
        """Inspeciona ZIPs em busca de executáveis internos."""
        if not self.check_zip_content:
            return True, ""
        ext = path.suffix.lower()
        if ext != ".zip":
            return True, ""
        try:
            with zipfile.ZipFile(path, "r") as zf:
                for name in zf.namelist():
                    inner_ext = Path(name).suffix.lower()
                    if inner_ext in BLOCKED_EXTENSIONS:
                        return False, (
                            f"ZIP suspeito: contém arquivo bloqueado internamente "
                            f"({Path(name).name})"
                        )
        except zipfile.BadZipFile:
            return False, "Arquivo ZIP corrompido ou inválido."
        except Exception as e:
            return False, f"Erro ao inspecionar ZIP: {e}"
        return True, ""

    def _check_magic_bytes(self, path: Path) -> tuple[bool, str]:
        """Valida que o arquivo é realmente áudio pelo conteúdo (magic bytes)."""
        if not self.check_magic:
            return True, ""
        ext = path.suffix.lower()
        signatures = AUDIO_MAGIC.get(ext)
        if not signatures:
            # Extensão sem assinatura conhecida — passa sem bloquear
            return True, ""
        try:
            with open(path, "rb") as fh:
                header = fh.read(16)
        except OSError as e:
            return False, f"Não foi possível ler o arquivo: {e}"

        for offset, magic in signatures:
            end = offset + len(magic)
            if len(header) >= end and header[offset:end] == magic:
                return True, ""

        return False, (
            f"Conteúdo não corresponde ao formato {ext.upper()}: "
            "o arquivo pode estar corrompido ou ser outro tipo disfarçado."
        )


# ── Utilitário de log amigável ───────────────────────────────────────────────

def security_summary(path: Path, reason: str) -> str:
    """Formata mensagem de bloqueio para exibição no log do app."""
    return f"🔒 BLOQUEADO  {path.name}\n   Motivo: {reason}"
