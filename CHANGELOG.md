# Changelog

Todas as mudanças notáveis do projeto estão documentadas aqui.
Formato baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/).

---

## [v1.5.1] - 2026-05-22
### Corrigido
- Removidos arquivos de build e documentos duplicados do repositório
- `.gitignore` atualizado para excluir artefatos de build

## [v1.5.0] - 2026-05-22
### Adicionado
- `CONTRIBUTING.md` com guia completo de contribuição
- `INSTRUCOES.md` com instruções detalhadas de uso
- README profissional com screenshots e tabela de download

## [v1.4.1] - 2026-05-22
### Adicionado
- Barra de progresso em tempo real no app
- Switch de detecção de energia/intensidade (Low/Mid/High/Peak)

## [v1.4.0] - 2026-05-22
### Adicionado
- Detecção de energia/intensidade usando RMS

## [v1.3.0] - 2026-05-22
### Adicionado
- Detecção de Major/Minor usando algoritmo Krumhansl-Schmuckler

## [v1.2.0] - 2026-05-21
### Adicionado
- Guia de fluxo Git e documentação de contribuição

## [v1.1.0] - 2026-05-21
### Adicionado
- Detecção de tom musical (key) com algoritmo Krumhansl-Schmuckler

## [v1.0.0] - 2026-05-20
### Adicionado
- Script de terminal `bpm_tagger.py`
- App desktop com interface gráfica `bpm_tagger_app.py`
- Detecção automática de BPM via librosa
- Suporte a MP3, FLAC, WAV, AIFF, OGG, M4A
- Modo simulação dry-run
- Exportação de relatório CSV
- CI/CD com GitHub Actions
- Atalho macOS com duplo clique
