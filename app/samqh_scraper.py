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

IMPL : str = 'SAMQH'
class Samqh(AQHLogin) :
    page : Page = None
    def __init__(self) :
        super().__init__(url="https://samqh.glch.cl", page = self.page)

    def get_impl(self) -> str:
        return IMPL

    def login(self, username: str, password: str)  -> tuple[int, str] :
        name: str = None
        grade: int = 0
        try :
            if self.page is not None :
                logging.info(f"[{IMPL}] - Esperando a lo más 10 seg para que se cargue la pagina")
                btn_ingresar = self.page.wait_for_selector("//a[@id='sub_form_b']/span[@class='btn-label']", timeout=10000)
                login = self.page.wait_for_selector("//input[@id='id_sc_field_login']", timeout=10000, )
                passwd = self.page.wait_for_selector("//input[@id='id_sc_field_pswd']", timeout=10000, )
                login.fill(username)
                passwd.fill(password)
                logging.info(f"[{IMPL}] - Presionando el boton de ingresar...")
                btn_ingresar.click()
                # Esperar a que se cargue el menu   
                logging.info(f"[{IMPL}] - Esperando max 10 seg para que se cargue la pagina")
                actas = self.page.wait_for_selector("//a[@id='item_33']", timeout=5000)
                self.page.screenshot(path='static/posterior_a_login.png', full_page=True)
                actas.click()
                logging.info(f"[{IMPL}] - Login exitoso, estamos dentro, ahora vemos el grado...")

                text_name = self.page.wait_for_selector("//span[@id='lin1_col2']", timeout=10000, )

                oneandtwo =  str(text_name.inner_text()).split('QH:. ')
                if len(oneandtwo) == 2 :
                    names = oneandtwo[1].split(' ')
                    name = str(names[0])
                    if len(names) > 0 : 
                        name = name + ' ' + str(names[1])
                    if len(names) > 1 : 
                        name = name + ' ' + str(names[2])

                logging.info(f"[{IMPL}] - Login exitoso, se detecta que el usuario es: " + str(name))
                grade = 1
        except Exception as e :
            logging.error(e)    
        finally :
            logging.info(f"[{IMPL}] - Fin proceso de login")  
        return grade, name 


