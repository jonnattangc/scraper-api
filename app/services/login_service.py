import logging
from typing import Optional, Tuple
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from core.database import DatabaseConnection
from scrapers.mimasoneria import Mimasoneria
from scrapers.elearn import Elearning
from scrapers.samqh import Samqh


class LoginService:
    """
    Orquesta la validación de hermanos (QH) usando base de datos
    y, si es necesario, una cascada de scrapers.
    """

    def __init__(self, db: DatabaseConnection):
        self.db = db

    # ------------------------------------------------------------------
    # Base de datos
    # ------------------------------------------------------------------
    def verify_brother(self, username: str, password: str) -> Tuple[Optional[str], int, str, bool]:
        """
        Verifica usuario/password contra la BD interna.
        Retorna (user, grade, name, maintainer).
        """
        logging.info(f"[LoginService] Verificando usuario en BD: {username}")
        user_resp = None
        grade = 0
        name = ''
        maintainer = False
        try:
            if not self.db.is_connected:
                return user_resp, grade, name, maintainer
            cursor = self.db.cursor()
            sql = "SELECT * FROM secure WHERE username = %s"
            cursor.execute(sql, (username,))
            for row in cursor.fetchall():
                password_bd = str(row['password'])
                user_bd = str(row['username'])
                name = str(row['name'])
                grade = int(row['grade'])
                maintainer = bool(row.get('maintainer', False))
                check = check_password_hash(password_bd, password)
                if user_bd.strip() == username.strip() and check:
                    user_resp = user_bd.strip()
                    logging.info(f"[LoginService] Usuario {username} validado Ok")
                else:
                    grade = 0
                    name = ''
                    maintainer = False
        except Exception as e:
            logging.error(f"[LoginService] Error BD verify_brother: {e}")
        return user_resp, grade, name, maintainer

    def save_brother(self, username: str, password: str, grade: int, real_name: str) -> bool:
        logging.info(f"[LoginService] Guardando QH: {username}")
        success = False
        try:
            if not self.db.is_connected:
                return False
            cursor = self.db.cursor()
            sql = """INSERT INTO secure (date_save, username, password, grade, name)
                     VALUES (%s, %s, %s, %s, %s)"""
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute(sql, (now, username, generate_password_hash(password), grade, real_name))
            self.db.commit()
            success = True
        except Exception as e:
            logging.error(f"[LoginService] Error BD save_brother: {e}")
            self.db.rollback()
        return success

    def get_grade(self, username: str) -> Tuple[str, int, int]:
        message = "Usuario no existe"
        grade = 0
        http_code = 409
        try:
            if not self.db.is_connected:
                return message, grade, http_code
            cursor = self.db.cursor()
            sql = "SELECT * FROM secure WHERE username = %s"
            cursor.execute(sql, (username,))
            for row in cursor.fetchall():
                grade = int(row['grade'])
                if 0 < grade <= 3:
                    message = f"Grado {grade}"
                    http_code = 200
        except Exception as e:
            logging.error(f"[LoginService] Error BD get_grade: {e}")
        logging.info(f"[LoginService] {message} para {username}")
        return message, grade, http_code

    def validate_access(self, username: str, grade: str) -> Tuple[str, int, int]:
        message = "Usuario no autorizado"
        code = -1
        http_code = 401
        try:
            grade_doc = int(grade)
            if not self.db.is_connected:
                return message, code, http_code
            cursor = self.db.cursor()
            sql = "SELECT * FROM secure WHERE username = %s"
            cursor.execute(sql, (username,))
            for row in cursor.fetchall():
                grade_qh = int(row['grade'])
                if grade_doc <= grade_qh:
                    code = 4500
                    message = f"Usuario es de grado {grade_qh}"
                    http_code = 200
        except Exception as e:
            logging.error(f"[LoginService] Error BD validate_access: {e}")
        logging.info(f"[LoginService] {username} -> {message}")
        return message, code, http_code

    # ------------------------------------------------------------------
    # Cascada de scrapers
    # ------------------------------------------------------------------
    def login_cascade(self, username: str, password: str) -> Tuple[Optional[str], int, str, int, bool]:
        """
        Intenta validar al hermano en BD; si falla, prueba scrapers en cascada.
        Retorna (name, grade, message, http_code, maintainer).
        """
        name, grade, message, code, maintainer = None, 0, "Ok", 200, False

        user, saved_grade, saved_name, maintainer = self.verify_brother(username, password)
        if user is not None:
            return saved_name, saved_grade, message, code, maintainer

        # No está en BD: cascada de scrapers
        scrapers = [
            ("Mimasoneria", Mimasoneria),
            ("Elearning", Elearning),
            ("Samqh", Samqh),
        ]

        for scraper_name, ScraperClass in scrapers:
            try:
                with ScraperClass() as scraper:
                    g, n = scraper.login(username, password)
                if 0 < g < 4:
                    if self.save_brother(username, password, g, n):
                        return n, g, "Usuario validado en GL", 201, False
            except Exception as e:
                logging.warning(f"[LoginService] Fallo en {scraper_name}: {e}")

        return None, 0, "El usuario es inválido", 409, False
