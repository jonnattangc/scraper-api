import logging
import os
import time
from flask import jsonify
from core.database import DatabaseConnection
from services.login_service import LoginService
from cipher import Cipher


class GranLogiaService:
    """Procesa requests relacionadas con la Gran Logia."""

    def __init__(self, root_dir: str):
        self.root_dir = root_dir
        self.api_key = str(os.environ.get('SERVER_API_KEY', 'None'))

    def _verify_api_key(self, request) -> bool:
        rx_api_key = request.headers.get('x-api-key')
        if rx_api_key is None:
            logging.error('[GranLogiaService] x-api-key no found')
            return False
        if str(rx_api_key) != str(self.api_key):
            logging.error('[GranLogiaService] x-api-key is not valid')
            return False
        return True

    def _decrypt_payload(self, request) -> str:
        request_data = request.get_json()
        if request_data and 'data' in request_data and request.method == 'POST':
            cipher = Cipher()
            data_clear = cipher.aes_decrypt(str(request_data['data']))
            del cipher
            return data_clear
        return None

    def request_process(self, request, subpath: str):
        logging.info(f"[GranLogiaService] Recv {request.method} Context: /scraper/{subpath}")
        if not self._verify_api_key(request):
            return jsonify({"message": "No autorizado"}), 401

        data_clear = self._decrypt_payload(request)
        db = DatabaseConnection()
        login_service = LoginService(db)

        data_response = jsonify({"message": f"No procesado el contexto: {subpath}"})
        http_code = 404

        if request.method == 'POST':
            if 'login' in subpath:
                data_response, http_code = self._handle_login(data_clear, login_service)
            elif 'access' in subpath:
                data_response, http_code = self._handle_access(data_clear, login_service)
            elif 'grade' in subpath:
                data_response, http_code = self._handle_grade(data_clear, login_service)
            elif 'docs/url' in subpath:
                data_response, http_code = self._handle_docs_url(data_clear, request, db)
            elif 'saved' in subpath:
                data_response, http_code = self._handle_saved(data_clear, login_service)

        db.close()
        return data_response, http_code

    def _handle_login(self, data_clear: str, login_service: LoginService):
        if data_clear is None:
            return jsonify({"message": "Payload inválido"}), 400
        datos = data_clear.split('|||')
        if len(datos) != 2:
            return jsonify({"message": "Payload inválido"}), 400
        user, passwd = datos[0].strip(), datos[1].strip()
        if not user or not passwd:
            return jsonify({"message": "Credenciales incompletas"}), 400

        logging.info(f"[GranLogiaService] Login user: {user}")
        name, grade, message, code, maintainer = login_service.login_cascade(user, passwd)
        return jsonify({
            'message': str(message),
            'user': str(user),
            'grade': str(grade),
            'name': str(name),
            'maintainer': bool(maintainer)
        }), code

    def _handle_access(self, data_clear: str, login_service: LoginService):
        if data_clear is None:
            return jsonify({"message": "Payload inválido"}), 400
        datos = data_clear.split('&&')
        if len(datos) != 2:
            return jsonify({"message": "Payload inválido"}), 400
        user, grade = datos[0].strip(), datos[1].strip()
        if not user or not grade:
            return jsonify({"message": "Datos incompletos"}), 400
        message, code, http_code = login_service.validate_access(user, grade)
        return jsonify({'message': str(message), 'code': str(code)}), http_code

    def _handle_grade(self, data_clear: str, login_service: LoginService):
        user = data_clear.strip() if data_clear else ''
        if not user:
            return jsonify({"message": "Usuario requerido"}), 400
        message, grade, http_code = login_service.get_grade(user)
        return jsonify({'message': str(message), 'grade': str(grade)}), http_code

    def _handle_docs_url(self, data_clear: str, request, db: DatabaseConnection):
        if data_clear is None:
            return jsonify({"message": "Payload inválido"}), 400
        datos = data_clear.split(';')
        if len(datos) != 3:
            return jsonify({"message": "Payload inválido"}), 400
        name_doc, grade_doc, user_name = datos[0].strip(), datos[1].strip(), datos[2].strip()
        if not name_doc or not grade_doc or not user_name:
            return jsonify({"message": "Datos incompletos"}), 400

        login_service = LoginService(db)
        message, code, http_code = login_service.validate_access(user_name, grade_doc)
        if code == -1 or http_code != 200:
            return jsonify({"message": str(message)}), http_code

        cipher = Cipher()
        data_cipher = cipher.aes_encrypt(name_doc)
        http_proto = request.headers.get('x-forwarded-proto', 'https')
        host = request.headers.get('x-forwarded-host', 'localhost')
        url_doc = f"{http_proto}://{host}/logia/docs/pdf/{time.monotonic_ns()}/{data_cipher}"
        logging.info(f'[GranLogiaService] URL Base: {url_doc}')
        return jsonify({'url': str(url_doc)}), 200

    def _handle_saved(self, data_clear: str, login_service: LoginService):
        if data_clear is None:
            return jsonify({"message": "Payload inválido"}), 400
        datos = data_clear.split('|||')
        if len(datos) != 2:
            return jsonify({"message": "Payload inválido"}), 400
        username, password = datos[0].strip(), datos[1].strip()
        if not username or not password:
            return jsonify({"message": "Credenciales incompletas"}), 400

        logging.info(f"[GranLogiaService] Guardando usuario: {username}")
        if login_service.save_brother(username, password, 1, 'Desconocido'):
            return jsonify({'Response': 'Ok'}), 201
        return jsonify({"message": "Error al guardar"}), 500
