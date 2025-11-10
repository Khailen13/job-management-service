import psycopg2
from psycopg2 import sql
from src.vacancy import Vacancy
import sys
from dotenv import load_dotenv
import os
from api import HeadHunterAPI

load_dotenv()

POSTGRESQL_USER = os.getenv("POSTGRESQL_USER")
POSTGRESQL_PASSWORD = os.getenv("POSTGRESQL_PASSWORD")
POSTGRESQL_DATABASE_AVAILABLE = os.getenv("POSTGRESQL_DATABASE_AVAILABLE")


class DBManager:
    """Класс для работы с базой данных PostgreSQL"""

    db_name: str

    # def __init__(self, db_name):
    #     """ Создает базу данных"""
    #
    #     self.db_name = db_name
    #
    #     self.__create_new_db()


    def __open(self) -> None:
        """Подключение к базе данных PostgreSQL и создание объекта взаимодействия cursor"""

        self.conn = psycopg2.connect(
            database=self.db_name,
            user=POSTGRESQL_USER,
            password=POSTGRESQL_PASSWORD,
        )
        # self.conn.autocommit = True
        self.cur = self.conn.cursor()

    def __close(self) -> None:
        self.cur.close()
        self.conn.close()

    def __check_db_exists(self) -> bool:
        """Проверяет существование базы данных"""

        try:
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
            cur.execute(
                "SELECT 1 from pg_catalog.pg_database where datname = %s",
                (self.db_name,),
            )
            exists = bool(cur.fetchone())
            conn.close()
            return exists
        except psycopg2.Error:
            return False

    def create_new_db(self, db_name) -> None:
        """Создает базу данных"""

        self.db_name = db_name
        conn = psycopg2.connect(
            database=POSTGRESQL_DATABASE_AVAILABLE,
            user=POSTGRESQL_USER,
            password=POSTGRESQL_PASSWORD,
        )
        conn.autocommit = True
        cur = conn.cursor()

        # Удаление базы db_name при ее наличии
        if self.__check_db_exists():
            query = sql.SQL("DROP database {} with(force)").format(
                sql.Identifier(self.db_name)
            )
            cur.execute(query)

        # Создание базы db_name
        query = sql.SQL("CREATE database {}").format(sql.Identifier(self.db_name))
        cur.execute(query)
        conn.close()

    def create_table_employers(self, vacancies) -> None:
        """Создает и заполняет"""

        # Удаление таблицы employers при ее наличии
        self.__drop_table('employers')

        self.conn = psycopg2.connect(
            database=self.db_name,
            user=POSTGRESQL_USER,
            password=POSTGRESQL_PASSWORD,
        )
        self.conn.autocommit = True
        self.cur = self.conn.cursor()

        # Формирование таблицы employers
        query = "CREATE TABLE employers(employer_id int PRIMARY KEY, employer_name varchar)"
        self.cur.execute(query)
        employers_id_list = list()
        for vacancy in vacancies:
            if vacancy.employer_id not in employers_id_list:
                emp_id = vacancy.employer_id
                emp_name = vacancy.employer_name
                self.cur.execute("INSERT INTO employers VALUES (%s, %s)",(emp_id, emp_name))
                employers_id_list.append(emp_id)
        self.cur.close()
        self.conn.close()

    def create_table_vacancies(self, vacancies: list) -> None:
        """Создает и заполняет"""

        # Удаление таблицы vacancies при ее наличии
        self.__drop_table('vacancies')

        self.conn = psycopg2.connect(
            database=self.db_name,
            user=POSTGRESQL_USER,
            password=POSTGRESQL_PASSWORD,
        )
        self.conn.autocommit = True
        self.cur = self.conn.cursor()

        # Формирование таблицы vacancies
        query = "CREATE TABLE vacancies(vacancy_id int PRIMARY KEY,employer_id int,vacancy_name varchar,vacancy_url varchar,vacancy_avg_salary real, CONSTRAINT fk_vacancies_employer_id FOREIGN KEY(employer_id) REFERENCES employers(employer_id))"
        self.cur.execute(query)
        for vacancy in vacancies:
            vac_id = vacancy.vacancy_id
            emp_id = vacancy.employer_id
            vac_name = vacancy.vacancy_name
            url = vacancy.vacancy_url
            salary = vacancy.vacancy_avg_salary
            self.cur.execute("INSERT INTO vacancies VALUES (%s, %s, %s, %s, %s)",(vac_id, emp_id, vac_name, url, salary))

        self.cur.close()
        self.conn.close()

    def __drop_table(self, table_name):
        """Удаляет таблицу из базы данных"""

        self.conn = psycopg2.connect(
            database=self.db_name,
            user=POSTGRESQL_USER,
            password=POSTGRESQL_PASSWORD,
        )
        self.conn.autocommit = True
        self.cur = self.conn.cursor()
        self.cur.execute("SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name=%s)", (table_name,))
        table_exists = self.cur.fetchone()[0]
        if table_exists:
            self.cur.execute("DROP TABLE employers")


    def get_companies_and_vacancies_count(self):
        """Получает список всех компаний и количество вакансий у каждой компании"""

        self.conn = psycopg2.connect(
            database=self.db_name,
            user=POSTGRESQL_USER,
            password=POSTGRESQL_PASSWORD,
        )
        self.conn.autocommit = True
        self.cur = self.conn.cursor()
        self.cur.execute("SELECT employer_name, COUNT(*) FROM employers JOIN vacancies USING (employer_id) GROUP BY employer_id")
        res = self.cur.fetchall()
        self.cur.close()
        self.conn.close()
        print(res)

    def get_all_vacancies(self):
        """Получает список всех вакансий с указанием названия компании, названия вакансии и зарплаты и ссылки на вакансию"""

        self.conn = psycopg2.connect(
            database=self.db_name,
            user=POSTGRESQL_USER,
            password=POSTGRESQL_PASSWORD,
        )
        self.conn.autocommit = True
        self.cur = self.conn.cursor()
        self.cur.execute(
            "SELECT employer_name, vacancy_name, vacancy_avg_salary, vacancy_url FROM vacancies JOIN employers USING (employer_id)")
        res = self.cur.fetchall()
        self.cur.close()
        self.conn.close()
        print(res)


    def get_avg_salary(self):
        """Получает среднюю зарплату по вакансиям"""

        self.conn = psycopg2.connect(
            database=self.db_name,
            user=POSTGRESQL_USER,
            password=POSTGRESQL_PASSWORD,
        )
        self.conn.autocommit = True
        self.cur = self.conn.cursor()
        self.cur.execute("SELECT AVG(vacancy_avg_salary) FROM vacancies")
        res = round(self.cur.fetchone()[0],2)
        self.cur.close()
        self.conn.close()
        print(res)


    def get_vacancies_with_higher_salary(self):
        """Получает список всех вакансий, у которых зарплата выше средней по всем вакансиям"""

        self.conn = psycopg2.connect(
            database=self.db_name,
            user=POSTGRESQL_USER,
            password=POSTGRESQL_PASSWORD,
        )
        self.conn.autocommit = True
        self.cur = self.conn.cursor()
        self.cur.execute("SELECT vacancy_name FROM vacancies WHERE vacancy_avg_salary > (SELECT AVG(vacancy_avg_salary) FROM vacancies)")
        res = self.cur.fetchall()
        self.cur.close()
        self.conn.close()
        print(res)

    def get_vacancies_with_keyword(self, keyword):
        """Получает список всех вакансий, в названии которых содержатся переданные в метод слова, например python"""

        pattern = f'%{keyword}%'
        self.conn = psycopg2.connect(
            database=self.db_name,
            user=POSTGRESQL_USER,
            password=POSTGRESQL_PASSWORD,
        )
        self.conn.autocommit = True
        self.cur = self.conn.cursor()
        # query = sql.SQL("SELECT vacancy_name FROM vacancies WHERE vacancy_name ILIKE {}").format(sql.Identifier('%brAiN%',))
        # self.cur.execute(query)
        # self.cur.execute("SELECT vacancy_name FROM vacancies WHERE vacancy_name ILIKE '%brAiN%'")
        self.cur.execute("SELECT vacancy_name FROM vacancies WHERE vacancy_name ILIKE %s", (pattern,))
        res = self.cur.fetchall()
        self.cur.close()
        self.conn.close()
        print(res)





employers_id = [10197972, 12304464]
hh = HeadHunterAPI()
vacancies = hh.get_vacancies(employers_id)
vacancies_obj_list = Vacancy.cast_to_object_list(vacancies)
db_manager = DBManager()
db_manager.create_new_db("test")
db_manager.create_table_employers(vacancies_obj_list)
db_manager.create_table_vacancies(vacancies_obj_list)
db_manager.get_companies_and_vacancies_count()
db_manager.get_all_vacancies()
db_manager.get_avg_salary()
db_manager.get_vacancies_with_higher_salary()
db_manager.get_vacancies_with_keyword("brain")





