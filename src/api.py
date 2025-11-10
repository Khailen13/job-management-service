import requests


class HeadHunterAPI:
    """Класс для работы с hh.ru"""

    def __init__(self) -> None:
        """Инициализация атрибутов"""

        self.__url = "https://api.hh.ru/vacancies"
        self.__headers = {"User-Agent": "HH-User-Agent"}
        self.__params = {"employer_id": "", "page": 0, "per_page": 100}
        self.__vacancies = []

    def __status_code(self) -> None:
        """Проверка подключения к API hh.ru"""

        if requests.get(self.__url).status_code != 200:
            raise requests.RequestException

    def get_vacancies(self, employers_id: list) -> list:
        """Получает данные вакансий из hh.ru, соответствующих ключевому слову"""

        try:
            self.__status_code()
        except requests.RequestException as error:
            print(f"Произошла ошибка при запросе вакансий {self.__url}. {error}")
        else:
            self.__params["employer_id"] = employers_id
            while self.__params.get("page") != 20:
                response = requests.get(self.__url, headers=self.__headers, params=self.__params)
                vacancies = response.json()["items"]
                self.__vacancies.extend(vacancies)
                self.__params["page"] += 1
        finally:
            return self.__vacancies
