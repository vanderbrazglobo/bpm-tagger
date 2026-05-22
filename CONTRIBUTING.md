# 🌿 Guia de Contribuição — BPM Tagger

> Como contribuir com o projeto usando branches, Pull Requests e releases automáticas.

---

## Regra de ouro

> **Nunca commitar diretamente na `main`.**
> Todo código passa por uma feature branch → PR → `develop` → `main`.

---

## 1. Estrutura de Branches

| Branch | Propósito | Regra |
|---|---|---|
| `main` | Código estável em produção | Nunca commitar direto. Só via merge da `develop`. |
| `develop` | Integração de features testadas | Base para todas as features. Sempre atualizada. |
| `feature/nome` | Uma funcionalidade ou correção | Criada a partir da `develop`. Deletada após merge. |

---

## 2. Fluxo Completo

```
feature/minha-feature
        ↓  git push → Abre Pull Request no GitHub
     develop
        ↓  CI verde → Merge PR → git merge develop
      main
        ↓  git tag v1.x.x → git push origin v1.x.x
   release v1.x.x  (CD automático cria o zip)
```

---

## 3. Passo a Passo — Dia a Dia

### Para cada nova feature ou correção:

**1. Sempre parta da `develop` atualizada**

```bash
cd ~/bpm-tagger
git checkout develop
git pull
```

> ⚠️ Nunca crie feature branch a partir da `main`.

**2. Crie a feature branch com nome descritivo**

```bash
git checkout -b feature/nome-da-feature

# Exemplos:
git checkout -b feature/detect-major-minor
git checkout -b feature/progress-bar
git checkout -b fix/csv-export-path
```

**3. Desenvolva, teste localmente e commite**

```bash
git add .
git commit -m "feat: descrição clara da mudança"
```

Tipos de commit:

| Prefixo | Uso |
|---|---|
| `feat:` | Nova funcionalidade |
| `fix:` | Correção de bug |
| `docs:` | Documentação |
| `ci:` | Pipeline / workflows |
| `chore:` | Tarefas de manutenção |
| `refactor:` | Refatoração sem mudar comportamento |

**4. Envie a branch para o GitHub**

```bash
git push -u origin feature/nome-da-feature
```

**5. Abra o Pull Request no GitHub**

No GitHub aparece o banner: **"Compare & pull request"** → clique nele.

- `base` deve ser: `develop` (não `main`!)
- Adicione título e descrição explicando o que muda
- O CI roda automaticamente — aguarde ficar verde ✅

**6. Merge após CI verde**

Clique em **Merge pull request** → **Confirm merge**.

> ⚠️ A branch `main` está protegida. O merge só é liberado quando lint, dependencies e testes passam.

**7. Atualize o local após o merge**

```bash
git checkout develop
git pull
```

---

## 4. Publicar uma Release

Quando a `develop` tiver features prontas para lançar:

**1. Merge `develop` → `main`**

```bash
git checkout main
git merge develop
git push
```

**2. Crie a tag de versão**

Siga o padrão: `v1.0.0` → `v1.1.0` (feature) ou `v1.0.1` (fix)

```bash
git tag v1.1.0
git push origin v1.1.0
```

> 🤖 Ao criar a tag, o GitHub Actions empacota os arquivos, gera o changelog e publica a release automaticamente.

---

## 5. Para Colaboradores Externos

Quem não tem acesso direto ao repositório deve usar o fluxo de fork:

```bash
# 1. Fork no GitHub (botão Fork na página do repo)

# 2. Clonar o próprio fork
git clone https://github.com/SEU-USUARIO/bpm-tagger.git
cd bpm-tagger

# 3. Adicionar o repositório original como upstream
git remote add upstream https://github.com/vanderbrazglobo/bpm-tagger.git

# 4. Criar feature branch
git checkout -b feature/minha-contribuicao

# 5. Desenvolver, commitar e push
git push origin feature/minha-contribuicao

# 6. Abrir PR no GitHub apontando para develop do repo original
```

**Manter o fork atualizado** — antes de começar qualquer trabalho:

```bash
git fetch upstream
git checkout develop
git merge upstream/develop
```

---

## 6. Referência Rápida de Comandos

| Comando | O que faz |
|---|---|
| `git checkout develop` | Muda para a branch develop |
| `git pull` | Atualiza a branch local com o GitHub |
| `git checkout -b feature/nome` | Cria e muda para nova feature branch |
| `git add .` | Prepara todos os arquivos para commit |
| `git commit -m "mensagem"` | Salva as mudanças com descrição |
| `git push -u origin feature/nome` | Envia a branch para o GitHub |
| `git checkout main && git merge develop` | Merge da develop na main |
| `git tag v1.x.x` | Cria tag de versão localmente |
| `git push origin v1.x.x` | Envia tag → dispara CD e release |
| `git branch -d feature/nome` | Deleta branch local após merge |
| `git push origin --delete feature/nome` | Deleta branch remota após merge |

---

[github.com/vanderbrazglobo/bpm-tagger](https://github.com/vanderbrazglobo/bpm-tagger)
