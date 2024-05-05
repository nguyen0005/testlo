import concurrent.futures
import requests
import os

os.system("color 0")
os.system("cls" if os.name == "nt" else "clear")

def kiem_tra_proxy(proxy, timeout):
    try:
        response = requests.get('http://103.195.236.167/a.html', proxies={'http': proxy, 'https': proxy}, timeout=timeout)
        if response.status_code == 200:
            return proxy
    except:
        pass
    return None

def loc_proxy_trung(proxies):
    proxies_uniques = set(proxies)
    return list(proxies_uniques)

def tai_danh_sach_proxy(ten_file):
    if not os.path.isfile(ten_file):
        print(f"  File '{ten_file}' không tồn tại. Vui lòng nhập lại.")
        return tai_danh_sach_proxy(input("  Nhập tên file chứa danh sách proxy: "))
    with open(ten_file) as f:
        return [line.strip() for line in f.readlines()]

def luu_danh_sach_proxy(proxies, ten_file):
    with open(ten_file, 'w') as f:
        f.write('\n'.join(proxies))

def luu_danh_sach_proxy_loc(proxies, ten_file):
    check_file = "" + ten_file
    with open(check_file, 'w') as f:
        f.write('\n'.join(proxies))

banner = """
---------------------
|   PROXY CHECKER   |
---------------------
"""

def main():
    print(banner)

    ten_file = input("\n  Enter name proxyFile : ")

    proxies = tai_danh_sach_proxy(ten_file)

    print("================================================")
    print("  1. Filter duplicate proxies")
    print("  2. Check the proxy works")

    choice = input("  Nhập lựa chọn: ")

    if choice == "1":
        proxies_uniques = loc_proxy_trung(proxies)
        luu_danh_sach_proxy(proxies_uniques, ten_file)
        print("================================================")
        print("\n  The proxy filtering results overlap")
        print(f'  Total number of proxies found: {len(proxies)}')
        print(f'  Total remaining proxies: {len(proxies_uniques)}')
        input()
    elif choice == "2":
        timeout = int(input("Enter timeout (number of seconds): "))
        print("\n Checking proxies. Please wait...")
        with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
            results = list(executor.map(lambda proxy: kiem_tra_proxy(proxy, timeout), proxies))

        proxies_loc = [proxy for proxy in results if proxy is not None]
        luu_danh_sach_proxy_loc(proxies_loc, ten_file)
        print("================================================")
        print("\n  Active proxy test results")
        print(f'  Total number of proxies found: {len(proxies)}')
        print(f'  Total number of active proxies: {len(proxies_loc)}')
        input()
    else:
        print("================================================")
        print("\n  Invalid selection. Program exited.")
        input()

if __name__ == "__main__":
    main()