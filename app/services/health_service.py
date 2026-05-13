import logging
import time
import os
import pymysql.cursors
from core.database import DatabaseConnection


class HealthService:
    """Provee información de salud del servidor y sus componentes."""

    def __init__(self):
        self.db = DatabaseConnection(database='security')

    def __del__(self):
        self.db.close()

    def get_info(self) -> dict:
        m1 = time.monotonic()
        logging.info("[HealthService] Check Status All Components")
        status_bd = self.db.is_connected
        time_response = time.monotonic() - m1

        data = {
            'Server': 'dev.jonnattan.com',
            'Owner': 'Jonnattan Griffiths Catalan',
            'Linkedin': 'https://www.linkedin.com/in/jonnattan',
            'Web': 'https://dev.jonnattan.com',
            'Files': True,
            'Data Base': status_bd,
            'Time': time_response
        }
        logging.info(f"[HealthService] Response in {time_response} ms")
        return data
