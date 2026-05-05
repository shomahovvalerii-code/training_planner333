import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
import requests
from datetime import datetime

# Конфигурация API
# API-ключ можно задать прямо здесь или через переменную окружения EXCHANGE_API_KEY
API_KEY = os.environ.get("EXCHANGE_API_KEY", "YOUR_API_KEY_HERE")
BASE_URL = "https://v6.exchangerate-api.com/v6"

# Список популярных валют (ISO 4217)
CURRENCIES = [
    "USD", "EUR", "GBP", "JPY", "CHF", "CAD", "AUD", "CNY", 
    "RUB", "INR", "BRL", "ZAR", "MXN", "SGD", "HKD", "KRW", 
    "TRY", "SEK", "NOK", "DKK", "PLN", "CZK", "HUF", "ILS"
]

class CurrencyConverter:
    def __init__(self, root):
        self.root = root
        self.root.title("Конвертер валют")
        self.root.geometry("800x600")
        
        self.history_file = "history.json"
        self.history = []
        self.load_history()
        
        self.create_widgets()
    
    # ---------- Работа с данными ----------
    def load_history(self):
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    self.history = json.load(f)
            except:
                self.history = []
    
    def save_history(self):
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self.history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить историю: {e}")
    
    # ---------- GUI ----------
    def create_widgets(self):
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill="both", expand=True)
        
        # Заголовок
        ttk.Label(main_frame, text="💰 Конвертер валют", font=("Arial", 14, "bold")).pack(pady=10)
        
        # Фрейм для ввода
        input_frame = ttk.LabelFrame(main_frame, text="Конвертация", padding=10)
        input_frame.pack(fill="x", pady=5)
        
        # Сумма
        ttk.Label(input_frame, text="Сумма:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.amount_var = tk.StringVar()
        self.amount_entry = ttk.Entry(input_frame, textvariable=self.amount_var, width=15)
        self.amount_entry.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        
        # Из валюты
        ttk.Label(input_frame, text="Из валюты:").grid(row=0, column=2, padx=5, pady=5, sticky="e")
        self.from_currency_var = tk.StringVar()
        self.from_combo = ttk.Combobox(input_frame, textvariable=self.from_currency_var,
                                       values=CURRENCIES, state="readonly", width=10)
        self.from_combo.grid(row=0, column=3, padx=5, pady=5, sticky="w")
        self.from_combo.current(0)  # USD по умолчанию
        
        # В валюту
        ttk.Label(input_frame, text="В валюту:").grid(row=0, column=4, padx=5, pady=5, sticky="e")
        self.to_currency_var = tk.StringVar()
        self.to_combo = ttk.Combobox(input_frame, textvariable=self.to_currency_var,
                                     values=CURRENCIES, state="readonly", width=10)
        self.to_combo.grid(row=0, column=5, padx=5, pady=5, sticky="w")
        self.to_combo.current(1)  # EUR по умолчанию
        
        # Кнопка конвертации
        convert_btn = ttk.Button(input_frame, text="⟳ Конвертировать", command=self.convert)
        convert_btn.grid(row=0, column=6, padx=10, pady=5)
        
        # Фрейм для результата
        result_frame = ttk.LabelFrame(main_frame, text="Результат", padding=10)
        result_frame.pack(fill="x", pady=5)
        
        self.result_var = tk.StringVar(value="Введите сумму и нажмите кнопку")
        ttk.Label(result_frame, textvariable=self.result_var, font=("Arial", 12)).pack()
        
        # История
        hist_frame = ttk.LabelFrame(main_frame, text="История конвертаций", padding=10)
        hist_frame.pack(fill="both", expand=True, pady=5)
        
        columns = ("date", "amount", "from_cur", "to_cur", "result", "rate")
        self.tree = ttk.Treeview(hist_frame, columns=columns, show="headings", height=10)
        
        headings = ["Дата", "Сумма", "Из", "В", "Результат", "Курс"]
        widths = [140, 90, 50, 50, 90, 90]
        for col, head, w in zip(columns, headings, widths):
            self.tree.heading(col, text=head)
            self.tree.column(col, width=w, anchor="center")
        
        vsb = ttk.Scrollbar(hist_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        
        self.tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")
        
        # Кнопки управления историей
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill="x", pady=5)
        ttk.Button(btn_frame, text="Очистить историю", command=self.clear_history).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Экспорт истории", command=self.export_history).pack(side="left", padx=5)
        
        self.display_history()
    
    # ---------- Логика конвертации ----------
    def fetch_conversion_rate(self, from_cur, to_cur):
        """Получает курс конвертации из API"""
        if API_KEY == "YOUR_API_KEY_HERE":
            raise Exception("API-ключ не задан. Установите переменную EXCHANGE_API_KEY или впишите ключ в код.")
        
        url = f"{BASE_URL}/{API_KEY}/pair/{from_cur}/{to_cur}"
        try:
            resp = requests.get(url, timeout=10)
            data = resp.json()
            if data.get("result") == "success":
                return data["conversion_rate"]
            else:
                raise Exception(data.get("error-type", "Неизвестная ошибка API"))
        except requests.exceptions.RequestException as e:
            raise Exception(f"Ошибка сети: {e}")
        except json.JSONDecodeError:
            raise Exception("Некорректный ответ от сервера")
    
    def convert(self):
        amount_str = self.amount_var.get().strip()
        from_cur = self.from_currency_var.get()
        to_cur = self.to_currency_var.get()
        
        # Валидация валют
        if from_cur == to_cur:
            messagebox.showerror("Ошибка", "Выберите разные валюты для конвертации")
            return
        
        # Валидация суммы
        try:
            amount = float(amount_str)
            if amount <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Ошибка", "Введите положительное число (например, 100)")
            return
        
        # Запрос к API и конвертация
        try:
            rate = self.fetch_conversion_rate(from_cur, to_cur)
            result = amount * rate
            self.result_var.set(f"{amount:.2f} {from_cur} = {result:.2f} {to_cur} (курс: {rate:.4f})")
            
            # Сохранение в историю
            history_entry = {
                "date": datetime.now().strftime("%d.%m.%Y %H:%M"),
                "amount": amount,
                "from_cur": from_cur,
                "to_cur": to_cur,
                "result": round(result, 2),
                "rate": rate
            }
            self.history.append(history_entry)
            self.save_history()
            self.display_history()
        except Exception as e:
            messagebox.showerror("Ошибка конвертации", str(e))
    
    # ---------- История ----------
    def display_history(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        # Показываем последние 50 записей, новые сверху
        for entry in reversed(self.history[-50:]):
            self.tree.insert("", "end", values=(
                entry["date"],
                f"{entry['amount']:.2f}",
                entry["from_cur"],
                entry["to_cur"],
                f"{entry['result']:.2f}",
                f"{entry['rate']:.4f}"
            ))
    
    def clear_history(self):
        if messagebox.askyesno("Подтверждение", "Удалить всю историю конвертаций?"):
            self.history = []
            self.save_history()
            self.display_history()
    
    def export_history(self):
        filename = f"conversions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write("История конвертаций валют\n")
                f.write("=" * 40 + "\n\n")
                for entry in self.history:
                    f.write(f"Дата: {entry['date']}\n")
                    f.write(f"{entry['amount']:.2f} {entry['from_cur']} → "
                            f"{entry['result']:.2f} {entry['to_cur']} (курс {entry['rate']:.4f})\n")
                    f.write("-" * 30 + "\n")
            messagebox.showinfo("Экспорт", f"История сохранена в {filename}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось экспортировать: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = CurrencyConverter(root)
    root.mainloop()