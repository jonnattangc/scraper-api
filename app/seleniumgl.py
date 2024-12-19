#!/usr/bin/python

try:
    import logging
    import sys
    import os
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
            browser.save_screenshot(os.path.join("./", "paso 1.png"))
            # browser.execute_script("window.scrollTo(0, 0);")
            element = self.wait.until(ec.visibility_of_element_located((By.XPATH, "//div[@id='custom_nav_chico']/nav/ul[2]/li/a/b/span")))
            name = str(element.text.strip())
            logging.info("Loging [Ok], Nombre: " + str(name) )
            oneandtwo =  name.split(' ')
            name = str(oneandtwo[0]) + ' ' + str(oneandtwo[1])
            grade = 1
            # me dirijo a la biblioteca
            element = self.wait.until(ec.visibility_of_element_located((By.XPATH, "//img[@alt='Biblioteca']")))
            element.click()
        except Exception as e:
            print("ERROR, no se pudo hacer login ", e)
            grade = 0
            try:
                browser.save_screenshot(os.path.join(self.root_dir, "/login_error.png"))
            except:
                pass

        if grade == 1 :
            try :
                element = browser.find_element(By.XPATH, "//img[@alt='Biblioteca Compañeros']")
                grade = 2
                logging.info("Se detecta que es grado 2")
            except Exception as e:
                print('No se encuentra indicios de ser compañero: ', e)

        if grade == 2 :
            try :
                element = browser.find_element(By.XPATH, "//img[@alt='Biblioteca Maestros']")
                grade = 3
                logging.info("Se detecta que es grado 3")
            except Exception as e:
                print('No se encuentra indicios de ser maestro: ', e)

        logging.info('El QH ' + str(name) + ' es del grado: ' + str(grade) )
        return grade, name
