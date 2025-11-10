import os
import sys

import psycopg2
from dotenv import load_dotenv
from psycopg2 import sql

load_dotenv()

POSTGRESQL_USER = os.getenv("POSTGRESQL_USER")
POSTGRESQL_PASSWORD = os.getenv("POSTGRESQL_PASSWORD")
POSTGRESQL_DATABASE_AVAILABLE = os.getenv("POSTGRESQL_DATABASE_AVAILABLE")


class DBManager:
    """Класс для работы с базой данных PostgreSQL"""

    def __init__(self, db_name: str):
        self.db_name = db_name
        self.create_new_db()

    def create_new_db(self) -> None:
        """Создает новую БД>"""

        # Подключение к БД по умолчанию
        try:
            conn = psycopg2.connect(
                database=POSTGRESQL_DATABASE_AVAILABLE,
                user=POSTGRESQL_USER,
                password=POSTGRESQL_PASSWORD,
            )
        except UnicodeDecodeError:
            print("Исправьте пользовательские данные user/password")
            sys.exit()
        conn.autocommit = True
        cur = conn.cursor()

        # Удаление БД db_name при ее наличии
        try:
            cur.execute(
                "SELECT 1 from pg_catalog.pg_database where datname = %s",
                (self.db_name,),
            )
            db_exists = bool(cur.fetchone())
        except psycopg2.Error:
            db_exists = False
        if db_exists:
            query = sql.SQL("DROP database {} with(force)").format(sql.Identifier(self.db_name))
            cur.execute(query)

        # Создание БД db_name
        query = sql.SQL("CREATE database {}").format(sql.Identifier(self.db_name))
        cur.execute(query)
        conn.close()

    def __open(self) -> None:
        """Подключается к новой БД PostgreSQL и создает объект взаимодействия cursor"""

        self.conn = psycopg2.connect(
            database=self.db_name,
            user=POSTGRESQL_USER,
            password=POSTGRESQL_PASSWORD,
        )
        self.conn.autocommit = True
        self.cur = self.conn.cursor()

    def create_table_employers(self, vacancies: list) -> None:
        """Создает и заполняет"""

        # Удаление таблицы employers при ее наличии
        self.__drop_table("employers")

        # Формирование таблицы employers
        self.__open()
        query = "CREATE TABLE employers(employer_id int PRIMARY KEY, employer_name varchar)"
        self.cur.execute(query)
        employers_id_list = list()
        for vacancy in vacancies:
            if vacancy.employer_id not in employers_id_list:
                emp_id = vacancy.employer_id
                emp_name = vacancy.employer_name
                self.cur.execute("INSERT INTO employers VALUES (%s, %s)", (emp_id, emp_name))
                employers_id_list.append(emp_id)
        self.conn.close()

    def create_table_vacancies(self, vacancies: list) -> None:
        """Создает и заполняет"""

        # Удаление таблицы vacancies при ее наличии
        self.__drop_table("vacancies")

        # Формирование таблицы vacancies
        self.__open()
        query = """CREATE TABLE vacancies(
        vacancy_id int PRIMARY KEY,
        employer_id int,
        vacancy_name varchar,
        vacancy_url varchar,
        vacancy_avg_salary real,
        CONSTRAINT fk_vacancies_employer_id FOREIGN KEY(employer_id) REFERENCES employers(employer_id))"""
        self.cur.execute(query)
        for vacancy in vacancies:
            vac_id = vacancy.vacancy_id
            emp_id = vacancy.employer_id
            vac_name = vacancy.vacancy_name
            url = vacancy.vacancy_url
            salary = vacancy.vacancy_avg_salary
            self.cur.execute(
                "INSERT INTO vacancies VALUES (%s, %s, %s, %s, %s)",
                (vac_id, emp_id, vac_name, url, salary),
            )
        self.conn.close()

    def __drop_table(self, table_name: str) -> None:
        """Удаляет таблицу из базы данных"""

        self.__open()
        self.cur.execute(
            "SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name=%s)",
            (table_name,),
        )
        table_exists = self.cur.fetchone()[0]
        if table_exists:
            self.cur.execute("DROP TABLE employers")
        self.conn.close()

    def get_companies_and_vacancies_count(self) -> list:
        """Получает список всех компаний и количество вакансий у каждой компании"""

        self.__open()
        self.cur.execute(
            "SELECT employer_name, COUNT(*) FROM employers JOIN vacancies USING (employer_id) GROUP BY employer_id"
        )
        result = self.cur.fetchall()
        self.conn.close()
        return result

    def get_all_vacancies(self) -> list:
        """Получает список всех вакансий с указанием названия компании,
        названия вакансии и зарплаты и ссылки на вакансию"""

        self.__open()
        self.cur.execute(
            """SELECT employer_name, vacancy_name, vacancy_avg_salary, vacancy_url
            FROM vacancies
            JOIN employers USING (employer_id)"""
        )
        result = self.cur.fetchall()
        self.conn.close()
        return result

    def get_avg_salary(self) -> float:
        """Получает среднюю зарплату по вакансиям"""

        self.__open()
        self.cur.execute("SELECT AVG(vacancy_avg_salary) FROM vacancies")
        result = round((self.cur.fetchone())[0], 2)
        self.conn.close()
        return result

    def get_vacancies_with_higher_salary(self) -> list:
        """Получает список всех вакансий, у которых зарплата выше средней по всем вакансиям"""

        self.__open()
        self.cur.execute(
            """SELECT vacancy_name
            FROM vacancies
            WHERE vacancy_avg_salary > (SELECT AVG(vacancy_avg_salary) FROM vacancies)"""
        )
        result = self.cur.fetchall()
        self.conn.close()
        return result

    def get_vacancies_with_keyword(self, keyword: str) -> list:
        """Получает список всех вакансий, в названии которых содержатся переданные в метод слова, например python"""

        pattern = f"%{keyword}%"
        self.__open()
        self.cur.execute("SELECT vacancy_name FROM vacancies WHERE vacancy_name ILIKE %s", (pattern,))
        result = self.cur.fetchall()
        self.conn.close()
        return result
