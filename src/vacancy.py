import re

import requests


class Vacancy:
    """Класс для работы с вакансиями"""

    __slots__ = [
        "vacancy_id",
        "vacancy_name",
        "vacancy_url",
        "vacancy_avg_salary",
        "employer_id",
        "employer_name",
    ]

    def __init__(
        self,
        vacancy_id,
        vacancy_name,
        vacancy_url,
        vacancy_avg_salary,
        employer_id,
        employer_name,
    ):

        # Исходное id вакансии
        self.vacancy_id = self.__id_valiadation(vacancy_id)

        # Название вакансии
        self.vacancy_name = vacancy_name if vacancy_name else "Не указано"

        # Ссылка на вакансию
        try:
            self.vacancy_url = self.__url_validation(vacancy_url)
        except ValueError:
            self.vacancy_url = "Некорректный адрес ссылки"

        # Средняя зарплата вакансии
        try:
            self.vacancy_avg_salary = self.__salary_validation(vacancy_avg_salary)
        except ValueError:
            self.vacancy_avg_salary = 0

        # Исходное id работодателя
        self.employer_id = self.__id_valiadation(employer_id)

        # Название работодателя
        self.employer_name = employer_name if employer_name else "Не указано"

    def __id_valiadation(self, current_id):
        """Проверка соответствия id положительному целому числу"""

        try:
            current_id = int(current_id) if int(current_id) > 0 else 0
        except ValueError:
            current_id = 0
        finally:
            return current_id

    def __salary_validation(self, vacancy_avg_salary):
        """Проверка соответствия зарплаты положительному числу"""

        try:
            vacancy_avg_salary = float(vacancy_avg_salary)
            if vacancy_avg_salary < 0:
                raise ValueError(f"Зарплата должна быть положительным числом")
            return vacancy_avg_salary
        except ValueError:
            raise ValueError(f"Указанное значение зарплаты не является числом")

    def __url_validation(self, url) -> str:
        """Проверка формата ссылки вакансии"""

        url_pattern = re.compile(r"https://hh.ru/vacancy/\d+")
        if re.fullmatch(url_pattern, str(url)):
            return str(url)
        else:
            raise ValueError("Cсылка не соответствует формату ссылки вакансии hh.ru")

    @classmethod
    def cast_to_object_list(cls, vacancies: list) -> list:
        """Выдает список вакансий в виде экземпляров класса Vacancy"""

        # Получение курса валют для перевода зарплат в руб.
        currency_rates = cls.get_currency_rates()

        # Формирование списка объектов вакансий
        objects_list = []
        if vacancies:
            for vacancy in vacancies:

                # id, название и ссылка для вакансии
                vacancy_id = vacancy.get("id")
                vacancy_name = vacancy.get("name")
                vacancy_url = vacancy.get("alternate_url")

                # Крайние значения диапазона зарплаты и валюта
                salary_start = cls.get_nested_dictionary_value(
                    vacancy, ["salary", "from"]
                )
                salary_stop = cls.get_nested_dictionary_value(vacancy, ["salary", "to"])
                salary_currency_original = cls.get_nested_dictionary_value(
                    vacancy, ["salary", "currency"]
                )

                # Перевод зарплаты в рубли
                if salary_currency_original not in ["RUR", None]:
                    currency_value = cls.get_nested_dictionary_value(
                        currency_rates, [salary_currency_original, "Value"]
                    )
                    currency_nominal = cls.get_nested_dictionary_value(
                        currency_rates, [salary_currency_original, "Nominal"]
                    )
                    currency_rate = (
                        currency_value / currency_nominal
                        if currency_value and currency_nominal
                        else None
                    )
                    salary_start = (
                        round((salary_start * currency_rate), 2)
                        if salary_start and currency_rate
                        else None
                    )
                    salary_stop = (
                        round((salary_stop * currency_rate), 2)
                        if salary_stop and currency_rate
                        else None
                    )

                # Среднее значение зарплаты вакансии
                if salary_start and salary_stop:
                    vacancy_avg_salary = (salary_start + salary_stop) / 2
                elif salary_start:
                    vacancy_avg_salary = salary_start
                elif salary_stop:
                    vacancy_avg_salary = salary_stop
                else:
                    vacancy_avg_salary = 0

                # id работодателя
                employer_id = cls.get_nested_dictionary_value(
                    vacancy, ["employer", "id"]
                )

                # название работодателя
                employer_name = cls.get_nested_dictionary_value(
                    vacancy, ["employer", "name"]
                )

                # Формирования объекта класса Vacancy и добавление к списку объектов
                vacancy_obj = cls(
                    vacancy_id,
                    vacancy_name,
                    vacancy_url,
                    vacancy_avg_salary,
                    employer_id,
                    employer_name,
                )
                objects_list.append(vacancy_obj)

        return objects_list

    @staticmethod
    def get_currency_rates():
        """Выдает список словарей с курсами валют из API ЦБ РФ"""

        url = "https://www.cbr-xml-daily.ru//daily_json.js"
        response = requests.get(url)
        currency_rates = {}
        if response.status_code == 200:
            currency_rates = response.json().get("Valute")
        currency_rates = currency_rates if currency_rates else {}
        return currency_rates

    @staticmethod
    def get_nested_dictionary_value(
        dictionary: dict, consecutive_keys_list: list
    ) -> int | float | str | None:
        """Выдает значение в многоуровневом словаре по последовательности ключей"""

        value = None
        if type(dictionary) is dict and type(consecutive_keys_list) is list:
            nested_dictionary = dictionary
            get_next = True
            key_index = 0

            while get_next and key_index <= len(consecutive_keys_list) - 1:
                try:
                    value = nested_dictionary.get(consecutive_keys_list[key_index])
                    if value:
                        nested_dictionary = value
                        key_index += 1
                    else:
                        get_next = False
                except AttributeError:
                    get_next = False
                    value = None
        return value
