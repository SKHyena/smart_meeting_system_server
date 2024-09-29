import logging
from typing import List, Any

import pymysql

class DatabaseManager:

    def __init__(
        self,
        user: str,
        password: str,
        host: str,
        database_name: str,
    ):
        self.user = user
        self.password = password
        self.host = host
        self.db_name = database_name
        self.logger = logging.getLogger("uvicorn")
        self.logger.setLevel(logging.INFO)        

    def _get_connetion(self):
        return pymysql.connect(
            host=self.host,
            user=self.user,
            password=self.password,
            db=self.db_name,
            charset="utf8",
        )
    
    def _build_create_complaint_table_query(self) -> str:
        return f"""
        CREATE TABLE IF NOT EXISTS complaint (
            id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
            timestamp BIGINT,
            speaker TEXT,
            origin_text TEXT,
            translated_text TEXT,
            locale TEXT NOT NULL
        )
        """
    
    def _build_create_total_complaint_table_query(self) -> str:
        return f"""
        CREATE TABLE IF NOT EXISTS totalcomplaint (
            id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
            summary TEXT,
            category TEXT,
            dialogue TEXT NOT NULL
        )
        """
    
    def _build_insert_complaint_table_query(self, data: dict) -> tuple[str, tuple]:
        query = """
            INSERT INTO complaint (timestamp, speaker, origin_text, translated_text, locale)
            VALUES (%s, %s, %s, %s, %s)
        """
        params = (data["timestamp"], data["speaker"], data["origin_text"], data["translated_text"], data["locale"])
        return query, params
    
    def _build_insert_total_complaint_table_query(self, data: dict) -> tuple[str, tuple]:
        query = """
            INSERT INTO totalcomplaint (summary, category, dialogue)
            VALUES (%s, %s, %s)
        """
        params = (data["summary"], data["category"], data["dialogue"])
        return query, params

    def _build_select_complaint_table_query(self, id: str) -> str:
        return f"""
            SELECT * FROM complaint where id={id}
        """
    
    def _build_select_all_complaint_table_query(self) -> str:
        return f"""
            SELECT * FROM complaint
        """
    
    def _build_select_total_complaint_table_query(self, id: str) -> str:
        return f"""
            SELECT * FROM totalcomplaint where id={id}
        """
    
    def _build_select_all_total_complaint_table_query(self) -> str:
        return f"""
            SELECT * FROM totalcomplaint ORDER BY id desc
        """
    
    def _build_drop_complaint_table_query(self) -> str:
        return "DROP TABLE IF EXISTS complaint"
    
    def _build_drop_total_complaint_table_query(self) -> str:
        return "DROP TABLE IF EXISTS totalcomplaint"
    
    def _execute_query(self, query: str) -> int:
        with self._get_connetion() as connection:
            cursor = connection.cursor(pymysql.cursors.DictCursor)
            return cursor.execute(query)

    def create_complaint_table(self) -> int:
        create_table_query = self._build_create_complaint_table_query()
        
        return self._execute_query(create_table_query)
    
    def create_total_complaint_table(self) -> int:
        create_table_query = self._build_create_total_complaint_table_query()

        return self._execute_query(create_table_query)
        
    def drop_complaint_table(self) -> int:
        drop_table_query = self._build_drop_complaint_table_query()

        return self._execute_query(drop_table_query)
    
    def drop_total_complaint_table(self) -> int:
        drop_table_query = self._build_drop_total_complaint_table_query()

        return self._execute_query(drop_table_query)
    
    def insert_complaint_table(self, data: dict) -> None:
        query, params = self._build_insert_complaint_table_query(data)
        self.logger.info("Executing query: %s with params: %s", query, params)

        with self._get_connetion() as connection:
            cursor = connection.cursor()
            cursor.execute(query, params)
            connection.commit()

    def insert_total_complaint_table(self, data: dict) -> None:
        query, params = self._build_insert_total_complaint_table_query(data)
        self.logger.info("Executing query: %s with params: %s", query, params)

        with self._get_connetion() as connection:
            cursor = connection.cursor()
            cursor.execute(query, params)
            connection.commit()
    
    def select_all_complaint_table(self) -> List[Any]:
        select_table_query = self._build_select_all_complaint_table_query()

        with self._get_connetion() as connection:
            cursor = connection.cursor(pymysql.cursors.DictCursor)
            cursor.execute(select_table_query)        
            data = cursor.fetchall()
            self.logger.info(data)

            return data
        
    def select_all_total_complaint_table(self) -> List[Any]:
        select_table_query = self._build_select_all_total_complaint_table_query()

        with self._get_connetion() as connection:
            cursor = connection.cursor(pymysql.cursors.DictCursor)
            cursor.execute(select_table_query)        
            data = cursor.fetchall()
            self.logger.info(data)

            return data

    def select_complaint_table_with_id(self, id: int) -> List[Any]:
        select_table_query = self._build_select_complaint_table_query(id)

        with self._get_connetion() as connection:
            cursor = connection.cursor(pymysql.cursors.DictCursor)
            cursor.execute(select_table_query)        
            data = cursor.fetchall()
            self.logger.info(data)

            return data
    
    def select_total_complaint_table_with_id(self, id: int) -> List[Any]:
        select_table_query = self._build_select_total_complaint_table_query(id)

        with self._get_connetion() as connection:
            cursor = connection.cursor(pymysql.cursors.DictCursor)
            cursor.execute(select_table_query)        
            data = cursor.fetchall()
            self.logger.info(data)

            return data
