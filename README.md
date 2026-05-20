# 🎵 BPM Tagger

Detecta BPM de arquivos MP3 e renomeia adicionando o BPM ao nome.

## Requisitos

- Python 3.11
- Homebrew (macOS)

## Instalação

### 1. Instale o Python 3.11
```
brew install python@3.11
```

### 2. Crie o ambiente virtual
```
/usr/local/opt/python@3.11/bin/python3.11 -m venv ~/envs/bpm
```

### 3. Ative o ambiente
```
source ~/envs/bpm/bin/activate
```

### 4. Instale as dependências
```
pip install librosa mutagen soundfile cffi audioread
pip install librosa mutagen soundfile --no-deps
pip install audioread decorator joblib numpy packaging pooch scikit-learn scipy soxr typing_extensions lazy_loader msgpack
```

## Uso

Sempre ative o ambiente antes de rodar:
```
source ~/envs/bpm/bin/activate
```

Simular sem renomear:
```
python bpm_tagger.py /caminho/da/pasta --dry-run
```

Renomear de verdade:
```
python bpm_tagger.py /caminho/da/pasta
```

Desativar o ambiente ao terminar:
```
deactivate
```

## Por que ambiente virtual?

O bpm_tagger usa Python 3.11 por compatibilidade com o librosa.
Usar um ambiente virtual garante que nenhum outro projeto Python no seu Mac seja afetado.
