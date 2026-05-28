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

# ... (previous imports)
chrome_options = Options()
if os.getenv('GITHUB_ACTIONS'):
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-gpu")

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)
wait = WebDriverWait(driver, 20) # Aumentado para 20 segundos

print("Iniciando acesso ao Feedz...")
driver.get("https://app.feedz.com.br/inicio")

print("Preenchendo login...")
wait.until(EC.presence_of_element_located((By.ID, "login_email"))).send_keys(login)
wait.until(EC.presence_of_element_located((By.ID, "passInput"))).send_keys(senha)
wait.until(EC.element_to_be_clickable((By.ID, "enter-login"))).click()

print("Login clicado, aguardando redirecionamento...")

# Verifica se o seletor de humor aparece
seletor_mood = "input.fdz_radio_button.input[value='4']"
try:
    print("Tentando encontrar o seletor de humor...")
    radio_button = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, seletor_mood)))
    driver.execute_script("arguments[0].click();", radio_button)
    print("Clique no botão de humor realizado com sucesso!")
    
    time.sleep(2)
    driver.find_element(By.ID, "fdz-btn-send-mood").click()
    print("Humor enviado!")
except Exception as e:
    print(f"Aviso: Não foi possível encontrar ou clicar no humor (Pode ser que ele já tenha sido respondido hoje). Erro: {type(e).__name__}")

time.sleep(5)
# ... rest of the code

URL_CELEBRACAO = "https://app.feedz.com.br/celebracoes"
driver.get(URL_CELEBRACAO)

wait.until(EC.frame_to_be_available_and_switch_to_it(0))
textarea = wait.until(EC.element_to_be_clickable((By.ID, "tinymce")))
driver.execute_script("arguments[0].click();", textarea)

try:
    textarea.clear()
    textarea.send_keys("Bom dia! @LucasNicoliniMartinsdeSouza @LiveaBritodaSilva @TassioLuizDantasdoCarmo @DiegoHenriquePereiraFreitas @VitorCarmodosSantos @LuizRzezak @JanaineMaielidaSilvaRibeiro @EduardoMazelli @RafaelAraujoMeiraDeJesus @EmmanoelPereiraVieira")
except:
    texto = "Bom dia! @LucasNicoliniMartinsdeSouza @LiveaBritodaSilva @TassioLuizDantasdoCarmo @DiegoHenriquePereiraFreitas @VitorCarmodosSantos  @LuizRzezak @JanaineMaielidaSilvaRibeiro @EduardoMazelli @RafaelAraujoMeiraDeJesus @EmmanoelPereiraVieira"
    driver.execute_script(f"arguments[0].innerHTML = '{texto}';", textarea)

driver.switch_to.default_content()

print("Automação executada com sucesso!")

driver.find_element(By.ID, "sendCelebration").click()

time.sleep(5)
driver.quit()