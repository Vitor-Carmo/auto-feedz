import os
import time
import random
import dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.chrome import ChromeDriverManager

# ── Credenciais ────────────────────────────────────────────────────────────────
dotenv.load_dotenv()

login = os.getenv('seu_login')
senha = os.getenv('sua_senha')

if not login or not senha:
    print("ERRO CRÍTICO: Variáveis 'seu_login' ou 'sua_senha' não encontradas!")
    exit(1)

# ── Helpers de comportamento humano ───────────────────────────────────────────

def human_delay(min_s=0.8, max_s=2.2):
    """Pausa com duração randômica natural."""
    time.sleep(random.uniform(min_s, max_s))

def human_type(element, text):
    """Digita caractere a caractere com velocidade variável."""
    for char in text:
        element.send_keys(char)
        time.sleep(random.uniform(0.08, 0.22))
        # Pausa ocasional mais longa (pensando...)
        if random.random() < 0.04:
            time.sleep(random.uniform(0.3, 0.6))

def move_and_click(driver, element):
    """Move o mouse até o elemento antes de clicar (mais humano)."""
    try:
        actions = ActionChains(driver)
        actions.move_to_element_with_offset(element, random.randint(-4, 4), random.randint(-4, 4))
        actions.pause(random.uniform(0.1, 0.25))
        actions.move_to_element(element)
        actions.pause(random.uniform(0.05, 0.15))
        actions.perform()
    except Exception:
        pass
    driver.execute_script("arguments[0].click();", element)

def soft_scroll(driver):
    """Scroll suave para simular idle humano."""
    try:
        driver.execute_script(f"window.scrollBy(0, {random.randint(0, 120)});")
    except Exception:
        pass

# ── Configuração do Chrome ─────────────────────────────────────────────────────

chrome_options = Options()

# Anti-detecção
chrome_options.add_argument("--disable-blink-features=AutomationControlled")
chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
chrome_options.add_experimental_option("useAutomationExtension", False)

# Fingerprint realista
chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
chrome_options.add_argument("--window-size=1920,1080")
chrome_options.add_argument("--lang=pt-BR,pt")
chrome_options.add_argument("--disable-infobars")
chrome_options.add_argument("--disable-notifications")

if os.getenv('GITHUB_ACTIONS'):
    print("Ambiente GitHub Actions detectado. Usando modo headless...")
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")

print("Iniciando navegador...")
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)

# Injeta patches ANTES da primeira página carregar via CDP
# Diferente de execute_script(), o CDP persiste em todas as páginas novas
driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
    "source": """
        Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
        Object.defineProperty(navigator, 'plugins',   {get: () => [1, 2, 3, 4, 5]});
        Object.defineProperty(navigator, 'languages', {get: () => ['pt-BR', 'pt', 'en-US']});
        delete window.cdc_adoQpoasnfa76pfcZLmcfl_Array;
        delete window.cdc_adoQpoasnfa76pfcZLmcfl_Promise;
        delete window.cdc_adoQpoasnfa76pfcZLmcfl_Symbol;
    """
})

wait = WebDriverWait(driver, 30)

# ── ETAPA 1: LOGIN ─────────────────────────────────────────────────────────────

print("--- ETAPA 1: LOGIN ---")
driver.get("https://app.feedz.com.br/inicio")
human_delay(2.5, 4.5)

# Scroll suave inicial (simula leitura da página antes de agir)
for _ in range(2):
    soft_scroll(driver)
    human_delay(0.5, 1.0)

try:
    print("Preenchendo campos de login...")
    email_field = wait.until(EC.element_to_be_clickable((By.ID, "login_email")))
    move_and_click(driver, email_field)
    human_delay(0.3, 0.7)
    human_type(email_field, login)

    human_delay(0.6, 1.4)

    pass_field = wait.until(EC.element_to_be_clickable((By.ID, "passInput")))
    move_and_click(driver, pass_field)
    human_delay(0.3, 0.6)
    human_type(pass_field, senha)

    human_delay(0.8, 1.8)

    print("Clicando no botão de entrar...")
    botao_login = wait.until(EC.element_to_be_clickable((By.ID, "enter-login")))
    move_and_click(driver, botao_login)

    print("Aguardando processamento...")
    wait.until(lambda d: "/inicio" not in d.current_url or d.find_elements(By.CLASS_NAME, "fdz-sidebar"))

    print(f"URL após login: {driver.current_url}")

    if "captcha" in driver.page_source.lower() or "recaptcha" in driver.page_source.lower():
        print("⚠️ ALERTA: Captcha detectado!")

except Exception as e:
    print(f"ERRO NO LOGIN: {type(e).__name__}: {e}")
    print(f"URL atual: {driver.current_url}")
    driver.quit()
    exit(1)

# ── ETAPA 2: HUMOR ─────────────────────────────────────────────────────────────

print("--- ETAPA 2: HUMOR ---")
try:
    # Scroll suave enquanto espera carregar
    for _ in range(3):
        soft_scroll(driver)
        human_delay(0.8, 1.5)

    seletor_mood = "input.fdz_radio_button.input[value='4']"
    radio_button = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, seletor_mood)))
    human_delay(0.4, 0.9)
    driver.execute_script("arguments[0].click();", radio_button)
    print("Humor selecionado!")

    human_delay(0.6, 1.2)

    botao_mood = wait.until(EC.element_to_be_clickable((By.ID, "fdz-btn-send-mood")))
    move_and_click(driver, botao_mood)
    print("Humor enviado!")

except Exception:
    print("Aviso: Humor ignorado (pode já ter sido preenchido hoje).")

# ── ETAPA 3: CELEBRAÇÃO ────────────────────────────────────────────────────────

print("--- ETAPA 3: CELEBRAÇÃO ---")
driver.get("https://app.feedz.com.br/celebracoes")

# Scroll suave enquanto o editor pesado carrega
for _ in range(5):
    soft_scroll(driver)
    human_delay(0.8, 1.5)

texto = (
    "Bom dia! "
    "@LucasNicoliniMartinsdeSouza @LiveaBritodaSilva @TassioLuizDantasdoCarmo "
    "@DiegoHenriquePereiraFreitas @VitorCarmodosSantos @LuizRzezak "
    "@JanaineMaielidaSilvaRibeiro @EduardoMazelli @RafaelAraujoMeiraDeJesus "
    "@EmmanoelPereiraVieira"
)

try:
    print("Aguardando o editor de celebração...")

    # Tenta inserir via API TinyMCE (mais estável que send_keys dentro do iframe)
    texto_inserido = False
    try:
        wait.until(lambda d: d.execute_script(
            "return typeof tinyMCE !== 'undefined' && tinyMCE.activeEditor !== null;"
        ))
        driver.execute_script(f"tinyMCE.activeEditor.setContent('{texto}');")
        driver.execute_script("tinyMCE.activeEditor.fire('change');")
        print("Texto inserido via API TinyMCE.")
        texto_inserido = True
    except Exception:
        pass

    # Fallback: iframe direto (igual ao código original)
    if not texto_inserido:
        print("Tentando inserção via iframe...")
        wait.until(EC.frame_to_be_available_and_switch_to_it(0))
        textarea = wait.until(EC.presence_of_element_located((By.ID, "tinymce")))
        textarea.click()
        driver.execute_script("arguments[0].innerHTML = '';", textarea)
        human_delay(0.5, 1.0)
        human_type(textarea, texto)
        print("Texto inserido via send_keys.")
        texto_inserido = True

    driver.switch_to.default_content()
    human_delay(1.5, 2.5)

    botao_enviar = wait.until(EC.element_to_be_clickable((By.ID, "sendCelebration")))
    driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", botao_enviar)
    human_delay(0.8, 1.4)
    move_and_click(driver, botao_enviar)
    print("Botão de enviar celebração clicado!")
    print("Automação finalizada com sucesso!")

except Exception as e:
    print(f"Erro na celebração: {type(e).__name__} - {str(e)}")
    try:
        driver.switch_to.default_content()
    except Exception:
        pass

human_delay(3.0, 5.0)
driver.quit()
print("Processo finalizado.")