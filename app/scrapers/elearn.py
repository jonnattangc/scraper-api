try:
    import logging
    from scrapers.base import BaseScraper

except ImportError:
    import logging
    import sys
    import os
    logging.error(ImportError)
    print((os.linesep * 2).join(['[Elearning] Error al buscar los modulos:', str(sys.exc_info()[1]), 'Debes Instalarlos para continuar', 'Deteniendo...']))
    sys.exit(-2)

IMPL: str = 'ELEARN'
TEXT: str = 'Catecismo del Grado de'


class Elearning(BaseScraper):

    def __init__(self):
        super().__init__(url="https://elearning.granlogia.cl/login/index.php")

    def get_impl(self) -> str:
        return IMPL

    def login(self, username: str, password: str) -> tuple[int, str]:
        name: str = "Desconocido"
        grade: int = 0
        try:
            logging.info(f"[{IMPL}] - Esperando formulario de login")
            self.fill_input("//input[@id='username']", username)
            self.fill_input("//input[@id='password']", password)
            self.click("//button[@id='loginbtn']")
            logging.info(f"[{IMPL}] - Presionando el boton de ingresar...")

            text_name = self.wait_for("//a[@id='dropdown-1']/span[@class='userbutton']/span[@class='usertext mr-1']", timeout=10000)
            raw_name = text_name.inner_text().strip()
            name = self.extract_first_names(raw_name, max_words=4)
            logging.info(f"[{IMPL}] - Nombre detectado: {name}, buscando grado...")

            # Navegar a home para detectar grado
            self.page.goto("https://elearning.granlogia.cl/?redirect=0", wait_until="networkidle")
            grade = self._detect_grade()

        except Exception as e:
            logging.error(f"[{IMPL}] - Error en login: {e}")
        finally:
            logging.info(f"[{IMPL}] - Fin proceso de login")

        return grade, name

    def _detect_grade(self) -> int:
        grade = 1
        try:
            xpath_c = "//div[@id='frontpage-course-list']//div[@class='courses frontpage-course-list-all']//div[@class='row']/div[@class='col-md-3 col-sm-6'][21]//h5/a"
            xpath_m = "//div[@id='frontpage-course-list']//div[@class='courses frontpage-course-list-all']//div[@class='row']/div[@class='col-md-3 col-sm-6'][15]//h5/a"

            c = self.wait_for(xpath_c, timeout=1000)
            m = self.wait_for(xpath_m, timeout=1000)

            if c and f"{TEXT} Compañero" in c.inner_text():
                grade = 2
            if m and f"{TEXT} Maestro" in m.inner_text():
                grade = 3

            logging.info(f"[{IMPL}] - Grado detectado: {grade}")
        except Exception as e:
            logging.error(f"[{IMPL}] - Error al buscar el grado: {e}")
        return grade
