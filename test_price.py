import tkinter as tk
from tkinter import ttk

try:
    from ventilation_company.price_list_tab import PriceListTab

    print("✅ Імпорт PriceListTab — OK")

    root = tk.Tk()
    root.title("Тест прайс-листа")
    root.geometry("900x600")

    notebook = ttk.Notebook(root)
    notebook.pack(fill="both", expand=True)

    # Створюємо ОКРЕМИЙ фрейм для вкладки і передаємо його + root
    tab_frame = tk.Frame(notebook)
    price_tab = PriceListTab(tab_frame, root)
    print("✅ PriceListTab створено")

    # Перевіряємо, чи є дерево
    if hasattr(price_tab, "tree"):
        print("✅ Таблиця (tree) є")
    else:
        print("❌ Таблиця (tree) відсутня!")

    # Перевіряємо, чи є фрейм
    if hasattr(price_tab, "frame"):
        print("✅ Фрейм є")
        notebook.add(price_tab.frame, text="Прайс-лист")
    else:
        print("❌ Фрейм відсутній!")

    root.mainloop()

except Exception as e:
    print(f"❌ ПОМИЛКА: {e}")
    import traceback

    traceback.print_exc()

input("Натисніть Enter...")
