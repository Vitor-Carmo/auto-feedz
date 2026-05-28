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
from webdriver_manager.chrome import ChromeDriverManager

# Carrega variáveis do arquivo .env se ele existir
dotenv.load_dotenv()

login = os.getenv('seu_login')
senha = os.getenv('sua_senha')

if not login or not senha:
    print("ERRO CRÍTICO: Variáveis 'seu_login' ou 'sua_senha' não encontradas!")
    exit(1)

chrome_options = Options()

# TÉCNICAS ANTI-DETECÇÃO
chrome_options.add_argument("--disable-blink-features=AutomationControlled")
chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
chrome_options.add_experimental_option("useAutomationExtension", False)
chrome_options.add_argument("--window-size=1920,1080")
chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

if os.getenv('GITHUB_ACTIONS'):
    print("Ambiente GitHub Actions detectado. Usando modo headless...")
    chrome_options.add_argument("--headless=new") # Usando o novo modo headless que é mais difícil de detectar
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

print("Iniciando navegador...")
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)

# Remove a propriedade navigator.webdriver para dificultar detecção
driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

wait = WebDriverWait(driver, 30)

def human_type(element, text):
    for char in text:
        element.send_keys(char)
        time.sleep(random.uniform(0.1, 0.3)) # Digitação humana

print("--- ETAPA 1: LOGIN ---")
driver.get("https://app.feedz.com.br/inicio")
time.sleep(3)

try:
    print("Preenchendo campos de login...")
    email_field = wait.until(EC.presence_of_element_located((By.ID, "login_email")))
    human_type(email_field, login)
    
    pass_field = wait.until(EC.presence_of_element_located((By.ID, "passInput")))
    human_type(pass_field, senha)
    
    time.sleep(random.uniform(1, 2)) # Pausa antes do clique
    
    print("Clicando no botão de entrar...")
    botao_login = wait.until(EC.element_to_be_clickable((By.ID, "enter-login")))
    botao_login.click()
    
    print("Aguardando processamento...")
    # Espera por qualquer sinal de sucesso ou erro
    wait.until(lambda d: "/inicio" not in d.current_url or d.find_elements(By.CLASS_NAME, "fdz-sidebar"))
    
    print(f"URL após login: {driver.current_url}")
    if "captcha" in driver.page_source.lower() or "google.com/recaptcha" in driver.page_source:
        print("⚠️ ALERTA: Captcha detectado! A automação provavelmente será bloqueada.")

except Exception as e:
    print(f"ERRO NO LOGIN: {type(e).__name__}")
    print(f"URL atual: {driver.current_url}")
    driver.quit()
    exit(1)

print("--- ETAPA 2: HUMOR ---")
try:
    # Pequena espera para carregar o humor
    time.sleep(5)
    seletor_mood = "input.fdz_radio_button.input[value='4']"
    radio_button = driver.find_element(By.CSS_SELECTOR, seletor_mood)
    driver.execute_script("arguments[0].click();", radio_button)
    print("Humor selecionado!")
    time.sleep(1)
    driver.find_element(By.ID, "fdz-btn-send-mood").click()
    print("Humor enviado!")
except:
    print("Aviso: Humor ignorado.")

print("--- ETAPA 3: CELEBRAÇÃO ---")
driver.get("https://app.feedz.com.br/celebracoes")
time.sleep(7) # Um pouco mais de tempo para carregar o editor pesado

try:
    print("Aguardando o editor de celebração...")
    wait.until(EC.frame_to_be_available_and_switch_to_it(0))
    
    # Encontra o corpo do editor
    textarea = wait.until(EC.presence_of_element_located((By.ID, "tinymce")))
    print("Editor encontrado. Focando e digitando...")
    
    # Clica e limpa o campo
    textarea.click()
    driver.execute_script("arguments[0].innerHTML = '';", textarea)
    time.sleep(1)

    # Insere o texto
    texto = "Bom dia! @LucasNicoliniMartinsdeSouza @LiveaBritodaSilva @TassioLuizDantasdoCarmo @DiegoHenriquePereiraFreitas @VitorCarmodosSantos @LuizRzezak @JanaineMaielidaSilvaRibeiro @EduardoMazelli @RafaelAraujoMeiraDeJesus @EmmanoelPereiraVieira"
    
    # Tenta usar a API do TinyMCE primeiro (mais garantido)
    try:
        driver.execute_script(f"tinyMCE.activeEditor.setContent('{texto}')")
        print("Texto inserido via API TinyMCE.")
    except:
        # Fallback se a API falhar
        textarea.send_keys(texto)
        print("Texto inserido via send_keys.")

    time.sleep(2)
    driver.switch_to.default_content()
    print("Voltando ao contexto principal...")

    # Espera o botão ficar clicável e clica
    botao_enviar = wait.until(EC.element_to_be_clickable((By.ID, "sendCelebration")))
    
    # Rola até o botão para garantir que ele esteja visível
    driver.execute_script("arguments[0].scrollIntoView(true);", botao_enviar)
    time.sleep(1)
    
    # Clica via JavaScript para evitar erros de "elemento interceptado"
    driver.execute_script("arguments[0].click();", botao_enviar)
    print("Botão de enviar celebração clicado!")
    
    print("Automação finalizada com sucesso!")

except Exception as e:
    print(f"Erro na celebração: {type(e).__name__} - {str(e)}")
    # Se der erro, tenta tirar o contexto do iframe para não travar o driver.quit()
    try: driver.switch_to.default_content() 
    except: pass

time.sleep(5)
driver.quit()
print("Processo finalizado.")
