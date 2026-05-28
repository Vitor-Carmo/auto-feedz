import os
import time
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
    print("Certifique-se de que configurou os Secrets no GitHub Settings > Secrets > Actions.")
    exit(1)

chrome_options = Options()
if os.getenv('GITHUB_ACTIONS'):
    print("Ambiente GitHub Actions detectado. Usando modo headless...")
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

print("Instalando/Iniciando ChromeDriver...")
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)
wait = WebDriverWait(driver, 25)

print("--- ETAPA 1: LOGIN ---")
driver.get("https://app.feedz.com.br/inicio")
print(f"Página de login carregada. Título: {driver.title}")

try:
    print("Preenchendo campos de login...")
    wait.until(EC.presence_of_element_located((By.ID, "login_email"))).send_keys(login)
    wait.until(EC.presence_of_element_located((By.ID, "passInput"))).send_keys(senha)
    
    print("Clicando no botão de entrar...")
    botao_login = wait.until(EC.element_to_be_clickable((By.ID, "enter-login")))
    botao_login.click()
    
    print("Aguardando confirmação de login (sidebar)...")
    wait.until(EC.presence_of_element_located((By.CLASS_NAME, "fdz-sidebar")))
    print("Login realizado com sucesso! Sidebar encontrada.")
except Exception as e:
    print(f"ERRO NO LOGIN: {type(e).__name__}")
    print(f"URL atual: {driver.current_url}")
    # print(f"Código fonte (trecho): {driver.page_source[:500]}")
    # Se falhar o login, não adianta continuar
    driver.quit()
    exit(1)

print("--- ETAPA 2: HUMOR ---")
seletor_mood = "input.fdz_radio_button.input[value='4']"
try:
    print("Tentando encontrar o seletor de humor...")
    # Espera curta para o humor, pois ele pode não existir
    wait_humor = WebDriverWait(driver, 10)
    radio_button = wait_humor.until(EC.presence_of_element_located((By.CSS_SELECTOR, seletor_mood)))
    driver.execute_script("arguments[0].click();", radio_button)
    print("Clique no botão de humor realizado!")
    
    time.sleep(2)
    driver.find_element(By.ID, "fdz-btn-send-mood").click()
    print("Humor enviado com sucesso!")
except:
    print("Aviso: Humor não encontrado ou já respondido.")

print("--- ETAPA 3: CELEBRAÇÃO ---")
print("Navegando para /celebracoes...")
driver.get("https://app.feedz.com.br/celebracoes")
time.sleep(5)
print(f"URL atual: {driver.current_url}")

if "/celebracoes" not in driver.current_url:
    print("AVISO: A URL atual não parece ser a de celebrações. Tentando forçar novamente...")
    driver.get("https://app.feedz.com.br/celebracoes")
    time.sleep(5)

try:
    print("Buscando iframes na página...")
    iframes = driver.find_elements(By.TAG_NAME, "iframe")
    print(f"Total de iframes: {len(iframes)}")

    print("Tentando entrar no iframe do editor...")
    wait.until(EC.frame_to_be_available_and_switch_to_it(0))
    print("Contexto alterado para o iframe.")

    print("Buscando textarea (tinymce)...")
    textarea = wait.until(EC.presence_of_element_located((By.ID, "tinymce")))
    print("Campo tinymce encontrado!")

    print("Limpando e inserindo texto...")
    driver.execute_script("arguments[0].innerHTML = '';", textarea)
    texto = "Bom dia! @LucasNicoliniMartinsdeSouza @LiveaBritodaSilva @TassioLuizDantasdoCarmo @DiegoHenriquePereiraFreitas @VitorCarmodosSantos @LuizRzezak @JanaineMaielidaSilvaRibeiro @EduardoMazelli @RafaelAraujoMeiraDeJesus @EmmanoelPereiraVieira"
    textarea.send_keys(texto)
    print("Texto inserido.")

    driver.switch_to.default_content()
    print("Voltando para o contexto principal...")

    print("Clicando em enviar celebração...")
    botao_enviar = wait.until(EC.element_to_be_clickable((By.ID, "sendCelebration")))
    botao_enviar.click()
    print("Botão de enviar clicado!")
    
    print("Automação finalizada com sucesso!")

except Exception as e:
    print(f"ERRO NA CELEBRAÇÃO: {type(e).__name__}")
    print(f"Mensagem: {str(e)}")
    print(f"URL no momento do erro: {driver.current_url}")

time.sleep(5)
driver.quit()
print("Sessão encerrada.")
