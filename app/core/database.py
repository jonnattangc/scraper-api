import os
import logging
import pymysql.cursors


class DatabaseConnection:
    """Gestiona una conexión única a MySQL con context manager."""

    def __init__(self, database: str = None):
        self.host = os.environ.get('HOST_BD', 'None')
        self.user = os.environ.get('USER_BD', 'None')
        self.password = os.environ.get('PASS_BD', 'None')
        self.port = int(os.environ.get('PORT_BD', 3306))
        self.database = database or os.environ.get('SCHEMA_BD', 'gral-purpose')
        self._conn = None
        self._connect()

    def _connect(self):
        try:
            self._conn = pymysql.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=self.database,
                cursorclass=pymysql.cursors.DictCursor
            )
        except Exception as e:
            logging.error(f"[DatabaseConnection] Error de conexión: {e}")
            self._conn = None

    @property
    def is_connected(self) -> bool:
        return self._conn is not None

    def cursor(self):
        if not self.is_connected:
            raise RuntimeError("No hay conexión activa a la base de datos")
        return self._conn.cursor()

    def commit(self):
        if self._conn:
            self._conn.commit()

    def rollback(self):
        if self._conn:
            self._conn.rollback()

    def close(self):
        if self._conn:
            self._conn.close()
            self._conn = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
