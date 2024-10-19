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
            topic TEXT,
            files TEXT,
            pt_contents TEXT,
            status TEXT,
            summary TEXT            
        )
        """
    
    def _build_create_attendee_table_query(self) -> str:
        return f"""
        CREATE TABLE IF NOT EXISTS attendee (
            id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
            meeting_name TEXT,
            name TEXT,
            organization TEXT,
            position TEXT,
            email_address TEXT,
            role TEXT,
            email_delivery_status BOOL,
            attendance_status BOOL,
            initial_attendance_time TEXT,
            connected_device TEXT
        )
        """
    
    def _build_create_qa_table_query(self) -> str:
        return f"""
        CREATE TABLE IF NOT EXISTS qa (
            id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
            speaker TEXT,
            timestamp TEXT,
            message TEXT
        )
        """
    
    def _build_insert_meeting_table_query(self, data: dict) -> tuple[str, tuple]:
        query = """
            INSERT INTO meeting (name, start_time, end_time, room, subject, topic, files, pt_contents, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        params = (data["name"], data["start_time"], data["end_time"], data["room"], data["subject"], data["topic"], data["files"], data["pt_contents"], data["status"])
        return query, params

    def _build_insert_attendee_info_table_query(self, data: dict) -> tuple[str, tuple]:
        query = """
            INSERT INTO attendee (meeting_name, name, organization, position, email_address, role, email_delivery_status)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        params = (data["meeting_name"], data["name"], data["organization"], data["position"], data["email_address"], data["role"], data["email_delivery_status"])
        return query, params
    
    def _build_insert_qa_table_query(self, data: dict) -> tuple[str, tuple]:
        query = """
            INSERT INTO qa (speaker, timestamp, message)
            VALUES (%s, %s, %s)
        """
        params = (data["speaker"], data["timestamp"], data["message"])
        return query, params
    
    def _build_update_attendee_attendance_info_table_query(self, data: dict) -> tuple[str, tuple]:
        query = """
            UPDATE attendee SET attendance_status = %s, initial_attendance_time = %s, connected_device = %s
            WHERE id = %s
        """
        params = (data["attendance_status"], data["initial_attendance_time"], data["connected_device"], data["id"])
        return query, params
    
    def _build_update_meeting_status_table_query(self, status: str) -> tuple[str, tuple]:
        query = """
            UPDATE meeting SET status = %s            
        """
        params = (status)
        return query, params
    
    def _build_update_meeting_summary_table_query(self, summary: str) -> tuple[str, tuple]:
        query = """
            UPDATE meeting SET summary = %s            
        """
        params = (summary)
        return query, params
    
    def _build_select_all_meeting_table_query(self) -> str:
        return f"""
            SELECT * FROM meeting ORDER BY id desc
        """
    
    def _build_select_all_attendee_table_query(self) -> str:
        return f"""
            SELECT * FROM attendee ORDER BY id
        """
    
    def _build_select_all_qa_table_query(self) -> str:
        return f"""
            SELECT * FROM qa ORDER BY id
        """
    
    def _build_select_attendee_table_query(self, id: int) -> str:
        return f"""
            SELECT * FROM attendee ORDER BY id desc WHERE id = {id}
        """
    
    def _build_delete_attendee_table_query(self, data: dict) -> tuple[str, tuple]:
        query = """
            DELETE FROM attendee WHERE name = %s AND email_address = %s
        """
        params = (data["name"], data["email_address"])
        return query, params
    
    def _build_delete_all_meeting_table_query(self) -> str:
        return """
            DELETE FROM meeting
        """
    
    def _build_delete_all_attendee_table_query(self) -> str:
        return """
            DELETE FROM attendee
        """
    
    def _build_delete_all_qa_table_query(self) -> str:
        return """
            DELETE FROM qa
        """
        
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
    
    def create_qa_table(self) -> int:
        create_table_query = self._build_create_qa_table_query()
        
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

    def insert_qa_table(self, data: dict) -> None:
        query, params = self._build_insert_qa_table_query(data)        
        self._execute_commit_query(query, params)

    def update_attendee_attendance_info_table(self, data: dict) -> None:
        query, params = self._build_update_attendee_attendance_info_table_query(data)        
        self._execute_commit_query(query, params)

    def update_meeting_status_table(self, status: str) -> None:
        query, params = self._build_update_meeting_status_table_query(status)
        self._execute_commit_query(query, params)

    def update_meeting_summary_table(self, summary: str) -> None:
        query, params = self._build_update_meeting_summary_table_query(summary)
        self._execute_commit_query(query, params)
    
    def select_all_meeting_table(self) -> List[Any]:
        select_table_query = self._build_select_all_meeting_table_query()

        return self._execute_select_query(select_table_query)
    
    def select_all_attendee_table(self) -> List[Any]:
        select_table_query = self._build_select_all_attendee_table_query()

        return self._execute_select_query(select_table_query)
    
    def select_all_qa_table(self) -> List[Any]:
        select_table_query = self._build_select_all_qa_table_query()

        return self._execute_select_query(select_table_query)
    
    def select_attendee_table_with_id(self, id: int) -> List[Any]:
        select_table_query = self._build_select_attendee_table_query(id)

        return self._execute_select_query(select_table_query)

    def delete_attendee_table_with_id(self, data: dict) -> None:
        query, params = self._build_delete_attendee_table_query(data)
        self._execute_commit_query(query, params)

    def delete_all_meeting_table(self) -> None:
        query = self._build_delete_all_meeting_table_query()
        self._execute_commit_query(query, ())

    def delete_all_attendee_table(self) -> None:
        query = self._build_delete_all_attendee_table_query()
        self._execute_commit_query(query, ())

    def delete_all_qa_table(self) -> None:
        query = self._build_delete_all_qa_table_query()
        self._execute_commit_query(query, ())
