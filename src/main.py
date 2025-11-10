from src.api import HeadHunterAPI
from src.db_manager import DBManager
from src.vacancy import Vacancy

# Компании по умолчанию
employers_default = {
    "DeNet": 1006928,
    "ООО НДК": 10197972,
    "Sofoil LLC": 126675703,
    "ООО Хайталент": 11599905,
    "ООО Верме": 3629847,
    "ООО СП Солюшен": 11545313,
    "STORYGOLD AI, INC": 12304464,
    "Your CodeReview": 5962259,
    "ООО ЦЕНТР И": 12420802,
    "ООО РУССМАРКЕТ": 127244399,
}

if __name__ == "__main__":

    # Выбор id компаний (по умолчанию/ручной ввод)
    print("Программа: По умолчанию рассматриваются вакансии следующих компаний:")
    employer_index = 1
    for employer in employers_default.keys():
        print(f"{employer_index}. {employer} (id на hh.ru: {employers_default[employer]})")
        employer_index += 1
    user_answer = input("\nПрограмма: Продолжить работу с данным списком? y/n\n\nПользователь: ")
    if user_answer in ("y", "Y"):
        employers_id_list = list(employers_default.values())
    else:
        employers_id_list_str = input(
            "\nПрограмма: Введите id компаний на hh.ru через пробел.\n\nПользователь: "
        ).split()
        employers_id_list = [int(id) for id in employers_id_list_str]

    # Запрос данных с hh.ru
    print("\nПрограмма: Выполняю запрос данных с hh.ru...")
    hh = HeadHunterAPI()
    vacancies_list_of_dict = hh.get_vacancies(employers_id_list)
    print(f"{' ' * 11}Загрузка данных с hh.ru выполнена успешно.")

    # Создание списка объектов Vacancy
    print(f"{' ' * 11}Формирую объекты Vacancy с отбором необходимых данных...")
    vacancies_list_of_obj = Vacancy.cast_to_object_list(vacancies_list_of_dict)
    print(f"{' ' * 11}Объекты Vacancy успешно сформированы.")

    # Создание базы данных PostgreSQL
    print(f"{' ' * 11}Формирую базу данных PostgreSQL с именем 'hh_vacancies'...")
    db_manager = DBManager("hh_vacancies")
    # db_manager.create_new_db()
    db_manager.create_table_employers(vacancies_list_of_obj)
    db_manager.create_table_vacancies(vacancies_list_of_obj)
    print(f"{' ' * 11}База данных успешно сформирована.")

    # Вывод списка всех компаний и количество вакансий у каждой компании
    print("\nПрограмма: Вывести список всех компаний и количество вакансий у каждой компании? y/n\n")
    user_answer = input("Пользователь: ")
    if user_answer in ("y", "Y"):
        print("\nРаботодатель -- Количество вакансий")
        result_list = db_manager.get_companies_and_vacancies_count()
        number = 1
        for item in result_list:
            print(f"{number}. {item[0]} -- {item[1]}")
            number += 1

    # Вывод списка всех вакансий с указанием названия компании, названия вакансии и зарплаты и ссылки на вакансию
    print(
        "\nПрограмма: Вывести список всех вакансий с указанием названия компании,"
        " названия вакансии и зарплаты и ссылки на вакансию? y/n\n"
    )
    user_answer = input("Пользователь: ")
    if user_answer in ("y", "Y"):
        print("\nКомпания -- Вакансия -- Зарплата, руб. -- Ссылка на вакансию")
        result_list = db_manager.get_all_vacancies()
        number = 1
        for item in result_list:
            print(f"{number}. {item[0]} -- {item[1]} -- {item[2]} -- {item[3]}")
            number += 1

    # Вывод средней зарплаты по вакансиям
    user_answer = input("\nПрограмма: Вывести среднюю зарплату по вакансиям? y/n\n\nПользователь: ")
    if user_answer in ("y", "Y"):
        avg_salary = db_manager.get_avg_salary()
        print(f"\nСредняя зарплата по вакансиям: {avg_salary} руб.")

    # Вывод списка всех вакансий с зарплатой выше средней
    print("\nПрограмма: Вывести список всех вакансий, у которых зарплата выше средней по всем вакансиям? y/n\n")
    user_answer = input("Пользователь: ")
    if user_answer in ("y", "Y"):
        print("\nСписок вакансий с зарплатой выше средней по всем вакансиям ")
        vacancies_with_higher_salary = db_manager.get_vacancies_with_higher_salary()
        number = 1
        for item in vacancies_with_higher_salary:
            print(f"{number}. {item[0]} ")
            number += 1

    # Вывод списка вакансий по ключевому слову
    print("\nПрограмма: Вывести список вакансий по ключевому слову? y/n\n")
    user_answer = input("Пользователь: ")
    if user_answer in ("y", "Y"):
        keyword = input("\nПрограмма: Введите ключевое слово.\n\nПользователь: ")
        vacancies_with_keyword = db_manager.get_vacancies_with_keyword(keyword)
        print(f"\nСписок вакансий по ключевому слову '{keyword}'")
        number = 1
        for item in vacancies_with_keyword:
            print(f"{number}. {item[0]} ")
            number += 1
