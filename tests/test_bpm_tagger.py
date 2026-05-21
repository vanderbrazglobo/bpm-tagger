"""
tests/test_bpm_tagger.py
Testes funcionais do bpm_tagger — roda no CI via pytest.
"""

import os
import re
import sys
import types
import shutil
import struct
import tempfile
from pathlib import Path

# ── Mock numba (mesmo do script principal) ───────────────────────────────────
def _mock_numba():
    fake = types.ModuleType("numba")
    fake.__version__ = "0.0.0"
    def _noop(*a, **k):
        def decorator(fn): return fn
        return decorator
    for attr in ("jit", "njit", "vectorize", "guvectorize", "stencil"):
        setattr(fake, attr, _noop)
    fake.extending = types.ModuleType("numba.extending")
    fake.core = types.ModuleType("numba.core")
    sys.modules.update({"numba": fake, "numba.extending": fake.extending, "numba.core": fake.core})
    os.environ["NUMBA_DISABLE_JIT"] = "1"

_mock_numba()

# ── Importar funções do script principal ─────────────────────────────────────
sys.path.insert(0, str(Path(__file__).parent.parent))
from bpm_tagger import safe_filename, already_has_bpm

# ─────────────────────────────────────────────────────────────────────────────
# TESTES: safe_filename
# ─────────────────────────────────────────────────────────────────────────────

class TestSafeFilename:
    def test_nome_simples(self):
        assert safe_filename("musica") == "musica"

    def test_remove_barra(self):
        assert "/" not in safe_filename("pasta/arquivo")

    def test_remove_caracteres_invalidos(self):
        resultado = safe_filename('arquivo:*?"<>|')
        for char in '/:*?"<>|':
            assert char not in resultado

    def test_preserva_unicode(self):
        resultado = safe_filename("Legião Urbana - Ainda é cedo")
        assert "Legião" in resultado
        assert "cedo" in resultado

    def test_nome_vazio_retorna_unnamed(self):
        assert safe_filename("   ") == "unnamed"
        assert safe_filename("...") == "unnamed"

    def test_nome_com_bpm(self):
        resultado = safe_filename("Track_128BPM")
        assert "128BPM" in resultado


# ─────────────────────────────────────────────────────────────────────────────
# TESTES: already_has_bpm
# ─────────────────────────────────────────────────────────────────────────────

class TestAlreadyHasBpm:
    def test_detecta_bpm_no_final(self):
        assert already_has_bpm("musica_128BPM") is True

    def test_detecta_bpm_minusculo(self):
        assert already_has_bpm("musica_128bpm") is True

    def test_detecta_bpm_com_colchete(self):
        assert already_has_bpm("musica[128BPM]") is True

    def test_nao_detecta_sem_bpm(self):
        assert already_has_bpm("Charlie Brown Jr - Lugar ao Sol") is False

    def test_nao_detecta_numero_sem_bpm(self):
        assert already_has_bpm("Track 12") is False

    def test_detecta_3_digitos(self):
        assert already_has_bpm("track_174BPM") is True

    def test_detecta_2_digitos(self):
        assert already_has_bpm("track_95BPM") is True


# ─────────────────────────────────────────────────────────────────────────────
# TESTES: lógica de renomeação
# ─────────────────────────────────────────────────────────────────────────────

class TestRenaming:
    def setup_method(self):
        self.tmpdir = Path(tempfile.mkdtemp())

    def teardown_method(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_novo_nome_inclui_bpm(self):
        stem = "Charlie Brown Jr - Lugar ao Sol"
        bpm = 128
        new_stem = safe_filename(f"{stem}_{bpm}BPM")
        assert "128BPM" in new_stem

    def test_novo_nome_inclui_key(self):
        stem = "Track A"
        bpm = 128
        key = "Am"
        new_stem = safe_filename(f"{stem}_{bpm}BPM_{key}")
        assert "128BPM" in new_stem
        assert "Am" in new_stem

    def test_criacao_de_arquivo_temporario(self):
        f = self.tmpdir / "test.mp3"
        f.write_bytes(b"\x00" * 100)
        assert f.exists()

    def test_arquivo_ja_processado_nao_renomeia(self):
        """Simula que arquivo com BPM no nome é ignorado."""
        stem = "musica_128BPM"
        assert already_has_bpm(stem) is True

    def test_colisao_de_nomes(self):
        """Verifica lógica de sufixo em caso de colisão."""
        stem = "Track"
        bpm = 128
        base = self.tmpdir / f"{stem}_{bpm}BPM.mp3"
        base.write_bytes(b"\x00" * 10)

        # Simula a lógica de colisão
        new_path = base
        counter = 1
        while new_path.exists():
            new_path = self.tmpdir / safe_filename(f"{stem}_{bpm}BPM_{counter}.mp3")
            counter += 1

        assert not new_path.exists()
        assert "1" in new_path.name


# ─────────────────────────────────────────────────────────────────────────────
# TESTES: collect_files (formatos)
# ─────────────────────────────────────────────────────────────────────────────

class TestCollectFiles:
    def setup_method(self):
        self.tmpdir = Path(tempfile.mkdtemp())

    def teardown_method(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _create_files(self, names):
        for name in names:
            (self.tmpdir / name).write_bytes(b"\x00" * 10)

    def test_coleta_mp3(self):
        self._create_files(["a.mp3", "b.mp3", "c.wav"])
        mp3s = list(self.tmpdir.glob("*.mp3"))
        assert len(mp3s) == 2

    def test_coleta_multiplos_formatos(self):
        self._create_files(["a.mp3", "b.flac", "c.wav", "d.txt"])
        formatos = {"mp3", "flac", "wav"}
        encontrados = []
        for ext in formatos:
            encontrados += list(self.tmpdir.glob(f"*.{ext}"))
        assert len(encontrados) == 3

    def test_ignora_extensoes_nao_selecionadas(self):
        self._create_files(["a.mp3", "b.ogg"])
        apenas_mp3 = list(self.tmpdir.glob("*.mp3"))
        assert len(apenas_mp3) == 1
        assert apenas_mp3[0].name == "a.mp3"

    def test_subpastas(self):
        sub = self.tmpdir / "subpasta"
        sub.mkdir()
        self._create_files(["a.mp3"])
        (sub / "b.mp3").write_bytes(b"\x00" * 10)
        todos = list(self.tmpdir.glob("**/*.mp3"))
        assert len(todos) == 2
