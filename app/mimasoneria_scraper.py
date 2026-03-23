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

IMPL : str = 'MIMASONERIA'
class Mimasoneria(AQHLogin) :
    page : Page = None
    def __init__(self) :
        super().__init__(url="https://www.mimasoneria.cl/web/login", page = self.page)

    def get_impl(self) -> str:
        return IMPL

    def login(self, username: str, password: str) :
        name: str = None
        grade: int = 0
        try :
            if self.page is not None :
                logging.info(f"[{IMPL}] - Esperando a lo más 10 seg para que se cargue la pagina")
                btn_ingresar = self.page.wait_for_selector("//div[3]/button", timeout=10000)
                
                login = self.page.wait_for_selector("//input[@id='login']", timeout=10000, )
                passwd = self.page.wait_for_selector("//input[@id='password']", timeout=10000, )
                login.fill(username)
                passwd.fill(password)
                logging.info(f"[{IMPL}] - Presionando el boton de ingresar...")
                btn_ingresar.click()
                # Esperar a que se cargue el menu   
                logging.info(f"[{IMPL}] - Esperando max 10 seg para que se cargue la pagina")
                imagen_biblioteca = self.page.wait_for_selector("//img[@alt='Biblioteca']", timeout=5000)
                self.page.screenshot(path='static/posterior_a_login.png', full_page=True)
                logging.info(f"[{IMPL}] - Login exitoso, estamos dentro, ahora vemos el grado...")
                imagen_biblioteca.click()
                text_name = self.page.wait_for_selector("//div[@id='custom_nav_chico']/nav", timeout=10000, )
                
                oneandtwo =  text_name.inner_text().split(' ')
                name = str(oneandtwo[0])
                if len(oneandtwo) > 1 : 
                    name = name + ' ' + str(oneandtwo[1])

                logging.info(f"[{IMPL}] - Login exitoso, se detecta que el usuario es: " + str(name))
                
                self.page.screenshot(path='static/buscando_grado.png', full_page=True)
                try :
                    self.page.wait_for_selector("//span[normalize-space()='Biblioteca Compañeros']", timeout=3000)
                    grade = 2
                    logging.info(f"[{IMPL}] - Se detecta que es compañero")
                except Exception as e:
                    print('No se encuentra indicios de ser compañero: ', e)

                try :
                    self.page.wait_for_selector("//span[normalize-space()='Biblioteca Maestros']", timeout=3000)
                    grade = 3
                    logging.info(f"[{IMPL}] - Se detecta que es maestro")
                except Exception as e:
                    print('No se encuentra indicios de ser maestro: ', e)

        except Exception as e :
            logging.error(e)    
        finally :
            logging.info(f"[{IMPL}] - Fin proceso")  
        return grade, name