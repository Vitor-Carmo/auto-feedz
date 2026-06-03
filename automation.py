"""
Feedz Automation — Login, Humor e Celebração
Compatível com Python 3.12 e execução em GitHub Actions (headless).
"""
from __future__ import annotations
import json
import logging
import os
import random
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable
from selenium import webdriver
from selenium.common.exceptions import (
    NoSuchFrameException,
    StaleElementReferenceException,
    TimeoutException,
    WebDriverException,
)
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

# ── Logging ────────────────────────────────────────────────────────────────────
logger = logging.getLogger(__name__)


def configure_logging(level: str = "INFO") -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )
    logging.getLogger("WDM").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("selenium").setLevel(logging.WARNING)


# ── Configuração ───────────────────────────────────────────────────────────────
@dataclass
class Config:
    login: str
    password: str
    mood_value: str = "4"
    celebration_text: str = (
        "Bom dia! "
        "@LucasNicoliniMartinsdeSouza @LiveaBritodaSilva @TassioLuizDantasdoCarmo "
        "@DiegoHenriquePereiraFreitas @LuizRzezak "
        "@JanaineMaielidaSilvaRibeiro @EduardoMazelli @RafaelAraujoMeiraDeJesus "
        "@EmmanoelPereiraVieira"
    )
    base_url: str = "https://app.feedz.com.br"
    headless: bool = field(default_factory=lambda: bool(os.getenv("CI") or os.getenv("GITHUB_ACTIONS")))
    screenshot_dir: Path = field(default_factory=lambda: Path(os.getenv("SCREENSHOT_DIR", "screenshots")))
    page_load_timeout: int = 60
    implicit_wait: int = 0
    explicit_wait: int = 30
    max_retries: int = 3
    log_level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))

    @classmethod
    def from_env(cls) -> "Config":
        login = os.getenv("FEEDZ_LOGIN") or os.getenv("seu_login", "")
        password = os.getenv("FEEDZ_PASSWORD") or os.getenv("sua_senha", "")
        if not login or not password:
            raise EnvironmentError(
                "Credenciais não encontradas. "
                "Defina FEEDZ_LOGIN e FEEDZ_PASSWORD (ou as variáveis legadas seu_login/sua_senha)."
            )
        return cls(
            login=login,
            password=password,
            mood_value=os.getenv("FEEDZ_MOOD", "4"),
        )


# ── Helpers de comportamento humano ───────────────────────────────────────────
def human_delay(min_s: float = 0.8, max_s: float = 2.2) -> None:
    """Pausa randômica para simular ritmo humano."""
    time.sleep(random.uniform(min_s, max_s))


def human_type(element: WebElement, text: str) -> None:
    """Digita caractere a caractere com velocidade variável."""
    for char in text:
        element.send_keys(char)
        time.sleep(random.uniform(0.07, 0.18))
        if random.random() < 0.04:
            time.sleep(random.uniform(0.25, 0.55))


def jitter_move_and_click(driver: WebDriver, element: WebElement) -> None:
    try:
        actions = ActionChains(driver)
        (
            actions
            .move_to_element_with_offset(element, random.randint(-3, 3), random.randint(-3, 3))
            .pause(random.uniform(0.08, 0.20))
            .move_to_element(element)
            .pause(random.uniform(0.05, 0.12))
            .click()
            .perform()
        )
    except WebDriverException:
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", element)
        time.sleep(0.2)
        element.click()


def scroll_to(driver: WebDriver, element: WebElement) -> None:
    driver.execute_script("arguments[0].scrollIntoView({behavior:'smooth',block:'center'});", element)
    time.sleep(random.uniform(0.3, 0.6))


# ── Utilitário de retry ────────────────────────────────────────────────────────
def with_retry(
    fn: Callable,
    *,
    retries: int = 3,
    delay: float = 2.0,
    exceptions: tuple[type[Exception], ...] = (Exception,),
    label: str = "operação",
) -> None:
    """Executa `fn` com retry exponencial em caso de falha."""
    for attempt in range(1, retries + 1):
        try:
            fn()
            return
        except exceptions as exc:
            logger.warning("Tentativa %d/%d falhou para %s: %s", attempt, retries, label, exc)
            if attempt == retries:
                raise
            time.sleep(delay * attempt)


# ── Chrome Driver Factory ──────────────────────────────────────────────────────
def build_driver(cfg: Config) -> WebDriver:
    options = Options()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    options.add_argument(
        "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    )
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--lang=pt-BR,pt")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-infobars")
    options.add_argument("--disable-dev-shm-usage")

    if cfg.headless:
        logger.info("Modo headless ativado (CI detectado).")
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-gpu")
        options.add_argument("--force-device-scale-factor=1")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": (
            "Object.defineProperty(navigator,'webdriver',{get:()=>undefined});"
            "Object.defineProperty(navigator,'languages',{get:()=>['pt-BR','pt','en-US']});"
        )
    })
    driver.set_page_load_timeout(cfg.page_load_timeout)
    return driver


# ── Screenshot em falha ────────────────────────────────────────────────────────
def save_failure_screenshot(driver: WebDriver, name: str, cfg: Config) -> None:
    cfg.screenshot_dir.mkdir(parents=True, exist_ok=True)
    path = cfg.screenshot_dir / f"{name}_{int(time.time())}.png"
    try:
        driver.save_screenshot(str(path))
        logger.info("Screenshot salvo: %s", path)
    except WebDriverException as exc:
        logger.warning("Não foi possível salvar screenshot: %s", exc)


# ── Etapas da automação ────────────────────────────────────────────────────────
class FeedzAutomation:
    def __init__(self, cfg: Config) -> None:
        self.cfg = cfg
        self.driver: WebDriver | None = None
        self._wait: WebDriverWait | None = None

    # ── Ciclo de vida ──────────────────────────────────────────────────────────
    def __enter__(self) -> "FeedzAutomation":
        self.driver = build_driver(self.cfg)
        self._wait = WebDriverWait(
            self.driver,
            self.cfg.explicit_wait,
            ignored_exceptions=(StaleElementReferenceException,),
        )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if self.driver:
            try:
                self.driver.quit()
                logger.info("Navegador encerrado.")
            except WebDriverException:
                pass

    @property
    def wait(self) -> WebDriverWait:
        assert self._wait is not None, "Driver não inicializado — use 'with FeedzAutomation(cfg) as fa:'"
        return self._wait

    # ── Helpers internos ───────────────────────────────────────────────────────
    def _go(self, path: str) -> None:
        url = f"{self.cfg.base_url}{path}"
        logger.debug("Navegando para: %s", url)
        self.driver.get(url)  # type: ignore[union-attr]

    def _screenshot_on_error(self, stage: str) -> None:
        if self.driver:
            save_failure_screenshot(self.driver, stage, self.cfg)

    # ── ETAPA 1: Login ─────────────────────────────────────────────────────────
    def login(self) -> None:
        logger.info("▶ Etapa 1: Login")
        self._go("/inicio")
        human_delay(2.0, 4.0)
        try:
            self._fill_login_form()
            self._await_post_login()
            logger.info("✔ Login concluído. URL: %s", self.driver.current_url)  # type: ignore[union-attr]
        except Exception as exc:
            self._screenshot_on_error("login_failure")
            raise RuntimeError(f"Falha no login: {exc}") from exc

    def _fill_login_form(self) -> None:
        d = self.driver
        email_field: WebElement = self.wait.until(
            EC.element_to_be_clickable((By.ID, "login_email"))
        )
        jitter_move_and_click(d, email_field)  # type: ignore[arg-type]
        human_delay(0.3, 0.6)
        human_type(email_field, self.cfg.login)
        human_delay(0.5, 1.2)

        pass_field: WebElement = self.wait.until(
            EC.element_to_be_clickable((By.ID, "passInput"))
        )
        jitter_move_and_click(d, pass_field)  # type: ignore[arg-type]
        human_delay(0.2, 0.5)
        human_type(pass_field, self.cfg.password)
        human_delay(0.7, 1.5)

        # ── Tenta resolver o reCAPTCHA antes de clicar em Entrar ──────────────
        self._try_solve_recaptcha()
        human_delay(0.5, 1.0)

        btn_login: WebElement = self.wait.until(
            EC.element_to_be_clickable((By.ID, "enter-login"))
        )
        jitter_move_and_click(d, btn_login)  # type: ignore[arg-type]

    def _try_solve_recaptcha(self) -> bool:
        """
        Tenta clicar no checkbox 'Não sou um robô' do reCAPTCHA v2.
        Retorna True se o clique foi realizado, False se o captcha não estava presente.

        Observação: isso resolve apenas o desafio de checkbox (reCAPTCHA v2 sem imagem).
        Se o Feedz exigir o desafio de imagens, a resolução automática não é possível
        com Selenium puro — nesse caso considere um serviço externo (2captcha, CapMonster)
        ou autenticação via cookie persistente (veja load_cookies()).
        """
        try:
            # Aguarda o iframe do reCAPTCHA (timeout curto: não trava se ausente)
            WebDriverWait(self.driver, 5).until(
                EC.frame_to_be_available_and_switch_to_it(
                    (By.XPATH, '//iframe[@title="reCAPTCHA"]')
                )
            )
            checkbox: WebElement = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((By.CLASS_NAME, "recaptcha-checkbox-border"))
            )
            jitter_move_and_click(self.driver, checkbox)  # type: ignore[arg-type]
            logger.info("✔ reCAPTCHA checkbox clicado.")
            time.sleep(3)  # aguarda validação visual do Google
            self.driver.switch_to.default_content()  # type: ignore[union-attr]
            return True
        except (TimeoutException, WebDriverException) as exc:
            self.driver.switch_to.default_content()  # type: ignore[union-attr]
            logger.debug("reCAPTCHA não encontrado ou não necessário: %s", exc)
            return False

    def _await_post_login(self) -> None:
        """
        Aguarda o redirecionamento pós-login.
        Considera sucesso quando a URL sai de /inicio OU a sidebar já carregou.
        """
        self.wait.until(
            lambda d: (
                "/inicio" not in d.current_url
                or d.find_elements(By.CLASS_NAME, "fdz-sidebar")
            )
        )

    # ── ETAPA 2: Humor ─────────────────────────────────────────────────────────
    def register_mood(self) -> None:
        logger.info("▶ Etapa 2: Humor")
        try:
            self._do_register_mood()
            logger.info("✔ Humor registrado.")
        except TimeoutException:
            logger.info("ℹ Humor ignorado (modal ausente — já preenchido hoje ou feature desabilitada).")
        except Exception as exc:
            self._screenshot_on_error("mood_failure")
            logger.warning("⚠ Falha ao registrar humor (não crítico): %s", exc)

    def _do_register_mood(self) -> None:
        selector = f"input.fdz_radio_button.input[value='{self.cfg.mood_value}']"
        radio: WebElement = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, selector))
        )
        human_delay(0.4, 0.9)
        self.driver.execute_script("arguments[0].click();", radio)  # type: ignore[union-attr]
        human_delay(0.5, 1.1)

        btn_send: WebElement = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.ID, "fdz-btn-send-mood"))
        )
        jitter_move_and_click(self.driver, btn_send)  # type: ignore[arg-type]

    # ── ETAPA 3: Celebração ────────────────────────────────────────────────────
    def post_celebration(self) -> None:
        logger.info("▶ Etapa 3: Celebração")
        try:
            with_retry(
                self._do_post_celebration,
                retries=self.cfg.max_retries,
                delay=3.0,
                exceptions=(WebDriverException, TimeoutException),
                label="post_celebration",
            )
            logger.info("✔ Celebração publicada.")
        except Exception as exc:
            self._screenshot_on_error("celebration_failure")
            raise RuntimeError(f"Falha ao publicar celebração: {exc}") from exc

    def _do_post_celebration(self) -> None:
        self._go("/celebracoes")
        human_delay(2.0, 3.5)

        if not self._insert_via_tinymce_api():
            self._insert_via_iframe_fallback()

        self.driver.switch_to.default_content()  # type: ignore[union-attr]
        human_delay(1.2, 2.0)

        btn_send: WebElement = self.wait.until(
            EC.element_to_be_clickable((By.ID, "sendCelebration"))
        )
        scroll_to(self.driver, btn_send)  # type: ignore[arg-type]
        jitter_move_and_click(self.driver, btn_send)  # type: ignore[arg-type]

    def _insert_via_tinymce_api(self) -> bool:
        """
        Tenta inserir o texto pela API JS do TinyMCE.
        Retorna True se bem-sucedido.
        """
        try:
            WebDriverWait(self.driver, 15).until(
                lambda d: d.execute_script(
                    "return typeof tinyMCE !== 'undefined' "
                    "&& tinyMCE.activeEditor !== null "
                    "&& tinyMCE.activeEditor.initialized === true;"
                )
            )
            escaped = self.cfg.celebration_text.replace("'", "\\'")
            self.driver.execute_script(  # type: ignore[union-attr]
                f"tinyMCE.activeEditor.setContent('{escaped}');"
                "tinyMCE.activeEditor.fire('change');"
                "tinyMCE.activeEditor.fire('input');"
            )
            logger.debug("Texto inserido via API TinyMCE.")
            return True
        except (TimeoutException, WebDriverException) as exc:
            logger.debug("TinyMCE API indisponível (%s); tentando iframe.", exc)
            return False

    def _insert_via_iframe_fallback(self) -> None:
        """Insere o texto diretamente no iframe do TinyMCE via send_keys."""
        try:
            self.wait.until(EC.frame_to_be_available_and_switch_to_it(0))
        except (TimeoutException, NoSuchFrameException) as exc:
            raise RuntimeError("Iframe do editor não encontrado.") from exc

        textarea: WebElement = self.wait.until(
            EC.presence_of_element_located((By.ID, "tinymce"))
        )
        textarea.click()
        self.driver.execute_script("arguments[0].innerHTML = '';", textarea)  # type: ignore[union-attr]
        human_delay(0.4, 0.8)
        human_type(textarea, self.cfg.celebration_text)
        logger.debug("Texto inserido via iframe (fallback send_keys).")

    # ── Pipeline principal ─────────────────────────────────────────────────────
    def run(self) -> None:
        self.login()
        self.register_mood()
        self.post_celebration()
        human_delay(2.0, 4.0)
        logger.info("✅ Automação finalizada com sucesso.")


def load_cookies(driver):
    cookies = json.loads(os.environ["FEEDZ_COOKIES"])
    driver.get("https://app.feedz.com.br")
    for cookie in cookies:
        try:
            cookie.pop("sameSite", None)
            driver.add_cookie(cookie)
        except Exception:
            pass
    driver.refresh()


# ── Entrypoint ─────────────────────────────────────────────────────────────────
def main() -> None:
    try:
        cfg = Config.from_env()
    except EnvironmentError as exc:
        logging.basicConfig(level=logging.ERROR)
        logger.error("%s", exc)
        raise SystemExit(1) from exc

    configure_logging(cfg.log_level)

    try:
        with FeedzAutomation(cfg) as automation:
            automation.run()
    except Exception as exc:
        logger.error("Automação encerrada com erro: %s", exc)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()