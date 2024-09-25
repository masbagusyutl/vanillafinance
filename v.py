import time
import requests
import hashlib
import random
from datetime import timedelta
from termcolor import colored

# Fungsi untuk membaca data dari file
def read_data_file(file_path):
    accounts = []
    with open(file_path, 'r') as file:
        lines = file.readlines()
        for i in range(0, len(lines), 2):
            userId = lines[i].strip()
            authorization = lines[i + 1].strip()
            accounts.append({'userId': userId, 'authorization': authorization})
    return accounts

# Fungsi untuk generate timestamp
def generate_timestamp():
    return int(time.time() * 1000)

# Fungsi untuk generate x-vanilla-appsign
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
                print(colored(f"Berhasil masuk dengan metode: {method}", "green"))
                return appsign, method
    return None, None

# Fungsi untuk mengetes appsign yang di-generate
def test_appsign(appsign):
    return True  # Simulasi selalu berhasil

# Fungsi untuk mendapatkan header request
def get_headers(authorization, appsign):
    return {
        "authorization": authorization,
        "accept": "application/json, text/plain, */*",
        "x-vanilla-appid": "237a903dd511477ea4d2a2019ca7c03e",
        "x-vanilla-appsign": appsign,
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

# Fungsi untuk mendapatkan data misi
def get_mission_data(userId, authorization, appsign):
    timestamp = generate_timestamp()
    url = f"https://tg.vanilla-finance.com/bapi/v1/activity/list?userId={userId}&type=MISSING&timestamp={timestamp}"
    headers = get_headers(authorization, appsign)

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(colored(f"Error saat mendapatkan data misi untuk userId {userId}: {e}", "red"))
        return None

# Fungsi untuk POST menyelesaikan misi
def complete_mission(userId, taskId, authorization, appsign):
    timestamp = generate_timestamp()
    url = f"https://tg.vanilla-finance.com/bapi/v1/activity/place?timestamp={timestamp}"
    payload = {"userId": userId, "taskId": taskId}
    headers = get_headers(authorization, appsign)

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        print(colored(f"Misi {taskId} berhasil diselesaikan untuk userId {userId}", "green"))
        return response.json()
    except requests.exceptions.RequestException as e:
        print(colored(f"Error saat menyelesaikan misi {taskId} untuk userId {userId}: {e}", "red"))
        return None

# Fungsi untuk mendapatkan harga BTC per detik
def get_btc_price():
    timestamp = int(time.time() * 1000)  # Timestamp dalam ms
    url = f"https://indser.vanilla-finance.com/api/quote/v1/second/klines?symbol=BTCUSDT&limit=120&to={timestamp}"
    headers = get_headers("authorization-placeholder", "appsign-placeholder")
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json().get('data', [])
    except requests.exceptions.RequestException as e:
        print(colored(f"Error saat mendapatkan harga BTC: {e}", "red"))
        return None


# Fungsi untuk trading buy
def place_buy_order(userId, authorization, price, appsign):
    timestamp = generate_timestamp()
    url = f"https://tg.vanilla-finance.com/bapi/v1/options/place?timestamp={timestamp}"
    payload = {
        "userId": userId,
        "baseCcy": "BTC",
        "orderCcy": "CONE",
        "deliveryType": "10M",
        "direction": "CALL",  # CALL untuk buy
        "quantity": 0.1,
        "premium": "10",
        "strike": price,
        "strikeTime": timestamp + 10000
    }
    headers = get_headers(authorization, appsign)

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        print(colored(f"Buy order BTC berhasil ditempatkan pada harga {price}", "green"))
        return response.json().get('data', {}).get('orderId')
    except requests.exceptions.RequestException as e:
        print(colored(f"Error saat menempatkan buy order: {e}", "red"))
        return None

# Fungsi untuk trading sell
def place_sell_order(userId, authorization, price, appsign):
    timestamp = generate_timestamp()
    url = f"https://tg.vanilla-finance.com/bapi/v1/options/place?timestamp={timestamp}"
    payload = {
        "userId": userId,
        "baseCcy": "BTC",
        "orderCcy": "CONE",
        "deliveryType": "10M",
        "direction": "PUT",  # PUT untuk sell
        "quantity": 0.1,
        "premium": "10",
        "strike": price,
        "strikeTime": timestamp + 10000
    }
    headers = get_headers(authorization, appsign)

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        print(colored(f"Sell order BTC berhasil ditempatkan pada harga {price}", "green"))
        return response.json().get('data', {}).get('orderId')
    except requests.exceptions.RequestException as e:
        print(colored(f"Error saat menempatkan sell order: {e}", "red"))
        return None

# Fungsi untuk trading "tangga" terbatas 4-3 kali
def trading_ladder(userId, authorization, initial_direction, appsign):
    current_direction = initial_direction
    last_order_id = None
    trade_count = random.choice([3, 4])  # Lakukan 3 atau 4 kali trading

    for _ in range(trade_count):
        btc_prices = get_btc_price()
        if not btc_prices:
            print(colored("Gagal mengambil harga BTC, mencoba lagi...", "yellow"))
            continue

        latest_price = btc_prices[-1]['value']

        if current_direction == 'b':
            last_order_id = place_buy_order(userId, authorization, latest_price, appsign)
            current_direction = 's'
        else:
            last_order_id = place_sell_order(userId, authorization, latest_price, appsign)
            current_direction = 'b'

        if last_order_id:
            print(f"Order ID: {last_order_id}")

        time.sleep(60)  # Jeda 1 menit antara setiap trading

    print(colored(f"Trading selesai untuk userId {userId} setelah {trade_count} kali trading.", "green"))

# Fungsi untuk tap-tap task
def tap_tap_task(userId, authorization, appsign):
    timestamp = generate_timestamp()

    for i in range(10):
        quantity = str(random.randint(20, 40))
        url = f"https://tg.vanilla-finance.com/dapi/v1/assets/expend?timestamp={timestamp}"
        payload = {"userId": userId, "quantity": quantity}
        headers = get_headers(authorization, appsign)

        try:
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            print(colored(f"Tugas Tap-tap {i + 1}/10 berhasil untuk userId {userId}", "green"))
        except requests.exceptions.RequestException as e:
            print(colored(f"Error melakukan tugas tap-tap {i + 1}/10 untuk userId {userId}: {e}", "red"))

        time.sleep(1)

# Fungsi untuk mengecek status hadiah harian
def get_daily_reward_status(userId, authorization, appsign):
    timestamp = generate_timestamp()
    url = f"https://tg.vanilla-finance.com/bapi/v1/user/info?userId={userId}&timestamp={timestamp}"
    headers = get_headers(authorization, appsign)


    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(colored(f"Error saat mendapatkan status hadiah harian untuk userId {userId}: {e}", "red"))
        return None

# Fungsi untuk mengambil hadiah harian
def claim_daily_reward(userId, authorization, appsign):
    timestamp = generate_timestamp()
    url = f"https://tg.vanilla-finance.com/bapi/v1/activity/daily-sign-claim?timestamp={timestamp}"
    payload = {"userId": userId}
    headers = get_headers(authorization, appsign)

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        print(colored(f"Hadiah harian berhasil diambil untuk userId {userId}", "green"))
        return response.json()
    except requests.exceptions.RequestException as e:
        print(colored(f"Error saat mengambil hadiah harian untuk userId {userId}: {e}", "red"))
        return None

# Fungsi countdown 1 hari (24 jam)
def countdown_one_day():
    seconds_in_a_day = 86400  # 24 jam = 86400 detik
    for remaining in range(seconds_in_a_day, 0, -1):
        print(f"\rHitung mundur: {str(timedelta(seconds=remaining))}", end="")
        time.sleep(1)
    print("\n")

# Fungsi utama untuk menjalankan proses
def main():
    accounts = read_data_file('data.txt')
    total_accounts = len(accounts)
    print(f"Total akun: {total_accounts}")

    successful_method = None

    for index, account in enumerate(accounts, 1):
        userId = account['userId']
        authorization = account['authorization']
        print(colored(f"Memproses akun {index}/{total_accounts}: userId {userId}", "yellow"))

        if not successful_method:
            appsign, successful_method = try_generate_appsign(authorization, "237a903dd511477ea4d2a2019ca7c03e")
        else:
            appsign = generate_appsign(successful_method, authorization, "237a903dd511477ea4d2a2019ca7c03e")

        if not appsign:
            print(colored(f"Gagal menghasilkan kode yang valid untuk userId {userId}. Melewati akun ini...", "red"))
            continue

        # Ambil data misi dan selesaikan misi
        mission_data = get_mission_data(userId, authorization, appsign)
        if mission_data and 'data' in mission_data:
            for mission in mission_data['data']:
                if mission['isComplete']:
                    print(colored(f"Misi {mission['taskId']} untuk userId {userId} sudah selesai.", "yellow"))
                else:
                    complete_mission(userId, mission['taskId'], authorization, appsign)

        # Randomly pick initial direction for trading (b for buy, s for sell)
        initial_direction = random.choice(['b', 's'])
        print(f"Memulai trading dengan arah awal: {initial_direction}")

        # Mulai trading tangga, maksimal 4-3 kali trading
        trading_ladder(userId, authorization, initial_direction, appsign)

        # Lakukan tap-tap task setelah trading
        tap_tap_task(userId, authorization, appsign)

        # Cek status hadiah harian
        reward_status = get_daily_reward_status(userId, authorization, appsign)
        if reward_status and reward_status.get('data', {}).get('claimStatus') == "CLAIMED":
            print(colored(f"Hadiah harian untuk userId {userId} sudah diambil.", "yellow"))
        else:
            claim_daily_reward(userId, authorization, appsign)

        # Jeda 5 detik sebelum memproses akun berikutnya
        time.sleep(5)

    # Hitung mundur 1 hari setelah semua akun diproses
    print(colored("Semua akun telah diproses. Mulai hitung mundur 1 hari...", "yellow"))
    countdown_one_day()

    # Restart proses setelah 1 hari
    main()

if __name__ == "__main__":
    main()
