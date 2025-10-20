#!/usr/bin/python

try:
    import logging
    import sys
    import os
    import unicodedata
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.wait import WebDriverWait
    from selenium.webdriver.support import expected_conditions as ec

except ImportError:
    logging.error(ImportError)
    print((os.linesep * 2).join(['[Selenium] Error al buscar los modulos:', str(sys.exc_info()[1]), 'Debes Instalarlos para continuar', 'Deteniendo...']))
    sys.exit(-2)

ROOT_DIR = os.path.dirname(__file__)

class Selenium() :
    driver = None
    hub = None
    wait = None
    root_dir = None

    def __init__(self, root_dir = str(ROOT_DIR)) :
        try:
            self.root_dir = root_dir
            self.hub = str(os.environ.get('HUB_SELENIUM_URL','None')) + '/wd/hub'
        except Exception as e :
            print("ERROR Selenium:", e)

    def __del__(self):
        if self.driver != None:
            self.driver.quit()
    def create_sesion(self):
        try:
            if self.hub != None :
                logging.info("Remote HUB: " + self.hub)
                #self.driver = webdriver.Remote(self.hub, desired_capabilities=webdriver.DesiredCapabilities.CHROME)
                self.driver = webdriver.Remote(self.hub, options=webdriver.ChromeOptions())
                self.wait = WebDriverWait(self.driver, 30)  # 30 segundos
        except Exception as e:
            self.driver = None
            logging.warning("ERROR :", e) 

    def get_driver(self):
        if self.driver == None :
            self.create_sesion()
        return self.driver

    # se realiza el login y de acuerdo a los menus se detecta el grado del QH
    def login(self, username, password):
        grade = 1 # Inicialmente es Aprendiz
        browser = self.get_driver()
        name = 'Desconocido'
        try:
            logging.info("Login..")
            browser.get('https://www.mimasoneria.cl/web/login')
            rut_user = browser.find_element(By.ID, 'login')
            rut_user.send_keys(username)
            pswd = browser.find_element(By.ID,'password')
            pswd.send_keys(password)
            element = browser.find_element(By.XPATH, "//div[3]/button")
            logging.info("Se presiona boton entrar")
            element.click()
        except Exception as e:
            try:
                browser.save_screenshot(os.path.join(self.root_dir, "/login_error.png"))
                print('ERROR: ', e)
                grade = 0
            except:
                pass
        try:
            logging.info("Verifico si entre...")
            # browser.save_screenshot(os.path.join("./", "paso 1.png"))
            # browser.execute_script("window.scrollTo(0, 0);")
            element = self.wait.until(ec.visibility_of_element_located((By.XPATH, "//div[@id='custom_nav_chico']/nav")))
            name = str(element.text.strip())
            logging.info("Loging [Ok], Nombre: " + str(name) )
            oneandtwo =  name.split(' ')
            name = str(oneandtwo[0])
            if len(oneandtwo) > 1 : 
                name = name + ' ' + str(oneandtwo[1])
            grade = 1
            # me dirijo a la biblioteca
            element = self.wait.until(ec.visibility_of_element_located((By.XPATH, "//img[@alt='Biblioteca']")))
            element.click()
        except Exception as e:
            print("ERROR, no se pudo hacer login ", str(e))
            grade = 0
            try:
                browser.save_screenshot(os.path.join(self.root_dir, "/login_error.png"))
            except:
                pass

        if grade == 1 :
            try :
                element = browser.find_element(By.XPATH, "//span[normalize-space()='Biblioteca Compañeros']")
                grade = 2
                logging.info("Se detecta que es grado 2")
            except Exception as e:
                print('No se encuentra indicios de ser compañero: ', e)

        if grade == 2 :
            try :
                element = browser.find_element(By.XPATH, "//span[normalize-space()='Biblioteca Maestros']")
                grade = 3
                logging.info("Se detecta que es grado 3")
            except Exception as e:
                print('No se encuentra indicios de ser maestro: ', e)
        
        name = self.limpiar_texto(name)
        logging.info('El QH ' + str(name) + ' es del grado: ' + str(grade) )
        
        return grade, name

    def limpiar_texto(self, texto, mantener_enie=True):
        # 1. Normalizar el texto a la forma 'NFKD' (Normal Form Compatibility Decomposition)
        # Esto separa los caracteres base de sus diacr'iticos (tildes, etc.)
        texto_normalizado = unicodedata.normalize('NFKD', texto)

        # 2. Filtrar caracteres:
        #    - Quedarse solo con los caracteres ASCII (letras sin acentos).
        #    - Manejar la 'ñ' y 'Ñ' específicamente.
        texto_limpio = []
        for caracter in texto_normalizado:
            if 'a' <= caracter.lower() <= 'z': # Verifica si es una letra del alfabeto ASCII
                texto_limpio.append(caracter)
            elif caracter.lower() == 'ñ':
                if mantener_enie:
                    texto_limpio.append(caracter)
                else:
                    texto_limpio.append('n') # Transforma 'ñ' a 'n'
            # Podrías añadir más condiciones si quieres mantener números, espacios, etc.
            elif caracter.isspace(): # Mantener espacios en blanco
                texto_limpio.append(caracter)
            # O si solo quieres letras y quitas todo lo dem'as:
            else:
                pass # No añade el caracter si no es una letra o ñ

        return "".join(texto_limpio)