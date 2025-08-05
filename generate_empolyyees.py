# Импорт необходимых библиотек
import psycopg2  # Для работы с PostgreSQL
from mimesis import Person, Generic, Field  # Генерация реалистичных данных
from mimesis.enums import Gender  # Гендер для генерации имен
from datetime import datetime, timedelta  # Работа с датами
import random  # Генерация случайных чисел

# Параметры подключения к PostgreSQL
DB_NAME = "employees_db"  # Название базы данных
DB_USER = "postgres"  # Имя пользователя БД
DB_PASSWORD = "_______"  # Пароль (заменить на реальный)
DB_HOST = "localhost"  # Хост базы данных
DB_PORT = "5432"  # Порт PostgreSQL


# Функция создания структуры базы данных
def create_database_structure():
    # Подключение к системной БД для создания новой БД
    conn = psycopg2.connect(
        dbname="postgres",  # Системная БД по умолчанию
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )
    conn.autocommit = True  # Разрешаем автоматическое подтверждение операций
    cursor = conn.cursor()  # Создаем курсор для выполнения SQL-запросов

    # Удаляем старую базу данных если существует
    cursor.execute(f"DROP DATABASE IF EXISTS {DB_NAME}")
    # Создаем новую базу данных
    cursor.execute(f"CREATE DATABASE {DB_NAME}")
    cursor.close()  # Закрываем курсор
    conn.close()  # Закрываем соединение

    # Подключаемся к только что созданной базе данных
    conn = psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )
    cursor = conn.cursor()  # Создаем новый курсор

    # Создаем таблицу сотрудников
    cursor.execute("""
    CREATE TABLE employees (
        id SERIAL PRIMARY KEY,  -- Автоинкрементный ID
        full_name VARCHAR(100) NOT NULL, -- ФИО сотрудника
        position VARCHAR(50) NOT NULL,  --Должность
        hire_date DATE NOT NULL, -- Дата приема на работу
        salary INTEGER NOT NULL,  -- Зарплата
        boss_id INTEGER REFERENCES employees(id)  -- ID начальника (внешний ключ)
    );
    """)
    conn.commit()  # Фиксируем изменения в БД
    return conn, cursor  # Возвращаем соединение и курсор


# Функция генерации сотрудников
def generate_employees(total_employees=50000):
    # Создаем структуру БД и получаем соединение
    conn, cursor = create_database_structure()
    # Инициализируем генераторы данных
    person = Person('ru')  # Генератор персональных данных (русские имена)
    generic = Generic('ru')  # Универсальный генератор данных

    # Словарь должностей по уровням иерархии
    positions = {
        1: "CEO",  # Уровень 1
        2: "Менеджер",  # Уровень 2
        3: "Тимлид",  # Уровень 3
        4: "Старший разработчик",  # Уровень 4
        5: "Разработчик"  # Уровень 5
    }

    # Словарь для хранения ID сотрудников по уровням
    hierarchy = {1: [], 2: [], 3: [], 4: [], 5: []}

    # Генерация CEO (уровень 1)
    ceo = (
        person.full_name(gender=Gender.MALE),  # Генерация ФИО (мужской)
        positions[1],  # Должность CEO
        generic.datetime.date(start=2000, end=2023),  # Дата приема (2000-2023)
        random.randint(300000, 500000),  # Зарплата 300-500 тыс.
        None  # У CEO нет начальника
    )
    # Вставляем CEO в таблицу и возвращаем его ID
    cursor.execute(
        "INSERT INTO employees (full_name, position, hire_date, salary, boss_id) VALUES (%s, %s, %s, %s, %s) RETURNING id",
        ceo
    )
    ceo_id = cursor.fetchone()[0]  # Получаем сгенерированный ID
    hierarchy[1].append(ceo_id)  # Добавляем ID в уровень иерархии
    conn.commit()  # Фиксируем изменения

    # Распределение сотрудников по уровням
    level_counts = {
        2: 5,  # 5 менеджеров
        3: 50,  # 50 тимлидов
        4: 500,  # 500 старших разработчиков
        5: total_employees - 556  # Остальные разработчики (50000 - 1-4 уровни)
    }

    # Функция для добавления сотрудников определенного уровня
    def add_employees(level, count, boss_level):
        for _ in range(count):  # Генерируем заданное количество сотрудников
            # Выбираем случайного начальника из предыдущего уровня
            boss_id = random.choice(hierarchy[boss_level])
            # Генерируем данные сотрудника
            employee = (
                person.full_name(),  # Случайное ФИО
                positions[level],  # Должность текущего уровня
                # Дата приема (2015-2023) - более поздние даты для нижестоящих
                generic.datetime.date(start=2015, end=2023),
                # Зарплата в зависимости от уровня:
                # Уровни 2-4: 100-300 тыс., уровень 5: 50-150 тыс.
                random.randint(100000, 300000) if level < 5 else random.randint(50000, 150000),
                boss_id  # ID начальника
            )
            # Вставляем сотрудника в таблицу
            cursor.execute(
                "INSERT INTO employees (full_name, position, hire_date, salary, boss_id) VALUES (%s, %s, %s, %s, %s) RETURNING id",
                employee
            )
            emp_id = cursor.fetchone()[0]  # Получаем ID нового сотрудника
            hierarchy[level].append(emp_id)  # Добавляем ID в текущий уровень

    # Последовательно генерируем сотрудников всех уровней
    add_employees(2, level_counts[2], 1)  # Менеджеры → подчиняются CEO (уровень 1)
    add_employees(3, level_counts[3], 2)  # Тимлиды → подчиняются менеджерам (уровень 2)
    add_employees(4, level_counts[4], 3)  # Senior → подчиняются тимлидам (уровень 3)
    add_employees(5, level_counts[5], 4)  # Разработчики → подчиняются Senior (уровень 4)

    conn.commit()  # Фиксируем все изменения
    cursor.close()  # Закрываем курсор
    conn.close()  # Закрываем соединение
    print(f"Сгенерировано {total_employees} сотрудников с 5 уровнями иерархии")


# Точка входа в программу
if __name__ == "__main__":
    generate_employees()  # Запуск генерации данных