import psycopg2
from psycopg2 import sql
from tabulate import tabulate
import argparse
import sys

# Конфигурация подключения к БД
DB_CONFIG = {
    "dbname": "employees_db",
    "user": "postgres",
    "password": "_____",  # Замените на ваш пароль
    "host": "localhost",
    "port": "5432"
}


def get_connection():
    """Установка соединения с базой данных"""
    return psycopg2.connect(**DB_CONFIG)


def list_employees(sort_by="id", filters=None, output_format="table"):
    """Получение списка сотрудников с сортировкой и фильтрацией"""
    conn = get_connection()
    cursor = conn.cursor()

    # Базовый запрос
    query = sql.SQL("SELECT * FROM employees")
    params = []
    conditions = []

    # Добавление фильтров
    if filters:
        for filter_expr in filters:
            # Поддерживаемые операторы: =, !=, >, <, >=, <=
            operators = ['!=', '>=', '<=', '=', '>', '<']
            found = False

            for op in operators:
                if op in filter_expr:
                    field, value = filter_expr.split(op, 1)
                    field = field.strip()
                    value = value.strip()

                    # Для числовых полей преобразуем значение
                    if field in ['id', 'salary', 'boss_id']:
                        try:
                            value = int(value)
                        except ValueError:
                            print(f"Некорректное числовое значение для {field}: {value}")
                            return

                    # Формируем условие SQL
                    condition = sql.SQL("{} {} %s").format(
                        sql.Identifier(field),
                        sql.SQL(op)
                    )

                    conditions.append(condition)
                    params.append(value)
                    found = True
                    break

            if not found:
                print(f"Некорректный фильтр: {filter_expr}")
                print("Поддерживаемые операторы: =, !=, >, <, >=, <=")
                return

    # Объединяем условия фильтрации
    if conditions:
        query = sql.SQL("{} WHERE {}").format(query, sql.SQL(" AND ").join(conditions))

    # Добавление сортировки
    try:
        query = sql.SQL("{} ORDER BY {}").format(query, sql.Identifier(sort_by))
    except:
        print(f"Некорректное поле для сортировки: {sort_by}")
        return

    try:
        cursor.execute(query, params)
        results = cursor.fetchall()
        colnames = [desc[0] for desc in cursor.description]

        if output_format == "table":
            print(tabulate(results, headers=colnames, tablefmt="grid"))
        elif output_format == "csv":
            print(",".join(colnames))
            for row in results:
                print(",".join(map(str, row)))
        print(f"Найдено записей: {len(results)}")

    except psycopg2.Error as e:
        print(f"Ошибка при выполнении запроса: {e}")
    finally:
        cursor.close()
        conn.close()


def add_employee(full_name, position, hire_date, salary, boss_id=None):
    """Добавление нового сотрудника"""
    conn = get_connection()
    cursor = conn.cursor()

    query = sql.SQL("""
        INSERT INTO employees (full_name, position, hire_date, salary, boss_id)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id
    """)

    try:
        cursor.execute(query, (full_name, position, hire_date, salary, boss_id))
        new_id = cursor.fetchone()[0]
        conn.commit()
        print(f"Добавлен новый сотрудник с ID: {new_id}")
    except psycopg2.Error as e:
        conn.rollback()
        print(f"Ошибка при добавлении сотрудника: {e}")
    finally:
        cursor.close()
        conn.close()


def update_employee(employee_id, **kwargs):
    """Обновление данных сотрудника"""
    if not kwargs:
        print("Не указаны поля для обновления")
        return

    conn = get_connection()
    cursor = conn.cursor()

    set_clause = sql.SQL(", ").join(
        sql.SQL("{} = %s").format(sql.Identifier(field))
        for field in kwargs.keys()
    )

    query = sql.SQL("""
        UPDATE employees
        SET {}
        WHERE id = %s
    """).format(set_clause)

    values = list(kwargs.values()) + [employee_id]

    try:
        cursor.execute(query, values)
        if cursor.rowcount > 0:
            conn.commit()
            print(f"Обновлен сотрудник с ID: {employee_id}")
        else:
            print("Сотрудник не найден")
    except psycopg2.Error as e:
        conn.rollback()
        print(f"Ошибка при обновлении сотрудника: {e}")
    finally:
        cursor.close()
        conn.close()


def delete_employee(employee_id):
    """Удаление сотрудника"""
    conn = get_connection()
    cursor = conn.cursor()

    query = sql.SQL("DELETE FROM employees WHERE id = %s")

    try:
        cursor.execute(query, (employee_id,))
        if cursor.rowcount > 0:
            conn.commit()
            print(f"Удален сотрудник с ID: {employee_id}")
        else:
            print("Сотрудник не найден")
    except psycopg2.Error as e:
        conn.rollback()
        print(f"Ошибка при удалении сотрудника: {e}")
    finally:
        cursor.close()
        conn.close()


def main():
    """Основной парсер командной строки"""
    parser = argparse.ArgumentParser(description="Управление базой данных сотрудников")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Парсер для команды list
    list_parser = subparsers.add_parser("list", help="Просмотр сотрудников")
    list_parser.add_argument("--sort", default="id", help="Поле для сортировки")
    list_parser.add_argument("--filter", action="append", help="Фильтр в формате поле=значение")
    list_parser.add_argument("--output", choices=["table", "csv"], default="table", help="Формат вывода")

    # Парсер для команды add
    add_parser = subparsers.add_parser("add", help="Добавить нового сотрудника")
    add_parser.add_argument("--full_name", required=True, help="Полное имя")
    add_parser.add_argument("--position", required=True, help="Должность")
    add_parser.add_argument("--hire_date", required=True, help="Дата приема (YYYY-MM-DD)")
    add_parser.add_argument("--salary", type=int, required=True, help="Зарплата")
    add_parser.add_argument("--boss_id", type=int, help="ID руководителя")

    # Парсер для команды update
    update_parser = subparsers.add_parser("update", help="Обновить данные сотрудника")
    update_parser.add_argument("id", type=int, help="ID сотрудника")
    update_parser.add_argument("--full_name", help="Полное имя")
    update_parser.add_argument("--position", help="Должность")
    update_parser.add_argument("--hire_date", help="Дата приема (YYYY-MM-DD)")
    update_parser.add_argument("--salary", type=int, help="Зарплата")
    update_parser.add_argument("--boss_id", type=int, help="ID руководителя")

    # Парсер для команды delete
    delete_parser = subparsers.add_parser("delete", help="Удалить сотрудника")
    delete_parser.add_argument("id", type=int, help="ID сотрудника")

    args = parser.parse_args()

    if args.command == "list":
        list_employees(
            sort_by=args.sort,
            filters=args.filter,
            output_format=args.output
        )
    elif args.command == "add":
        add_employee(
            full_name=args.full_name,
            position=args.position,
            hire_date=args.hire_date,
            salary=args.salary,
            boss_id=args.boss_id
        )
    elif args.command == "update":
        update_params = {k: v for k, v in vars(args).items()
                         if v is not None and k not in ["command", "id"]}
        update_employee(args.id, **update_params)
    elif args.command == "delete":
        delete_employee(args.id)


if __name__ == "__main__":
    main()