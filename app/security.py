try:
    import logging
    import sys
    import os
    import pymysql.cursors
    import json
    from datetime import datetime
    from werkzeug.security import generate_password_hash, check_password_hash
    from cipher import Cipher
    from flask import jsonify
    

except ImportError:
    logging.error(ImportError)
    print((os.linesep * 2).join(['[Security] Error al buscar los modulos:', str(sys.exc_info()[1]), 'Debes Instalarlos para continuar', 'Deteniendo...']))
    sys.exit(-2)

class Security() :
    db = None
    api_key = None
    def __init__(self) :
        try:
            host = os.environ.get('HOST_BD','None')
            user = os.environ.get('USER_BD','None')
            password = os.environ.get('PASS_BD','None')
            port = int(os.environ.get('PORT_BD', 3306))
            eschema = str(os.environ.get('SCHEMA_BD','gral-purpose'))
            self.api_key = str(os.environ.get('SERVER_API_KEY','None'))
            self.db = pymysql.connect(host=host, port=port, user=user, password=password, database=eschema, cursorclass=pymysql.cursors.DictCursor)
        except Exception as e :
            print("ERROR BD __init__() :", e)
            self.db = None

    def __del__(self):
        if self.db != None:
            self.db.close()

    def isConnect(self) :
        return self.db != None

    def verifiyUserPass( self, username, password ) :
        logging.info("Rescato password para usuario: " + str(username) )
        passwordBd = None
        userBd = None
        try :
            if self.db != None :
                cursor = self.db.cursor()
                sql = """select * from basic where username = %s"""
                cursor.execute(sql, (username))
                results = cursor.fetchall()
                for row in results:
                    passwordBd = str(row['password'])
                    userBd = str(row['username'])
                if userBd != None and passwordBd != None :
                    check = check_password_hash(passwordBd, password )
                    if userBd != username or not check :
                      userBd = None

        except Exception as e:
            print("ERROR BD verifiyUserPass():", e)
        return userBd

    def generateUser(self, user, password) :
        logging.info("Genero nuevo usuario: " + str(user) )
        try :
            if self.db != None :
                cursor = self.db.cursor()
                sql = """INSERT INTO basic (create_at, username, password ) VALUES(%s, %s, %s)"""
                now = datetime.now()
                cursor.execute(sql, (now.strftime("%Y-%m-%d %H:%M:%S"), user, generate_password_hash(password)))
                self.db.commit()
        except Exception as e:
            print("ERROR BD:", e)
            self.db.rollback()


    def preproccess_request(self, request, subpath: str = None ) :
        logging.info("=============================== INIT ===============================" )
        logging.info("Reciv " + str(request.method) + " Acción: " + str(subpath) )
        logging.info("Reciv Data: " + str(request.data) )
        logging.info("Reciv Header : " + str(request.headers) )

        http_code  = 409
        json_data = {"message" : "No autorizado", "data": None}

        rx_api_key: str = request.headers.get('x-api-key')
        if rx_api_key == None :
            logging.error('x-api-key no found')
            http_code  = 401
            return  data_response, subpath, http_code
        else :
            logging.info(f'x-api-key found : {rx_api_key}')
            if str(rx_api_key) != str(self.api_key) :
                logging.error('x-api-key is not valid')
                data_response = {"message" : "No autorizado", "data": None}
                http_code  = 401
                return  data_response, subpath, http_code

        path : str = None 
        if subpath != None : 
            path = subpath.lower().strip()

        logging.info(f'path found : {path}')

        if request.method == 'POST' :
            request_data = request.get_json()
            request_type = None
            data_rx = None
            try :
                request_type = request_data['type']
            except Exception as e :
                request_type = None
            try :
                data_rx = request_data['data']
            except Exception as e :
                data_rx = None
            if request_type != None :
                # encrypted or inclear
                if data_rx != None and str(request_type) == 'encrypted' :
                    cipher = Cipher()
                    data_cipher = str(data_rx)
                    logging.info('Data Encrypt: ' + str(data_cipher) )
                    data_clear = cipher.aes_decrypt(data_cipher)
                    logging.info('Data EnClaro: ' + str(data_clear) )
                    data_clear = str(data_clear).replace("'", '"')
                    json_data = json.loads(data_clear)
                    del cipher
                else: 
                    json_data = data_rx
                http_code  = 200
            else: 
                    json_data = data_rx
        return json_data, path, http_code