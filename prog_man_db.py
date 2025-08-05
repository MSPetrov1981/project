import tkinter as tk  # Импорт библиотеки для создания GUI
from tkinter import ttk, messagebox, simpledialog  # Дополнительные компоненты GUI
import psycopg2  # Библиотека для работы с PostgreSQL
from psycopg2 import sql  # Безопасное создание SQL-запросов
from datetime import datetime  # Работа с датами и временем


class EmployeeDBApp:
    def __init__(self, root):
        # Инициализация главного окна приложения
        self.root = root  # Сохранение ссылки на корневое окно
        self.root.title("Управление базой данных сотрудников")  # Заголовок окна
        self.root.geometry("900x750")  # Увеличим высоту окна для статусной строки

        # Параметры подключения к БД
        self.db_params = {
            'dbname': 'employees_db',  # Имя базы данных
            'user': 'postgres',  # Имя пользователя
            'password': '_____',  # Пароль
            'host': 'localhost',  # Хост
            'port': '5432'  # Порт
        }
        # Добавляем атрибуты для хранения состояния фильтра########
        self.current_filter_condition = None
        self.current_filter_params = None
        self.conn = None  # Инициализация соединения с БД
        self.connect_to_db()  # Подключение к БД
        # Добавляем атрибуты для хранения состояния сортировк######
        self.current_sort_column = None
        self.current_sort_direction = "ASC"
        self.last_sorted_column = None  # Добавляем для отслеживания последнего отсортированного столбца

        self.create_widgets()  # Создание элементов интерфейса
        self.configure_treeview_style()  # Затем настраиваем стиль
        self.load_employees()  # Загрузка данных сотрудников





    def connect_to_db(self):
        """Подключение к базе данных"""
        try:
            # Установка соединения с использованием параметров
            self.conn = psycopg2.connect(**self.db_params)
        except psycopg2.Error as e:
            # Обработка ошибки подключения
            messagebox.showerror("Ошибка БД", f"Ошибка подключения к базе данных:\n{str(e)}")
            self.root.destroy()  # Закрытие приложения при ошибке

    def create_widgets(self):
        """Создание элементов интерфейса"""
        main_frame = ttk.Frame(self.root)  # Основной фрейм
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)  # Размещение с заполнением

        # Фрейм для кнопок управления
        control_frame = ttk.LabelFrame(main_frame, text="Управление")
        control_frame.pack(fill=tk.X, padx=5, pady=5)  # Размещение с заполнением по X

        # Фрейм для таблицы сотрудников
        table_frame = ttk.LabelFrame(main_frame, text="Сотрудники")
        table_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)  # Размещение с заполнением

        # Фрейм для фильтров и сортировки
        filter_frame = ttk.LabelFrame(main_frame, text="Фильтрация и сортировка")
        filter_frame.pack(fill=tk.X, padx=5, pady=5)  # Размещение с заполнением по X

        # Кнопки управления
        ttk.Button(control_frame, text="Добавить сотрудника", command=self.add_employee).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Редактировать данные", command=self.edit_employee).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Удалить данные", command=self.delete_employee).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Обновить", command=self.load_employees).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Показать иерархию", command=self.show_hierarchy).pack(side=tk.LEFT, padx=5)

        # Настройка таблицы - добавляем столбец с порядковым номером
        #columns = ("number", "id", "full_name", "position", "hire_date", "salary", "boss_name")  # Колонки таблицы
        self.columns = ("number", "id", "full_name", "position", "hire_date", "salary", "boss_name")
        # Русские названия колонок
        russian_columns = {
            "number": "№",
            "id": "ID",
            "full_name": "ФИО",
            "position": "Должность",
            "hire_date": "Дата приема",
            "salary": "Зарплата",
            "boss_name": "Руководитель"
        }

        # Создание виджета Treeview для отображения таблицы
        self.tree = ttk.Treeview(table_frame, columns=self.columns, show="headings", selectmode="browse")
        # Устанавливаем высоту строки
        style = ttk.Style()
        style.configure("Treeview", rowheight=30)
        # Настройка колонок с русскими названиями
        col_widths = [40, 50, 200, 150, 100, 80, 150]  # Ширины колонок
        for col, width in zip(self.columns, col_widths):
            # Настройка заголовков с привязкой к сортировке (кроме колонки с номером)
            if col == "number":
                self.tree.heading(col, text=russian_columns[col])
            else:
                self.tree.heading(col, text=russian_columns[col],
                                  command=lambda c=col: self.sort_treeview(c))

            # Добавляем вертикальные разделители
            self.tree.column(col, width=width, anchor=tk.CENTER, stretch=tk.NO)
        # Настраиваем отображение вертикальных линий
        style = ttk.Style()
        style.configure("Treeview",
                            background="#FFFFFF",
                            fieldbackground="#FFFFFF",
                            bordercolor="#E0E0E0",
                            relief="flat",
                            borderwidth=1)

        # Полоса прокрутки
        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)  # Привязка скроллбара к таблице
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)  # Размещение таблицы
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)  # Размещение скроллбара

        # Фильтры
        ttk.Label(filter_frame, text="Фильтр:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)

        self.filter_var = tk.StringVar()  # Переменная для типа фильтра
        # Варианты фильтров (добавлены новые фильтры для диапазонов)
        filter_options = [
            "Все",
            "Должность",
            "Зарплата >",
            "Зарплата <",
            "Зарплата между",  # НОВЫЙ ФИЛЬТР ДЛЯ ДИАПАЗОНА ЗАРПЛАТ
            "Дата приема >",
            "Дата приема <",
            "Дата приема между",  # НОВЫЙ ФИЛЬТР ДЛЯ ДИАПАЗОНА ДАТ
            "Руководитель"
        ]
        # Выпадающий список для выбора типа фильтра
        ttk.Combobox(filter_frame, textvariable=self.filter_var, values=filter_options, width=15).grid(
            row=0, column=1, padx=5, pady=5, sticky=tk.W)
        self.filter_var.set("Все")  # Значение по умолчанию

        self.filter_value = tk.StringVar()  # Переменная для значения фильтра
        # Поле ввода значения фильтра
        ttk.Entry(filter_frame, textvariable=self.filter_value, width=20).grid(
            row=0, column=2, padx=5, pady=5, sticky=tk.W)

        # Кнопка применения фильтра
        ttk.Button(filter_frame, text="Применить фильтр", command=self.apply_filter).grid(
            row=0, column=3, padx=5, pady=5)
        # Добавляем кнопку помощи в ту же строку
        ttk.Button(filter_frame, text="Помощь", command=self.show_help).grid(
            row=0, column=4, padx=5, pady=5)  ####################
        # Сортировка
        ttk.Label(filter_frame, text="Сортировка:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)

        self.sort_var = tk.StringVar()  # Переменная для типа сортировки
        sort_options = ["ID", "ФИО", "Должность", "Дата приема", "Зарплата"]  # Варианты сортировки
        # Выпадающий список для выбора типа сортировки
        ttk.Combobox(filter_frame, textvariable=self.sort_var, values=sort_options, width=15).grid(
            row=1, column=1, padx=5, pady=5, sticky=tk.W)
        self.sort_var.set("ID")  # Значение по умолчанию

        self.sort_order_var = tk.StringVar(value="ASC")  # Переменная для направления сортировки
        # Радиокнопки для выбора направления сортировки
        ttk.Radiobutton(filter_frame, text="Возрастание", variable=self.sort_order_var, value="ASC").grid(
            row=1, column=2, padx=5, pady=5, sticky=tk.W)
        ttk.Radiobutton(filter_frame, text="Убывание", variable=self.sort_order_var, value="DESC").grid(
            row=1, column=3, padx=5, pady=5, sticky=tk.W)

        # Кнопка применения сортировки
        ttk.Button(filter_frame, text="Применить сортировку", command=self.apply_sort).grid(
            row=1, column=4, padx=5, pady=5)

        # Статусная строка для отображения количества записей
        self.status_var = tk.StringVar()
        self.status_var.set("Всего записей: 0")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=5)

        # Новый метод для отображения помощи

    def show_help(self):
        """Отображение окна помощи по фильтрации и сортировке"""
        help_window = tk.Toplevel(self.root)
        help_window.title("Помощь по фильтрации и сортировке")
        help_window.geometry("700x500")

        # Основной фрейм
        main_frame = ttk.Frame(help_window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Создаем текстовое поле с прокруткой
        text_frame = ttk.Frame(main_frame)
        text_frame.pack(fill=tk.BOTH, expand=True)

        text_area = tk.Text(text_frame, wrap="word", font=("Arial", 10))
        scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=text_area.yview)
        text_area.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        text_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Текст помощи
        help_text = """
           Справка по фильтрации и сортировке данных

           1. Фильтрация данных:
           ----------------------
           - Выберите тип фильтра из выпадающего списка
           - Введите значение для фильтрации в поле ввода
           - Нажмите "Применить фильтр"

           Доступные фильтры:
           - Все: Показать всех сотрудников (без фильтрации)
           - Должность: Фильтр по названию должности (частичное совпадение)
           - Зарплата >: Сотрудники с зарплатой БОЛЬШЕ указанного значения
           - Зарплата <: Сотрудники с зарплатой МЕНЬШЕ указанного значения
           - Зарплата между: Сотрудники с зарплатой в диапазоне (введите два значения через запятую)
           - Дата приема >: Сотрудники, принятые ПОСЛЕ указанной даты (формат: ГГГГ-ММ-ДД)
           - Дата приема <: Сотрудники, принятые ДО указанной даты (формат: ГГГГ-ММ-ДД)
           - Дата приема между: Сотрудники, принятые в диапазоне дат (введите две даты через запятую)
           - Руководитель: Все подчиненные (включая косвенных) для руководителя с указанным ID

           2. Сортировка данных:
           ---------------------
           - Выберите поле для сортировки
           - Выберите направление сортировки (возрастание/убывание)
           - Нажмите "Применить сортировку"

           Также вы можете сортировать данные, нажимая на заголовки столбцов в таблице.

           3. Советы:
           ----------
           - Для отмены фильтрации выберите "Все" и нажмите "Применить фильтр"
           - Для обновления данных нажмите кнопку "Обновить" в верхней панели
           - Вы можете комбинировать фильтрацию и сортировку
           - Для поиска руководителя используйте его ID (отображается в таблице)
           """

        # Вставляем текст и делаем его доступным только для чтения
        text_area.insert(tk.END, help_text.strip())
        text_area.config(state=tk.DISABLED)

        # Кнопка закрытия
        ttk.Button(main_frame, text="Закрыть", command=help_window.destroy).pack(pady=10)

    def configure_treeview_style(self):
        """Настройка стиля Treeview с серой сеткой"""
        style = ttk.Style()
        # Переопределяем layout для добавления отступов
        style.layout("Treeview.Item", [
            ('Treeitem.padding', {
                'sticky': 'nswe',
                'children': [
                    ('Treeitem.indicator', {'side': 'left', 'sticky': ''}),
                    ('Treeitem.image', {'side': 'left', 'sticky': ''}),
                    ('Treeitem.text', {'side': 'left', 'sticky': ''})
                ]
            })
        ])
        # Базовая настройка стиля
        # Настройка отступов
        style.configure("Treeview",
                        padding=(10, 3),  # Горизонтальный и вертикальный отступы
                        background="#FFFFFF",
                        foreground="black",
                        rowheight=30,
                        font=("Arial", 10))
        style.configure("Treeview",
                        background="#FFFFFF",
                        foreground="black",
                        rowheight=20,  # Увеличим высоту строк для лучшего восприятия
                        font=("Arial", 10))

        style.configure("Treeview.Heading",
                        background="#F0F0F0",
                        foreground="black",
                        font=("Arial", 10, "bold"),
                        padding=5)

        # Настройка цветов для чередующихся строк
        style.map("Treeview", background=[("selected", "Gray")])##4A6984

        # Создаем теги для строк
        self.tree.tag_configure("oddrow", background="#FFFFFF")
        self.tree.tag_configure("evenrow", background="#DDDDDD")
        # Для серых линий используем отдельный тег
        self.tree.tag_configure("gridline", background="#E0E0E0")


    def execute_query(self, query, params=None):
        """Выполнение SQL-запроса"""
        try:
            with self.conn.cursor() as cur:  # Создание курсора
                cur.execute(query, params)  # Выполнение запроса
                if cur.description:  # Если есть результат (SELECT запрос)
                    return cur.fetchall()  # Возврат результатов
                self.conn.commit()  # Фиксация изменений для INSERT/UPDATE/DELETE
                return True  # Успешное выполнение
        except psycopg2.Error as e:
            self.conn.rollback()  # Откат изменений при ошибке
            messagebox.showerror("Ошибка БД", f"Ошибка выполнения запроса:\n{str(e)}")
            return None  # Возврат None при ошибке

    def load_employees(self):
        """Загрузка сотрудников с сохранением параметров  фильтрации и сортировки"""
        query = """
          SELECT e.id, e.full_name, e.position, e.hire_date, e.salary, 
                 b.full_name AS boss_name
          FROM employees e
          LEFT JOIN employees b ON e.boss_id = b.id
          """

        # Добавление условий фильтрации (если есть сохраненные)
        if self.current_filter_condition:
            query += f" WHERE {self.current_filter_condition}"
            params = self.current_filter_params
        else:
            params = None
        # Добавление сортировки (если указан столбец)
        if self.current_sort_column:
            query += f" ORDER BY {self.current_sort_column} {self.current_sort_direction}"

        # Выполнение запроса
        employees = self.execute_query(query, params)

        # Очистка таблицы
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Обновление статусной строки
        count = len(employees) if employees else 0
        self.status_var.set(f"Найдено записей: {count}")

        # Заполнение таблицы с добавлением порядкового номера
        if employees:
            for i, emp in enumerate(employees, start=1):
                # Форматирование данных
                formatted_emp = list(emp)
                formatted_emp[3] = formatted_emp[3].strftime("%Y-%m-%d")  # Формат даты
                formatted_emp[4] = f"{formatted_emp[4]:,}"  # Формат зарплаты
                # Определяем тег для строки (чередование цветов)
                tag = "evenrow" if i % 2 == 0 else "oddrow"
                # Добавляем порядковый номер в начало
                row_data = [i] + formatted_emp
                # Вставка данных в таблицу
                self.tree.insert("", tk.END, values=row_data, tags=(tag,))
                # Добавляем горизонтальную линию после каждой строки
                #if i < len(employees):  # Не добавляем после последней строки
                #    # ИСПРАВЛЕНО: используем self.columns
                #    self.tree.insert("", tk.END, values=[""] * len(self.columns), tags=("gridline",))

    def sort_treeview(self, column):
        """Сортировка по выбранной колонке (исключая колонку с номером), с учетом текущего фильтра"""
        # Соответствие колонок таблицы полям БД
        column_mapping = {
            "id": "e.id",
            "full_name": "e.full_name",
            "position": "e.position",
            "hire_date": "e.hire_date",
            "salary": "e.salary",
            "boss_name": "b.full_name"
        }

        if column in column_mapping:
            column_db = column_mapping[column]
            #если это тот же столбец -меняем направление
            if self.last_sorted_column == column_db:
                self.current_sort_direction = "DESC" if self.current_sort_direction == "ASC" else "ASC"
                #если новый столбец - сбрасываем направление
            # Используем сохраненные параметры фильтра
            else:

                self.current_sort_direction = "ASC"
            # Обновляем текущий столбец и сохраняем последний отсортированный
            self.current_sort_column = column_db
            self.last_sorted_column = column_db
            # Загружаем данные с текущими параметрами фильтра и сортировки
            self.load_employees()
    def apply_filter(self):
        """Применение выбранного фильтра"""
        filter_type = self.filter_var.get()  # Тип фильтра
        filter_val = self.filter_value.get().strip()  # Значение фильтра

        condition = None  # Условие WHERE
        params = None  # Параметры для запроса

        if filter_type == "Все":  # Без фильтра
            condition = "1=1"  # Все записи
        elif filter_type == "Должность" and filter_val:  # Фильтр по должности
            condition = "e.position ILIKE %s"
            params = (f"%{filter_val}%",)
        elif filter_type == "Зарплата >" and filter_val:  # Зарплата больше
            try:
                salary = int(filter_val)
                condition = "e.salary > %s"
                params = (salary,)
            except ValueError:
                messagebox.showerror("Ошибка", "Зарплата должна быть числом")
                return
        elif filter_type == "Зарплата <" and filter_val:  # Зарплата меньше
            try:
                salary = int(filter_val)
                condition = "e.salary < %s"
                params = (salary,)
            except ValueError:
                messagebox.showerror("Ошибка", "Зарплата должна быть числом")
                return
        # НОВЫЙ ФИЛЬТР: ЗАРПЛАТА МЕЖДУ ДВУМЯ ЗНАЧЕНИЯМИ
        elif filter_type == "Зарплата между" and filter_val:
            try:
                # Разделение значений по запятой
                values = filter_val.split(',')
                if len(values) != 2:
                    raise ValueError("Нужно два значения через запятую")

                # Преобразование в числа и проверка диапазона
                min_salary = int(values[0].strip())
                max_salary = int(values[1].strip())

                if min_salary > max_salary:
                    min_salary, max_salary = max_salary, min_salary

                condition = "e.salary BETWEEN %s AND %s"
                params = (min_salary, max_salary)
            except ValueError as e:
                messagebox.showerror("Ошибка", f"Некорректный диапазон зарплат:\n{str(e)}")
                return
        elif filter_type == "Дата приема >" and filter_val:  # Дата приема после
            # обработка года (4 цифры) или года-месяца
            if len(filter_val) == 4 and filter_val.isdigit():
                # если указан только год-фильтр за весь год и позже
                condition = "e.hire_date >= %s"
                params = (f"{filter_val}-01-01",)
            elif len(filter_val) == 7 and filter_val[4] == '-':  # Формат ГГГГ-ММ
                try:
                    year, month = filter_val.split('-')
                    # Проверка валидности месяца
                    if 1 <= int(month) <= 12:
                        condition = "e.hire_date >= %s"
                        params = (f"{year}-{month}-01",)
                    else:
                        raise ValueError("Некорректный месяц")
                except ValueError:
                    messagebox.showerror("Ошибка", "Используйте формат ГГГГ-ММ")
                    return
            else:
                try:
                    # Проверка формата полной даты
                    datetime.strptime(filter_val, "%Y-%m-%d")
                    condition = "e.hire_date > %s"
                    params = (filter_val,)
                except ValueError:
                    messagebox.showerror("Ошибка", "Используйте формат ГГГГ, ГГГГ-ММ или ГГГГ-ММ-ДД")
                    return

        elif filter_type == "Дата приема <" and filter_val:  # Дата приема до
            if len(filter_val) == 4 and filter_val.isdigit():
                # если указан только год-фильтр до начала года
                condition = "e.hire_date < %s"
                params = (f"{filter_val}-01-01",)
            elif len(filter_val) == 7 and filter_val[4] == '-':  # Формат ГГГГ-ММ
                try:
                    year, month = filter_val.split('-')
                    # Проверка валидности месяца
                    if 1 <= int(month) <= 12:
                        # Рассчитываем последний день месяца
                        next_month = int(month) % 12 + 1
                        next_year = int(year) + (int(month) // 12)
                        condition = "e.hire_date < %s"
                        params = (f"{next_year}-{next_month:02d}-01",)
                    else:
                        raise ValueError("Некорректный месяц")
                except ValueError:
                    messagebox.showerror("Ошибка", "Используйте формат ГГГГ-ММ")
                    return
            else:
                try:
                    datetime.strptime(filter_val, "%Y-%m-%d")
                    condition = "e.hire_date < %s"
                    params = (filter_val,)
                except ValueError:
                    messagebox.showerror("Ошибка", "Используйте формат ГГГГ, ГГГГ-ММ или ГГГГ-ММ-ДД")
                    return

        # НОВЫЙ ФИЛЬТР: ДАТА ПРИЕМА МЕЖДУ ДВУМЯ ДАТАМИ
        elif filter_type == "Дата приема между" and filter_val:
            try:
                # Разделение значений по запятой
                dates = filter_val.split(',')
                if len(dates) != 2:
                    raise ValueError("Нужно две даты через запятую")

                start_date_str = dates[0].strip()
                end_date_str = dates[1].strip()

                # Обработка форматов для начальной даты
                if len(start_date_str) == 4 and start_date_str.isdigit():
                    start_date = f"{start_date_str}-01-01"
                elif len(start_date_str) == 7 and start_date_str[4] == '-':
                    year, month = start_date_str.split('-')
                    if 1 <= int(month) <= 12:
                        start_date = f"{year}-{month}-01"
                    else:
                        raise ValueError("Некорректный месяц в начальной дате")
                else:
                    # Проверка формата полной даты
                    datetime.strptime(start_date_str, "%Y-%m-%d")
                    start_date = start_date_str

                # Обработка форматов для конечной даты
                if len(end_date_str) == 4 and end_date_str.isdigit():
                    end_date = f"{end_date_str}-12-31"
                elif len(end_date_str) == 7 and end_date_str[4] == '-':
                    year, month = end_date_str.split('-')
                    if 1 <= int(month) <= 12:
                        # Рассчитываем последний день месяца
                        next_month = int(month) % 12 + 1
                        next_year = int(year) + (int(month) // 12)
                        end_date = f"{next_year}-{next_month:02d}-01"
                    else:
                        raise ValueError("Некорректный месяц в конечной дате")
                else:
                    # Проверка формата полной даты
                    datetime.strptime(end_date_str, "%Y-%m-%d")
                    end_date = end_date_str

                # Проверка формата обеих дат
                datetime.strptime(start_date, "%Y-%m-%d")
                datetime.strptime(end_date, "%Y-%m-%d")

                # Установка диапазона
                condition = "e.hire_date BETWEEN %s AND %s"
                params = (start_date, end_date)
            except ValueError as e:
                messagebox.showerror("Ошибка", f"Некорректный диапазон дат:\n{str(e)}")
                return

        elif filter_type == "Руководитель" and filter_val:  # Фильтр по руководителю
            try:
                # Получаем ID руководителя как число
                boss_id_val = int(filter_val)
                # Проверка существования руководителя
                check_query = "SELECT id FROM employees WHERE id = %s"
                cur = self.conn.cursor()
                cur.execute(check_query, (boss_id_val,))
                if not cur.fetchone():
                    messagebox.showerror("Ошибка", "Руководитель с таким ID не найден")
                    cur.close()
                    return
                cur.close()

                # Рекурсивный запрос для получения подчиненных
                recursive_query = """
                WITH RECURSIVE subordinates AS (
                    SELECT id
                    FROM employees
                    WHERE boss_id = %s
                    UNION ALL
                    SELECT e.id
                    FROM employees e
                    INNER JOIN subordinates s ON e.boss_id = s.id
                )
                SELECT id FROM subordinates
                """
                cur = self.conn.cursor()
                cur.execute(recursive_query, (boss_id_val,))

                # Получаем ID как целые числа
                ids = [row[0] for row in cur.fetchall()]
                cur.close()

                if ids:
                    # Формируем список ID в виде кортежа
                    id_tuple = tuple(ids)
                    condition = "e.id IN %s"
                    params = (id_tuple,)
                else:
                    condition = "1=0"  # Нет результатов
                    params = None
            except ValueError:
                messagebox.showerror("Ошибка", "ID руководителя должен быть числом")
                return

        # Загрузка данных с примененным фильтром
        if condition:
            #сохраняем параметры фильтра перед загрузкой
            self.current_filter_condition = condition
            self.current_filter_params = params
        else:
            #сбрасываем фильтр при выборе "все"
            self.current_filter_condition = None
            self.current_filter_params = None
        self.load_employees()
    def apply_sort(self):
        """Применение выбранной сортировки"""
        sort_column = self.sort_var.get()  # Выбранная колонка для сортировки
        # Соответствие названий колонок полям БД
        column_mapping = {
            "ID": "e.id",
            "ФИО": "e.full_name",
            "Должность": "e.position",
            "Дата приема": "e.hire_date",
            "Зарплата": "e.salary"
        }

        if sort_column in column_mapping:
            #обновляем параметры сортировки
            self.current_sort_column = column_mapping[sort_column]
            self.current_sort_direction = self.sort_order_var.get()
            self.last_sorted_column = self.current_sort_column
            # Загрузка данных с новой сортировкой
            self.load_employees()

    def show_hierarchy(self):
        """Отображение иерархии подчиненных для выбранного сотрудника"""
        selected = self.tree.selection()  # Выбранный элемент в таблице
        if not selected:
            messagebox.showwarning("Внимание", "Выберите сотрудника")
            return

        # Получение ID выбранного сотрудника (второй столбец, так как первый - номер)
        emp_id = self.tree.item(selected[0], "values")[1]

        # Создание нового окна для иерархии
        hierarchy_window = tk.Toplevel(self.root)
        hierarchy_window.title(f"Иерархия подчиненных")
        hierarchy_window.geometry("820x600")

        # Создаем основной фрейм
        main_frame = ttk.Frame(hierarchy_window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Создаем контейнер для Treeview и скроллбаров
        container = ttk.Frame(main_frame)
        container.pack(fill=tk.BOTH, expand=True)

        # Создание Treeview для отображения иерархии
        tree = ttk.Treeview(container, columns=("id", "full_name", "position"), show="tree headings")

        tree.heading("#0", text="Сотрудник")  # Заголовок древовидного представления
        tree.column("#0", width=250)  # Ширина колонки
        tree.heading("id", text="ID")  # Заголовок колонки ID
        tree.column("id", width=50, anchor=tk.CENTER)  # Ширина и выравнивание
        tree.heading("full_name", text="ФИО")  # Заголовок колонки ФИО
        tree.column("full_name", width=250)  # Ширина колонки
        tree.heading("position", text="Должность")  # Заголовок колонки должности
        tree.column("position", width=200)  # Ширина колонки

        # Вертикальный скроллбар
        vsb = ttk.Scrollbar(container, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=vsb.set)

        #

        # Размещение элементов
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)




        # Настройка стиля для отображения сетки
        style = ttk.Style(hierarchy_window)
        style.configure("Treeview",
                        background="#FFFFFF",
                        foreground="black",
                        rowheight=30,
                        font=("Arial", 10),
                        bordercolor="#E0E0E0",
                        relief="solid",
                        borderwidth=1)

        style.configure("Treeview.Heading",
                        background="#F0F0F0",
                        foreground="black",
                        font=("Arial", 10, "bold"),
                        padding=5)

        # Создаем теги для строк
       # tree.tag_configure("oddrow", background="#FFFFFF")
       # tree.tag_configure("evenrow", background="#DDDDDD")
        # используем цвет в зависимости от уровня вложенности
        level_colors = {
            1: "#FFFFFF",  # Белый для корневого уровня
            2: "#CCFFFF",  # Голубой для первого уровня подчинения
            3: "#CCCCFF",  # Светло-сиреневый для второго уровня
            4: "#FFF8DC",  # Светло-бежевый для третьего уровня
            5: "#FFCCCC",  #светло коричневый
        }
        # Создаем теги для разных уровней
        for level, color in level_colors.items():
            tree.tag_configure(f"level{level}", background=color)

        # Кнопка закрытия
        close_button = ttk.Button(main_frame, text="Закрыть", command=hierarchy_window.destroy)
        close_button.pack(pady=10)

        try:
            with self.conn.cursor() as cur:
                # Рекурсивный запрос для получения иерархии подчиненных
                hierarchy_query = """
                WITH RECURSIVE employee_hierarchy AS (
                    SELECT id, full_name, position, boss_id, 1 AS level
                    FROM employees
                    WHERE id = %s
                    UNION ALL
                    SELECT e.id, e.full_name, e.position, e.boss_id, eh.level + 1
                    FROM employees e
                    INNER JOIN employee_hierarchy eh ON e.boss_id = eh.id
                )
                SELECT id, full_name, position, boss_id, level
                FROM employee_hierarchy
                ORDER BY level, id
                """
                cur.execute(hierarchy_query, (emp_id,))
                employees = cur.fetchall()  # Получение результатов

                if not employees:
                    messagebox.showinfo("Информация", "У выбранного сотрудника нет подчиненных")
                    hierarchy_window.destroy()
                    return

                # Словарь для хранения узлов дерева
                nodes = {}

                for emp in employees:
                    emp_id, full_name, position, boss_id, level = emp


                    # Определяем тег для строки (чередование цветов)
                    tag = f"level{level}" if level in level_colors else ""

                    # Корневой элемент (выбранный сотрудник)
                    if level == 1:
                        node = tree.insert("", "end", iid=emp_id, text=f"{full_name} ({position})",
                                           values=(emp_id, full_name, position), tags=(tag,),open=True)
                        nodes[emp_id] = node
                    else:
                        # Поиск родительского узла
                        parent_node = nodes.get(boss_id)
                        if parent_node:
                            # Добавление дочернего узла
                            node = tree.insert(parent_node, "end", iid=emp_id, text=f"{full_name} ({position})",
                                               values=(emp_id, full_name, position),tags=(tag,))
                            nodes[emp_id] = node



        except psycopg2.Error as e:
            messagebox.showerror("Ошибка БД", f"Ошибка получения иерархии:\n{str(e)}")
            hierarchy_window.destroy()  # Закрытие окна при ошибке

    def add_employee(self):
        """Добавление нового сотрудника"""
        # Создание диалогового окна
        dialog = EmployeeDialog(self.root, "Добавить сотрудника")
        self.root.wait_window(dialog.top)  # Ожидание закрытия диалога

        if dialog.result:  # Если данные введены
            query = """
            INSERT INTO employees (full_name, position, hire_date, salary, boss_id)
            VALUES (%s, %s, %s, %s, %s)
            """
            params = (
                dialog.result["full_name"],
                dialog.result["position"],
                dialog.result["hire_date"],
                dialog.result["salary"],
                dialog.result["boss_id"]
            )

            if self.execute_query(query, params):
                self.load_employees()  # Обновление данных
                messagebox.showinfo("Успех", "Сотрудник добавлен")  # Уведомление

    def edit_employee(self):
        """Редактирование данных сотрудника"""
        selected = self.tree.selection()  # Выбранный сотрудник
        if not selected:
            messagebox.showwarning("Внимание", "Выберите сотрудника")
            return

        item = selected[0]
        # ID сотрудника находится во втором столбце
        emp_id = self.tree.item(item, "values")[1]

        # Получение данных сотрудника
        query = "SELECT * FROM employees WHERE id = %s"
        employee = self.execute_query(query, (emp_id,))

        if employee:
            # Создание диалога с текущими данными
            dialog = EmployeeDialog(
                self.root,
                "Редактировать сотрудника",
                initial_data={
                    "id": emp_id,
                    "full_name": employee[0][1],
                    "position": employee[0][2],
                    "hire_date": employee[0][3].strftime("%Y-%m-%d"),
                    "salary": employee[0][4],
                    "boss_id": employee[0][5]
                }
            )
            self.root.wait_window(dialog.top)  # Ожидание закрытия диалога

            if dialog.result:
                query = """
                UPDATE employees
                SET full_name = %s, position = %s, hire_date = %s, 
                    salary = %s, boss_id = %s
                WHERE id = %s
                """
                params = (
                    dialog.result["full_name"],
                    dialog.result["position"],
                    dialog.result["hire_date"],
                    dialog.result["salary"],
                    dialog.result["boss_id"],
                    emp_id
                )

                if self.execute_query(query, params):
                    self.load_employees()  # Обновление данных
                    messagebox.showinfo("Успех", "Данные обновлены")  # Уведомление

    def delete_employee(self):
        """Удаление сотрудника"""
        selected = self.tree.selection()  # Выбранный сотрудник
        if not selected:
            messagebox.showwarning("Внимание", "Выберите сотрудника")
            return

        item = selected[0]
        # ID сотрудника находится во втором столбце
        emp_id = self.tree.item(item, "values")[1]
        # Имя сотрудника в третьем столбце
        emp_name = self.tree.item(item, "values")[2]

        # Подтверждение удаления
        if messagebox.askyesno(
                "Подтверждение",
                f"Удалить {emp_name} (ID: {emp_id})?"
        ):
            query = "DELETE FROM employees WHERE id = %s"  # Запрос на удаление
            if self.execute_query(query, (emp_id,)):
                self.load_employees()  # Обновление данных
                messagebox.showinfo("Успех", "Сотрудник удален")  # Уведомление

    def __del__(self):
        """Закрытие соединения с БД при уничтожении объекта"""
        if self.conn:
            self.conn.close()  # Закрытие соединения


class EmployeeDialog:
    """Диалоговое окно для добавления/редактирования сотрудника"""

    def __init__(self, parent, title, initial_data=None):
        self.top = tk.Toplevel(parent)  # Создание диалогового окна
        self.top.title(title)  # Заголовок окна
        self.top.geometry("400x300")  # Размер окна
        self.top.transient(parent)  # Установка отношения родитель-потомок
        self.top.grab_set()  # Захват фокуса

        self.result = None  # Результат работы диалога
        self.initial_data = initial_data or {}  # Начальные данные

        self.create_widgets()  # Создание элементов
        self.load_initial_data()  # Загрузка начальных данных

    def create_widgets(self):
        """Создание элементов диалогового окна"""
        main_frame = ttk.Frame(self.top)  # Основной фрейм
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)  # Размещение

        # Поля формы
        fields = [
            ("full_name", "ФИО:"),
            ("position", "Должность:"),
            ("hire_date", "Дата приема (ГГГГ-ММ-ДД):"),
            ("salary", "Зарплата:"),
            ("boss_id", "ID Руководителя:")
        ]

        self.entries = {}  # Словарь для полей ввода
        for i, (field, label) in enumerate(fields):
            ttk.Label(main_frame, text=label).grid(row=i, column=0, padx=5, pady=5, sticky=tk.W)  # Метка
            entry = ttk.Entry(main_frame)  # Поле ввода
            entry.grid(row=i, column=1, padx=5, pady=5, sticky=tk.EW)  # Размещение
            self.entries[field] = entry  # Сохранение ссылки

        button_frame = ttk.Frame(main_frame)  # Фрейм для кнопок
        button_frame.grid(row=len(fields), column=0, columnspan=2, pady=10)  # Размещение

        # Кнопки
        ttk.Button(button_frame, text="Сохранить", command=self.save).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Отмена", command=self.cancel).pack(side=tk.LEFT, padx=5)
        main_frame.columnconfigure(1, weight=1)  # Настройка расширения колонки

    def load_initial_data(self):
        """Загрузка начальных данных для редактирования"""
        for field, entry in self.entries.items():
            if field in self.initial_data:  # Если есть значение
                entry.insert(0, str(self.initial_data[field]))  # Вставка в поле

    def save(self):
        """Сохранение данных из формы"""
        data = {}  # Словарь для данных
        errors = []  # Список ошибок

        # Валидация ФИО
        data["full_name"] = self.entries["full_name"].get().strip()
        if not data["full_name"]:
            errors.append("Укажите ФИО")

        # Валидация должности
        data["position"] = self.entries["position"].get().strip()
        if not data["position"]:
            errors.append("Укажите должность")

        # Валидация даты приема
        hire_date = self.entries["hire_date"].get().strip()
        if hire_date:
            try:
                datetime.strptime(hire_date, "%Y-%m-%d")  # Проверка формата
                data["hire_date"] = hire_date
            except ValueError:
                errors.append("Неверный формат даты. Используйте ГГГГ-ММ-ДД")
        else:
            errors.append("Укажите дату приема")

        # Валидация зарплаты
        salary = self.entries["salary"].get().strip()
        if salary:
            try:
                data["salary"] = int(salary)  # Преобразование в число
            except ValueError:
                errors.append("Зарплата должна быть числом")
        else:
            errors.append("Укажите зарплату")

        # Валидация ID руководителя
        boss_id = self.entries["boss_id"].get().strip()
        if boss_id:
            try:
                data["boss_id"] = int(boss_id)  # Преобразование в число
            except ValueError:
                errors.append("ID руководителя должен быть числом")
        else:
            data["boss_id"] = None  # Руководитель не указан

        if errors:
            messagebox.showerror("Ошибки", "\n".join(errors))  # Показ ошибок
            return

        self.result = data  # Сохранение результата
        self.top.destroy()  # Закрытие диалога

    def cancel(self):
        """Отмена действия"""
        self.result = None  # Сброс результата
        self.top.destroy()  # Закрытие диалога


if __name__ == "__main__":
    root = tk.Tk()  # Создание главного окна
    app = EmployeeDBApp(root)  # Создание экземпляра приложения
    root.mainloop()  # Запуск главного цикла