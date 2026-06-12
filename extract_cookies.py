"""
Extract Feedz session cookies for GitHub Actions authentication.

Run this script LOCALLY after logging into Feedz manually.
It exports your session cookies as JSON — paste the output into
the FEEDZ_COOKIES secret in your GitHub repository.

Usage:
    python extract_cookies.py
    python extract_cookies.py -o cookies.json       # also save to file
"""
from __future__ import annotations

import argparse
import json

from playwright.sync_api import sync_playwright


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract Feedz cookies for GitHub Actions")
    parser.add_argument("-o", "--output", help="Save cookies to file (optional)")
    args = parser.parse_args()

    print("=" * 60)
    print("  Extrator de Cookies — Feedz")
    print("=" * 60)
    print()

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            args=["--disable-blink-features=AutomationControlled"],
        )
        page = browser.new_page(viewport={"width": 1280, "height": 900})

        print("▶ Navegando para app.feedz.com.br ...")
        page.goto("https://app.feedz.com.br")

        print()
        print("╔══════════════════════════════════════════════════════════════╗")
        print("║  Faça login MANUALMENTE no Feedz que abriu no navegador.   ║")
        print("║  Resolva o CAPTCHA com seus olhos 😄                       ║")
        print("║                                                             ║")
        print("║  Após o login, volte aqui e aperte ENTER...                 ║")
        print("╚══════════════════════════════════════════════════════════════╝")
        input()

        page.wait_for_timeout(2000)

        cookies = page.context.cookies()

        if not cookies:
            print("❌ Nenhum cookie encontrado. Verifique se o login foi concluído.")
            return 1

        cookie_json = json.dumps(cookies, indent=2, ensure_ascii=False)

        print()
        print("=" * 60)
        print("  COOKIES EXTRAÍDOS (copie o JSON abaixo):")
        print("=" * 60)
        print()
        print(cookie_json)
        print()

        if args.output:
            with open(args.output, "w") as f:
                f.write(cookie_json)
            print(f"✅ Cookies salvos em: {args.output}")

        print()
        print("╔══════════════════════════════════════════════════════════════════╗")
        print("║  INSTRUÇÕES — GitHub Actions                                   ║")
        print("║  1. Acesse: GitHub → Settings → Secrets and variables → Actions║")
        print("║  2. Crie um secret chamado FEEDZ_COOKIES                        ║")
        print("║  3. Cole todo o JSON acima como valor                           ║")
        print("║  4. Salve                                                      ║")
        print("║  ⚠ Os cookies expiram (30-90 dias). Repita quando falhar.      ║")
        print("╚══════════════════════════════════════════════════════════════════╝")

    return 0


if __name__ == "__main__":
    exit(main())
