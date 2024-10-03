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
    
    def _build_create_meeting_table_query(self) -> str:
        return f"""
        CREATE TABLE IF NOT EXISTS meeting (
            id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
            name TEXT,
            start_time TEXT,
            end_time TEXT,
            room TEXT,
            subject TEXT,
            topic TEXT
        )
        """
    
    def _build_create_attendee_table_query(self) -> str:
        return f"""
        CREATE TABLE IF NOT EXISTS attendee (
            id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
            meeting_name TEXT,
            name TEXT,
            group TEXT,
            position TEXT,
            email_address TEXT,
            role TEXT,
            email_delivery_status BOOL,
            attendance_status BOOL,
            initial_attendance_time TEXT,
            connected_device TEXT
        )
        """
    
    def _build_insert_meeting_table_query(self, data: dict) -> tuple[str, tuple]:
        query = """
            INSERT INTO meeting (name, start_time, end_time, room, subject, topic)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        params = (data["name"], data["start_time"], data["end_time"], data["room"], data["subject"], data["topic"])
        return query, params

    def _build_insert_attendee_info_table_query(self, data: dict) -> tuple[str, tuple]:
        query = """
            INSERT INTO attendee (meeting_name, name, group, position, email_address, role, email_delivery_status)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        params = (data["meeting_name"], data["name"], data["group"], data["position"], data["email_address"], data["role"], data["email_delivery_status"])
        return query, params
    
    def _build_update_attendee_attendance_info_table_query(self, data: dict) -> tuple[str, tuple]:
        query = """
            UPDATE attendee SET attendance_status = %s, initial_attendance_time = %s, connected_device = %s
            WHERE name = %s AND email_address = %s
        """
        params = (data["attendance_status"], data["initial_attendance_time"], data["connected_device"], data["name"], data["email_address"])
        return query, params
    
    def _build_select_all_meeting_table_query(self) -> str:
        return f"""
            SELECT * FROM meeting ORDER BY id desc
        """
    
    def _build_select_all_attendee_table_query(self) -> str:
        return f"""
            SELECT * FROM attendee ORDER BY id desc
        """
    
    def _build_delete_attendee_table_query(self, data: dict) -> tuple[str, tuple]:
        query = """
            DELETE FROM attendee WHERE name = %s AND email_address = %s
        """
        params = (data["name"], data["email_address"])
        return query, params
        
    def _build_drop_meeting_table_query(self) -> str:
        return "DROP TABLE IF EXISTS meeting"
    
    def _build_drop_attendee_table_query(self) -> str:
        return "DROP TABLE IF EXISTS attendee"
        
    def _execute_query(self, query: str) -> int:
        with self._get_connetion() as connection:
            cursor = connection.cursor(pymysql.cursors.DictCursor)
            return cursor.execute(query)
        
    def _execute_select_query(self, select_table_query):
        with self._get_connetion() as connection:
            cursor = connection.cursor(pymysql.cursors.DictCursor)
            cursor.execute(select_table_query)        
            data = cursor.fetchall()
            self.logger.info(data)

            return data
    
    def _execute_commit_query(self, query, params):
        self.logger.info(f"Executing query: {query} with params: {params}")

        with self._get_connetion() as connection:
            cursor = connection.cursor()
            cursor.execute(query, params)
            connection.commit()

    def create_meeting_table(self) -> int:
        create_table_query = self._build_create_meeting_table_query()
        
        return self._execute_query(create_table_query)
    
    def create_attendee_table(self) -> int:
        create_table_query = self._build_create_attendee_table_query()
        
        return self._execute_query(create_table_query)
            
    def drop_meeting_table(self) -> int:
        drop_table_query = self._build_drop_meeting_table_query()

        return self._execute_query(drop_table_query)
    
    def drop_attendee_table(self) -> int:
        drop_table_query = self._build_drop_attendee_table_query()

        return self._execute_query(drop_table_query)
    
    def insert_meeting_table(self, data: dict) -> None:
        query, params = self._build_insert_meeting_table_query(data)        
        self._execute_commit_query(query, params)

    def insert_attendee_info_table(self, data: dict) -> None:
        query, params = self._build_insert_attendee_info_table_query(data)        
        self._execute_commit_query(query, params)

    def update_attendee_attendance_info_table(self, data: dict) -> None:
        query, params = self._build_update_attendee_attendance_info_table_query(data)        
        self._execute_commit_query(query, params)
    
    def select_all_meeting_table(self) -> List[Any]:
        select_table_query = self._build_select_all_meeting_table_query()

        return self._execute_select_query(select_table_query)
    
    def select_all_attendee_table(self) -> List[Any]:
        select_table_query = self._build_select_all_attendee_table_query()

        return self._execute_select_query(select_table_query)

    def delete_attendee_table_with_id(self, data: dict) -> None:
        query, params = self._build_delete_attendee_table_query(data)
        self._execute_commit_query(query, params)
