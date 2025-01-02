try:
    import logging
    import sys
    import os
    import pymysql.cursors
    from datetime import datetime
    from seleniumgl import Selenium
    import time
    from cipher import Cipher
    from werkzeug.security import generate_password_hash, check_password_hash
    from flask import send_from_directory, jsonify

except ImportError:
    logging.error(ImportError)
    print((os.linesep * 2).join(['[GranLogia] Error al buscar los modulos:', str(sys.exc_info()[1]), 'Debes Instalarlos para continuar', 'Deteniendo...']))
    sys.exit(-2)

ROOT_DIR = os.path.dirname(__file__)

class GranLogia () :
    api_key = None
    root_dir = None
    def __init__(self, root_dir = str(ROOT_DIR)) :
        try:
            self.root_dir = root_dir
            self.api_key = str(os.environ.get('SERVER_API_KEY','None'))
        except Exception as e :
            print("ERROR :", e)
            self.logia_api_key = None
            self.root_dir = None

    def __del__(self):
        self.api_key = None
        self.root_dir = None

    def request_process(self, request, subpath ) :
        message = "No autorizado"
        data_response = jsonify({"message" : message})
        http_code  = 401
        logging.info("Reciv " + str(request.method) + " Contex: /scraper/" + str(subpath) )
        logging.info("Reciv Data: " + str(request.data) )
        logging.info("Reciv Header :\n" + str(request.headers) )
        # evlua pai key inmediatamente
        rx_api_key = request.headers.get('x-api-key')
        if rx_api_key == None :
            logging.error('API Key NOk')
            return  data_response, http_code
        if str(rx_api_key) != str(self.api_key) :
            logging.error('Error API Key')
            return  data_response, http_code
        
        request_data = request.get_json()
        # se decifra el payload que llega si existe
        cipher = Cipher()
        data_clear = None
        if request_data['data'] != None and request.method == 'POST' :
            data_cipher = str(request_data['data'])
            logging.info('API Key Ok, Data Recibida: ' + data_cipher )
            data_clear = cipher.aes_decrypt(data_cipher)
            # logging.info('Data Claro: ' + str(data_clear) )
        # proceso
        if request.method == 'POST' :
            if str(subpath).find('login') >= 0 :
                user = name = grade = None
                if data_clear != None :
                    datos = data_clear.split('|||')
                    if len(datos) == 2 and datos[0] != None and datos[1] != None :
                        user = str(datos[0]).strip()
                        passwd = str(datos[1]).strip()
                        logging.info('User: ' + str(user) + " Passwd: ******** " )
                        if user != '' and passwd != '' :
                            name, grade, message, http_code  = self.login_system( user, passwd )
                            data_response = jsonify({
                                'message' : str(message),
                                'user' : str(user),
                                'grade' : str(grade),
                                'name' : str(name)
                            })
            elif str(subpath).find('access') >= 0 :
                if data_clear != None :
                    datos = data_clear.split('&&')
                    if len(datos) == 2 and datos[0] != None and datos[1] != None :
                        user = str(datos[0]).strip()
                        grade = str(datos[1]).strip()
                        if user != '' and grade != '' :
                            db = GranLogiaBd()
                            message, code, http_code  = db.validate_access( user, grade )
                            del db
                            data_response = jsonify({
                                'message' : str(message),
                                'code' : str(code)
                            })
            elif str(subpath).find('grade') >= 0 :
                if data_clear != None :
                    user = data_clear.strip()
                    if user != '' :
                        db = GranLogiaBd()
                        message, grade, http_code  = db.get_grade( user )
                        del db
                        data_response = jsonify({
                            'message' : str(message),
                            'grade' : str(grade)
                        })
            elif str(subpath).find('docs/url') >= 0 :
                if data_clear != None :
                    datos = data_clear.split(';')
                    if len(datos) == 3 and datos[0] != None and datos[1] != None and datos[2] != None :
                        name_doc = str(datos[0]).strip()
                        grade_doc = str(datos[1]).strip()
                        user_name = str(datos[2]).strip()
                        if name_doc != '' and grade_doc != '' and user_name != '' :
                            db = GranLogiaBd()
                            message, code, http_code  = db.validate_access( user_name, grade_doc )
                            del db
                            if code != -1 and message != None and http_code == 200 :
                                http = request.headers.get('x-forwarded-proto')
                                host = request.headers.get('x-forwarded-host')
                                data_cipher = cipher.aes_encrypt( name_doc )
                                url_doc = str(http) + '://' + str(host) + '/logia/docs/pdf/' + str(time.monotonic_ns()) + '/' + str(data_cipher)
                                logging.info('URL Base: ' + str(url_doc) )
                                data_response = jsonify({
                                    'url'  : str(url_doc)
                                })
            else: 
                data_response = jsonify({"message" : "No procesado el contexto: " + str(subpath)})
                http_code = 404
        del cipher
        return  data_response, http_code

    def login_system(self, username : str, password) :
        logging.info("Verifico Usuario: " + str(username) )
        message = "Ok"
        code = 200
        db_gl = GranLogiaBd()
        user, saved_grade, name_saved = db_gl.verifiy_brother( username, password )
        if user == None :
            scraper = Selenium()
            grade, name_saved = scraper.login( username, password )
            del scraper
            if grade > 0 and grade < 4 :
                if db_gl.save_brother(username, password, grade, name_saved ) :
                    saved_grade = grade
                    message = "Usuario validado en GL"
                    code = 201
            else :
                message = "El usuario es inválido"
                code = 409
        del db_gl
        return name_saved, saved_grade, message, code 
class GranLogiaBd() :
    db = None
    host = os.environ.get('HOST_BD','None')
    user = os.environ.get('USER_BD','None')
    password = os.environ.get('PASS_BD','None')
    database = 'gral-purpose'

    def __init__(self) :
        try:
            self.db = pymysql.connect(host=self.host, user=self.user, password=self.password, database=self.database,cursorclass=pymysql.cursors.DictCursor)
        except Exception as e :
            print("ERROR BD:", e)
            self.db = None

    def __del__(self):
        if self.db != None:
            self.db.close()

    def connect( self ) :
        try:
            if self.db == None :
                self.db = pymysql.connect(host=self.host, user=self.user, password=self.password, database=self.database,cursorclass=pymysql.cursors.DictCursor)
        except Exception as e :
            print("ERROR BD:", e)
            self.db = None
    
    def isConnect(self) :
        return self.db != None

    #================================================================================================
    # Guarda info del qh
    #================================================================================================
    def save_brother(self, username, password, grade, real_name ):
        logging.info('Guardo al Qh: ' + str(username))
        success = False
        try :
            if self.db != None :
                cursor = self.db.cursor()
                sql = """INSERT INTO secure (date_save, username, password, grade, name ) VALUES(%s, %s, %s, %s, %s)"""
                now = datetime.now()
                cursor.execute(sql, (now.strftime("%Y-%m-%d %H:%M:%S"), username, generate_password_hash(password), grade, real_name ))
                self.db.commit()
                success = True
        except Exception as e:
            print("ERROR BD:", e)
            self.db.rollback()
            success = False
        return success
    #================================================================================================
    # obtiene grado del qh
    #================================================================================================
    def get_grade(self, username ) :
        logging.info('Obtiene grado de: ' + str(username))
        message = "Usuario no existe"
        grade  = 0
        http_code = 409
        try :
            if self.db != None :
                cursor = self.db.cursor()
                sql = """select * from secure where username = %s"""
                cursor.execute(sql, (username))
                results = cursor.fetchall()
                for row in results:
                    grade = int(row['grade'])
                    if grade > 0 and grade <=3 :
                        message = 'Grado ' + str(grade)
                        http_code = 200
        except Exception as e:
            print("ERROR BD:", e)

        logging.info('Message: ' + str(message) + ' para ' + str(username) )
        return message, grade, http_code

    #================================================================================================
    # Valido el grado del QH logeado con el del documento que desea ver
    #================================================================================================
    def validate_access(self, username, grade) :
        logging.info('Valido acceso de usuario: ' + str(username)  + ' a cosas de ' + str(grade))
        message = "Usuario no autorizado"
        code  = -1
        http_code = 401
        grade_doc = int(grade)
        try :
            if self.db != None :
                cursor = self.db.cursor()
                sql = """select * from secure where username = %s"""
                cursor.execute(sql, (username))
                results = cursor.fetchall()
                for row in results:
                    grade_qh = int(row['grade'])
                    if grade_doc <= grade_qh :
                        code = 4500
                        message = 'Usuario es de grado ' + str(grade_qh)
                        http_code = 200
        except Exception as e:
            print("ERROR BD:", e)

        logging.info(str(username)  + ' ' + str(message))
        return message, code, http_code

    #================================================================================================
    # Verifica si exsite el QH en la base de datos y compara la contrasenna
    #================================================================================================
    def verifiy_brother( self, username, password ) :
        logging.info("Rescato password para usuario: " + str(username) )
        passwordBd = None
        userResp = None
        grade = 0
        name = ''
        try :
            if self.db != None :
                cursor = self.db.cursor()
                sql = """select * from secure where username = %s"""
                cursor.execute(sql, (username))
                results = cursor.fetchall()
                passwordBd = None
                userBd = None
                # saco los datos de la BD
                for row in results :
                    passwordBd = str(row['password'])
                    userBd = str(row['username'])
                    name = str(row['name'])
                    grade = int(str(row['grade']))
                    logging.info("Usuario " + str(name) + " encontrado en BD interna")
                # guardo lo que se necesita y solo si existen ambos valores
                if userBd != None and passwordBd != None :
                    check = check_password_hash(passwordBd, password ) 
                    if userBd.strip() == username.strip() and check :
                        logging.info("Usuario " + str(username) + " validado Ok")
                        userResp = userBd.strip()
                    else :
                        logging.info("Ckeck: " + str(check)+ " Error validando passwd de " + str(username) ) 
                        grade = 0
                        name = ''
                else :
                  logging.info('user y/o password no encontrado')  
                  grade = 0
                  name = ''
        except Exception as e:
            print("ERROR BD:", e)
        return userResp, grade, name
