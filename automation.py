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
from datetime import datetime
from pathlib import Path
from typing import Callable
from zoneinfo import ZoneInfo

from dotenv import load_dotenv
from playwright.sync_api import (
    Browser,
    BrowserContext,
    Page,
    TimeoutError as PwTimeoutError,
    sync_playwright,
)

# ── Logging ────────────────────────────────────────────────────────────────────
logger = logging.getLogger(__name__)


def configure_logging(level: str = "INFO") -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )
    logging.getLogger("urllib3").setLevel(logging.WARNING)


# ── Configuração ───────────────────────────────────────────────────────────────
@dataclass
class Config:
    login: str
    password: str
    mood_value: str = "4"
    _base_celebration_text: str = (
        "@LucasNicoliniMartinsdeSouza @LiveaBritodaSilva @SamuelHeitorMaragatoFerreiraApolinari "
        "@DiegoHenriquePereiraFreitas @LuizRzezak @LuisHenriqueRibeiro "
        "@JanaineMaielidaSilvaRibeiro @EduardoMazelli @RafaelAraujoMeiraDeJesus "
        "@EmmanoelPereiraVieira @EduardaRibasdaSilva @AnneRodriguesdosSantos "
        "@AlexSandroSoaresFerreira @VitoriaAlbertinaRibeirodeSantana @LeonardoSegobiaPapini"
    )

    def get_celebration_text(self) -> str:
        return f"{greeting_by_time()}, galera! {self._base_celebration_text}"

    base_url: str = "https://app.feedz.com.br"
    headless: bool = field(
        default_factory=lambda: bool(os.getenv("CI") or os.getenv("GITHUB_ACTIONS"))
    )
    screenshot_dir: Path = field(
        default_factory=lambda: Path(os.getenv("SCREENSHOT_DIR", "screenshots"))
    )
    explicit_wait: int = 30_000  # ms
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
    time.sleep(random.uniform(min_s, max_s))


def human_type(page: Page, selector: str, text: str) -> None:
    locator = page.locator(selector)
    locator.click()
    page.wait_for_timeout(random.randint(100, 300))
    locator.fill("")
    page.keyboard.type(text, delay=random.randint(70, 180))


def jitter_move_and_click(page: Page, selector: str) -> None:
    locator = page.locator(selector)
    box = locator.bounding_box()
    if box:
        page.mouse.move(
            box["x"] + box["width"] / 2 + random.randint(-3, 3),
            box["y"] + box["height"] / 2 + random.randint(-3, 3),
        )
        page.wait_for_timeout(random.randint(80, 200))
    locator.click()


def scroll_to(page: Page, selector: str) -> None:
    page.locator(selector).scroll_into_view_if_needed()
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
    for attempt in range(1, retries + 1):
        try:
            fn()
            return
        except exceptions as exc:
            logger.warning(
                "Tentativa %d/%d falhou para %s: %s", attempt, retries, label, exc
            )
            if attempt == retries:
                raise
            time.sleep(delay * attempt)


# ── Saudação baseada no horário ────────────────────────────────────────────────
TZ_BR = ZoneInfo("America/Sao_Paulo")


def greeting_by_time() -> str:
    hour = datetime.now(TZ_BR).hour
    if hour < 12:
        return "Bom dia"
    if hour < 18:
        return "Boa tarde"
    return "Boa noite"


# ── Screenshot em falha ────────────────────────────────────────────────────────
def save_failure_screenshot(page: Page, name: str, cfg: Config) -> None:
    cfg.screenshot_dir.mkdir(parents=True, exist_ok=True)
    path = cfg.screenshot_dir / f"{name}_{int(time.time())}.png"
    try:
        page.screenshot(path=str(path))
        logger.info("Screenshot salvo: %s", path)
    except Exception as exc:
        logger.warning("Não foi possível salvar screenshot: %s", exc)


# ── Etapas da automação ────────────────────────────────────────────────────────
class FeedzAutomation:
    def __init__(self, cfg: Config) -> None:
        self.cfg = cfg
        self._pw = None
        self._browser: Browser | None = None
        self._context: BrowserContext | None = None
        self._page: Page | None = None

    # ── Ciclo de vida ──────────────────────────────────────────────────────────
    def __enter__(self) -> "FeedzAutomation":
        self._pw = sync_playwright().start()
        self._browser = self._pw.chromium.launch(
            headless=self.cfg.headless,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
                "--no-sandbox",
                "--disable-gpu",
            ],
        )
        self._context = self._browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/126.0.0.0 Safari/537.36"
            ),
            locale="pt-BR",
            timezone_id="America/Sao_Paulo",
        )
        self._page = self._context.new_page()
        self._page.set_default_timeout(self.cfg.explicit_wait)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        try:
            if self._browser:
                self._browser.close()
        finally:
            if self._pw:
                self._pw.stop()

    # ── Helpers internos ──────────────────────────────────────────────────────
    @property
    def page(self) -> Page:
        assert self._page is not None, "Navegador não inicializado"
        return self._page

    def _go(self, path: str) -> None:
        self.page.goto(f"{self.cfg.base_url}{path}", wait_until="domcontentloaded")

    def _screenshot_on_error(self, stage: str) -> None:
        if self._page:
            save_failure_screenshot(self._page, stage, self.cfg)

    # ── Autenticação via cookie (CI) ─────────────────────────────────────────
    def _try_cookie_auth(self) -> bool:
        cookies_json = os.getenv("FEEDZ_COOKIES")
        if not cookies_json:
            logger.info("FEEDZ_COOKIES não definido — usando login normal.")
            return False
        try:
            cookies = json.loads(cookies_json)
            self._go("")
            self._context.add_cookies(cookies)
            self.page.reload()
            human_delay(2.5, 4.0)
            if "login" in self.page.url.lower():
                logger.warning(
                    "Cookies não funcionaram — ainda na página de login."
                )
                self._screenshot_on_error("cookies_expired")
                return False
            if self.page.locator(".fdz-sidebar").count() > 0 or "/inicio" in self.page.url:
                logger.info("✔ Cookies carregados — sessão restaurada com sucesso.")
                return True
            logger.warning(
                "Cookies expirados ou inválidos — fallback para login via credenciais."
            )
            self._screenshot_on_error("cookies_expired")
            return False
        except (json.JSONDecodeError, Exception) as exc:
            logger.warning(
                "Falha ao processar FEEDZ_COOKIES: %s. Usando login normal.", exc
            )
            return False

    # ── ETAPA 1: Login ─────────────────────────────────────────────────────────
    def login(self) -> None:
        logger.info("▶ Etapa 1: Login")
        if self._try_cookie_auth():
            return
        self._go("/inicio")
        human_delay(2.0, 4.0)
        try:
            self._fill_login_form()
            self._await_post_login()
            logger.info("✔ Login concluído. URL: %s", self.page.url)
        except Exception as exc:
            self._screenshot_on_error("login_failure")
            raise RuntimeError(f"Falha no login: {exc}") from exc

    def _fill_login_form(self) -> None:
        p = self.page
        p.locator("#login_email").click()
        human_delay(0.3, 0.6)
        p.locator("#login_email").fill(self.cfg.login)
        human_delay(0.5, 1.2)

        p.locator("#passInput").click()
        human_delay(0.2, 0.5)
        p.locator("#passInput").fill(self.cfg.password)
        human_delay(0.7, 1.5)

        self._try_solve_recaptcha()
        human_delay(0.5, 1.0)

        jitter_move_and_click(p, "#enter-login")

    def _try_solve_recaptcha(self) -> bool:
        try:
            frame = self.page.frame_locator('iframe[title="reCAPTCHA"]')
            frame.locator(".recaptcha-checkbox-border").click(timeout=5000)
            logger.info("✔ reCAPTCHA checkbox clicado.")
            self.page.wait_for_timeout(3000)
            return True
        except (PwTimeoutError, Exception) as exc:
            logger.debug("reCAPTCHA não encontrado ou não necessário: %s", exc)
            return False

    def _await_post_login(self) -> None:
        try:
            self.page.wait_for_function(
                "window.location.href.indexOf('/inicio') === -1"
                " || document.querySelector('.fdz-sidebar') !== null",
                timeout=self.cfg.explicit_wait,
            )
        except PwTimeoutError:
            pass

    # ── ETAPA 2: Humor ─────────────────────────────────────────────────────────
    def register_mood(self) -> None:
        logger.info("▶ Etapa 2: Humor")
        try:
            self._do_register_mood()
            logger.info("✔ Humor registrado.")
        except PwTimeoutError:
            logger.info(
                "ℹ Humor ignorado (modal ausente — já preenchido hoje ou feature desabilitada)."
            )
        except Exception as exc:
            self._screenshot_on_error("mood_failure")
            logger.warning("⚠ Falha ao registrar humor (não crítico): %s", exc)

    def _do_register_mood(self) -> None:
        p = self.page
        mood_map = {
            "1": "Muito triste", "2": "Triste", "3": "Neutro",
            "4": "Feliz", "5": "Muito feliz",
        }
        mood_alt = mood_map.get(self.cfg.mood_value, "Feliz")

        try:
            img = p.locator(f"label.radio-inline img[alt='{mood_alt}']")
            img.wait_for(timeout=5_000)
            img.click()
            logger.debug("Humor clicado via imagem: %s", mood_alt)
        except PwTimeoutError:
            sel = f"input.fdz_radio_button.input[value='{self.cfg.mood_value}']"
            radio = p.locator(sel)
            radio.wait_for(timeout=5_000, state="attached")
            radio.evaluate("el => el.click()")
            logger.debug("Humor clicado via JS no input.")

        human_delay(0.5, 1.1)

        btn_send = p.locator("#fdz-btn-send-mood")
        btn_send.wait_for(timeout=10_000)
        btn_send.click()

    # ── ETAPA 3: Celebração ────────────────────────────────────────────────────
    def post_celebration(self) -> None:
        logger.info("▶ Etapa 3: Celebração")
        try:
            with_retry(
                self._do_post_celebration,
                retries=self.cfg.max_retries,
                delay=3.0,
                exceptions=(PwTimeoutError, Exception),
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

        human_delay(1.2, 2.0)

        btn_send = self.page.locator("#sendCelebration")
        btn_send.scroll_into_view_if_needed()
        btn_send.click()

    def _insert_via_tinymce_api(self) -> bool:
        try:
            self.page.wait_for_function(
                "typeof tinyMCE !== 'undefined'"
                " && tinyMCE.activeEditor !== null"
                " && tinyMCE.activeEditor.initialized === true",
                timeout=15_000,
            )
            escaped = self.cfg.get_celebration_text().replace("'", "\\'")
            self.page.evaluate(
                f"tinyMCE.activeEditor.setContent('{escaped}');"
                "tinyMCE.activeEditor.fire('change');"
                "tinyMCE.activeEditor.fire('input');"
            )
            logger.debug("Texto inserido via API TinyMCE.")
            return True
        except PwTimeoutError as exc:
            logger.debug("TinyMCE API indisponível (%s); tentando iframe.", exc)
            return False

    def _insert_via_iframe_fallback(self) -> None:
        try:
            self.page.wait_for_selector("iframe.tox-edit-area__iframe", timeout=10_000)
        except PwTimeoutError as exc:
            raise RuntimeError("Iframe do editor não encontrado.") from exc

        frame = self.page.frame_locator("iframe.tox-edit-area__iframe")
        editor = frame.locator("#tinymce")
        editor.click()
        editor.evaluate("el => el.innerHTML = ''")
        human_delay(0.4, 0.8)
        self.page.keyboard.type(self.cfg.get_celebration_text(), delay=80)
        logger.debug("Texto inserido via iframe (fallback).")

    # ── Pipeline principal ─────────────────────────────────────────────────────
    def run(self) -> None:
        self.login()
        self.register_mood()
        self.post_celebration()
        human_delay(2.0, 4.0)
        logger.info("✅ Automação finalizada com sucesso.")


# ── Entrypoint ─────────────────────────────────────────────────────────────────
def main() -> None:
    load_dotenv()

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
