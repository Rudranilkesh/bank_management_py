import json
import re
import secrets
import string
from pathlib import Path

import streamlit as st


DATA_FILE = Path(__file__).with_name("data.json")
MAX_TRANSACTION_AMOUNT = 10_000


def load_accounts():
    """Return saved accounts, treating a missing or empty file as no accounts."""
    if not DATA_FILE.exists() or DATA_FILE.stat().st_size == 0:
        return []

    try:
        with DATA_FILE.open("r", encoding="utf-8") as file:
            accounts = json.load(file)
        return accounts if isinstance(accounts, list) else []
    except json.JSONDecodeError:
        st.warning("data.json is invalid, so the app started with no loaded accounts.")
        return []


def save_accounts(accounts):
    with DATA_FILE.open("w", encoding="utf-8") as file:
        json.dump(accounts, file, indent=2)


def generate_account_number(accounts):
    existing_numbers = {account["accountNo"] for account in accounts}
    alphabet = string.ascii_uppercase
    while True:
        account_number = "".join(secrets.choice(alphabet + string.digits) for _ in range(9))
        if account_number not in existing_numbers:
            return account_number


def valid_email(email):
    return bool(re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email))


def valid_pin(pin):
    return len(pin) == 4 and pin.isdigit()


def find_account(accounts, account_number, pin):
    return next(
        (
            account
            for account in accounts
            if account["accountNo"] == account_number.strip().upper()
            and str(account["pin"]) == pin
        ),
        None,
    )


def account_login(accounts, key_prefix):
    account_number = st.text_input("Account number", key=f"{key_prefix}_account")
    pin = st.text_input("4-digit PIN", type="password", max_chars=4, key=f"{key_prefix}_pin")
    return find_account(accounts, account_number, pin)


def create_account_page(accounts):
    st.subheader("Create an account")
    with st.form("create_account"):
        name = st.text_input("Full name")
        age = st.number_input("Age", min_value=0, max_value=130, step=1)
        email = st.text_input("Email address")
        pin = st.text_input("Choose a 4-digit PIN", type="password", max_chars=4)
        confirm_pin = st.text_input("Confirm PIN", type="password", max_chars=4)
        submitted = st.form_submit_button("Create account")

    if submitted:
        if not name.strip():
            st.error("Enter your name.")
        elif age < 18:
            st.error("You must be at least 18 years old to create an account.")
        elif not valid_email(email.strip()):
            st.error("Enter a valid email address.")
        elif not valid_pin(pin):
            st.error("Your PIN must contain exactly four digits.")
        elif pin != confirm_pin:
            st.error("The PINs do not match.")
        else:
            account = {
                "name": name.strip(),
                "age": int(age),
                "email": email.strip().lower(),
                "pin": pin,
                "accountNo": generate_account_number(accounts),
                "balance": 0.0,
            }
            accounts.append(account)
            save_accounts(accounts)
            st.success("Account created successfully.")
            st.info(f"Your account number is: **{account['accountNo']}**")


def deposit_page(accounts):
    st.subheader("Deposit money")
    with st.form("deposit"):
        account = account_login(accounts, "deposit")
        amount = st.number_input("Amount", min_value=0.0, step=100.0, format="%.2f")
        submitted = st.form_submit_button("Deposit")

    if submitted:
        if not account:
            st.error("Account number or PIN is incorrect.")
        elif not 0 < amount <= MAX_TRANSACTION_AMOUNT:
            st.error(f"Enter an amount between 0 and {MAX_TRANSACTION_AMOUNT:,}.")
        else:
            account["balance"] += amount
            save_accounts(accounts)
            st.success(f"{amount:,.2f} deposited. New balance: {account['balance']:,.2f}")


def withdraw_page(accounts):
    st.subheader("Withdraw money")
    with st.form("withdraw"):
        account = account_login(accounts, "withdraw")
        amount = st.number_input("Amount", min_value=0.0, step=100.0, format="%.2f")
        submitted = st.form_submit_button("Withdraw")

    if submitted:
        if not account:
            st.error("Account number or PIN is incorrect.")
        elif not 0 < amount <= MAX_TRANSACTION_AMOUNT:
            st.error(f"Enter an amount between 0 and {MAX_TRANSACTION_AMOUNT:,}.")
        elif amount > account["balance"]:
            st.error("Insufficient balance.")
        else:
            account["balance"] -= amount
            save_accounts(accounts)
            st.success(f"{amount:,.2f} withdrawn. New balance: {account['balance']:,.2f}")


def details_page(accounts):
    st.subheader("Account details")
    with st.form("details"):
        account = account_login(accounts, "details")
        submitted = st.form_submit_button("Show details")

    if submitted:
        if not account:
            st.error("Account number or PIN is incorrect.")
        else:
            st.metric("Balance", f"{account['balance']:,.2f}")
            st.write(f"**Name:** {account['name']}")
            st.write(f"**Age:** {account['age']}")
            st.write(f"**Email:** {account['email']}")
            st.write(f"**Account number:** {account['accountNo']}")


def update_page(accounts):
    st.subheader("Update account details")
    with st.form("update"):
        account = account_login(accounts, "update")
        name = st.text_input("New name (leave blank to keep current)")
        email = st.text_input("New email (leave blank to keep current)")
        new_pin = st.text_input("New 4-digit PIN (leave blank to keep current)", type="password", max_chars=4)
        submitted = st.form_submit_button("Update details")

    if submitted:
        if not account:
            st.error("Account number or PIN is incorrect.")
        elif email and not valid_email(email.strip()):
            st.error("Enter a valid email address.")
        elif new_pin and not valid_pin(new_pin):
            st.error("Your new PIN must contain exactly four digits.")
        elif not any([name.strip(), email.strip(), new_pin]):
            st.info("No changes were entered.")
        else:
            if name.strip():
                account["name"] = name.strip()
            if email.strip():
                account["email"] = email.strip().lower()
            if new_pin:
                account["pin"] = new_pin
            save_accounts(accounts)
            st.success("Account details updated successfully.")


def delete_page(accounts):
    st.subheader("Delete account")
    st.warning("This action permanently removes the account and its balance.")
    with st.form("delete"):
        account = account_login(accounts, "delete")
        confirmed = st.checkbox("I understand that this cannot be undone.")
        submitted = st.form_submit_button("Delete account", type="primary")

    if submitted:
        if not account:
            st.error("Account number or PIN is incorrect.")
        elif not confirmed:
            st.error("Confirm deletion before continuing.")
        else:
            accounts.remove(account)
            save_accounts(accounts)
            st.success("Account deleted successfully.")


def main():
    st.set_page_config(page_title="Bank Management", page_icon="🏦", layout="centered")
    st.title("🏦 Bank Management System")
    st.caption("A simple Streamlit app with JSON file storage.")

    accounts = load_accounts()
    page = st.sidebar.radio(
        "Choose an option",
        ["Create account", "Deposit", "Withdraw", "Account details", "Update details", "Delete account"],
    )

    pages = {
        "Create account": create_account_page,
        "Deposit": deposit_page,
        "Withdraw": withdraw_page,
        "Account details": details_page,
        "Update details": update_page,
        "Delete account": delete_page,
    }
    pages[page](accounts)


if __name__ == "__main__":
    main()
