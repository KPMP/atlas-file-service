import os
import mysql.connector
from dotenv import load_dotenv
import logging

logger = logging.getLogger("lib-MYSQLConnection")
logging.basicConfig(level=logging.ERROR)


class MYSQLConnection:
    def __init__(self):
        logger.debug(
            "Start: MYSQLConnection().__init__(), trying to load environment variables in docker"
        )
        self.host = None
        self.port = 3306
        self.user = None
        self.password = None
        self.database_name = "knowledge_environment"

        try:
            self.host = os.environ["MYSQL_HOST"]
            self.user = os.environ["MYSQL_USER"]
            self.password = os.environ["MYSQL_PWD"]
        except Exception as connectError:
            logger.warning(
                "Can't load environment variables from docker... trying local .env file instead...", connectError
            )

    def get_db_cursor(self):
        try:
            self.cursor = self.database.cursor(buffered=False, dictionary=True)
            return self.cursor
        except Exception as error:
            logger.error("Can't get mysql cursor", error)
            os.sys.exit()

    def get_db_connection(self):
        try:
            self.database = mysql.connector.connect(
                host=self.host,
                user=self.user,
                port=self.port,
                password=self.password,
                database=self.database_name,
            )
            self.database.get_warnings = True
            return self.database
        except Exception as error:
            logger.error("Can't connect to MySQL", error)
            os.sys.exit()

    def insert_data(self, sql, data):
        try:
            self.get_db_cursor()
            self.cursor.execute(sql, data)
            warning = self.cursor.fetchwarnings()
            if warning is not None:
                logger.warning(warning)

        except Exception as error:
            logger.error(f"Cannot insert with query: {sql}; and the data: {data}", error)
        finally:
            self.database.commit()
            row_id = self.cursor.lastrowid
            self.cursor.close()
            return row_id

    def get_data(self, sql, query_data=None):
        try:
            self.get_db_cursor()
            data = []
            self.cursor.execute(sql, query_data)
            for row in self.cursor:
                data.append(row)
            return data
        except Exception as error:
            logger.error("Can't get knowledge_environment data.", error)
        finally:
            self.cursor.close()
