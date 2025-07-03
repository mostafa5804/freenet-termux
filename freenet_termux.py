# freenet_termux.py

import os
import sys
import json
import base64
import urllib.parse
import subprocess
import time
import requests
import random
import socket
import threading
import concurrent.futures
from urllib.parse import urlparse, parse_qs
from datetime import datetime
from tqdm import tqdm

# --- ANSI Color Codes ---
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    RESET = '\033[0m'

# --- Configuration (Matched with freenet.py) ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.expanduser('~/storage/shared/Download/freenet')
XRAY_PATH = os.path.join(BASE_DIR, "xray")
TEMP_FOLDER = os.path.join(BASE_DIR, "temp")

BEST_CONFIGS_FILE = os.path.join(OUTPUT_DIR, "best_configs.txt")
LOG_FILE = os.path.join(OUTPUT_DIR, "log.txt")

# --- Settings from freenet.py ---
PING_TEST_URL = "https://old-queen-f906.mynameissajjad.workers.dev/login"
TEST_TIMEOUT = 4  # The actual timeout used in the original script's request

MIRRORS = {
    "barry-far": "https://raw.githubusercontent.com/barry-far/V2ray-Config/refs/heads/main/All_Configs_Sub.txt",
    "SoliSpirit": "https://raw.githubusercontent.com/SoliSpirit/v2ray-configs/refs/heads/main/all_configs.txt",
    "mrvcoder": "https://raw.githubusercontent.com/mrvcoder/V2rayCollector/refs/heads/main/mixed_iran.txt",
    "MatinGhanbari": "https://raw.githubusercontent.com/MatinGhanbari/v2ray-configs/main/subscriptions/v2ray/all_sub.txt",
}

# --- Helper Functions ---

def log(message, color=Colors.WHITE):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    console_message = f"{color}[{timestamp}] {message}{Colors.RESET}"
    file_message = f"[{timestamp}] {message}\n"
    print(console_message)
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(file_message)

def setup_environment():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(TEMP_FOLDER, exist_ok=True)
    if not os.path.exists(LOG_FILE):
        open(LOG_FILE, 'w').close()
    log("Environment is ready.", Colors.CYAN)
    log(f"Output files will be saved in: {OUTPUT_DIR}", Colors.CYAN)

def clear_temp_folder():
    try:
        for filename in os.listdir(TEMP_FOLDER):
            file_path = os.path.join(TEMP_FOLDER, filename)
            if os.path.isfile(file_path):
                os.unlink(file_path)
    except Exception as e:
        log(f"Error clearing temp folder: {e}", Colors.RED)

def kill_xray_processes():
    try:
        subprocess.run(['pkill', '-f', 'xray'], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        log("Killed previous Xray processes.", Colors.YELLOW)
    except Exception as e:
        log(f"Error killing Xray processes: {e}", Colors.RED)

def send_notification(title, message):
    try:
        subprocess.run(['termux-notification', '--title', title, '--content', message], check=False)
    except FileNotFoundError:
        log("Termux-API is not installed. Cannot send notifications.", Colors.YELLOW)
    except Exception as e:
        log(f"Error sending notification: {e}", Colors.RED)

# --- Core Logic ---

class ConfigTester:
    def __init__(self):
        self.stop_event = threading.Event()

    def fetch_configs(self, url):
        try:
            log(f"Fetching configs from: {url}", Colors.CYAN)
            response = requests.get(url, timeout=15)
            response.raise_for_status()
            response.encoding = 'utf-8'
            configs = [line.strip() for line in response.text.splitlines() if line.strip()]
            log(f"Successfully fetched {len(configs)} configs.", Colors.GREEN)
            return configs[::-1] # Reverse the list to match freenet.py
        except requests.RequestException as e:
            log(f"Error fetching configs: {e}", Colors.RED)
            return []

    def is_port_available(self, port):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(('127.0.0.1', port))
                return True
            except:
                return False

    def get_available_port(self):
        for _ in range(10): # Try 10 times to find a random port
            port = random.randint(49152, 65535)
            if self.is_port_available(port):
                return port
        return random.randint(10800, 11800) # Fallback

    # --- Start of Parsers (Corrected and Adapted) ---
    def vmess_to_json(self, vmess_url, port):
        if not vmess_url.startswith("vmess://"):
            raise ValueError("Invalid VMess URL format")
        
        base64_str = vmess_url[8:]
        padded = base64_str + '=' * (4 - len(base64_str) % 4)
        decoded_bytes = base64.urlsafe_b64decode(padded)
        decoded_str = decoded_bytes.decode('utf-8')
        vmess_config = json.loads(decoded_str)
        
        xray_config = {
            "inbounds": [{
                "port": port,
                "listen": "127.0.0.1",
                "protocol": "socks",
                "settings": {"udp": True}
            }],
            "outbounds": [{
                "protocol": "vmess",
                "settings": {
                    "vnext": [{
                        "address": vmess_config["add"],
                        "port": int(vmess_config["port"]),
                        "users": [{
                            "id": vmess_config["id"],
                            "alterId": int(vmess_config.get("aid", 0)),
                            "security": vmess_config.get("scy", "auto")
                        }]
                    }]
                },
                "streamSettings": {
                    "network": vmess_config.get("net", "tcp"),
                    "security": vmess_config.get("tls", ""),
                    "tcpSettings": {
                        "header": {
                            "type": vmess_config.get("type", "none"),
                            "request": {
                                "path": [vmess_config.get("path", "/")],
                                "headers": {
                                    "Host": [vmess_config.get("host", "")]
                                }
                            }
                        }
                    } if vmess_config.get("net") == "tcp" and vmess_config.get("type") == "http" else None
                }
            }]
        }
        
        if not xray_config["outbounds"][0]["streamSettings"]["security"]:
            del xray_config["outbounds"][0]["streamSettings"]["security"]
        if not xray_config["outbounds"][0]["streamSettings"].get("tcpSettings"):
            xray_config["outbounds"][0]["streamSettings"].pop("tcpSettings", None)
        
        return xray_config

    def parse_vless(self, uri, port):
        parsed = urllib.parse.urlparse(uri)
        config = {
            "inbounds": [{
                "port": port,
                "listen": "127.0.0.1",
                "protocol": "socks",
                "settings": {"udp": True}
            }],
            "outbounds": [{
                "protocol": "vless",
                "settings": {
                    "vnext": [{
                        "address": parsed.hostname,
                        "port": parsed.port,
                        "users": [{
                            "id": parsed.username,
                            "encryption": parse_qs(parsed.query).get("encryption", ["none"])[0]
                        }]
                    }]
                },
                "streamSettings": {
                    "network": parse_qs(parsed.query).get("type", ["tcp"])[0],
                    "security": parse_qs(parsed.query).get("security", ["none"])[0]
                }
            }]
        }
        return config

    def parse_shadowsocks(self, uri, port):
        if not uri.startswith("ss://"):
            raise ValueError("Invalid Shadowsocks URI")
        
        parts = uri[5:].split("#", 1)
        encoded_part = parts[0]
        remark = urllib.parse.unquote(parts[1]) if len(parts) > 1 else "Imported Shadowsocks"

        if "@" in encoded_part:
            userinfo, server_part = encoded_part.split("@", 1)
        else:
            decoded = base64.b64decode(encoded_part + '=' * (-len(encoded_part) % 4)).decode('utf-8')
            if "@" in decoded:
                userinfo, server_part = decoded.split("@", 1)
            else:
                userinfo = decoded
                server_part = ""

        if ":" in server_part:
            server, port_num = server_part.rsplit(":", 1)
            port_num = int(port_num)
        else:
            server = server_part
            port_num = 443

        try:
            decoded_userinfo = base64.b64decode(userinfo + '=' * (-len(userinfo) % 4)).decode('utf-8')
        except:
            decoded_userinfo = base64.b64decode(encoded_part + '=' * (-len(encoded_part) % 4)).decode('utf-8')
            if "@" in decoded_userinfo:
                userinfo_part, server_part = decoded_userinfo.split("@", 1)
                if ":" in server_part:
                    server, port_num = server_part.rsplit(":", 1)
                    port_num = int(port_num)
                decoded_userinfo = userinfo_part

        if ":" not in decoded_userinfo:
            raise ValueError("Invalid Shadowsocks URI")
        
        method, password = decoded_userinfo.split(":", 1)

        config = {
            "inbounds": [{
                "port": port,
                "listen": "127.0.0.1",
                "protocol": "socks",
                "settings": {"udp": True}
            }],
            "outbounds": [
                {
                    "protocol": "shadowsocks",
                    "settings": {
                        "servers": [{
                            "address": server,
                            "port": port_num,
                            "method": method,
                            "password": password
                        }]
                    },
                    "tag": "proxy"
                },
                {
                    "protocol": "freedom",
                    "tag": "direct"
                }
            ],
            "routing": {
                "domainStrategy": "IPOnDemand",
                "rules": [{
                    "type": "field",
                    "ip": ["geoip:private"],
                    "outboundTag": "direct"
                }]
            }
        }
        
        return config

    def parse_trojan(self, uri, port):
        if not uri.startswith("trojan://"):
            raise ValueError("Invalid Trojan URI")
        
        parsed = urllib.parse.urlparse(uri)
        password = parsed.username
        server = parsed.hostname
        port_num = parsed.port
        query = parse_qs(parsed.query)
        remark = urllib.parse.unquote(parsed.fragment) if parsed.fragment else "Imported Trojan"
        
        config = {
            "inbounds": [{
                "port": port,
                "listen": "127.0.0.1",
                "protocol": "socks",
                "settings": {"udp": True}
            }],
            "outbounds": [
                {
                    "protocol": "trojan",
                    "settings": {
                        "servers": [{
                            "address": server,
                            "port": port_num,
                            "password": password
                        }]
                    },
                    "streamSettings": {
                        "network": query.get("type", ["tcp"])[0],
                        "security": "tls",
                        "tcpSettings": {
                            "header": {
                                "type": query.get("headerType", ["none"])[0],
                                "request": {
                                    "headers": {
                                        "Host": [query.get("host", [""])[0]]
                                    }
                                }
                            }
                        }
                    },
                    "tag": "proxy"
                },
                {
                    "protocol": "freedom",
                    "tag": "direct"
                }
            ],
            "routing": {
                "domainStrategy": "IPOnDemand",
                "rules": [{
                    "type": "field",
                    "ip": ["geoip:private"],
                    "outboundTag": "direct"
                }]
            }
        }
        
        return config

    def parse_protocol(self, uri, port):
        try:
            if uri.startswith("vmess://"):
                return self.vmess_to_json(uri, port)
            elif uri.startswith("vless://"):
                return self.parse_vless(uri, port)
            elif uri.startswith("ss://"):
                return self.parse_shadowsocks(uri, port)
            elif uri.startswith("trojan://"):
                return self.parse_trojan(uri, port)
        except Exception:
            return None # Return None on any parsing error
        return None # Return None for unsupported protocols
    # --- End of Parsers ---

    def measure_latency(self, config_uri):
        if self.stop_event.is_set():
            return config_uri, float('inf')

        latency = float('inf')
        xray_process = None
        temp_config_file = None
        
        try:
            socks_port = self.get_available_port()
            config = self.parse_protocol(config_uri, socks_port)
            
            if not config:
                return config_uri, float('inf')

            rand_suffix = random.randint(1000, 9999)
            temp_config_file = os.path.join(TEMP_FOLDER, f"temp_config_{rand_suffix}.json")

            with open(temp_config_file, "w", encoding='utf-8') as f:
                json.dump(config, f)

            xray_process = subprocess.Popen(
                [XRAY_PATH, "run", "-config", temp_config_file],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            
            time.sleep(1) # Give Xray time to start

            proxies = {'http': f'socks5://127.0.0.1:{socks_port}', 'https': f'socks5://127.0.0.1:{socks_port}'}
            headers = {'Cache-Control': 'no-cache', 'Connection': 'close'}

            try:
                start_time = time.perf_counter()
                response = requests.get(PING_TEST_URL, proxies=proxies, timeout=TEST_TIMEOUT, headers=headers)
                if response.status_code == 200:
                    latency = (time.perf_counter() - start_time) * 1000
            except requests.RequestException:
                pass # Latency remains 'inf'
        
        except Exception:
            pass # Latency remains 'inf'
        
        finally:
            if xray_process:
                try:
                    xray_process.terminate()
                    xray_process.wait(timeout=2)
                except (subprocess.TimeoutExpired, ProcessLookupError):
                    xray_process.kill()

            if temp_config_file and os.path.exists(temp_config_file):
                try:
                    os.remove(temp_config_file)
                except OSError:
                    pass
            
            time.sleep(0.1)
            return config_uri, latency

# --- CLI Interface ---

def display_menu():
    print(f"\n{Colors.CYAN}--- Freenet Termux Menu ---{Colors.RESET}")
    print(f"{Colors.YELLOW}1.{Colors.WHITE} Fetch & Test New Configs")
    print(f"{Colors.YELLOW}2.{Colors.WHITE} View Top 10 Saved Configs")
    print(f"{Colors.YELLOW}3.{Colors.WHITE} Exit")
    choice = input(f"{Colors.CYAN}Please select an option (1-3): {Colors.RESET}")
    return choice

def get_user_choices():
    # 1. Select Mirror
    print(f"\n{Colors.CYAN}--- Select a Mirror ---{Colors.RESET}")
    mirror_keys = list(MIRRORS.keys())
    for i, name in enumerate(mirror_keys, 1):
        print(f"{Colors.YELLOW}{i}.{Colors.WHITE} {name}")
    
    mirror_choice = 0
    while mirror_choice not in range(1, len(MIRRORS) + 1):
        try:
            choice_str = input(f"{Colors.CYAN}Select a mirror (1-{len(MIRRORS)}): {Colors.RESET}")
            if choice_str:
                choice = int(choice_str)
                if 1 <= choice <= len(MIRRORS):
                    mirror_choice = choice
            else:
                print(f"{Colors.RED}Please enter a number.{Colors.RESET}")
        except ValueError:
            print(f"{Colors.RED}Please enter a valid number.{Colors.RESET}")
    
    selected_mirror_url = MIRRORS[mirror_keys[mirror_choice - 1]]

    # 2. Select Protocol
    print(f"\n{Colors.CYAN}--- Filter by Protocol Type ---{Colors.RESET}")
    protocols = ["All", "vmess", "vless", "trojan", "ss"]
    for i, proto in enumerate(protocols, 1):
        print(f"{Colors.YELLOW}{i}.{Colors.WHITE} {proto}")
    
    protocol_choice = 0
    while protocol_choice not in range(1, len(protocols) + 1):
        try:
            choice_str = input(f"{Colors.CYAN}Select protocol type (1-{len(protocols)}, default is All): {Colors.RESET}")
            if not choice_str:
                protocol_choice = 1 # Default to All
                break
            choice = int(choice_str)
            if 1 <= choice <= len(protocols):
                protocol_choice = choice
        except ValueError:
            print(f"{Colors.RED}Please enter a valid number.{Colors.RESET}")

    selected_protocol = protocols[protocol_choice - 1]

    # 3. Number of threads
    print(f"\n{Colors.CYAN}--- Select Number of Threads ---{Colors.RESET}")
    thread_options = [10, 20, 50, 100]
    for i, count in enumerate(thread_options, 1):
        print(f"{Colors.YELLOW}{i}.{Colors.WHITE} {count} Threads")
    
    thread_count_choice = 0
    while thread_count_choice not in range(1, len(thread_options) + 1):
        try:
            choice_str = input(f"{Colors.CYAN}Select thread count (1-{len(thread_options)}), default is 100: {Colors.RESET}")
            if not choice_str:
                thread_count_choice = 4 # Default to 100
                break
            choice = int(choice_str)
            if 1 <= choice <= len(thread_options):
                thread_count_choice = choice
        except ValueError:
            print(f"{Colors.RED}Please enter a valid number.{Colors.RESET}")
            
    selected_threads = thread_options[thread_count_choice - 1]

    # 4. Number of configs to test
    print(f"\n{Colors.CYAN}--- Number of Configs to Test ---{Colors.RESET}")
    num_to_test = 0
    while num_to_test <= 0:
        try:
            num_str = input(f"{Colors.CYAN}How many configs should be tested? (e.g., 50): {Colors.RESET}")
            if num_str:
                num = int(num_str)
                if num > 0:
                    num_to_test = num
            else:
                print(f"{Colors.RED}Please enter a number.{Colors.RESET}")
        except ValueError:
            print(f"{Colors.RED}Please enter a valid number.{Colors.RESET}")

    return selected_mirror_url, selected_protocol, num_to_test, selected_threads

def run_test_flow():
    clear_temp_folder()
    kill_xray_processes()
    
    mirror_url, protocol, num_to_test, threads = get_user_choices()
    
    tester = ConfigTester()
    configs = tester.fetch_configs(mirror_url)
    
    if not configs:
        return

    if protocol != "All":
        configs = [c for c in configs if c.startswith(f"{protocol}://")]
        log(f"Filtered for {protocol}. Remaining configs: {len(configs)}", Colors.YELLOW)
    
    if not configs:
        log("No configs found with the specified filter.", Colors.RED)
        return
        
    random.shuffle(configs)
    configs_to_test = configs[:num_to_test]
    log(f"Starting test on {len(configs_to_test)} configs with {threads} threads...", Colors.CYAN)
    
    working_configs = []
    
    with tqdm(total=len(configs_to_test), desc="Testing Latency", bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt}") as pbar:
        with concurrent.futures.ThreadPoolExecutor(max_workers=threads) as executor:
            future_to_config = {executor.submit(tester.measure_latency, config): config for config in configs_to_test}
            
            for future in concurrent.futures.as_completed(future_to_config):
                try:
                    uri, latency = future.result()
                    pbar.update(1)
                    if latency != float('inf'):
                        working_configs.append((uri, latency))
                        pbar.write(f"{Colors.GREEN}OK >>{Colors.RESET} Latency: {latency:.2f}ms - {uri[:30]}...")
                except Exception as e:
                    pbar.write(f"{Colors.RED}ERROR >>{Colors.RESET} Tester error: {e}")

    kill_xray_processes()

    if not working_configs:
        log("Sorry, no working configs were found.", Colors.RED)
        send_notification("Freenet Test Finished", "No working configs found.")
        return
        
    working_configs.sort(key=lambda x: x[1])
    
    best_10 = working_configs[:10]
    log(f"Test complete! Found {len(working_configs)} working configs.", Colors.GREEN)
    log("Top 10 configs:", Colors.YELLOW)
    
    with open(BEST_CONFIGS_FILE, 'w', encoding='utf-8') as f:
        for i, (uri, latency) in enumerate(best_10, 1):
            line = f"({i}) Latency: {latency:<7.2f}ms | {uri}"
            print(f"{Colors.YELLOW}{line}{Colors.RESET}")
            f.write(uri + '\n')
            
    log(f"Top 10 configs saved to {BEST_CONFIGS_FILE}", Colors.GREEN)
    send_notification("Freenet Test Finished", f"{len(working_configs)} working configs found. Best ones saved.")

def view_best_configs():
    print(f"\n{Colors.CYAN}--- Displaying Saved Best Configs ---{Colors.RESET}")
    if not os.path.exists(BEST_CONFIGS_FILE):
        print(f"{Colors.RED}No configs saved yet. Please run option 1 first.{Colors.RESET}")
        return
        
    with open(BEST_CONFIGS_FILE, 'r', encoding='utf-8') as f:
        configs = f.readlines()
        if not configs:
            print(f"{Colors.YELLOW}The best configs file is empty.{Colors.RESET}")
            return
        
        print(f"{Colors.GREEN}Configs from the last test:{Colors.RESET}")
        for i, config in enumerate(configs, 1):
            print(f"{Colors.WHITE}{i}. {config.strip()}{Colors.RESET}")

# --- Main Execution ---
def main():
    if not os.path.exists(XRAY_PATH):
        print(f"{Colors.RED}Error: Xray executable not found at {XRAY_PATH}{Colors.RESET}")
        print(f"{Colors.YELLOW}Please run the installer or place 'xray' in the script directory.{Colors.RESET}")
        sys.exit(1)
    
    # Check for execute permissions and set them if not present
    if not os.access(XRAY_PATH, os.X_OK):
        print(f"{Colors.YELLOW}Xray executable not found or not executable. Attempting to set permissions...{Colors.RESET}")
        try:
            os.chmod(XRAY_PATH, 0o755)
            log("Set execute permission for Xray.", Colors.CYAN)
        except Exception as e:
            print(f"{Colors.RED}Failed to set execute permission: {e}{Colors.RESET}")
            sys.exit(1)

    setup_environment()
    
    while True:
        choice = display_menu()
        if choice == '1':
            run_test_flow()
        elif choice == '2':
            view_best_configs()
        elif choice == '3':
            print(f"{Colors.CYAN}Exiting. Goodbye!{Colors.RESET}")
            break
        else:
            print(f"{Colors.RED}Invalid option. Please try again.{Colors.RESET}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Colors.RED}Program interrupted by user.{Colors.RESET}")
        kill_xray_processes()
        clear_temp_folder()
        sys.exit(0)
