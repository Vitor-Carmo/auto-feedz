# Feedz Automation

Automação diária do Feedz: login, registro de humor e publicação de celebração.

---

## Estrutura do projeto

```
feedz_automation/
├── src/feedz/
│   ├── __init__.py
│   └── automation.py       ← código principal
├── .github/workflows/
│   └── feedz_daily.yml     ← workflow diário
├── .env.example
├── .gitignore
├── pyproject.toml
└── requirements.txt
```

---

## Uso local

```bash
# 1. Criar e ativar ambiente virtual
python -m venv .venv && source .venv/bin/activate   # Linux/macOS
python -m venv .venv && .venv\Scripts\activate       # Windows

# 2. Instalar dependências
pip install -r requirements.txt

# 3. Configurar credenciais
cp .env.example .env
# Edite .env com seu login e senha

# 4. Executar
python -m feedz.automation
```

---

## Uso em GitHub Actions

1. Adicione os **Secrets** no repositório:
   - `FEEDZ_LOGIN` — seu e-mail de login
   - `FEEDZ_PASSWORD` — sua senha

2. Opcionalmente, adicione a **Variable** `FEEDZ_MOOD` (padrão `4`).

3. O workflow dispara automaticamente de segunda a sexta às 08:30 (Brasília).
   Também pode ser disparado manualmente em **Actions → Run workflow**.

---

## Sobre captchas em ambiente CI

### Por que o captcha aparece em GitHub Actions?

Os runners do GitHub Actions são máquinas virtuais efêmeras cujos **IPs
públicos são amplamente conhecidos e catalogados como datacenter/cloud**.
Sistemas anti-bot (como reCAPTCHA e hCaptcha) usam reputação de IP, ausência
de histórico de navegação, ausência de cookies reais e fingerprint de Canvas/
WebGL para classificar o cliente como suspeito.

Por mais sofisticado que seja o Selenium, ele não consegue:
- Apresentar um IP residencial ou corporativo confiável.
- Simular o histórico de cookies de um usuário real.
- Passar na análise comportamental de longo prazo (mouse, scroll, tempo de
  sessão em visitas anteriores).

### Alternativas legítimas

| Abordagem | Como funciona | Complexidade |
|-----------|---------------|--------------|
| **Cookie/token persistente** | Faz login uma vez num browser real, exporta os cookies para um arquivo `.json`, e o script os carrega via `driver.add_cookie()` antes de navegar. | Baixa |
| **Perfil Chrome persistente** | Usa `--user-data-dir` apontando para um perfil Chrome já autenticado, armazenado como artefato criptografado no repositório ou em storage externo. | Média |
| **Self-hosted runner** | Executa o workflow numa máquina que você controla (servidor, VPS, Raspberry Pi), com IP fixo e perfil de navegação legítimo. | Média |
| **API oficial do Feedz** | Se o Feedz expõe API REST, use tokens de acesso em vez de Selenium. Elimina todo o problema. | Baixa (se disponível) |

A abordagem de **cookie persistente** é geralmente a mais simples:

```python
import json
from selenium.webdriver.remote.webdriver import WebDriver

def load_cookies(driver: WebDriver, path: str) -> None:
    driver.get("https://app.feedz.com.br")
    with open(path) as f:
        for cookie in json.load(f):
            driver.add_cookie(cookie)
    driver.refresh()
```

Os cookies devem ser renovados quando expirarem (geralmente a cada 30–90 dias).
