import logging
import os
import json
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from core.database import DatabaseConnection
from cipher import Cipher


class SecurityService:
    """Gestiona autenticación básica y preprocesamiento de requests."""

    def __init__(self):
        self.api_key = str(os.environ.get('SERVER_API_KEY', 'None'))
        self.db = DatabaseConnection()

    def __del__(self):
        self.db.close()

    # ------------------------------------------------------------------
    # Auth básica (HTTPBasicAuth)
    # ------------------------------------------------------------------
    def verify_user_pass(self, username: str, password: str) -> str:
        logging.info(f"[SecurityService] Verificando usuario: {username}")
        user_bd = None
        try:
            if not self.db.is_connected:
                return user_bd
            cursor = self.db.cursor()
            sql = "SELECT * FROM oauth WHERE username = %s"
            cursor.execute(sql, (username,))
            for row in cursor.fetchall():
                password_bd = str(row['password'])
                user = str(row['username'])
                if check_password_hash(password_bd, password) and user == username:
                    user_bd = user
                    break
                else:
                    user_bd = None
                    logging.error(f"[SecurityService] Error verificando usuario: {username}")
        except Exception as e:
            logging.error(f"[SecurityService] Error verify_user_pass: {e}")
        return user_bd

    def generate_user(self, user: str, password: str) -> None:
        logging.info(f"[SecurityService] Generando usuario: {user}")
        try:
            if not self.db.is_connected:
                return
            cursor = self.db.cursor()
            sql = "INSERT INTO oauth (create_at, username, password) VALUES (%s, %s, %s)"
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute(sql, (now, user, generate_password_hash(password)))
            self.db.commit()
        except Exception as e:
            logging.error(f"[SecurityService] Error generate_user: {e}")
            self.db.rollback()

    # ------------------------------------------------------------------
    # Preprocesamiento de requests (API key + payload)
    # ------------------------------------------------------------------
    def preproccess_request(self, request, subpath: str = None):
        logging.info("[SecurityService] =============================== INIT ===============================")
        logging.info(f"[SecurityService] Method: {request.method} | Acción: {subpath}")
        http_code = 409
        json_data = {"message": "No autorizado", "data": None}

        rx_api_key = request.headers.get('x-api-key')
        if rx_api_key is None:
            logging.error('[SecurityService] x-api-key no found')
            http_code = 401
            return json_data, subpath, http_code

        if str(rx_api_key) != str(self.api_key):
            logging.error('[SecurityService] x-api-key is not valid')
            http_code = 401
            return json_data, subpath, http_code

        path = subpath.lower().strip() if subpath else None
        logging.info(f'[SecurityService] path found: {path}')

        if request.method == 'POST':
            request_data = request.get_json() or {}
            request_type = request_data.get('type')
            data_rx = request_data.get('data')

            if request_type is not None:
                if data_rx is not None and str(request_type) == 'encrypted':
                    cipher = Cipher()
                    data_cipher = str(data_rx)
                    logging.info(f'[SecurityService] Data Encrypt: {data_cipher}')
                    data_clear = cipher.aes_decrypt(data_cipher)
                    logging.info(f'[SecurityService] Data Claro: {data_clear}')
                    data_clear = str(data_clear).replace("'", '"')
                    json_data = json.loads(data_clear)
                    del cipher
                else:
                    json_data = data_rx
                http_code = 200
            else:
                json_data = data_rx

        return json_data, path, http_code
