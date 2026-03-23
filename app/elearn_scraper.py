try:
    import logging
    import sys
    import os
    from aqh_login import AQHLogin
    from playwright.sync_api import Page

except ImportError:
    logging.error(ImportError)
    print((os.linesep * 2).join(['[Security] Error al buscar los modulos:', str(sys.exc_info()[1]), 'Debes Instalarlos para continuar', 'Deteniendo...']))
    sys.exit(-2)

IMPL : str = 'ELEARN'
TEXT : str = 'Catecismo del Grado de'
class Elearning(AQHLogin) :
    page : Page = None
    def __init__(self) :
        super().__init__(url="https://elearning.granlogia.cl/login/index.php", page = self.page)

    def get_impl(self) -> str:
        return IMPL

    def login(self, username: str, password: str)  -> tuple[int, str] :
        name: str = None
        grade: int = 0
        try :
            if self.page is not None :
                logging.info(f"[{IMPL}] - Esperando a lo más 10 seg para que se cargue la pagina")
                btn_ingresar = self.page.wait_for_selector("//button[@id='loginbtn']", timeout=10000)
                login = self.page.wait_for_selector("//input[@id='username']", timeout=10000, )
                passwd = self.page.wait_for_selector("//input[@id='password']", timeout=10000, )
                login.fill(username)
                passwd.fill(password)
                logging.info(f"[{IMPL}] - Presionando el boton de ingresar...")
                btn_ingresar.click()
                text_name = self.page.wait_for_selector("//a[@id='dropdown-1']/span[@class='userbutton']/span[@class='usertext mr-1']", timeout=10000 )
                logging.info(f"[{IMPL}] - Login exitoso, estamos dentro, ahora vemos el nombre y grado...")
                names =  str(text_name.inner_text()).split(' ')
                if len(names) > 0 :
                    name = str(names[0])
                    if len(names) > 0 : 
                        name = name + ' ' + str(names[1])
                    if len(names) > 1 : 
                        name = name + ' ' + str(names[2])
                    if len(names) > 2 : 
                        name = name + ' ' + str(names[3])
                # Esperar a que se cargue el menu   
                logging.info(f"[{IMPL}] - Nombre detectado: {name}, ahora buscamos el grado" )
                try :
                    logging.info(f"[{IMPL}] - Home cargado o ya abierto, ahora vemos el grado")
                    self.page.goto("https://elearning.granlogia.cl/?redirect=0", wait_until="networkidle")

                    xpath_grado : str = "//div[@id='frontpage-course-list']/div[@class='courses frontpage-course-list-all']/div[@class='row']/div[@class='col-md-3 col-sm-6'][21]/div[@class='fp-coursebox']/div[@class='fp-courseinfo']/h5/a"
                    c = self.page.wait_for_selector(xpath_grado, timeout=1000)
                    logging.info(f"[{IMPL}] - Texto detectado: {c.inner_text()}")
                    xpath_grado = "//div[@id='frontpage-course-list']/div[@class='courses frontpage-course-list-all']/div[@class='row']/div[@class='col-md-3 col-sm-6'][15]/div[@class='fp-coursebox']/div[@class='fp-courseinfo']/h5/a"
                    m = self.page.wait_for_selector(xpath_grado, timeout=1000)
                    logging.info(f"[{IMPL}] - Texto detectado: {m.inner_text()}")
                    grade = 1
                    if c != None and c.inner_text().find(f"{TEXT} Compañero") != -1 :
                        grade = 2
                    if m != None and m.inner_text().find(f"{TEXT} Maestro") != -1 :
                        grade = 3
                except Exception as e:
                    logging.error(f"[{IMPL}] - Error al buscar el grado: {e}")

        except Exception as e :
            logging.error(e)    
        finally :
            logging.info(f"[{IMPL}] - Fin proceso de login")  
        return grade, name 


