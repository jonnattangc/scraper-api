try:
    import logging
    from scrapers.base import BaseScraper

except ImportError:
    import logging
    import sys
    import os
    logging.error(ImportError)
    print((os.linesep * 2).join(['[Mimasoneria] Error al buscar los modulos:', str(sys.exc_info()[1]), 'Debes Instalarlos para continuar', 'Deteniendo...']))
    sys.exit(-2)

IMPL: str = 'MIMASONERIA'


class Mimasoneria(BaseScraper):

    def __init__(self):
        super().__init__(url="https://www.mimasoneria.cl/web/login")

    def get_impl(self) -> str:
        return IMPL

    def login(self, username: str, password: str) -> tuple[int, str]:
        name: str = "Desconocido"
        grade: int = 0
        try:
            logging.info(f"[{IMPL}] - Esperando formulario de login")
            self.fill_input("//input[@id='login']", username)
            self.fill_input("//input[@id='password']", password)
            self.click("//div[3]/button")
            logging.info(f"[{IMPL}] - Presionando el boton de ingresar...")

            # Esperar menú principal
            self.wait_for("//img[@alt='Biblioteca']", timeout=5000)
            self.screenshot("posterior_a_login.png")
            logging.info(f"[{IMPL}] - Login exitoso, detectando grado...")

            self.click("//img[@alt='Biblioteca']")
            text_name = self.wait_for("//div[@id='custom_nav_chico']/nav", timeout=10000)
            raw_name = text_name.inner_text().strip()
            name = self.extract_first_names(raw_name, max_words=2)
            logging.info(f"[{IMPL}] - Nombre detectado: {name}")

            self.screenshot("buscando_grado.png")

            grade = 1
            try:
                self.wait_for("//span[normalize-space()='Biblioteca Compañeros']", timeout=3000)
                grade = 2
                logging.info(f"[{IMPL}] - Se detecta que es compañero")
            except Exception:
                logging.debug(f"[{IMPL}] - No se encuentra indicios de ser compañero")

            if grade == 2:
                try:
                    self.wait_for("//span[normalize-space()='Biblioteca Maestros']", timeout=3000)
                    grade = 3
                    logging.info(f"[{IMPL}] - Se detecta que es maestro")
                except Exception:
                    logging.debug(f"[{IMPL}] - No se encuentra indicios de ser maestro")

        except Exception as e:
            logging.error(f"[{IMPL}] - Error en login: {e}")
        finally:
            logging.info(f"[{IMPL}] - Fin proceso")

        return grade, name
