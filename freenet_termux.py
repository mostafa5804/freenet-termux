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

# --- Configuration ---
# مسیرهای اصلی برنامه
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.expanduser('~/storage/shared/Download/freenet')
XRAY_PATH = os.path.join(BASE_DIR, "xray")
TEMP_FOLDER = os.path.join(BASE_DIR, "temp")

# فایل‌های خروجی
BEST_CONFIGS_FILE = os.path.join(OUTPUT_DIR, "best_configs.txt")
LOG_FILE = os.path.join(OUTPUT_DIR, "log.txt")

# تنظیمات تست
PING_TEST_URL = "http://cp.cloudflare.com/"
TEST_TIMEOUT = 10
DEFAULT_LATENCY_WORKERS = 50

# مخازن کانفیگ (Mirrors)
MIRRORS = {
    "barry-far": "https://raw.githubusercontent.com/barry-far/V2ray-Config/main/All_Configs_Sub.txt",
    "SoliSpirit": "https://raw.githubusercontent.com/SoliSpirit/v2ray-configs/main/all_configs.txt",
    "mrvcoder": "https://raw.githubusercontent.com/mrvcoder/V2rayCollector/main/mixed_iran.txt",
    "MatinGhanbari": "https://raw.githubusercontent.com/MatinGhanbari/v2ray-configs/main/subscriptions/v2ray/all_sub.txt",
}

# --- Helper Functions ---

def log(message, color=Colors.WHITE):
    """Logs a message to the console and a file."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    console_message = f"{color}[{timestamp}] {message}{Colors.RESET}"
    file_message = f"[{timestamp}] {message}\n"
    
    print(console_message)
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(file_message)

def setup_environment():
    """Creates necessary directories and files."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(TEMP_FOLDER, exist_ok=True)
    # Create log file if it doesn't exist
    if not os.path.exists(LOG_FILE):
        open(LOG_FILE, 'w').close()
    log("محیط برنامه آماده شد.", Colors.CYAN)
    log(f"فایل‌های خروجی در این مسیر ذخیره می‌شوند: {OUTPUT_DIR}", Colors.CYAN)

def clear_temp_folder():
    """Clears all temporary config files."""
    try:
        for filename in os.listdir(TEMP_FOLDER):
            file_path = os.path.join(TEMP_FOLDER, filename)
            if os.path.isfile(file_path):
                os.unlink(file_path)
    except Exception as e:
        log(f"خطا در پاک‌سازی پوشه temp: {e}", Colors.RED)

def kill_xray_processes():
    """Kill any existing Xray processes on Linux/Android."""
    try:
        # pkill is effective and available in Termux
        subprocess.run(['pkill', '-f', 'xray'], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        log("فرآیندهای قبلی Xray متوقف شدند.", Colors.YELLOW)
    except Exception as e:
        log(f"خطا در توقف فرآیندهای Xray: {e}", Colors.RED)

def send_notification(title, message):
    """Sends a notification in Termux."""
    try:
        subprocess.run(['termux-notification', '--title', title, '--content', message], check=False)
    except FileNotFoundError:
        log("بسته termux-api نصب نیست. امکان ارسال نوتیفیکیشن وجود ندارد.", Colors.YELLOW)
    except Exception as e:
        log(f"خطا در ارسال نوتیفیکیشن: {e}", Colors.RED)

# --- Core Logic (Adapted from the original script) ---

class ConfigTester:
    def __init__(self):
        self.stop_event = threading.Event()

    def fetch_configs(self, url):
        """Fetches configs from a given URL."""
        try:
            log(f"در حال دریافت کانفیگ‌ها از: {url}", Colors.CYAN)
            response = requests.get(url, timeout=15)
            response.raise_for_status()
            response.encoding = 'utf-8'
            configs = [line.strip() for line in response.text.splitlines() if line.strip()]
            log(f"تعداد {len(configs)} کانفیگ با موفقیت دریافت شد.", Colors.GREEN)
            return configs
        except requests.RequestException as e:
            log(f"خطا در دریافت کانفیگ‌ها: {e}", Colors.RED)
            return []

    def measure_latency(self, config_uri, pbar):
        """Measures the latency of a single config."""
        # A random port for each thread to avoid conflicts
        socks_port = random.randint(10800, 11800)
        
        try:
            config_json = self.parse_protocol(config_uri, socks_port)
            if not config_json:
                return config_uri, float('inf')

            rand_suffix = random.randint(1000, 9999)
            temp_config_file = os.path.join(TEMP_FOLDER, f"temp_config_{rand_suffix}.json")

            with open(temp_config_file, "w", encoding='utf-8') as f:
                json.dump(config_json, f)

            xray_process = subprocess.Popen(
                [XRAY_PATH, "run", "-config", temp_config_file],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            time.sleep(1.5) # Give Xray time to start

            proxies = {'http': f'socks5://127.0.0.1:{socks_port}', 'https': f'socks5://127.0.0.1:{socks_port}'}
            latency = float('inf')

            try:
                start_time = time.perf_counter()
                response = requests.get(PING_TEST_URL, proxies=proxies, timeout=TEST_TIMEOUT)
                if response.status_code == 200:
                    latency = (time.perf_counter() - start_time) * 1000
            except requests.RequestException:
                pass # Latency remains inf
            finally:
                xray_process.terminate()
                xray_process.wait(timeout=2)
                os.remove(temp_config_file)
        
        except Exception:
            latency = float('inf')
        
        finally:
            pbar.update(1) # Update progress bar
            return config_uri, latency

    # --- Protocol Parsers (simplified and combined) ---
    def parse_protocol(self, uri, port):
        try:
            if uri.startswith("vmess://"):
                return self.vmess_to_json(uri, port)
            elif uri.startswith("vless://"):
                return self.vless_to_json(uri, port)
            # Add other parsers (trojan, ss) here if needed and adapt them similarly
        except Exception:
            return None
        return None

    def vmess_to_json(self, vmess_url, port):
        base64_str = vmess_url[8:]
        padded = base64_str + '=' * (4 - len(base64_str) % 4)
        decoded = json.loads(base64.urlsafe_b64decode(padded).decode('utf-8'))
        
        return {
            "inbounds": [{"port": port, "listen": "127.0.0.1", "protocol": "socks", "settings": {"udp": True}}],
            "outbounds": [{
                "protocol": "vmess",
                "settings": {"vnext": [{"address": decoded["add"], "port": int(decoded["port"]), "users": [{"id": decoded["id"], "alterId": int(decoded.get("aid", 0)), "security": decoded.get("scy", "auto")}]}]},
                "streamSettings": {"network": decoded.get("net", "tcp"), "security": decoded.get("tls", ""), "wsSettings": {"path": decoded.get("path", "/"), "headers": {"Host": decoded.get("host", "")}} if decoded.get("net") == "ws" else {}}
            }]
        }

    def vless_to_json(self, vless_url, port):
        parsed = urlparse(vless_url)
        params = parse_qs(parsed.query)
        
        return {
            "inbounds": [{"port": port, "listen": "127.0.0.1", "protocol": "socks", "settings": {"udp": True}}],
            "outbounds": [{
                "protocol": "vless",
                "settings": {"vnext": [{"address": parsed.hostname, "port": parsed.port, "users": [{"id": parsed.username, "encryption": params.get("encryption", ["none"])[0]}]}]},
                "streamSettings": {"network": params.get("type", ["tcp"])[0], "security": params.get("security", ["none"])[0], "wsSettings": {"path": params.get("path", ["/"])[0], "headers": {"Host": params.get("host", [""])[0]}} if params.get("type", ["tcp"])[0] == "ws" else {}}
            }]
        }


# --- CLI Interface ---

def display_menu():
    """Displays the main menu."""
    print(f"\n{Colors.CYAN}--- منوی اصلی Freenet Termux ---{Colors.RESET}")
    print(f"{Colors.YELLOW}1.{Colors.WHITE} دریافت و تست کانفیگ‌های جدید")
    print(f"{Colors.YELLOW}2.{Colors.WHITE} نمایش ۱۰ کانفیگ برتر ذخیره شده")
    print(f"{Colors.YELLOW}3.{Colors.WHITE} خروج")
    choice = input(f"{Colors.CYAN}لطفا گزینه مورد نظر را انتخاب کنید (1-3): {Colors.RESET}")
    return choice

def get_user_choices():
    """Gets test parameters from the user."""
    # 1. Select Mirror
    print(f"\n{Colors.CYAN}--- انتخاب Mirror ---{Colors.RESET}")
    for i, name in enumerate(MIRRORS.keys(), 1):
        print(f"{Colors.YELLOW}{i}.{Colors.WHITE} {name}")
    
    mirror_choice = -1
    while mirror_choice not in range(1, len(MIRRORS) + 1):
        try:
            choice = int(input(f"{Colors.CYAN}لطفا Mirror را انتخاب کنید (1-{len(MIRRORS)}): {Colors.RESET}"))
            if 1 <= choice <= len(MIRRORS):
                mirror_choice = choice
            else:
                print(f"{Colors.RED}انتخاب نامعتبر است.{Colors.RESET}")
        except ValueError:
            print(f"{Colors.RED}لطفا یک عدد وارد کنید.{Colors.RESET}")
    
    selected_mirror_url = list(MIRRORS.values())[mirror_choice - 1]

    # 2. Select Protocol
    print(f"\n{Colors.CYAN}--- فیلتر نوع پروتکل ---{Colors.RESET}")
    protocols = ["All", "vmess", "vless", "trojan", "ss"]
    for i, proto in enumerate(protocols, 1):
        print(f"{Colors.YELLOW}{i}.{Colors.WHITE} {proto}")
    
    protocol_choice = -1
    while protocol_choice not in range(1, len(protocols) + 1):
        try:
            choice = int(input(f"{Colors.CYAN}نوع پروتکل را انتخاب کنید (1-{len(protocols)}): {Colors.RESET}"))
            if 1 <= choice <= len(protocols):
                protocol_choice = choice
            else:
                print(f"{Colors.RED}انتخاب نامعتبر است.{Colors.RESET}")
        except ValueError:
            print(f"{Colors.RED}لطفا یک عدد وارد کنید.{Colors.RESET}")

    selected_protocol = protocols[protocol_choice - 1]

    # 3. Number of configs to test
    print(f"\n{Colors.CYAN}--- تعداد کانفیگ برای تست ---{Colors.RESET}")
    num_to_test = 0
    while num_to_test <= 0:
        try:
            num = int(input(f"{Colors.CYAN}چه تعداد از کانفیگ‌های جدید تست شوند؟ (مثال: 50): {Colors.RESET}"))
            if num > 0:
                num_to_test = num
            else:
                print(f"{Colors.RED}تعداد باید بزرگتر از صفر باشد.{Colors.RESET}")
        except ValueError:
            print(f"{Colors.RED}لطفا یک عدد وارد کنید.{Colors.RESET}")

    return selected_mirror_url, selected_protocol, num_to_test

def run_test_flow():
    """The main workflow for fetching and testing configs."""
    clear_temp_folder()
    kill_xray_processes()
    
    mirror_url, protocol, num_to_test = get_user_choices()
    
    tester = ConfigTester()
    configs = tester.fetch_configs(mirror_url)
    
    if not configs:
        return

    # Filter by protocol
    if protocol != "All":
        configs = [c for c in configs if c.startswith(f"{protocol}://")]
        log(f"کانفیگ‌ها به پروتکل {protocol} فیلتر شدند. تعداد باقی‌مانده: {len(configs)}", Colors.YELLOW)
    
    if not configs:
        log("هیچ کانفیگی با فیلتر مشخص شده یافت نشد.", Colors.RED)
        return
        
    # Limit number of configs and shuffle them
    random.shuffle(configs)
    configs_to_test = configs[:num_to_test]
    log(f"تست روی {len(configs_to_test)} کانفیگ آغاز می‌شود...", Colors.CYAN)
    
    working_configs = []
    
    with tqdm(total=len(configs_to_test), desc="Testing Latency", bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt}") as pbar:
        with concurrent.futures.ThreadPoolExecutor(max_workers=DEFAULT_LATENCY_WORKERS) as executor:
            future_to_config = {executor.submit(tester.measure_latency, config, pbar): config for config in configs_to_test}
            
            for future in concurrent.futures.as_completed(future_to_config):
                try:
                    uri, latency = future.result()
                    if latency != float('inf'):
                        working_configs.append((uri, latency))
                        pbar.write(f"{Colors.GREEN}OK >>{Colors.RESET} Latency: {latency:.2f}ms - {uri[:30]}...")
                except Exception as e:
                    pbar.write(f"{Colors.RED}ERROR >>{Colors.RESET} خطای تستر: {e}")

    kill_xray_processes()

    if not working_configs:
        log("متاسفانه هیچ کانفیگ سالمی یافت نشد.", Colors.RED)
        send_notification("Freenet تست تمام شد", "هیچ کانفیگ سالمی یافت نشد.")
        return
        
    # Sort by latency
    working_configs.sort(key=lambda x: x[1])
    
    # Save the top 10 best configs
    best_10 = working_configs[:10]
    log(f"تست کامل شد! {len(working_configs)} کانفیگ سالم یافت شد.", Colors.GREEN)
    log("۱۰ کانفیگ برتر:", Colors.YELLOW)
    
    with open(BEST_CONFIGS_FILE, 'w', encoding='utf-8') as f:
        for i, (uri, latency) in enumerate(best_10, 1):
            line = f"({i}) Latency: {latency:<7.2f}ms | {uri}"
            print(f"{Colors.YELLOW}{line}{Colors.RESET}")
            f.write(uri + '\n')
            
    log(f"۱۰ کانفیگ برتر در فایل {BEST_CONFIGS_FILE} ذخیره شد.", Colors.GREEN)
    send_notification("Freenet تست تمام شد", f"{len(working_configs)} کانفیگ سالم یافت شد. بهترین‌ها ذخیره شدند.")

def view_best_configs():
    """Displays the last saved best configs."""
    print(f"\n{Colors.CYAN}--- نمایش بهترین کانفیگ‌های ذخیره شده ---{Colors.RESET}")
    if not os.path.exists(BEST_CONFIGS_FILE):
        print(f"{Colors.RED}هنوز هیچ کانفیگی ذخیره نشده است. لطفا ابتدا گزینه ۱ را اجرا کنید.{Colors.RESET}")
        return
        
    with open(BEST_CONFIGS_FILE, 'r', encoding='utf-8') as f:
        configs = f.readlines()
        if not configs:
            print(f"{Colors.YELLOW}فایل کانفیگ‌های برتر خالی است.{Colors.RESET}")
            return
        
        print(f"{Colors.GREEN}کانفیگ‌های زیر از آخرین تست ذخیره شده‌اند:{Colors.RESET}")
        for i, config in enumerate(configs, 1):
            print(f"{Colors.WHITE}{i}. {config.strip()}{Colors.RESET}")

# --- Main Execution ---
def main():
    """Main function to run the CLI application."""
    # Check for Xray executable
    if not os.path.exists(XRAY_PATH):
        print(f"{Colors.RED}خطا: فایل اجرایی xray در مسیر {XRAY_PATH} یافت نشد.{Colors.RESET}")
        print(f"{Colors.YELLOW}لطفا اسکریپت install.sh را اجرا کنید تا وابستگی‌ها نصب شوند.{Colors.RESET}")
        sys.exit(1)

    setup_environment()
    
    while True:
        choice = display_menu()
        if choice == '1':
            run_test_flow()
        elif choice == '2':
            view_best_configs()
        elif choice == '3':
            print(f"{Colors.CYAN}خداحافظ!{Colors.RESET}")
            break
        else:
            print(f"{Colors.RED}انتخاب نامعتبر است. لطفا دوباره تلاش کنید.{Colors.RESET}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Colors.RED}برنامه توسط کاربر متوقف شد.{Colors.RESET}")
        kill_xray_processes()
        clear_temp_folder()
        sys.exit(0)
