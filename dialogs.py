# ---------- dialogs.py ----------
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

class EmployeeDialog:
    def __init__(self, parent, title, initial_data=None):
        self.top = tk.Toplevel(parent)
        self.top.title(title)
        self.top.geometry("400x300")
        self.top.transient(parent)
        self.top.grab_set()
        
        self.result = None
        self.initial_data = initial_data or {}
        
        self.create_widgets()
        self.load_initial_data()
    
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
