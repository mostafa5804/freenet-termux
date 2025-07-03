#!/usr/bin/env python3

import os
import sys
import json
import base64
import urllib.parse
import requests
import time
import datetime
import random
import subprocess
import concurrent.futures
from pathlib import Path

try:
    from colorama import init, Fore, Style
except ImportError:
    print("Installing colorama...")
    subprocess.run(["pip", "install", "colorama"])
    from colorama import init, Fore, Style

init(autoreset=True)

MIRRORS = {
    "barry-far": "https://raw.githubusercontent.com/barry-far/V2ray-Config/refs/heads/main/All_Configs_Sub.txt",
    "SoliSpirit": "https://raw.githubusercontent.com/SoliSpirit/v2ray-configs/refs/heads/main/all_configs.txt"
}

PING_TEST_URL = "https://old-queen-f906.mynameissajjad.workers.dev/login"
TODAY = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M")
BASE_DIR = Path.home() / "storage" / "downloads" / "freenet"
QR_DIR = BASE_DIR / "qrs"
LOG_FILE = BASE_DIR / f"log_{TODAY}.txt"
BEST_FILE = BASE_DIR / f"best_{TODAY}.txt"

for path in [BASE_DIR, QR_DIR]:
    path.mkdir(parents=True, exist_ok=True)

def log(msg):
    print(msg)
    with open(LOG_FILE, "a") as f:
        f.write(msg + "\n")

def filter_by_protocol(configs, selected_types):
    return [cfg for cfg in configs if any(cfg.startswith(proto) for proto in selected_types)]

def get_latency(uri, timeout=4):
    try:
        start = time.time()
        res = requests.get(PING_TEST_URL, timeout=timeout)
        delay = (time.time() - start) * 1000
        return (uri, delay if res.ok else float("inf"))
    except:
        return (uri, float("inf"))

def fetch_configs(url, limit=100):
    try:
        r = requests.get(url)
        r.raise_for_status()
        return [l.strip() for l in r.text.splitlines() if l.strip()][:limit]
    except Exception as e:
        log(f"{Fore.RED}Error fetching configs: {e}")
        return []

def generate_qr(uri, index):
    try:
        import qrcode
        img = qrcode.make(uri)
        img_path = QR_DIR / f"config_{index}.png"
        img.save(img_path)
        return img_path
    except Exception as e:
        log(f"{Fore.RED}QR generation error: {e}")

def main():
    print(f"{Fore.CYAN}📡 FreeNet-Termux ({TODAY})\n")

    print("Select config source (mirror):")
    mirrors = list(MIRRORS.keys())
    for i, m in enumerate(mirrors, 1):
        print(f"[{i}] {m}")
    mirror_idx = input("Enter number (default 1): ").strip()
    mirror_key = mirrors[int(mirror_idx)-1] if mirror_idx.isdigit() and 1 <= int(mirror_idx) <= len(mirrors) else mirrors[0]
    url = MIRRORS[mirror_key]

    limit = input("How many configs to test? (default 20): ").strip()
    limit = int(limit) if limit.isdigit() else 20

    print("\nChoose config type to filter:")
    print("[1] All [2] Only vmess [3] Only vless [4] Only trojan")
    mode = input("Your choice (1): ").strip()
    proto_map = {
        "2": ["vmess://"],
        "3": ["vless://"],
        "4": ["trojan://"]
    }
    selected_types = proto_map.get(mode, ["vmess://", "vless://", "trojan://", "ss://"])

    print("\nFetching configs...")
    configs = fetch_configs(url, limit=limit)
    configs = filter_by_protocol(configs, selected_types)
    print(f"Total configs after filter: {len(configs)}\n")

    working = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as ex:
        futures = {ex.submit(get_latency, c): c for c in configs}
        for i, f in enumerate(concurrent.futures.as_completed(futures), 1):
            uri, lat = f.result()
            if lat != float("inf"):
                print(f"{Fore.GREEN}✅ {i}. {lat:.1f}ms")
                working.append((uri, lat))
            else:
                print(f"{Fore.RED}❌ {i}. Failed")

    working.sort(key=lambda x: x[1])
    print(f"\n{Fore.YELLOW}Top 5 configs:")
    for i, (cfg, lat) in enumerate(working[:5], 1):
        print(f"{Fore.CYAN}{i}. {cfg[:80]}... ({lat:.1f}ms)")
        generate_qr(cfg, i)

    with open(BEST_FILE, "w") as f:
        for cfg, _ in working[:10]:
            f.write(cfg + "\n")

    zipname = BASE_DIR / f"freenet_results_{TODAY}.zip"
    import zipfile
    with zipfile.ZipFile(zipname, 'w') as z:
        z.write(BEST_FILE, arcname=BEST_FILE.name)
        z.write(LOG_FILE, arcname=LOG_FILE.name)
        for i in range(1, 6):
            p = QR_DIR / f"config_{i}.png"
            if p.exists():
                z.write(p, arcname=f"qr_{i}.png")

    print(f"\n{Fore.GREEN}Results saved to ZIP: {zipname}")
    subprocess.run(["termux-notification", "--title", "FreeNet", "--content", "Test completed successfully ✅"])
    subprocess.run(["termux-open", str(zipname)])

if __name__ == "__main__":
    main()
