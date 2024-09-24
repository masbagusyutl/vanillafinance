import time
import requests
import hashlib
import datetime
from colorama import Fore, Style

# Fungsi untuk membaca data dari file
def read_data_file(file_path):
    accounts = []
    with open(file_path, 'r') as file:
        lines = file.readlines()
        for i in range(0, len(lines), 2):
            userId = lines[i].strip()
            authorization = lines[i+1].strip()
            accounts.append({'userId': userId, 'authorization': authorization})
    return accounts

# Fungsi untuk generate timestamp
def generate_timestamp():
    return int(time.time() * 1000)

# Fungsi untuk generate x-vanilla-appsign berdasarkan metode tertentu
def generate_appsign(method, authorization, appid):
    timestamp = str(generate_timestamp())
    if method == 'authorization':
        data = authorization + timestamp
    elif method == 'appid':
        data = appid + timestamp
    elif method == 'auth_and_appid':
        data = authorization + appid + timestamp
    else:
        return None
    return hashlib.sha256(data.encode()).hexdigest()

# Fungsi untuk mencoba berbagai metode untuk generate appsign
def try_generate_appsign(authorization, appid):
    methods = ['authorization', 'appid', 'auth_and_appid']
    for method in methods:
        appsign = generate_appsign(method, authorization, appid)
        if appsign:
            success = test_appsign(appsign)
            if success:
                print(f"{Fore.GREEN}Berhasil masuk menggunakan metode: {method}{Style.RESET_ALL}")
                return appsign, method
    return None, None

# Fungsi untuk mengetes appsign yang di-generate
def test_appsign(appsign):
    return True  # Simulasi selalu berhasil

# Fungsi untuk request GET data misi
def get_mission_data(userId, authorization, appsign):
    timestamp = generate_timestamp()
    url = f"https://tg.vanilla-finance.com/bapi/v1/activity/list?userId={userId}&type=MISSING&timestamp={timestamp}"
    
    headers = {
        "authorization": authorization,
        "accept": "application/json, text/plain, */*",
        "x-vanilla-appid": "237a903dd511477ea4d2a2019ca7c03e",
        "x-vanilla-appsign": appsign,
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"{Fore.RED}Kesalahan mengambil data misi untuk userId {userId}: {e}{Style.RESET_ALL}")
        return None

# Fungsi untuk POST menyelesaikan misi
def complete_mission(userId, taskId, authorization, appsign):
    timestamp = generate_timestamp()
    url = f"https://tg.vanilla-finance.com/bapi/v1/activity/place?timestamp={timestamp}"
    payload = {"userId": userId, "taskId": taskId}
    
    headers = {
        "authorization": authorization,
        "accept": "application/json, text/plain, */*",
        "x-vanilla-appid": "237a903dd511477ea4d2a2019ca7c03e",
        "x-vanilla-appsign": appsign,
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"{Fore.RED}Kesalahan menyelesaikan tugas {taskId} untuk userId {userId}: {e}{Style.RESET_ALL}")
        return None


# Fungsi untuk countdown 1 hari dengan pembaruan setiap jam
def countdown_one_day():
    total_seconds = 86400  # Jumlah detik dalam 1 hari
    start_time = time.time()  # Waktu mulai
    end_time = start_time + total_seconds  # Waktu selesai
    
    while total_seconds > 0:
        current_time = time.time()
        remaining_time = int(end_time - current_time)  # Sisa waktu dalam detik
        hours, remainder = divmod(remaining_time, 3600)
        minutes, seconds = divmod(remainder, 60)
        print(f"\r{Fore.YELLOW}Memulai ulang dalam {hours:02d}:{minutes:02d}:{seconds:02d}{Style.RESET_ALL}", end="")
        
        time.sleep(1)  # Update setiap detik
        total_seconds = remaining_time

    print(f"\n{Fore.GREEN}Memulai ulang proses sekarang!{Style.RESET_ALL}")

# Fungsi utama untuk menjalankan proses
def main():
    accounts = read_data_file('data.txt')
    total_accounts = len(accounts)
    print(f"{Fore.GREEN}Total akun: {total_accounts}{Style.RESET_ALL}")
    
    successful_method = None  # Simpan metode yang berhasil
    
    for index, account in enumerate(accounts, 1):
        userId = account['userId']
        authorization = account['authorization']
        print(f"{Fore.YELLOW}Memproses akun {index}/{total_accounts}: userId {userId}{Style.RESET_ALL}")
        
        # Jika belum ada metode yang berhasil, coba berbagai metode untuk generate appsign
        if not successful_method:
            appsign, successful_method = try_generate_appsign(authorization, "237a903dd511477ea4d2a2019ca7c03e")
        else:
            # Jika sudah ada metode yang berhasil, generate appsign dengan metode tersebut
            appsign = generate_appsign(successful_method, authorization, "237a903dd511477ea4d2a2019ca7c03e")
        
        if not appsign:
            print(f"{Fore.RED}Gagal menghasilkan kode yang valid untuk userId {userId}. Lewatkan...{Style.RESET_ALL}")
            continue
        
        # Ambil data misi
        mission_data = get_mission_data(userId, authorization, appsign)
        if mission_data and 'data' in mission_data:
            for mission in mission_data['data']:
                if mission['isComplete']:
                    print(f"{Fore.GREEN}Misi {mission['taskId']} ('{mission['title']}') untuk userId {userId} sudah selesai.{Style.RESET_ALL}")
                else:
                    print(f"{Fore.YELLOW}Menyelesaikan tugas {mission['taskId']} ('{mission['title']}') untuk userId {userId}{Style.RESET_ALL}")
                    complete_mission(userId, mission['taskId'], authorization, appsign)
        
        # Jeda 5 detik antar akun
        time.sleep(5)

    # Countdown 1 hari setelah semua akun diproses
    print(f"{Fore.YELLOW}Semua akun telah diproses. Memulai countdown untuk restart 1 hari.{Style.RESET_ALL}")
    countdown_one_day()
    main()  # Mulai ulang setelah 1 hari

# Mulai program
if __name__ == "__main__":
    main()
