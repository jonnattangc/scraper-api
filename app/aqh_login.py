#!/usr/bin/python

try:
    import logging
    import sys
    import os
    import json
    from abc import ABC, abstractmethod
    from playwright.sync_api import sync_playwright
    from playwright.sync_api import Page

except ImportError:
    logging.error(ImportError)
    print((os.linesep * 2).join(['[AQHLogin] Error al buscar los modulos:', str(sys.exc_info()[1]), 'Debes Instalarlos para continuar', 'Deteniendo...']))
    sys.exit(-2)

ROOT_DIR = os.path.dirname(__file__)

class AQHLogin(ABC):
    p = None
    browser = None
    page : Page = None
    url = None

    def __init__(self, *args, **kwargs) :
        if len(args) > 0 or kwargs['url'] is not None:
            self.url = kwargs['url']
            self.page = kwargs['page']
            self.initialize()
        else :
            logging.error(f"[{self}] - ERROR: URL no encontrada")
            raise Exception("URL no encontrada")

    def close_browser(self):
        if self.page:
            self.page.close()
            logging.info(f"[{self}] - Pagina Cerrada")
        if self.browser:
            self.browser.close()
            logging.info(f"[{self}] - Browser Cerrado")
        if self.p != None :
            self.p.stop()
            logging.info(f"[{self}] - Playwright Cerrado")
    @abstractmethod
    def login(self, username: str, password: str)  -> tuple[int, str] :
        pass

    def initialize(self): 
        try :
            logging.info(f"[{self}] - Iniciando Playwright headless")
            self.p = sync_playwright().start()
            self.browser = self.p.chromium.launch(headless=True) 
            self.page = self.browser.new_page()
            self.page.goto(self.url)
            logging.info(f"[{self}] - Navegando a {self.url}")
        except Exception as e:
            logging.error(f"[{self}] - {e}")

    @abstractmethod
    def get_impl(self) -> str:
        pass 

    def __str__(self):
        return f"{self.get_impl()}"
