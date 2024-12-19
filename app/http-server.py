#!/usr/bin/python

try:
    import logging
    import sys
    import os
    import time
    import requests
    import json
    from flask_cors import CORS
    from flask_wtf.csrf import CSRFProtect
    from flask_httpauth import HTTPBasicAuth
    from flask_login import LoginManager, UserMixin, current_user, login_required, login_user
    from flask import Flask, render_template, abort, make_response, request, redirect, jsonify, send_from_directory
    # Clases personales
    from cipher import Cipher
    from security import Security
    from check import Checker
    from granl import GranLogia

except ImportError:

    logging.error(ImportError)
    print((os.linesep * 2).join(['[http-server] Error al buscar los modulos:',
                                 str(sys.exc_info()[1]), 'Debes Instalarlos para continuar', 'Deteniendo...']))
    sys.exit(-2)

############################# Configuraci'on de Registro de Log  ################################
FORMAT = '%(asctime)s %(levelname)s : %(message)s'
root = logging.getLogger()
root.setLevel(logging.INFO)
formatter = logging.Formatter(FORMAT)
# Log en pantalla
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.INFO)
handler.setFormatter(formatter)
#fh = logging.FileHandler('logger.log')
#fh.setLevel(logging.INFO)
#fh.setFormatter(formatter)
# se meten ambas configuraciones
root.addHandler(handler)
#root.addHandler(fh)

logger = logging.getLogger('HTTP')
# ===============================================================================
# Configuraciones generales del servidor Web
# ===============================================================================

SECRET_KEY = os.environ.get('RECAPTCHA_SECRET_KEY','NO_SECRET_KEY')
SECRET_CSRF = os.environ.get('SECRET_KEY_CSRF','KEY-CSRF-ACA-DEBE-IR')

app = Flask(__name__)
app.config.update( DEBUG=False, SECRET_KEY = str(SECRET_CSRF), )

#login_manager = LoginManager()
#login_manager.init_app(app)

csrf = CSRFProtect()
csrf.init_app(app)

auth = HTTPBasicAuth()
# cors = CORS(app, resources={r"/page/*": {"origins": ["*"]}})
cors = CORS(app, resources={r"/scraper/*": {"origins": ["dev.jonnattan.com"]}})
# ===============================================================================
# variables globales
# ===============================================================================
ROOT_DIR = os.path.dirname(__file__)

#===============================================================================
# Redirige
#===============================================================================
@app.route('/', methods=['GET', 'POST'])
@csrf.exempt
def index():
    logging.info("Reciv solicitude endpoint: /" )
    return redirect('/info'), 302

#===============================================================================
# Redirige
#===============================================================================
@app.route('/<path:subpath>', methods=('GET', 'POST'))
@csrf.exempt
def process_context( subpath ):
    logging.info("Reciv solicitude endpoint: " + subpath )
    return redirect('/info'), 302

#===============================================================================
# Informaci'on
#===============================================================================
@app.route('/info', methods=['GET', 'POST'])
@csrf.exempt
def info_proccess():
    return jsonify({
        "Servidor": "dev.jonnattan.com",
        "Nombre": "API de Scrapper para distitnas cosas",
        "Docs":"proximamente"
    })
#===============================================================================
# Metodo solicitado por la biblioteca de autenticaci'on b'asica
#===============================================================================
@auth.verify_password
def verify_password(username, password):
    user = None
    if username != None :
        basicAuth = Security()
        user =  basicAuth.verifiyUserPass(username, password)
        del basicAuth
    return user

#===============================================================================
# Implementacion del handler que respondera el error en caso de mala autenticacion
#===============================================================================
@auth.error_handler
def unauthorized():
    return make_response(jsonify({'message':'invalid credentials'}), 401)

#===============================================================================
# Se checkea el estado del servidor completo para reportar
#===============================================================================
@app.route('/checkall', methods=['GET'])
@auth.login_required
@csrf.exempt
def check_proccess():
    checker = Checker()
    json = checker.get_info()
    del checker
    return jsonify(json)

# ==============================================================================
# Procesa peticiones de la pagina de la logia
# ==============================================================================
@app.route('/scraper/logia/<path:subpath>', methods=['POST', 'GET'])
@csrf.exempt
@auth.login_required
def gran_logia_process_scraper(subpath):
    gl = GranLogia( ROOT_DIR )
    data, code = gl.request_process( request, subpath )
    del gl
    return data, code

# ==============================================================================
# Procesa peticiones de la pagina de la logia
# ==============================================================================
@app.route('/scraper/ionix/<path:subpath>', methods=['POST', 'GET'])
@csrf.exempt
@auth.login_required
def ionix_process_scraper(subpath):
    gl = GranLogia( ROOT_DIR )
    data, code = gl.request_process( request, subpath )
    del gl
    return data, code


# ===============================================================================
# Favicon
# ===============================================================================
@app.route('/favicon.ico', methods=['POST','GET','PUT'])
@csrf.exempt
def favicon():
    file_path = os.path.join(ROOT_DIR, 'static')
    file_path = os.path.join(file_path, 'image')
    logging.info("Icono: " + str( file_path ) )
    return send_from_directory(file_path,
            'favicon.ico', mimetype='image/vnd.microsoft.icon')


@app.route('/page/cipher', methods=['POST'])
@csrf.exempt
@auth.login_required
def cipher_test():
    cipher = Cipher()
    data, code = cipher.test( request )
    del cipher
    return jsonify(data), code

# ===============================================================================
# Metodo Principal que levanta el servidor
# ===============================================================================
if __name__ == "__main__":
    listenPort = 8085
    logger.info("ROOT_DIR: " + ROOT_DIR)
    logger.info("ROOT_DIR: " + app.root_path)
    if(len(sys.argv) == 1):
        logger.error("Se requiere el puerto como parametro")
        exit(0)
    try:
        logger.info("Server listen at: " + sys.argv[1])
        listenPort = int(sys.argv[1])
        # app.run(ssl_context='adhoc', host='0.0.0.0', port=listenPort, debug=True)
        # app.run( ssl_context=('cert_jonnattan.pem', 'key_jonnattan.pem'), host='0.0.0.0', port=listenPort, debug=True)
        app.run( host='0.0.0.0', port=listenPort)
    except Exception as e:
        print("ERROR MAIN:", e)

    logging.info("PROGRAM FINISH")
