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

print("Acessando página de celebrações...")
URL_CELEBRACAO = "https://app.feedz.com.br/celebracoes"
driver.get(URL_CELEBRACAO)
print(f"URL atual: {driver.current_url}")

try:
    print("Aguardando carregamento do iframe de celebração...")
    # Tenta esperar pelo iframe antes de trocar
    wait.until(EC.presence_of_element_located((By.TAG_NAME, "iframe")))
    print("Iframe encontrado, tentando trocar de contexto...")
    
    wait.until(EC.frame_to_be_available_and_switch_to_it(0))
    print("Contexto trocado para o iframe.")

    print("Buscando campo de texto (tinymce)...")
    textarea = wait.until(EC.element_to_be_clickable((By.ID, "tinymce")))
    print("Campo de texto encontrado!")

    driver.execute_script("arguments[0].click();", textarea)
    print("Campo de texto clicado.")

    try:
        textarea.clear()
        textarea.send_keys("Bom dia! @LucasNicoliniMartinsdeSouza @LiveaBritodaSilva @TassioLuizDantasdoCarmo @DiegoHenriquePereiraFreitas @VitorCarmodosSantos @LuizRzezak @JanaineMaielidaSilvaRibeiro @EduardoMazelli @RafaelAraujoMeiraDeJesus @EmmanoelPereiraVieira")
        print("Texto inserido via send_keys.")
    except Exception as e:
        print(f"Erro ao usar send_keys, tentando via script... ({type(e).__name__})")
        texto = "Bom dia! @LucasNicoliniMartinsdeSouza @LiveaBritodaSilva @TassioLuizDantasdoCarmo @DiegoHenriquePereiraFreitas @VitorCarmodosSantos @LuizRzezak @JanaineMaielidaSilvaRibeiro @EduardoMazelli @RafaelAraujoMeiraDeJesus @EmmanoelPereiraVieira"
        driver.execute_script(f"arguments[0].innerHTML = '{texto}';", textarea)
        print("Texto inserido via execute_script.")

    driver.switch_to.default_content()
    print("Voltando para o contexto principal.")

    print("Tentando clicar no botão de enviar celebração...")
    botao_enviar = wait.until(EC.element_to_be_clickable((By.ID, "sendCelebration")))
    botao_enviar.click()
    print("Botão de enviar clicado!")

    print("Automação executada com sucesso!")

except Exception as e:
    print(f"ERRO CRÍTICO na parte de celebrações: {type(e).__name__}")
    print(f"Mensagem de erro: {str(e)}")
    # Opcional: print do código fonte para depuração se necessário
    # print(driver.page_source[:500]) 

time.sleep(5)
driver.quit()
print("Driver encerrado.")