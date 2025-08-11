# ---------- utils.py ----------
import tkinter as tk
from tkinter import ttk

def configure_treeview_style():
    style = ttk.Style()
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
    
    style.configure("Treeview",
                   padding=(10, 3),
                   background="#FFFFFF",
                   foreground="black",
                   rowheight=30,
                   font=("Arial", 10),
                   bordercolor="#E0E0E0")
    
    style.configure("Treeview.Heading",
                   background="#F0F0F0",
                   foreground="black",
                   font=("Arial", 10, "bold"),
                   padding=5)
    
    style.map("Treeview", background=[("selected", "Gray")])