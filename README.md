# phishSa - WiFi Penetration Testing Dashboard
![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54) 
![Kali](https://img.shields.io/badge/Kali-268BEE?style=for-the-badge&logo=kalilinux&logoColor=white) 
![Ubuntu](https://img.shields.io/badge/Ubuntu-E95420?style=for-the-badge&logo=ubuntu&logoColor=white)

## 🔍 Overview
> phishSa is an advanced dashboard for monitoring and managing WiFi penetration testing operations. It provides real-time visualization of connected clients, captured credentials, and attack analytics with an intuitive web interface.

Designed for:
- Security researchers testing WPA/WPA2-PSK and WPA2 Enterprise setups
- Red teams conducting physical security assessments
- Network administrators validating their defenses

**Key Technical Components:**
- Python-based control system
- `dnsmasq` for DHCP/DNS spoofing
- `hostapd` for AP management
- `iptables` for traffic redirection
- `Lighttpd` web server for captive portal
  
## ✨ Features
- **Real-time Client Monitoring**
  - MAC address tracking
  - Vendor identification
  - Signal strength analysis
  - Client blocking capability  *(under development)*
- **Credential Capture**
  - SSID/Password collection
  - Toggle password visibility
  - Export functionality (JSON/CSV/TXT)  *(under development)*
- **Attack Analytics**
  - Live traffic charts
  - Activity trend visualization
  - Historical data logging
- **Access Point Control**
  - SSID/channel monitoring
  - Interface management

### Prerequisites
- Python 3.8+
- Flask
- Scapy
- socket.io
- ApexCharts

## 🛠️ Installation
```bash
# Clone repository

git clone https://github.com/SaherMuhamed/phishSa.git
cd phishSa

# Install dependencies
sudo apt update && sudo apt install -y hostapd dnsmasq lighttpd

# Install required packages for python
pip install -r requirements.txt
```
## Usage
```bash
sudo python3 phishSa.py --ssid Saher_Wi-Fi --channel 7 --interface wlan0
```

## Screenshots
##### Terminal CLI look
![](https://github.com/SaherMuhamed/phishSa/blob/main/screenshots/Screenshot%202025-05-09%20185258.png)

##### Terminal CLI look (with detailed output)
![](https://github.com/SaherMuhamed/phishSa/blob/main/screenshots/Screenshot%202025-05-09%20185s612.png)

##### Web interface dashboard (light mode)
![](https://github.com/SaherMuhamed/phishSa/blob/main/screenshots/Screenshot%202025-05-09%20185336.png)

##### Web interface dashboard (dark mode) with captured cerdentials
![](https://github.com/SaherMuhamed/phishSa/blob/main/screenshots/Screenshot%202025-05-09%20185441.png)

##### Phishing page from an android mobile after connected to the fake AP
![](https://github.com/SaherMuhamed/phishSa/blob/main/screenshots/phone-1.jpg)

##### Phishing page from an android mobile after connected to the fake AP and enter credentials
![](https://github.com/SaherMuhamed/phishSa/blob/main/screenshots/phone-2.jpg)

> Note: You can modify the `index.html` file and comment the username input field if you target WPA2-PSK (personal home wireless network) not a captive portal

### Options:
```bash
-s, --ssid       SSID for the fake AP
-c, --channel    WiFi channel number
-i, --interface  Wireless interface to use
```

## Ethical Notice
⚠️ This tool is for **authorized security testing and educational purposes only**<br>
❗ Never use against networks **you don't own or have permission** to test.

###### Development Date ==> Ramadan 27/03/2025
