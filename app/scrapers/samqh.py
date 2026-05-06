try:
    import logging
    from scrapers.base import BaseScraper

except ImportError:
    import logging
    import sys
    import os
    logging.error(ImportError)
    print((os.linesep * 2).join(['[Samqh] Error al buscar los modulos:', str(sys.exc_info()[1]), 'Debes Instalarlos para continuar', 'Deteniendo...']))
    sys.exit(-2)

IMPL: str = 'SAMQH'


class Samqh(BaseScraper):

    def __init__(self):
        super().__init__(url="https://samqh.glch.cl")

    def get_impl(self) -> str:
        return IMPL

    def login(self, username: str, password: str) -> tuple[int, str]:
        name: str = "Desconocido"
        grade: int = 0
        try:
            logging.info(f"[{IMPL}] - Esperando formulario de login")
            self.fill_input("//input[@id='id_sc_field_login']", username)
            self.fill_input("//input[@id='id_sc_field_pswd']", password)
            self.click("//a[@id='sub_form_b']/span[@class='btn-label']")
            logging.info(f"[{IMPL}] - Presionando el boton de ingresar...")

            self.wait_for("//a[@id='item_33']", timeout=5000)
            self.screenshot("posterior_a_login.png")
            self.click("//a[@id='item_33']")
            logging.info(f"[{IMPL}] - Login exitoso, detectando nombre...")

            text_name = self.wait_for("//span[@id='lin1_col2']", timeout=10000)
            raw = str(text_name.inner_text())
            parts = raw.split('QH:. ')
            if len(parts) == 2:
                name = self.extract_first_names(parts[1], max_words=3)
            logging.info(f"[{IMPL}] - Nombre detectado: {name}")
            grade = 1

        except Exception as e:
            logging.error(f"[{IMPL}] - Error en login: {e}")
        finally:
            logging.info(f"[{IMPL}] - Fin proceso de login")

        return grade, name
