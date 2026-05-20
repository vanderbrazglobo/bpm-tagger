# 🎵 BPM Tagger

Detecta BPM de arquivos MP3 e renomeia adicionando o BPM ao nome.
Disponível em dois modos: script de terminal e app desktop com interface gráfica.

## Requisitos

- Python 3.11 (python.org — não use o Homebrew)
- macOS

## Instalação

### 1. Instale o Python 3.11
Baixe em: https://www.python.org/downloads/release/python-31110/
Use o instalador: macOS 64-bit universal2 installer

### 2. Crie o ambiente virtual
```
/Library/Frameworks/Python.framework/Versions/3.11/bin/python3.11 -m venv ~/envs/bpm
```

### 3. Ative o ambiente
```
source ~/envs/bpm/bin/activate
```

### 4. Instale as dependências
```
pip install customtkinter mutagen soundfile cffi audioread
pip install --no-deps librosa
pip install audioread decorator joblib numpy packaging pooch scikit-learn scipy soxr typing_extensions lazy_loader msgpack
```

## Uso

### App com interface gráfica
```
~/envs/bpm/bin/python3.11 bpm_tagger_app.py
```

### Script de terminal
```
~/envs/bpm/bin/python3.11 bpm_tagger.py /caminho/da/pasta --dry-run
~/envs/bpm/bin/python3.11 bpm_tagger.py /caminho/da/pasta
```

## Por que ambiente virtual?

O bpm_tagger usa Python 3.11 por compatibilidade com o librosa.
Usar um ambiente virtual garante que nenhum outro projeto Python no seu Mac seja afetado.
