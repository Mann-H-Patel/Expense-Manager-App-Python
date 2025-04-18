import tkinter as tk
from tkinter import ttk, messagebox
import tkcalendar  # <-- Import DateEntry safely
import sqlite3
from datetime import datetime
import csv

# Get the database file name based on month and year
def get_db_filename(year, month):
    month_name = datetime(year, month, 1).strftime('%B')
    return f"{month_name}_{year}.db"

# Create SQLite table in the specified database
def create_db(year, month):
    db_name = get_db_filename(year, month)
    conn = sqlite3.connect(db_name)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS expenses (
                    id INTEGER PRIMARY KEY,
                    date TEXT,
                    category TEXT,
                    amount REAL,
                    description TEXT,
                    payment_method TEXT,
                    recurring TEXT)''')
    conn.commit()
    conn.close()

# Add an expense to the specific monthly database
def add_expense(date, category, amount, description, payment_method, recurring):
    dt = datetime.strptime(date, "%Y-%m-%d")
    db_name = get_db_filename(dt.year, dt.month)
    create_db(dt.year, dt.month)
    conn = sqlite3.connect(db_name)
    c = conn.cursor()
    c.execute('INSERT INTO expenses (date, category, amount, description, payment_method, recurring) VALUES (?, ?, ?, ?, ?, ?)',
              (date, category, amount, description, payment_method, recurring))
    conn.commit()
    conn.close()

# Retrieve all expenses from current month’s DB
def get_all_expenses():
    now = datetime.now()
    return get_expenses_by_month(now.year, now.month)

# Get expenses for selected month/year
def get_expenses_by_month(year, month):
    try:
        db_name = get_db_filename(year, month)
        conn = sqlite3.connect(db_name)
        c = conn.cursor()
        c.execute('SELECT * FROM expenses ORDER BY date')
        rows = c.fetchall()
        conn.close()
        return rows
    except sqlite3.OperationalError:
        return []

# Delete an expense by ID from current month
def delete_expense(expense_id, year, month):
    db_name = get_db_filename(year, month)
    conn = sqlite3.connect(db_name)
    c = conn.cursor()
    c.execute('DELETE FROM expenses WHERE id = ?', (expense_id,))
    conn.commit()
    conn.close()

# Export to CSV from current month
def export_to_csv(year, month):
    rows = get_expenses_by_month(year, month)
    filename = get_db_filename(year, month).replace('.db', '.csv')
    with open(filename, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["ID", "Date", "Category", "Amount", "Description", "Payment Method", "Recurring"])
        writer.writerows(rows)
    messagebox.showinfo("Export", f"Data exported to {filename}")

# GUI class
class ExpenseManagerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Expense Manager")
        self.current_year = datetime.now().year
        self.current_month = datetime.now().month

        create_db(self.current_year, self.current_month)
        self.setup_ui()

    def setup_ui(self):
        # UI Layout
        self.frame = ttk.Frame(self.root, padding=10)
        self.frame.grid(row=0, column=0)

        # Date
        tk.Label(self.frame, text="Date:").grid(row=0, column=0, sticky='e')
        self.date_entry = tkcalendar.DateEntry(self.frame, date_pattern='yyyy-mm-dd', width=18)
        self.date_entry.grid(row=0, column=1, padx=5, pady=5)

        # Category
        tk.Label(self.frame, text="Category:").grid(row=1, column=0, sticky='e')
        self.category_entry = ttk.Combobox(self.frame, values=["Food", "Housing", "Transport", "Utilities", "Entertainment", "Income"], width=17)
        self.category_entry.grid(row=1, column=1, padx=5, pady=5)

        # Amount
        tk.Label(self.frame, text="Amount:").grid(row=2, column=0, sticky='e')
        self.amount_entry = ttk.Entry(self.frame, width=20)
        self.amount_entry.grid(row=2, column=1, padx=5, pady=5)

        # Description
        tk.Label(self.frame, text="Description:").grid(row=3, column=0, sticky='e')
        self.description_entry = ttk.Entry(self.frame, width=20)
        self.description_entry.grid(row=3, column=1, padx=5, pady=5)

        # Payment Method
        tk.Label(self.frame, text="Payment Method:").grid(row=4, column=0, sticky='e')
        self.payment_method_entry = ttk.Combobox(self.frame, values=["Cash", "Credit Card", "Debit Card", "UPI"], width=17)
        self.payment_method_entry.grid(row=4, column=1, padx=5, pady=5)

        # Recurring
        tk.Label(self.frame, text="Recurring:").grid(row=5, column=0, sticky='e')
        self.recurring_entry = ttk.Combobox(self.frame, values=["No", "Daily", "Weekly", "Monthly"], width=17)
        self.recurring_entry.grid(row=5, column=1, padx=5, pady=5)

        # Buttons
        ttk.Button(self.frame, text="Add Expense", command=self.add_expense).grid(row=6, column=0, padx=5, pady=10)
        ttk.Button(self.frame, text="Export to CSV", command=self.export_data).grid(row=6, column=1, padx=5, pady=10)
        ttk.Button(self.frame, text="Get Data", command=self.get_data).grid(row=7, column=0, padx=5, pady=5)
        ttk.Button(self.frame, text="Delete Data", command=self.delete_data).grid(row=7, column=1, padx=5, pady=5)

        # Treeview
        self.tree = ttk.Treeview(self.root, columns=("ID", "Date", "Category", "Amount", "Description", "Payment Method", "Recurring"), show="headings", height=12)
        for col in self.tree["columns"]:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100, anchor="center")
        self.tree.grid(row=1, column=0, padx=10, pady=10)

        self.load_expenses()

    def load_expenses(self, year=None, month=None):
        if year is None: year = self.current_year
        if month is None: month = self.current_month
        for item in self.tree.get_children():
            self.tree.delete(item)
        for exp in get_expenses_by_month(year, month):
            self.tree.insert("", "end", values=exp)

    def add_expense(self):
        date = self.date_entry.get()
        category = self.category_entry.get()
        description = self.description_entry.get()
        payment_method = self.payment_method_entry.get()
        recurring = self.recurring_entry.get()

        try:
            amount = float(self.amount_entry.get())
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter a valid amount.")
            return

        if not (date and category and payment_method):
            messagebox.showerror("Missing Fields", "Date, Category, and Payment Method are required.")
            return

        add_expense(date, category, amount, description, payment_method, recurring)
        dt = datetime.strptime(date, "%Y-%m-%d")
        self.load_expenses(dt.year, dt.month)

    def delete_data(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showerror("No Selection", "Select a record to delete.")
            return
        expense_id = self.tree.item(selected)["values"][0]
        delete_expense(expense_id, self.current_year, self.current_month)
        self.load_expenses()

    def export_data(self):
        export_to_csv(self.current_year, self.current_month)

    def get_data(self):
        popup = tk.Toplevel(self.root)
        popup.title("Select Month & Year")
        popup.geometry("250x150")

        tk.Label(popup, text="Month:").pack(pady=5)
        month_var = tk.StringVar()
        months = ["January", "February", "March", "April", "May", "June",
                  "July", "August", "September", "October", "November", "December"]
        month_box = ttk.Combobox(popup, textvariable=month_var, values=months, state="readonly")
        month_box.current(self.current_month - 1)
        month_box.pack()

        tk.Label(popup, text="Year:").pack(pady=5)
        year_var = tk.IntVar()
        year_spin = tk.Spinbox(popup, from_=2000, to=2100, textvariable=year_var, width=10)
        year_spin.delete(0, "end")
        year_spin.insert(0, self.current_year)
        year_spin.pack()

        def fetch_and_display():
            if not month_var.get():
                messagebox.showerror("Input Required", "Please select a month.")
                return
            month = months.index(month_var.get()) + 1
            year = int(year_var.get())
            self.current_year, self.current_month = year, month
            self.load_expenses(year, month)
            if not get_expenses_by_month(year, month):
                messagebox.showinfo("No Data", f"No expenses found for {month_var.get()} {year}")
            popup.destroy()

        ttk.Button(popup, text="OK", command=fetch_and_display).pack(pady=10)

if __name__ == "__main__":
    root = tk.Tk()
    app = ExpenseManagerApp(root)
    root.mainloop()
