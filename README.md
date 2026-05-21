## 🎵 Sobre BPM e Musical Key

O projeto realiza análise automática de arquivos de áudio para identificar informações musicais importantes como:

- **BPM (Beats Per Minute)** → velocidade da música
- **Key (Tom musical)** → tonalidade principal da faixa

### Exemplos

| Música | BPM | Key |
|---|---|---|
| Track A | 128 | A Minor |
| Track B | 95 | C Major |

### O que é BPM?

BPM representa a quantidade de batidas por minuto da música.

Exemplos:
- 70–90 BPM → Hip Hop / Lo-fi
- 120–130 BPM → House / EDM
- 160+ BPM → Drum and Bass

### O que é Key?

Key (tom musical) define o centro tonal da música, indicando quais notas e acordes predominam na composição.

Exemplos:
- `C Major`
- `A Minor`
- `F# Minor`

Essas informações são amplamente utilizadas por:
- DJs para harmonic mixing
- produtores musicais
- organização automática de bibliotecas
- sistemas de recomendação musical

### Recursos do projeto

- Detecção automática de BPM
- Identificação de tonalidade musical (Key)
- Renomeação automática de arquivos
- Organização inteligente da biblioteca musical
- Compatível com workflows de DJs e produtores

### Exemplo de saída

```bash
Artist - Track Name [128 BPM - A Minor].mp3.


# 🎵 BPM Tagger

Disponível em dois modos: script de terminal e app desktop com interface gráfica.

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

## Por que ambiente virtual?

O bpm_tagger usa Python 3.11 por compatibilidade com o librosa.
Usar um ambiente virtual garante que nenhum outro projeto Python no seu Mac seja afetado.



### Install no Linux Ubuntu

## 1- Baixar o Python - https://www.python.org/downloads/release/python-3110rc2/

## 2- Descompactar e entrar na pasta  e rodar os comando abaixo

sudo apt update
sudo apt install -y \
build-essential \
zlib1g-dev \
libncurses5-dev \
libgdbm-dev \
libnss3-dev \
libssl-dev \
libreadline-dev \
libffi-dev \
libsqlite3-dev \
wget \
libbz2-dev \
tk-dev \
xz-utils \
liblzma-dev \
uuid-dev

## 3- ./configure --enable-optimizations
## 4- make -j$(nproc)
## 5- sudo make altinstall
## 6- python3.11 --version

## 6.1- Verifique primeiro:
    which python3
    python3 --version

## 6.2- Depois crie o venv:
    python3 -m venv ~/envs/bpm

## 7- Ative o ambiente
source ~/envs/bpm/bin/activate
O terminal ficará parecido com:
(bpm) user@ubuntu:~$

## 8- Verifique se o Python existe
ls ~/envs/bpm/bin/

Você deve ver:
python
python3
pip
activate

## 9- Instale dependências Dentro do projeto:
cd ~/Downloads/bpm-tagger
pip install -r requirements.txt

## 10- Execute corretamente Com o ambiente ativado:
python bpm_tagger_app.py

