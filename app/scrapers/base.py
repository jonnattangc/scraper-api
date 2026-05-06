import logging
import os
import unicodedata
from abc import ABC, abstractmethod
from typing import Optional
from playwright.sync_api import sync_playwright, Page, Locator

ROOT_DIR = os.path.dirname(os.path.dirname(__file__))


class BaseScraper(ABC):
    """Clase abstracta base para todos los scrapers basados en Playwright."""

    def __init__(self, url: str, headless: bool = True, screenshot_dir: Optional[str] = None):
        self.url = url
        self.headless = headless
        self.screenshot_dir = screenshot_dir or os.path.join(ROOT_DIR, 'static')
        self._p = None
        self._browser = None
        self._page: Optional[Page] = None
        self._impl_name = self.get_impl()

    # ------------------------------------------------------------------
    # Ciclo de vida del browser
    # ------------------------------------------------------------------
    def start(self) -> None:
        if self._p is not None:
            return
        try:
            logging.info(f"[{self._impl_name}] - Iniciando Playwright (headless={self.headless})")
            self._p = sync_playwright().start()
            self._browser = self._p.chromium.launch(headless=self.headless)
            self._page = self._browser.new_page()
            self._page.goto(self.url)
            logging.info(f"[{self._impl_name}] - Navegando a {self.url}")
        except Exception as e:
            logging.error(f"[{self._impl_name}] - Error al iniciar: {e}")
            self.close()
            raise

    def close(self) -> None:
        try:
            if self._page:
                self._page.close()
                self._page = None
                logging.info(f"[{self._impl_name}] - Pagina cerrada")
        except Exception as e:
            logging.warning(f"[{self._impl_name}] - Error cerrando pagina: {e}")

        try:
            if self._browser:
                self._browser.close()
                self._browser = None
                logging.info(f"[{self._impl_name}] - Browser cerrado")
        except Exception as e:
            logging.warning(f"[{self._impl_name}] - Error cerrando browser: {e}")

        try:
            if self._p:
                self._p.stop()
                self._p = None
                logging.info(f"[{self._impl_name}] - Playwright detenido")
        except Exception as e:
            logging.warning(f"[{self._impl_name}] - Error deteniendo playwright: {e}")

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    # ------------------------------------------------------------------
    # Acceso seguro al page
    # ------------------------------------------------------------------
    @property
    def page(self) -> Page:
        if self._page is None:
            raise RuntimeError("El browser no ha sido iniciado. Usa 'with' o llama a start() primero.")
        return self._page

    # ------------------------------------------------------------------
    # Helpers comunes
    # ------------------------------------------------------------------
    def wait_for(self, selector: str, timeout: int = 10000) -> Locator:
        return self.page.wait_for_selector(selector, timeout=timeout)

    def fill_input(self, selector: str, value: str, timeout: int = 10000) -> Locator:
        element = self.wait_for(selector, timeout=timeout)
        element.fill(value)
        return element

    def click(self, selector: str, timeout: int = 10000) -> Locator:
        element = self.wait_for(selector, timeout=timeout)
        element.click()
        return element

    def screenshot(self, filename: str, full_page: bool = True) -> None:
        path = os.path.join(self.screenshot_dir, filename)
        try:
            self.page.screenshot(path=path, full_page=full_page)
            logging.info(f"[{self._impl_name}] - Screenshot: {path}")
        except Exception as e:
            logging.warning(f"[{self._impl_name}] - No se pudo guardar screenshot: {e}")

    @staticmethod
    def clean_text(texto: str, mantener_enie: bool = True) -> str:
        texto_normalizado = unicodedata.normalize('NFKD', texto)
        texto_limpio = []
        for caracter in texto_normalizado:
            if 'a' <= caracter.lower() <= 'z':
                texto_limpio.append(caracter)
            elif caracter.lower() == 'ñ':
                texto_limpio.append(caracter if mantener_enie else 'n')
            elif caracter.isspace():
                texto_limpio.append(caracter)
        return "".join(texto_limpio)

    def extract_first_names(self, full_name: str, max_words: int = 2) -> str:
        """Extrae las primeras N palabras de un nombre y limpia acentos."""
        cleaned = self.clean_text(full_name.strip())
        parts = cleaned.split()
        return " ".join(parts[:max_words]) if parts else "Desconocido"

    # ------------------------------------------------------------------
    # Abstractos
    # ------------------------------------------------------------------
    @abstractmethod
    def login(self, username: str, password: str) -> tuple[int, str]:
        """
        Realiza el login y retorna (grado, nombre).
        grado: 0 = fallo, 1 = Aprendiz, 2 = Compañero, 3 = Maestro
        """
        pass

    @abstractmethod
    def get_impl(self) -> str:
        """Retorna el identificador único del scraper."""
        pass

    def __str__(self):
        return self._impl_name
