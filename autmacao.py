import os
import time
import dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

login = os.getenv('seu_login')
senha = os.getenv('sua_senha')

driver = webdriver.Chrome()
wait = WebDriverWait(driver, 10)

driver.get("https://app.feedz.com.br/inicio")

wait.until(EC.presence_of_element_located((By.ID, "login_email"))).send_keys(login)
wait.until(EC.presence_of_element_located((By.ID, "passInput"))).send_keys(senha)
wait.until(EC.element_to_be_clickable((By.ID, "enter-login"))).click()

seletor_mood = "input.fdz_radio_button.input[value='4']"
radio_button = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, seletor_mood)))

driver.execute_script("arguments[0].click();", radio_button)

print("Clique no botão de humor realizado com sucesso!")
time.sleep(5)
driver.find_element(By.ID, "fdz-btn-send-mood").click()
time.sleep(10)

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