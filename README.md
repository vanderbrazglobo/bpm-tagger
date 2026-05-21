# 🎵 BPM Tagger

Detecta BPM e tom musical de arquivos de áudio e renomeia automaticamente.
Disponível em dois modos: app desktop com interface gráfica e script de terminal.

## 📸 Screenshots

### App principal
![BPM Tagger App](assets/app_screenshot.png)

### Relatório CSV gerado
![Relatório CSV](assets/csv_screenshot.png)

## 📦 Download

**[⬇️ Baixar bpm-tagger-v1.0.0.zip](https://github.com/vanderbrazglobo/bpm-tagger/releases/download/v1.0.0/bpm-tagger-v1.0.0.zip)**

Ou acesse: [Releases](https://github.com/vanderbrazglobo/bpm-tagger/releases)

## Requisitos

- Python 3.11 (python.org — não use o Homebrew)
- macOS ou Linux Ubuntu

## Instalação macOS

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

## Funcionalidades

- 🎵 Detecção automática de BPM
- 🎼 Identificação de tom musical (key)
- 📁 Processamento de subpastas
- 📊 Exportação de relatório CSV
- 🎧 Suporte a MP3, FLAC, WAV, AIFF, OGG, M4A
- 🔍 Modo simulação (dry-run)
- 🛡️ Preservação de metadados ID3

## Por que ambiente virtual?

O bpm_tagger usa Python 3.11 por compatibilidade com o librosa.
Usar um ambiente virtual garante que nenhum outro projeto Python no seu Mac seja afetado.
