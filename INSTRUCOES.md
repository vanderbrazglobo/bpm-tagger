# 🎵 BPM Tagger — Instruções de Uso

> Versão 1.4.2 • macOS e Linux Ubuntu

---

## O que é o BPM Tagger?

Script Python e app desktop que lê arquivos de áudio de uma pasta, detecta automaticamente o **BPM** e o **tom musical (key)** de cada faixa, e renomeia os arquivos adicionando essas informações ao nome. Arquivos já processados são ignorados automaticamente.

---

## 1. O que está no pacote

| Arquivo | Descrição |
|---|---|
| `bpm_tagger_app.py` | App desktop com interface gráfica moderna (CustomTkinter). Recomendado para uso geral. |
| `bpm_tagger.py` | Script de terminal para uso avançado com opções de linha de comando. |
| `BPM Tagger.command` | Atalho para macOS. Duplo clique abre o app diretamente sem precisar do terminal. |
| `requirements.txt` | Lista de dependências Python necessárias. |
| `README.md` | Documentação completa do projeto. |

---

## 2. Download

| Plataforma | Arquivo |
|---|---|
| macOS (instalador) | [⬇️ BPM-Tagger-1.4.2.dmg](https://github.com/vanderbrazglobo/bpm-tagger/releases/download/v1.4.2/BPM-Tagger-1.4.2.dmg) |
| macOS / Linux (zip) | [⬇️ bpm-tagger-v1.4.2.zip](https://github.com/vanderbrazglobo/bpm-tagger/releases/download/v1.4.2/bpm-tagger-v1.4.2.zip) |

Ou acesse a página de releases: [github.com/vanderbrazglobo/bpm-tagger/releases](https://github.com/vanderbrazglobo/bpm-tagger/releases)

---

## 3. Requisitos

- Python 3.11 — instale em [python.org](https://www.python.org/downloads/release/python-31110/) (não use o Homebrew no macOS)
- macOS (qualquer versão) ou Linux Ubuntu 20.04+
- Conexão com internet para instalar as dependências

---

## 4. Instalação no macOS

### Opção 1 — DMG (recomendado)

1. Baixe o arquivo `BPM-Tagger-1.4.2.dmg`
2. Abra o arquivo
3. Arraste **BPM Tagger** para a pasta **Aplicativos**
4. Abra e aproveite ✅

### Opção 2 — ZIP

**Passo 1** — Instale o Python 3.11

Acesse [python.org/downloads/release/python-31110](https://www.python.org/downloads/release/python-31110/) e baixe o **macOS 64-bit universal2 installer**.

**Passo 2** — Descompacte o arquivo baixado

Clique duas vezes no `bpm-tagger-v1.4.2.zip` para extrair.

**Passo 3** — Abra o terminal e crie o ambiente virtual

```bash
/Library/Frameworks/Python.framework/Versions/3.11/bin/python3.11 -m venv ~/envs/bpm
source ~/envs/bpm/bin/activate
```

> Isso garante que o projeto não afete outros scripts Python do seu Mac.

**Passo 4** — Instale as dependências

```bash
pip install customtkinter mutagen soundfile cffi audioread
pip install --no-deps librosa
pip install audioread decorator joblib numpy packaging pooch \
            scikit-learn scipy soxr typing_extensions lazy_loader msgpack
```

**Passo 5** — Abra o app

```bash
~/envs/bpm/bin/python3.11 bpm_tagger_app.py
```

> 💡 Após a instalação, você também pode abrir o app com duplo clique no arquivo `BPM Tagger.command`.

---

## 5. Instalação no Linux Ubuntu

**Passo 1** — Instale as dependências do sistema

```bash
sudo apt update
sudo apt install -y build-essential python3.11 python3.11-tk \
                    python3.11-venv ffmpeg libsndfile1
```

**Passo 2** — Crie e ative o ambiente virtual

```bash
python3.11 -m venv ~/envs/bpm
source ~/envs/bpm/bin/activate
```

**Passo 3** — Instale as dependências Python

```bash
pip install customtkinter mutagen soundfile cffi audioread
pip install --no-deps librosa
pip install audioread decorator joblib numpy packaging pooch \
            scikit-learn scipy soxr typing_extensions lazy_loader msgpack
```

**Passo 4** — Execute o app

```bash
python bpm_tagger_app.py
```

---

## 6. Como usar o app

### Interface principal

1. Clique em **Selecionar** para escolher a pasta com os arquivos de áudio
2. Configure as opções desejadas (veja seção 7)
3. Clique em **Iniciar Varredura**
4. Acompanhe o progresso no log em tempo real

### Resultado nos arquivos

```
Antes:  musica.mp3
Depois: musica_128BPM.mp3

Com tom ativado:
Depois: musica_128BPM_Am.mp3
```

---

## 7. Opções disponíveis

| Opção | O que faz |
|---|---|
| **Modo simulação (dry-run)** | Mostra o que seria renomeado sem alterar nenhum arquivo. Sempre use antes de rodar de verdade. |
| **Detectar tom musical (key)** | Identifica a tonalidade da música (ex: Am, C, F#) e adiciona ao nome. |
| **Processar subpastas** | Varre todas as pastas dentro da pasta selecionada recursivamente. |
| **Exportar relatório CSV** | Ao terminar, abre uma janela para escolher onde salvar um relatório com BPM, tom e formato de cada arquivo. |
| **Formatos (MP3, FLAC, WAV...)** | Selecione quais tipos de arquivo serão processados. |

---

## 8. Uso pelo terminal (avançado)

```bash
# Simular sem renomear (sempre use antes de rodar de verdade)
~/envs/bpm/bin/python3.11 bpm_tagger.py /caminho/da/pasta --dry-run

# Renomear de verdade
~/envs/bpm/bin/python3.11 bpm_tagger.py /caminho/da/pasta

# Log detalhado
~/envs/bpm/bin/python3.11 bpm_tagger.py /caminho/da/pasta --debug
```

---

## 9. Arquivos já processados

O BPM Tagger detecta automaticamente se um arquivo já tem BPM no nome (padrão `_128BPM`) e pula esse arquivo. Você pode rodar o script várias vezes na mesma pasta sem risco de duplicar as informações.

---

## 10. Links úteis

| | |
|---|---|
| 📦 Download latest | [github.com/vanderbrazglobo/bpm-tagger/releases/latest](https://github.com/vanderbrazglobo/bpm-tagger/releases/latest) |
| 💻 Repositório | [github.com/vanderbrazglobo/bpm-tagger](https://github.com/vanderbrazglobo/bpm-tagger) |
| 🐛 Problemas / Sugestões | [github.com/vanderbrazglobo/bpm-tagger/issues](https://github.com/vanderbrazglobo/bpm-tagger/issues) |
