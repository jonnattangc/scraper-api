try:
    import logging
    import sys
    import os
    from security import Security
    from playwright.sync_api import sync_playwright

except ImportError:
    logging.error(ImportError)
    print((os.linesep * 2).join(['[Security] Error al buscar los modulos:', str(sys.exc_info()[1]), 'Debes Instalarlos para continuar', 'Deteniendo...']))
    sys.exit(-2)


class Playwrightgl() :
    
    def __init__(self) :
        pass

    def __del__(self) :
        pass

    def login(self, username: str, password: str) :
        logging.info("Abriendo navegador con Playwright, en modo headless")
        logging.info(f"Iniciando sesion con user: {username} y password: ********")
        browser = None
        name: str = None
        grade: int = 1
        try :
            p = sync_playwright().start()
            browser = p.chromium.launch(headless=True) 
            # Esto abrirá una ventana visible del navegador
            page = browser.new_page()
            page.goto("https://www.mimasoneria.cl/web/login")
            logging.info("Esperando 10 seg para que se cargue la pagina")
            
            btn_ingresar = page.wait_for_selector("//div[3]/button", timeout=10000)
            
            login = page.wait_for_selector("//input[@id='login']", timeout=10000, )
            passwd = page.wait_for_selector("//input[@id='password']", timeout=10000, )
            login.fill(username)
            passwd.fill(password)
            logging.info("Presionando el boton de ingresar...")
            btn_ingresar.click()
            # Esperar a que se cargue el menu   
            logging.info("Esperando max 10 seg para que se cargue la pagina")
            imagen_biblioteca = page.wait_for_selector("//img[@alt='Biblioteca']", timeout=5000)
            page.screenshot(path='static/posterior_a_login.png', full_page=True)
            logging.info("Login exitoso, estamos dentro, ahora vemos el grado...")
            imagen_biblioteca.click()
            text_name = page.wait_for_selector("//div[@id='custom_nav_chico']/nav", timeout=10000, )
            
            oneandtwo =  text_name.inner_text().split(' ')
            name = str(oneandtwo[0])
            if len(oneandtwo) > 1 : 
                name = name + ' ' + str(oneandtwo[1])

            logging.info("Login exitoso, se detecta que el usuario es: " + str(name))
            
            page.screenshot(path='static/buscando_grado.png', full_page=True)
            try :
                page.wait_for_selector("//span[normalize-space()='Biblioteca Compañeros']", timeout=3000)
                grade = 2
                logging.info("Se detecta que es compañero")
            except Exception as e:
                print('No se encuentra indicios de ser compañero: ', e)

            try :
                page.wait_for_selector("//span[normalize-space()='Biblioteca Maestros']", timeout=3000)
                grade = 3
                logging.info("Se detecta que es maestro")
            except Exception as e:
                print('No se encuentra indicios de ser maestro: ', e)

            #text_name.click()
            #btn_cierre = page.wait_for_selector("//a[@id='o_logout']", timeout=10000, )
            #btn_cierre.click()
            logging.info("Cerrando sesion...")

        except Exception as e :
            logging.error(e)    
        finally :
            if browser != None :
                browser.close()
            logging.info("Finalizando sesion")  
        return grade, name

    def request_process(self, request, context) :
        message = "Servicio ejecutado exitosamente"
        data_response = {"message" : message}
        http_code  = 200
        logging.info("Reciv " + str(request.method) + " Contex: /bch/" + str(context) )
        logging.info("Reciv Data: " + str(request.data) )
        logging.info("Reciv Header :\n" + str(request.headers) )

        security : Security = Security()
        json_data, path, http_code = security.preproccess_request(request, context )

        if http_code == 200 and json_data != None :
            if path.find("login") != -1 :
                user : str = json_data["username"]
                pwrd : str = json_data["password"]
                self.login(user, pwrd)
        else : 
            data_response = json_data
        return data_response, http_code    


