try:
    import logging
    import sys
    import os
    import pymysql.cursors
    from datetime import datetime
    from werkzeug.security import generate_password_hash, check_password_hash

except ImportError:
    logging.error(ImportError)
    print((os.linesep * 2).join(['[Security] Error al buscar los modulos:', str(sys.exc_info()[1]), 'Debes Instalarlos para continuar', 'Deteniendo...']))
    sys.exit(-2)

class Security() :
    db = None

    def __init__(self) :
        try:
            host = os.environ.get('HOST_BD','None')
            user = os.environ.get('USER_BD','None')
            password = os.environ.get('PASS_BD','None')
            port = int(os.environ.get('PORT_BD', 3306))
            eschema = str(os.environ.get('SCHEMA_BD','gral-purpose'))
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