import requests
import json
import base64
import urllib.parse
import random
import time
import concurrent.futures
import os
import argparse

CONFIGS_URLS = {
    "barry-far": "https://raw.githubusercontent.com/barry-far/V2ray-Config/refs/heads/main/All_Configs_Sub.txt",
    "SoliSpirit": "https://raw.githubusercontent.com/SoliSpirit/v2ray-configs/refs/heads/main/all_configs.txt"
}

PING_TEST_URL = "https://old-queen-f906.mynameissajjad.workers.dev/login"
WORKING_FILE = "working_configs.txt"
BEST_FILE = "best_configs.txt"

def parse_vmess(uri):
    try:
        if not uri.startswith("vmess://"):
            return None
        data = base64.urlsafe_b64decode(uri[8:] + '==').decode('utf-8')
        return json.loads(data)
    except:
        return None

def parse_vless(uri):
    try:
        parsed = urllib.parse.urlparse(uri)
        return parsed.hostname, parsed.port
    except:
        return None

def measure_latency(config_uri, timeout=4):
    import socks
    import socket
    import requests

    port = random.randint(30000, 40000)
    try:
        proxies = {
            "http": f"socks5h://127.0.0.1:{port}",
            "https": f"socks5h://127.0.0.1:{port}"
        }
        start = time.time()
        r = requests.get(PING_TEST_URL, proxies=proxies, timeout=timeout)
        latency = (time.time() - start) * 1000
        return (config_uri, latency if r.status_code == 200 else float('inf'))
    except:
        return (config_uri, float('inf'))

def fetch_configs(url):
    try:
        r = requests.get(url)
        r.raise_for_status()
        lines = [line.strip() for line in r.text.splitlines() if line.strip()]
        return lines[::-1]  # آخرین کانفیگ‌ها جلوتر
    except Exception as e:
        print(f"خطا در دریافت کانفیگ‌ها: {e}")
        return []

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mirror", default="barry-far", choices=CONFIGS_URLS.keys())
    parser.add_argument("--count", type=int, default=20, help="تعداد کانفیگ برای تست")
    args = parser.parse_args()

    print("در حال دریافت کانفیگ‌ها...")
    configs = fetch_configs(CONFIGS_URLS[args.mirror])[:args.count]
    print(f"{len(configs)} کانفیگ دریافت شد. در حال تست...")

    working = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(measure_latency, c): c for c in configs}
        for future in concurrent.futures.as_completed(futures):
            uri, latency = future.result()
            if latency != float('inf'):
                print(f"✅ {latency:.1f} ms")
                working.append((uri, latency))
            else:
                print("❌ Fail")

    working.sort(key=lambda x: x[1])

    with open(WORKING_FILE, 'w') as f:
        for c, _ in working:
            f.write(c + '\n')

    with open(BEST_FILE, 'w') as f:
        for c, _ in working[:10]:
            f.write(c + '\n')

    print(f"✅ تست تمام شد. {len(working)} کانفیگ موفق یافت شد.")
    print(f"📁 ذخیره شد در '{WORKING_FILE}' و '{BEST_FILE}'")

if __name__ == "__main__":
    main()
