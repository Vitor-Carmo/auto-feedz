# Feedz Automation 🤖

<p align="center">
  <b>Login · Humor · Celebração</b><br>
  <sub>Automação diária do Feedz com Playwright + GitHub Actions</sub>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.8%2B-blue?logo=python">
  <img src="https://img.shields.io/badge/Playwright-1.48-green?logo=google-chrome">
  <img src="https://img.shields.io/badge/GitHub%20Actions-schedule-brightgreen?logo=githubactions">
  <img src="https://img.shields.io/badge/license-MIT-blue">
</p>

---

## 📋 Índice

- [Pipeline](#-pipeline)
- [Estrutura do projeto](#-estrutura-do-projeto)
- [Stack](#-stack)
- [Setup local](#-setup-local)
- [Extrair cookies (recomendado para CI)](#-extrair-cookies-recomendado-para-ci)
- [GitHub Actions](#-github-actions)
- [Estratégias anti-CAPTCHA](#-estratégias-anti-captcha)
- [Como funciona o código](#-como-funciona-o-código)
- [Solução de problemas](#-solução-de-problemas)
- [Manutenção](#-manutenção)

---

## 🧠 Pipeline

```
                         ┌──────────────────────┐
                         │   FEEDZ AUTOMATION    │
                         │  Login · Humor · Cele │
                         └──────────┬───────────┘
                                    │
                                    ▼
                        ┌───────────────────────┐
                        │    FEEDZ_COOKIES      │
                        │   está definido?      │
                        └───────┬───────┬───────┘
                              YES       NO
                                │        │
                                ▼        ▼
                    ┌──────────────┐ ┌──────────────────┐
                    │  Carregar    │ │  Navegar /inicio  │
                    │  cookies via │ │                   │
                    │  add_cookies │ │  Preencher email  │
                    │  + reload    │ │  + senha          │
                    └──────┬───────┘ └────────┬─────────┘
                           │                  │
                           ▼                  ▼
                    ┌──────────────────────────────┐
                    │         LOGIN OK?            │
                    │  URL ≠ login & sidebar OK    │
                    └──────┬──────────────┬────────┘
                         YES              NO
                           │                │
                           │                ▼
                           │        ┌────────────────┐
                           │        │  Screenshot    │
                           │        │  + Erro        │
                           │        └────────────────┘
                           │
                           ▼
                    ┌───────────────────────┐
                    │   ETAPA 2 — HUMOR     │
                    │                       │
                    │  ┌─────────────────┐  │
                    │  │  Clica na       │  │
                    │  │  imagem do      │  │
                    │  │  humor (Feliz)  │  │
                    │  └────────┬────────┘  │
                    │           │           │
                    │           ▼           │
                    │  ┌─────────────────┐  │
                    │  │  Fallback: JS   │  │
                    │  │  click no input │  │
                    │  └─────────────────┘  │
                    │                       │
                    │  Clica "Enviar"       │
                    └──────────┬────────────┘
                               │
                               ▼
                    ┌───────────────────────┐
                    │  ETAPA 3 — CELEBRAÇÃO │
                    │                       │
                    │  ┌─────────────────┐  │
                    │  │  TinyMCE API    │──┼──▶ setContent()
                    │  └────────┬────────┘  │
                    │           │           │
                    │      FALHOU?          │
                    │           │           │
                    │           ▼           │
                    │  ┌─────────────────┐  │
                    │  │  Fallback:      │  │
                    │  │  iframe #tinymce│  │
                    │  │  keyboard.type  │  │
                    │  └─────────────────┘  │
                    │                       │
                    │  Clica "Enviar"       │
                    │  (com retry 3x)       │
                    └──────────┬────────────┘
                               │
                               ▼
                    ┌───────────────────────┐
                    │   ✅ FINALIZADO       │
                    │   Humor registrado    │
                    │   Celebração publicada│
                    └───────────────────────┘
```

---

## 📁 Estrutura do projeto

```
auto-feedz/
├── automation.py              ← Código principal (Playwright)
├── extract_cookies.py         ← Extrator de cookies para CI
├── .github/
│   └── workflows/
│       └── feedz_daily.yml    ← Workflow GitHub Actions
├── .env.example               ← Template de variáveis de ambiente
├── .gitignore
├── requirements.txt
└── README.md
```

---

## 🛠 Stack

| Tecnologia | Versão | Função |
|------------|--------|--------|
| **Python** | 3.8+ | Linguagem |
| **Playwright** | 1.40+ | Automação do navegador (Chromium) |
| **python-dotenv** | 1.0+ | Carregar `.env` local |
| **GitHub Actions** | — | CI/CD agendado (cron) |

Playwright foi escolhido por:
- ✅ **Anti-detecção nativa** — não expõe `navigator.webdriver`, não precisa de CDP commands manuais
- ✅ **Auto-instalação do Chromium** — `playwright install chromium` baixa o navegador, sem depender de Chrome instalado no sistema
- ✅ **API moderna e concisa** — `page.locator()`, `page.wait_for_selector()`, `context.add_cookies()`
- ✅ **Suporte a iframes** — `frame_locator()` para reCAPTCHA e TinyMCE

---

## 🚀 Setup local

```bash
# 1. Criar e ativar ambiente virtual
python -m venv .venv
source .venv/bin/activate        # Linux/macOS
# .venv\Scripts\activate         # Windows

# 2. Instalar dependências
pip install -r requirements.txt

# 3. Baixar Chromium (Playwright gerencia o navegador)
playwright install chromium --with-deps

# 4. Configurar credenciais
cp .env.example .env
# Edite .env com seu email e senha:
#   FEEDZ_LOGIN=seu-email@exemplo.com
#   FEEDZ_PASSWORD=sua-senha

# 5. Executar
python automation.py
```

> 💡 Para testar rapidamente, você pode definir as variáveis diretamente:
> ```bash
> FEEDZ_LOGIN=seu@email.com FEEDZ_PASSWORD=senha python automation.py
> ```

---

## 🍪 Extrair cookies (recomendado para CI)

### Por que isso é necessário?

O Google reCAPTCHA identifica IPs de datacenter (GitHub Actions) e **sempre** exige desafio de imagens — não apenas o checkbox "Não sou um robô". O Playwright **não consegue** resolver esse desafio automaticamente.

A solução é **extrair os cookies de uma sessão logada** e injetá-los no navegador headless do CI, pulando completamente a tela de login e o CAPTCHA.

### Como extrair

O script `extract_cookies.py` faz todo o trabalho:

```bash
python extract_cookies.py
```

**O que acontece passo a passo:**

```
 1. Playwright abre Chromium (janela visível, 1280×900)
 2. Navega para https://app.feedz.com.br
 3. ┌─────────────────────────────────────────────────────┐
    │  🛑 PAUSA — Faça login MANUALMENTE no navegador    │
    │  (resolva o CAPTCHA com seus olhos)                │
    │  Depois aperte ENTER no terminal                   │
    └─────────────────────────────────────────────────────┘
 4. Script extrai todos os cookies via page.context.cookies()
 5. Exibe o JSON no terminal — você copia
 6. (Opcional) Salva em arquivo com -o cookies.json
```

**Saída gerada:**

```json
[
  {
    "name": "_session_id",
    "value": "abc123def456...",
    "domain": "app.feedz.com.br",
    "path": "/",
    "expires": 1760000000.0,
    "httpOnly": true,
    "secure": true,
    "sameSite": "Lax"
  }
]
```

### Configurar no GitHub

```
1. GitHub → Settings → Secrets and variables → Actions
2. New repository secret
3. Nome: FEEDZ_COOKIES
4. Valor: cole todo o JSON gerado
5. Salvar
```

> ⚠ Os cookies expiram em 30–90 dias. Quando a automação no CI falhar com "cookies expired", repita o processo.

---

## ⚙️ GitHub Actions

O workflow `feedz_daily.yml` roda de segunda a sexta às **08:30 BRT** (11:30 UTC).

Também pode ser disparado manualmente em **Actions → Feedz Daily Automation → Run workflow**.

### Secrets necessários

| Secret | Descrição | Obrigatório |
|--------|-----------|:-----------:|
| `FEEDZ_LOGIN` | E-mail de acesso ao Feedz | ✅ Sim |
| `FEEDZ_PASSWORD` | Senha do Feedz | ✅ Sim |
| `FEEDZ_COOKIES` | JSON dos cookies de sessão | ◻️ Ideal |

### Variable opcional

| Variable | Padrão | Descrição |
|----------|--------|-----------|
| `FEEDZ_MOOD` | `4` | Valor do humor (1 = Muito triste, 2 = Triste, 3 = Neutro, 4 = Feliz, 5 = Muito feliz) |

### Fluxo no CI

```
1. Checkout do repositório
2. Setup Python 3.12 (com cache pip)
3. pip install -r requirements.txt
4. playwright install chromium --with-deps  ← baixa Chromium + libs do sistema
5. Executa: python automation.py
   ├── FEEDZ_COOKIES definido?
   │   ├── SIM → carrega cookies → pula login → Humor → Celebração
   │   └── NÃO → login normal (email + senha + reCAPTCHA)
   └── Falhou? → Upload de screenshots como artefato
```

---

## 🛡 Estratégias anti-CAPTCHA

O Feedz usa reCAPTCHA v2. Abaixo as estratégias para lidar com ele, em ordem de recomendação.

### ① Cookie persistence ✅ (já implementado — recomendado)

**Como funciona:** Extrai cookies uma vez de um navegador real, armazena como secret e injeta em toda execução do CI.

**Prós:** ✅ Gratuito, ✅ Simples, ✅ Funciona 100%
**Contras:** ⚠ Cookies expiram (renovar a cada 30-90 dias)

```python
# Código já implementado em _try_cookie_auth()
cookies = json.loads(os.getenv("FEEDZ_COOKIES"))
context.add_cookies(cookies)
page.reload()
```

### ② Self-hosted runner

**Como funciona:** Roda o workflow numa máquina que você controla (VPS, Raspberry Pi, PC ligado 24h) com IP residencial/corporativo.

**Prós:** ✅ IP confiável, ✅ Sem limite de execução
**Contras:** ❌ Precisa de máquina dedicada, ❌ Configuração adicional

```yaml
# Adicione ao workflow:
runs-on: self-hosted
```

### ③ Serviço de resolução de CAPTCHA (pago)

**Como funciona:** Integra com serviços como 2Captcha, CapMonster ou Anti-Captcha que resolvem desafios de imagem por ~$3/1000 resoluções.

**Prós:** ✅ Automático, ✅ Funciona em qualquer IP
**Contras:** ❌ Custo recorrente, ❌ Dependência externa

```python
# Exemplo conceitual com 2Captcha:
solver = TwoCaptcha("API_KEY")
result = solver.recaptcha(sitekey="...", url="...")
page.evaluate(f"grecaptcha.execute('{result}')")
```

### ④ Playwright stealth plugin

**Como funciona:** Usa `playwright-stealth` que patenteia o Chromium para esconder ainda mais o fingerprint de automação.

```bash
pip install playwright-stealth
```

```python
from playwright_stealth import stealth_sync

stealth_sync(page)
```

**Prós:** ✅ Reduz detecção, ✅ Simples
**Contras:** ❌ Não resolve CAPTCHA de imagem, ❌ Pode quebrar com updates

### ⑤ Headless detection tricks

O Playwright já faz um bom trabalho, mas você pode reforçar:

| Técnica | Implementado | Descrição |
|---------|:-----------:|-----------|
| User-Agent realista | ✅ | `Chrome/126 Windows NT 10.0` |
| Viewport 1920×1080 | ✅ | Tamanho de tela comum |
| Locale pt-BR | ✅ | `locale="pt-BR"` |
| Timezone SP | ✅ | `timezone_id="America/Sao_Paulo"` |
| Desabilitar Blink automation | ✅ | `--disable-blink-features=AutomationControlled` |
| Argumentos headless | ✅ | `--no-sandbox`, `--disable-dev-shm-usage` |

### ⑥ Human-like behavior

Movimentos e digitação que imitam humanos:

| Técnica | Implementado | Descrição |
|---------|:-----------:|-----------|
| `human_delay()` | ✅ | Pausas aleatórias entre ações |
| `jitter_move_and_click()` | ✅ | Mouse se move com pequeno desvio antes de clicar |
| `human_type()` | ✅ | Digita caractere por caractere com delay variável |
| `scroll_to()` | ✅ | Scroll suave antes de interagir |

---

## 🔍 Como funciona o código

### `automation.py` — 3 etapas

A classe `FeedzAutomation` gerencia o ciclo de vida do navegador e executa as etapas sequencialmente:

```
FeedzAutomation()
├── __enter__() → inicia Playwright, Chromium, contexto e página
├── run()
│   ├── login()
│   │   ├── _try_cookie_auth()   ← COOKIES primeiro
│   │   └── _fill_login_form()   ← fallback email + senha
│   │       └── _try_solve_recaptcha()
│   ├── register_mood()
│   │   └── _do_register_mood()  ← imagem visível → fallback JS
│   └── post_celebration()
│       └── _do_post_celebration()
│           ├── _insert_via_tinymce_api()   ← API JS
│           └── _insert_via_iframe_fallback() ← iframe
└── __exit__() → fecha browser
```

### `extract_cookies.py` — Extrator de cookies

Script auxiliar que abre Chromium em modo visível, espera o usuário fazer login manual e exporta os cookies como JSON.

```python
with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page(viewport={"width": 1280, "height": 900})
    page.goto("https://app.feedz.com.br")
    input("Faça login e aperte ENTER...")
    cookies = page.context.cookies()
    print(json.dumps(cookies, indent=2))
```

### Por que cookies em vez de login?

| Abordagem | CI (IP datacenter) | Local (IP residencial) |
|-----------|:------------------:|:---------------------:|
| Login + CAPTCHA | ❌ Bloqueado | ✅ Funciona |
| Cookies de sessão | ✅ Funciona | ✅ Funciona |
| Self-hosted runner | ✅ Funciona | N/A |

---

## 🔧 Solução de problemas

| Erro | Causa | Solução |
|------|-------|---------|
| `TimeoutError: waiting for locator("#login_email")` | Cookies expirados ou inválidos | Re-extrair cookies com `extract_cookies.py` |
| `Executable doesn't exist at ...` | Chromium não baixado | `playwright install chromium --with-deps` |
| `Locator.click: Timeout 5000ms` — reCAPTCHA | reCAPTCHA com desafio de imagem | Usar cookies (estratégia ①) |
| `PwTimeoutError` no humor | Modal de humor não apareceu | Já preenchido hoje — não é erro |
| Screenshot mostra página em branco | Headless sem GPU | Já configurado (`--disable-gpu`) |
| Push rejeitado: `workflow scope` | Token sem permissão | Adicionar escopo `workflow` no token |

---

## 📅 Manutenção

### Cookie expiry

Os cookies de sessão do Feedz expiram em **30 a 90 dias**. Quando a automação no GitHub Actions começar a falhar com:

```
Cookies expirados ou inválidos — fallback para login via credenciais.
→ login_failure.png
```

É hora de renovar:

```bash
python extract_cookies.py
# login manual → copiar JSON → atualizar secret FEEDZ_COOKIES
```

### Atualizar dependências

```bash
pip install --upgrade -r requirements.txt
playwright install chromium --with-deps
```

### Verificar logs

No GitHub Actions, os screenshots de falha ficam disponíveis como **artefatos** da run por 7 dias.

---

<p align="center">
  <sub>Feito com ☕ e Playwright</sub>
</p>
