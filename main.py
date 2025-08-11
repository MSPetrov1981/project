# ---------- main.py ----------
import tkinter as tk
from app import EmployeeDBApp

if __name__ == "__main__":
    root = tk.Tk()
    app = EmployeeDBApp(root)
    root.mainloop()