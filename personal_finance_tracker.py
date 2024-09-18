import csv
import os
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
from colorama import init, Fore
from cryptography.fernet import Fernet
import getpass
from sklearn.linear_model import LinearRegression
import numpy as np
import random

# Initialize colorama for colorful terminal output
init(autoreset=True)

# Global variables
FILE_NAME = "finance_data.csv"
BUDGET_FILE = "budgets.csv"
CATEGORIES = ["Income", "Rent", "Groceries", "Utilities", "Entertainment", "Miscellaneous"]
KEY_FILE = "key.key"
PASSWORD_FILE = "password.bin"

# Function to generate encryption key (Run this once to generate a key)
def generate_key():
    key = Fernet.generate_key()
    with open(KEY_FILE, "wb") as key_file:
        key_file.write(key)

# Load encryption key
def load_key():
    if not os.path.exists(KEY_FILE):
        print(f"{Fore.YELLOW}Encryption key not found. Generating a new key.")
        generate_key()  # Generate the key if it doesn't exist
    return open(KEY_FILE, "rb").read()

# Encrypt and store password
def set_password():
    password = getpass.getpass("Set your password: ")
    key = load_key()
    cipher_suite = Fernet(key)
    encrypted_password = cipher_suite.encrypt(password.encode())
    
    with open(PASSWORD_FILE, "wb") as password_file:
        password_file.write(encrypted_password)
    print(f"{Fore.GREEN}Password set successfully!")

# Check password for login
def check_password():
    key = load_key()
    cipher_suite = Fernet(key)
    
    with open(PASSWORD_FILE, "rb") as password_file:
        encrypted_password = password_file.read()
    
    saved_password = cipher_suite.decrypt(encrypted_password).decode()
    input_password = getpass.getpass("Enter your password: ")
    
    if input_password == saved_password:
        print(f"{Fore.GREEN}Access granted!")
        return True
    else:
        print(f"{Fore.RED}Access denied!")
        return False

# Check if data file exists, create one if not
def initialize_file():
    if not os.path.exists(FILE_NAME):
        with open(FILE_NAME, mode="w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(["Date", "Description", "Category", "Amount"])
        print(f"Created new file: {FILE_NAME}")

# Load budgets from file
def load_budgets():
    if not os.path.exists(BUDGET_FILE):
        return {category: 0 for category in CATEGORIES}
    
    budgets = {}
    with open(BUDGET_FILE, mode="r") as file:
        reader = csv.reader(file)
        for row in reader:
            category, amount = row
            budgets[category] = float(amount)
    return budgets

# Save budgets to file
def save_budgets(budgets):
    with open(BUDGET_FILE, mode="w", newline="") as file:
        writer = csv.writer(file)
        for category, amount in budgets.items():
            writer.writerow([category, amount])

# Initialize global budgets dictionary
budgets = load_budgets()

# Function to add a new transaction
def add_transaction():
    date = input("Enter date (YYYY-MM-DD) or leave blank for today: ")
    if not date:
        date = datetime.today().strftime('%Y-%m-%d')
    description = input("Enter transaction description: ")
    print(f"Categories: {', '.join(CATEGORIES)}")
    category = input("Enter category: ").capitalize()
    while category not in CATEGORIES:
        print(f"{Fore.RED}Invalid category. Please choose from {', '.join(CATEGORIES)}")
        category = input("Enter category: ").capitalize()
    amount = float(input("Enter amount (+ for income, - for expense): "))

    with open(FILE_NAME, mode="a", newline="") as file:
        writer = csv.writer(file)
        writer.writerow([date, description, category, amount])
    
    if category != "Income" and amount < 0:
        check_budget(category)
    print(f"{Fore.GREEN}Transaction added successfully!")

# Function to view transactions
def view_transactions():
    df = pd.read_csv(FILE_NAME)
    if df.empty:
        print(f"{Fore.RED}No transactions to display.")
    else:
        print(f"\n{Fore.CYAN}--- Transactions ---")
        print(df)
        print(f"{Fore.CYAN}--------------------")

# Function to generate a report
def generate_report():
    df = pd.read_csv(FILE_NAME)
    if df.empty:
        print(f"{Fore.RED}No transactions available for report.")
        return
    category_group = df.groupby("Category")["Amount"].sum().reset_index()
    print(f"\n{Fore.YELLOW}--- Expense Report ---")
    print(category_group)

    total_income = df[df["Amount"] > 0]["Amount"].sum()
    total_expenses = df[df["Amount"] < 0]["Amount"].sum()
    print(f"\n{Fore.YELLOW}Total Income: {Fore.GREEN}{total_income}")
    print(f"{Fore.YELLOW}Total Expenses: {Fore.RED}{total_expenses}")
    print(f"{Fore.YELLOW}Net Balance: {Fore.CYAN}{total_income + total_expenses}")

# Function to delete a transaction by index
def delete_transaction():
    df = pd.read_csv(FILE_NAME)
    if df.empty:
        print(f"{Fore.RED}No transactions to delete.")
        return
    
    print(f"\n{Fore.CYAN}--- Transactions ---")
    print(df)
    try:
        index = int(input(f"\n{Fore.YELLOW}Enter the index of the transaction to delete: "))
        df.drop(index, inplace=True)
        df.to_csv(FILE_NAME, index=False)
        print(f"{Fore.GREEN}Transaction deleted successfully!")
    except ValueError:
        print(f"{Fore.RED}Invalid index.")
    except KeyError:
        print(f"{Fore.RED}Transaction not found at the given index.")

# Function to clear all transactions and reset the tracker
def clear_all_transactions():
    confirm = input(f"{Fore.YELLOW}Are you sure you want to clear all transactions and reset? (yes/no): ").lower()
    if confirm == 'yes':
        with open(FILE_NAME, mode="w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(["Date", "Description", "Category", "Amount"])
        print(f"{Fore.RED}All transactions cleared. Tracker reset.")
    else:
        print(f"{Fore.CYAN}Operation canceled.")

# Function to check budget for a category
def check_budget(category):
    df = pd.read_csv(FILE_NAME)
    total_expense = df[df["Category"] == category]["Amount"].sum()

    if abs(total_expense) > budgets[category]:
        print(f"{Fore.RED}Warning! You have exceeded the budget for {category}. Total spent: {abs(total_expense)}")

# Function to set custom budget for categories
def set_custom_budget():
    print(f"\n{Fore.CYAN}--- Set Custom Budgets ---")
    for category in CATEGORIES:
        if category != "Income":
            try:
                budget = float(input(f"Enter the budget for {category} (current: {budgets.get(category, 0)}): "))
                budgets[category] = budget
            except ValueError:
                print(f"{Fore.RED}Invalid input. Budget for {category} not updated.")
    save_budgets(budgets)
    print(f"{Fore.GREEN}Custom budgets have been updated successfully!")

# Function to generate pie chart for expenses by category
def generate_pie_chart():
    df = pd.read_csv(FILE_NAME)
    expense_df = df[df['Amount'] < 0]  # Only consider expenses (negative amounts)
    category_group = expense_df.groupby('Category')['Amount'].sum()

    if category_group.empty:
        print(f"{Fore.RED}No expenses to visualize.")
        return
    
    # Convert negative amounts to positive for the pie chart
    category_group = category_group.abs()

    category_group.plot.pie(autopct='%1.1f%%', startangle=90)
    plt.title("Expenses by Category")
    plt.ylabel('')  # Remove the default y-axis label for aesthetics
    plt.show()

# Function to generate bar chart for monthly expenses
def generate_bar_chart():
    df = pd.read_csv(FILE_NAME)
    df['Date'] = pd.to_datetime(df['Date'])
    df['Month'] = df['Date'].dt.to_period('M')
    
    expense_df = df[df['Amount'] < 0]
    monthly_expense = expense_df.groupby('Month')['Amount'].sum().abs()  # Use absolute values
    
    if monthly_expense.empty:
        print(f"{Fore.RED}No monthly expenses to visualize.")
        return
    
    monthly_expense.plot(kind='bar', color='red')
    plt.title("Monthly Expenses")
    plt.xlabel("Month")
    plt.ylabel("Total Expenses")
    plt.xticks(rotation=45)
    plt.show()

# Predict next month's expenses based on historical data
def predict_expenses():
    df = pd.read_csv(FILE_NAME)
    df['Date'] = pd.to_datetime(df['Date'])
    df['Month'] = df['Date'].dt.to_period('M')
    
    expense_df = df[df['Amount'] < 0]
    monthly_expense = expense_df.groupby('Month')['Amount'].sum().abs().reset_index()  # Use absolute values
    monthly_expense['Month'] = monthly_expense['Month'].astype(str)
    
    if len(monthly_expense) == 0:
        print(f"{Fore.RED}Not enough data for expense prediction.")
        return
    
    X = np.arange(len(monthly_expense)).reshape(-1, 1)
    y = monthly_expense['Amount'].values
    
    model = LinearRegression()
    model.fit(X, y)
    
    next_month = len(monthly_expense) + 1
    predicted_expense = model.predict(np.array([[next_month]]))
    print(f"{Fore.CYAN}Predicted expenses for next month: {predicted_expense[0]:.2f}")

# Predict future balance based on trends
def predict_balance():
    df = pd.read_csv(FILE_NAME)
    if df.empty:
        print(f"{Fore.RED}No data available to predict balance.")
        return

    df['Date'] = pd.to_datetime(df['Date'])
    df['Month'] = df['Date'].dt.to_period('M')
    
    balance_df = df.groupby('Month')['Amount'].sum().reset_index()
    balance_df['Month'] = balance_df['Month'].astype(str)
    
    X = np.arange(len(balance_df)).reshape(-1, 1)
    y = balance_df['Amount'].cumsum().values  # Cumulative sum for balance
    
    model = LinearRegression()
    model.fit(X, y)
    
    next_month = len(balance_df) + 1
    predicted_balance = model.predict(np.array([[next_month]]))
    print(f"{Fore.CYAN}Predicted balance for next month: {predicted_balance[0]:.2f}")

# Generate finance tips based on spending habits
def generate_finance_tips():
    tips = [
        "Tip: Try to save at least 20% of your income each month.",
        "Tip: You're spending too much on entertainment. Consider cutting back to stay within budget.",
        "Tip: Avoid impulse buying—track your expenses daily to stay on track.",
        "Tip: Consider automating your savings to ensure you're setting aside money each month.",
        "Tip: Review subscriptions or recurring payments to ensure you're not overpaying."
    ]
    
    df = pd.read_csv(FILE_NAME)
    if df.empty:
        print(f"{Fore.YELLOW}No transactions available for personalized finance tips.")
        return
    
    total_income = df[df["Amount"] > 0]["Amount"].sum()
    total_expenses = abs(df[df["Amount"] < 0]["Amount"].sum())
    
    # Provide personalized tips based on income and expenses
    if total_expenses > total_income * 0.7:
        print(f"{Fore.YELLOW}You're spending more than 70% of your income. {random.choice(tips)}")
    elif total_expenses < total_income * 0.5:
        print(f"{Fore.GREEN}Great job! You're keeping your expenses under 50% of your income.")
    else:
        print(f"{Fore.CYAN}{random.choice(tips)}")

# Export transactions to Excel
def export_to_excel():
    df = pd.read_csv(FILE_NAME)
    if df.empty:
        print(f"{Fore.RED}No transactions to export.")
    else:
        output_file = "transactions.xlsx"
        df.to_excel(output_file, index=False)
        print(f"{Fore.GREEN}Transactions exported to {output_file}")

# Display dashboard
def display_dashboard():
    df = pd.read_csv(FILE_NAME)
    if df.empty:
        print(f"{Fore.YELLOW}No transactions yet. Add some to see the summary!")
        return

    total_income = df[df["Amount"] > 0]["Amount"].sum()
    total_expenses = df[df["Amount"] < 0]["Amount"].sum()
    net_balance = total_income + total_expenses
    
    print(f"\n{Fore.CYAN}--- Financial Summary ---")
    print(f"{Fore.GREEN}Total Income: {total_income}")
    print(f"{Fore.RED}Total Expenses: {total_expenses}")
    print(f"{Fore.CYAN}Net Balance: {net_balance}")
    
    print(f"\n{Fore.YELLOW}--- Budgets Status ---")
    for category, budget in budgets.items():
        spent = abs(df[df["Category"] == category]["Amount"].sum())
        print(f"{category}: {Fore.GREEN if spent <= budget else Fore.RED}{spent} / {budget}")

# Display menu
def display_menu():
    print(f"\n{Fore.MAGENTA}--- Personal Finance Tracker ---")
    print(f"1. Add Transaction")
    print(f"2. View Transactions")
    print(f"3. Generate Report")
    print(f"4. Delete Transaction")
    print(f"5. Display Summary Dashboard")
    print(f"6. Set Custom Budgets")
    print(f"7. Generate Pie Chart (Expenses by Category)")
    print(f"8. Generate Bar Chart (Monthly Expenses)")
    print(f"9. Predict Next Month's Expenses")
    print(f"10. Predict Future Balance")
    print(f"11. Generate Finance Tips")
    print(f"12. Export Transactions to Excel")
    print(f"13. Clear All Transactions and Reset")
    print(f"14. Exit")

# Main function to run the tracker
def main():
    initialize_file()
    
    while True:
        display_menu()
        choice = input("\nChoose an option: ")

        if choice == "1":
            add_transaction()
        elif choice == "2":
            view_transactions()
        elif choice == "3":
            generate_report()
        elif choice == "4":
            delete_transaction()
        elif choice == "5":
            display_dashboard()
        elif choice == "6":
            set_custom_budget()
        elif choice == "7":
            generate_pie_chart()
        elif choice == "8":
            generate_bar_chart()
        elif choice == "9":
            predict_expenses()
        elif choice == "10":
            predict_balance()
        elif choice == "11":
            generate_finance_tips()
        elif choice == "12":
            export_to_excel()
        elif choice == "13":
            clear_all_transactions()
        elif choice == "14":
            print(f"{Fore.CYAN}Goodbye!")
            break
        else:
            print(f"{Fore.RED}Invalid option, please try again.")

# Check password before proceeding with the tracker
if __name__ == "__main__":
    if not os.path.exists(PASSWORD_FILE):
        print(f"{Fore.YELLOW}No password set. You must create a password.")
        set_password()
    
    if not check_password():
        print(f"{Fore.RED}Exiting program.")
        exit()

    main()
