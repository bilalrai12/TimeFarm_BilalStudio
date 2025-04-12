from datetime import datetime
import time
from colorama import Fore
import requests
import random
from fake_useragent import UserAgent
import asyncio
import json
import gzip
import brotli
import zlib
import chardet
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class timefarm:
    BASE_URL = "https://tg-bot-tap.laborx.io/api/v1/"
    HEADERS = {
        "accept": "*/*",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "en-GB,en;q=0.9,en-US;q=0.8",
        "content-type": "application/json",
        "origin": "https://timefarm.app",
        "priority": "u=1, i",
        "referer": "https://timefarm.app/",
        "sec-ch-ua": '"Microsoft Edge WebView2";v="135", "Chromium";v="135", "Not-A.Brand";v="8", "Microsoft Edge";v="135"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "cross-site",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36 Edg/135.0.0.0"
    }

    def __init__(self):
        self.query_list = self.load_query("query.txt")
        self.token = None
        self.config = self.load_config()
        self.session = self.sessions()
        self._original_requests = {
            "get": requests.get,
            "post": requests.post,
            "put": requests.put,
            "delete": requests.delete,
        }
        self.proxy_session = None

    def banner(self) -> None:
        """Displays the banner for the bot."""
        self.log("🎉 Time Farm Bot", Fore.CYAN)
        self.log("🚀 Created by BILAL STUDIO", Fore.CYAN)
        self.log("📢 Channel: https://t.me/BilalStudio3\n", Fore.CYAN)

    def log(self, message, color=Fore.RESET):
        safe_message = message.encode("utf-8", "backslashreplace").decode("utf-8")
        print(
            Fore.LIGHTBLACK_EX
            + datetime.now().strftime("[%Y:%m:%d ~ %H:%M:%S] |")
            + " "
            + color
            + safe_message
            + Fore.RESET
        )

    def sessions(self):
        session = requests.Session()
        retries = Retry(
            total=3, backoff_factor=1, status_forcelist=[500, 502, 503, 504, 520]
        )
        session.mount("https://", HTTPAdapter(max_retries=retries))
        return session

    def decode_response(self, response):
        """
        Mendekode response dari server secara umum.

        Parameter:
            response: objek requests.Response

        Mengembalikan:
            - Jika Content-Type mengandung 'application/json', maka mengembalikan objek Python (dict atau list) hasil parsing JSON.
            - Jika bukan JSON, maka mengembalikan string hasil decode.
        """
        # Ambil header
        content_encoding = response.headers.get("Content-Encoding", "").lower()
        content_type = response.headers.get("Content-Type", "").lower()

        # Tentukan charset dari Content-Type, default ke utf-8
        charset = "utf-8"
        if "charset=" in content_type:
            charset = content_type.split("charset=")[-1].split(";")[0].strip()

        # Ambil data mentah
        data = response.content

        # Dekompresi jika perlu
        try:
            if content_encoding == "gzip":
                data = gzip.decompress(data)
            elif content_encoding in ["br", "brotli"]:
                data = brotli.decompress(data)
            elif content_encoding in ["deflate", "zlib"]:
                data = zlib.decompress(data)
        except Exception:
            # Jika dekompresi gagal, lanjutkan dengan data asli
            pass

        # Coba decode menggunakan charset yang didapat
        try:
            text = data.decode(charset)
        except Exception:
            # Fallback: deteksi encoding dengan chardet
            detection = chardet.detect(data)
            detected_encoding = detection.get("encoding", "utf-8")
            text = data.decode(detected_encoding, errors="replace")

        # Jika konten berupa JSON, kembalikan hasil parsing JSON
        if "application/json" in content_type:
            try:
                return json.loads(text)
            except Exception:
                # Jika parsing JSON gagal, kembalikan string hasil decode
                return text
        else:
            return text

    def load_config(self) -> dict:
        """
        Loads configuration from config.json.

        Returns:
            dict: Configuration data or an empty dictionary if an error occurs.
        """
        try:
            with open("config.json", "r") as config_file:
                config = json.load(config_file)
                self.log("✅ Configuration loaded successfully.", Fore.GREEN)
                return config
        except FileNotFoundError:
            self.log("❌ File not found: config.json", Fore.RED)
            return {}
        except json.JSONDecodeError:
            self.log(
                "❌ Failed to parse config.json. Please check the file format.",
                Fore.RED,
            )
            return {}

    def load_query(self, path_file: str = "query.txt") -> list:
        """
        Loads a list of queries from the specified file.

        Args:
            path_file (str): The path to the query file. Defaults to "query.txt".

        Returns:
            list: A list of queries or an empty list if an error occurs.
        """
        self.banner()

        try:
            with open(path_file, "r") as file:
                queries = [line.strip() for line in file if line.strip()]

            if not queries:
                self.log(f"⚠️ Warning: {path_file} is empty.", Fore.YELLOW)

            self.log(f"✅ Loaded {len(queries)} queries from {path_file}.", Fore.GREEN)
            return queries

        except FileNotFoundError:
            self.log(f"❌ File not found: {path_file}", Fore.RED)
            return []
        except Exception as e:
            self.log(f"❌ Unexpected error loading queries: {e}", Fore.RED)
            return []

    def login(self, index: int) -> None:
        # Logging in progress
        self.log("🔐 Attempting to log in...", Fore.GREEN)
        
        # Check if the provided index is valid for the query list
        if index >= len(self.query_list):
            self.log("❌ Invalid login index. Please check again.", Fore.RED)
            return

        # Retrieve the token from the query list based on the index provided
        token = self.query_list[index]
        self.log(f"📋 Using token: {token[:10]}... (truncated for security)", Fore.CYAN)
        
        # API 1: Validate Initial Data via auth/validate-init/v2
        validate_url = f"{self.BASE_URL}auth/validate-init/v2"
        validate_payload = json.dumps({"initData": token, "platform": "tdesktop"})
        validate_headers = self.HEADERS

        try:
            self.log("📡 Sending validate-init request...", Fore.CYAN)
            validate_response = requests.post(validate_url, headers=validate_headers, data=validate_payload)
            validate_response.raise_for_status()
            validate_data = self.decode_response(validate_response)
        except requests.exceptions.RequestException as e:
            self.log(f"❌ Failed to send validate-init request: {e}", Fore.RED)
            try:
                self.log(f"📄 Response content: {validate_response.text}", Fore.RED)
            except Exception:
                pass
            return
        except Exception as e:
            self.log(f"❌ Unexpected error during validate-init: {e}", Fore.RED)
            try:
                self.log(f"📄 Response content: {validate_response.text}", Fore.RED)
            except Exception:
                pass
            return

        # Process validate-init response and store the access token
        try:
            self.token = validate_data.get("token", "")
            self.log("✅ Login successful! Processed validate-init response.", Fore.GREEN)
        except Exception as e:
            self.log(f"❌ Error processing validate-init response: {e}", Fore.RED)
            return

        # API 2: Get Farming Info via farming/info
        farming_info_url = f"{self.BASE_URL}farming/info"
        headers_with_auth = {**self.HEADERS, "authorization": f"Bearer {self.token}"}

        try:
            self.log("📡 Sending farming info request...", Fore.CYAN)
            farming_response = requests.get(farming_info_url, headers=headers_with_auth)
            farming_response.raise_for_status()
            farming_data = self.decode_response(farming_response)

            # Log farming info details
            self.log("💰 Farming Info:", Fore.GREEN)
            self.log(f"    - Balance: {farming_data.get('balance', 'N/A')}", Fore.CYAN)
            self.log(f"    - Farming Duration In Sec: {farming_data.get('farmingDurationInSec', 'N/A')}", Fore.CYAN)
            self.log(f"    - Farming Reward: {farming_data.get('farmingReward', 'N/A')}", Fore.CYAN)
            self.log(f"    - Multiplier: {farming_data.get('multiplier', 'N/A')}", Fore.CYAN)
        except requests.exceptions.RequestException as e:
            self.log(f"❌ Failed to fetch farming info: {e}", Fore.RED)
            try:
                self.log(f"📄 Response content: {farming_response.text}", Fore.RED)
            except Exception:
                pass
        except Exception as e:
            self.log(f"❌ Unexpected error in farming info request: {e}", Fore.RED)
            try:
                self.log(f"📄 Response content: {farming_response.text}", Fore.RED)
            except Exception:
                pass

    def task(self) -> None:
        import time
        import os

        # === READ PROCESSED TASKS FROM FILE ===
        processed_tasks = {}
        file_path = "task.json"
        if os.path.exists(file_path):
            try:
                with open(file_path, "r") as f:
                    processed_tasks = json.load(f)  # Format: { "taskid": code, ... }
                self.log("✅ Loaded processed tasks from task.json.", Fore.GREEN)
            except Exception as e:
                self.log(f"❌ Failed to read task.json: {e}", Fore.RED)
        else:
            self.log("ℹ️ task.json not found, proceeding without processed tasks.", Fore.YELLOW)

        headers = {**self.HEADERS, "authorization": f"Bearer {self.token}"}
        
        # === FETCH TASKS (FIRST TIME) ===
        tasks_url = f"{self.BASE_URL}tasks"
        try:
            self.log("📡 Requesting tasks list...", Fore.CYAN)
            tasks_response = requests.get(tasks_url, headers=headers)
            tasks_response.raise_for_status()
            tasks_data = self.decode_response(tasks_response)
        except requests.exceptions.RequestException as e:
            self.log(f"❌ Failed to fetch tasks: {e}", Fore.RED)
            return
        except Exception as e:
            self.log(f"❌ Unexpected error while fetching tasks: {e}", Fore.RED)
            return

        if not isinstance(tasks_data, list):
            self.log("❌ Invalid tasks response format.", Fore.RED)
            return

        # Filter tasks berdasarkan file task.json (skip task yang sudah pernah diproses)
        filtered_tasks = []
        for task in tasks_data:
            task_id = task.get("id")
            if task_id in processed_tasks:
                self.log(f"⚠️ Skipping task {task_id} as it is already processed.", Fore.YELLOW)
                continue
            filtered_tasks.append(task)

        if not filtered_tasks:
            self.log("ℹ️ No new tasks available to process.", Fore.YELLOW)
            return

        # === PHASE 1: Task Submissions (hanya untuk task yang belum pernah disubmit) ===
        submission_tasks = []  # Task yang belum ada properti submission (belum disubmit)
        
        for task in filtered_tasks:
            submission = task.get("submission")
            if submission is None:
                submission_tasks.append(task)
            else:
                status = submission.get("status")
                if status == "COMPLETED":
                    # Jika sudah complete, cukup nantinya akan diproses di Phase 2.
                    continue
                elif status in ["CLAIMED", "SUBMITTED"]:
                    self.log(f"⚠️ Skipping task {task.get('id')} as its submission status is '{status}'.", Fore.YELLOW)
        
        if submission_tasks:
            self.log("🚀 Starting Phase 1: Task Submissions...", Fore.GREEN)
            for task in submission_tasks:
                task_id = task.get("id")
                submission_url = f"{self.BASE_URL}tasks/submissions/v2"
                submission_payload = json.dumps({"taskId": task_id})
                
                try:
                    self.log(f"📡 Sending submission request for task {task_id}...", Fore.CYAN)
                    submission_response = requests.post(submission_url, headers=headers, data=submission_payload)
                    submission_response.raise_for_status()
                    submission_data = self.decode_response(submission_response)
                    
                    if submission_data.get("result", {}).get("status") == "COMPLETED":
                        self.log(f"✅ Task {task_id} submission successful.", Fore.GREEN)
                    else:
                        self.log(f"⚠️ Task {task_id} submission did not complete as expected.", Fore.YELLOW)
                except requests.exceptions.RequestException as e:
                    self.log(f"❌ Failed to submit task {task_id}: {e}", Fore.RED)
                except Exception as e:
                    self.log(f"❌ Unexpected error for task {task_id}: {e}", Fore.RED)
            
            self.log("⏳ Waiting 5 seconds before re-fetching tasks...", Fore.CYAN)
            time.sleep(5)
        else:
            self.log("ℹ️ No tasks need submission. Skipping Phase 1...", Fore.CYAN)
        
        # === REFRESH TASK LIST (SECOND FETCH) BEFORE PHASE 2 ===
        try:
            self.log("📡 Re-requesting tasks list for Phase 2...", Fore.CYAN)
            tasks_response = requests.get(tasks_url, headers=headers)
            tasks_response.raise_for_status()
            tasks_data = self.decode_response(tasks_response)
        except requests.exceptions.RequestException as e:
            self.log(f"❌ Failed to re-fetch tasks for Phase 2: {e}", Fore.RED)
            return
        except Exception as e:
            self.log(f"❌ Unexpected error while re-fetching tasks for Phase 2: {e}", Fore.RED)
            return

        if not isinstance(tasks_data, list):
            self.log("❌ Invalid tasks response format on re-fetch.", Fore.RED)
            return

        # Filter ulang dari tasks yang masih belum di-skip (dengan reference file task.json)
        claim_tasks = []
        for task in tasks_data:
            task_id = task.get("id")
            if task_id in processed_tasks:
                self.log(f"⚠️ Skipping task {task_id} as it is already processed.", Fore.YELLOW)
                continue
            
            submission = task.get("submission")
            if submission:
                status = submission.get("status")
                if status == "COMPLETED":
                    claim_tasks.append(task)
                elif status in ["CLAIMED", "SUBMITTED"]:
                    self.log(f"⚠️ Skipping task {task_id} as its submission status is '{status}'.", Fore.YELLOW)
            else:
                # Jika masih belum disubmit, maka task tersebut juga akan diproses untuk klaim
                claim_tasks.append(task)
        
        # === PHASE 2: Task Claims ===
        if claim_tasks:
            self.log("🚀 Starting Phase 2: Task Claims...", Fore.GREEN)
            for task in claim_tasks:
                task_id = task.get("id")
                claim_url = f"{self.BASE_URL}tasks/{task_id}/claims"
                
                try:
                    self.log(f"📡 Sending claim request for task {task_id}...", Fore.CYAN)
                    claim_response = requests.post(claim_url, headers=headers, data=json.dumps({}))
                    claim_response.raise_for_status()
                    
                    # Expecting response text "OK"
                    if claim_response.text.strip() == "OK":
                        self.log(f"✅ Task {task_id} claimed successfully.", Fore.GREEN)
                    else:
                        self.log(f"⚠️ Task {task_id} claim response not as expected: {claim_response.text}", Fore.YELLOW)
                except requests.exceptions.RequestException as e:
                    self.log(f"❌ Failed to claim task {task_id}: {e}", Fore.RED)
                except Exception as e:
                    self.log(f"❌ Unexpected error claiming task {task_id}: {e}", Fore.RED)
            
            self.log("⏳ Waiting 5 seconds after Phase 2...", Fore.CYAN)
            time.sleep(5)
        else:
            self.log("ℹ️ No tasks to claim. Skipping Phase 2...", Fore.CYAN)

    def farming(self) -> None:
        import time
        import datetime

        headers = {**self.HEADERS, "authorization": f"Bearer {self.token}"}
        
        # Step 1: Get farming info from API
        farming_info_url = f"{self.BASE_URL}farming/info"
        try:
            self.log("📡 Requesting farming info...", Fore.CYAN)
            farming_info_response = requests.get(farming_info_url, headers=headers)
            farming_info_response.raise_for_status()
            farming_info = self.decode_response(farming_info_response)
        except requests.exceptions.RequestException as e:
            self.log(f"❌ Failed to fetch farming info: {e}", Fore.RED)
            return
        except Exception as e:
            self.log(f"❌ Unexpected error while fetching farming info: {e}", Fore.RED)
            return

        # Log farming info data
        self.log(f"ℹ️ Farming info: {farming_info}", Fore.CYAN)
        
        # Step 2: Check if there's no active farming and/or no activeFarmingStartedAt timestamp.
        if farming_info.get("balance", "0.000") == "0.000" or not farming_info.get("activeFarmingStartedAt"):
            self.log("🚀 No active farming detected. Starting new farming...", Fore.GREEN)
            start_url = f"{self.BASE_URL}farming/start"
            try:
                start_response = requests.post(start_url, headers=headers, data=json.dumps({}))
                start_response.raise_for_status()
                start_data = self.decode_response(start_response)
                self.log(f"✅ Farming started successfully: {start_data}", Fore.GREEN)
            except requests.exceptions.RequestException as e:
                self.log(f"❌ Failed to start farming: {e}", Fore.RED)
            except Exception as e:
                self.log(f"❌ Unexpected error while starting farming: {e}", Fore.RED)
            return

        # Step 3: If there is an active farming (activeFarmingStartedAt exists), then check finish time.
        active_start = farming_info.get("activeFarmingStartedAt")
        duration_sec = farming_info.get("farmingDurationInSec", 0)
        
        try:
            # Convert activeFarmingStartedAt from ISO format to datetime object
            active_start_dt = datetime.datetime.fromisoformat(active_start.replace("Z", "+00:00"))
        except Exception as e:
            self.log(f"❌ Error parsing activeFarmingStartedAt: {e}", Fore.RED)
            return

        # Calculate finish time by adding duration (in seconds)
        finish_time = active_start_dt + datetime.timedelta(seconds=duration_sec)
        current_time = datetime.datetime.now(datetime.timezone.utc)
        time_remaining = (finish_time - current_time).total_seconds()

        if time_remaining <= 0:
            self.log("🚀 Farming duration met. Claiming farming reward...", Fore.GREEN)
            # Step 4: Claim farming reward with API "farming/finish"
            finish_url = f"{self.BASE_URL}farming/finish"
            try:
                finish_response = requests.post(finish_url, headers=headers, data=json.dumps({}))
                finish_response.raise_for_status()
                finish_data = self.decode_response(finish_response)
                self.log(f"✅ Farming finished successfully: {finish_data}", Fore.GREEN)
            except requests.exceptions.RequestException as e:
                self.log(f"❌ Failed to finish farming: {e}", Fore.RED)
            except Exception as e:
                self.log(f"❌ Unexpected error while finishing farming: {e}", Fore.RED)
            
            # After claim, start new farming
            self.log("🚀 Starting new farming after finishing the previous one...", Fore.GREEN)
            start_url = f"{self.BASE_URL}farming/start"
            try:
                start_response = requests.post(start_url, headers=headers, data=json.dumps({}))
                start_response.raise_for_status()
                start_data = self.decode_response(start_response)
                self.log(f"✅ New farming started successfully: {start_data}", Fore.GREEN)
            except requests.exceptions.RequestException as e:
                self.log(f"❌ Failed to start new farming: {e}", Fore.RED)
            except Exception as e:
                self.log(f"❌ Unexpected error while starting new farming: {e}", Fore.RED)
        else:
            self.log(f"ℹ️ Farming in progress. Time remaining until finish: {int(time_remaining)} seconds", Fore.CYAN)

    def load_proxies(self, filename="proxy.txt"):
        """
        Reads proxies from a file and returns them as a list.

        Args:
            filename (str): The path to the proxy file.

        Returns:
            list: A list of proxy addresses.
        """
        try:
            with open(filename, "r", encoding="utf-8") as file:
                proxies = [line.strip() for line in file if line.strip()]
            if not proxies:
                raise ValueError("Proxy file is empty.")
            return proxies
        except Exception as e:
            self.log(f"❌ Failed to load proxies: {e}", Fore.RED)
            return []

    def set_proxy_session(self, proxies: list) -> requests.Session:
        """
        Creates a requests session with a working proxy from the given list.

        If a chosen proxy fails the connectivity test, it will try another proxy
        until a working one is found. If no proxies work or the list is empty, it
        will return a session with a direct connection.

        Args:
            proxies (list): A list of proxy addresses (e.g., "http://proxy_address:port").

        Returns:
            requests.Session: A session object configured with a working proxy,
                            or a direct connection if none are available.
        """
        # If no proxies are provided, use a direct connection.
        if not proxies:
            self.log("⚠️ No proxies available. Using direct connection.", Fore.YELLOW)
            self.proxy_session = requests.Session()
            return self.proxy_session

        # Copy the list so that we can modify it without affecting the original.
        available_proxies = proxies.copy()

        while available_proxies:
            proxy_url = random.choice(available_proxies)
            self.proxy_session = requests.Session()
            self.proxy_session.proxies = {"http": proxy_url, "https": proxy_url}

            try:
                test_url = "https://httpbin.org/ip"
                response = self.proxy_session.get(test_url, timeout=5)
                response.raise_for_status()
                origin_ip = response.json().get("origin", "Unknown IP")
                self.log(
                    f"✅ Using Proxy: {proxy_url} | Your IP: {origin_ip}", Fore.GREEN
                )
                return self.proxy_session
            except requests.RequestException as e:
                self.log(f"❌ Proxy failed: {proxy_url} | Error: {e}", Fore.RED)
                # Remove the failed proxy and try again.
                available_proxies.remove(proxy_url)

        # If none of the proxies worked, use a direct connection.
        self.log("⚠️ All proxies failed. Using direct connection.", Fore.YELLOW)
        self.proxy_session = requests.Session()
        return self.proxy_session

    def override_requests(self):
        import random

        """Override requests functions globally when proxy is enabled."""
        if self.config.get("proxy", False):
            self.log("[CONFIG] 🛡️ Proxy: ✅ Enabled", Fore.YELLOW)
            proxies = self.load_proxies()
            self.set_proxy_session(proxies)

            # Override request methods
            requests.get = self.proxy_session.get
            requests.post = self.proxy_session.post
            requests.put = self.proxy_session.put
            requests.delete = self.proxy_session.delete
        else:
            self.log("[CONFIG] proxy: ❌ Disabled", Fore.RED)
            # Restore original functions if proxy is disabled
            requests.get = self._original_requests["get"]
            requests.post = self._original_requests["post"]
            requests.put = self._original_requests["put"]
            requests.delete = self._original_requests["delete"]


async def process_account(account, original_index, account_label, timefar, config):

    ua = UserAgent()
    timefar.HEADERS["user-agent"] = ua.random

    # Menampilkan informasi akun
    display_account = account[:10] + "..." if len(account) > 10 else account
    timefar.log(f"👤 Processing {account_label}: {display_account}", Fore.YELLOW)

    # Override proxy jika diaktifkan
    if config.get("proxy", False):
        timefar.override_requests()
    else:
        timefar.log("[CONFIG] Proxy: ❌ Disabled", Fore.RED)

    # Login (fungsi blocking, dijalankan di thread terpisah) dengan menggunakan index asli (integer)
    await asyncio.to_thread(timefar.login, original_index)

    timefar.log("🛠️ Starting task execution...", Fore.CYAN)
    tasks_config = {
        "task": "Automatically solving tasks 🤖",
        "farming": "Automatic farming for abundant harvest 🌾",
    }

    for task_key, task_name in tasks_config.items():
        task_status = config.get(task_key, False)
        color = Fore.YELLOW if task_status else Fore.RED
        timefar.log(
            f"[CONFIG] {task_name}: {'✅ Enabled' if task_status else '❌ Disabled'}",
            color,
        )
        if task_status:
            timefar.log(f"🔄 Executing {task_name}...", Fore.CYAN)
            await asyncio.to_thread(getattr(timefar, task_key))

    delay_switch = config.get("delay_account_switch", 10)
    timefar.log(
        f"➡️ Finished processing {account_label}. Waiting {Fore.WHITE}{delay_switch}{Fore.CYAN} seconds before next account.",
        Fore.CYAN,
    )
    await asyncio.sleep(delay_switch)


async def worker(worker_id, timefar, config, queue):
    """
    Setiap worker akan mengambil satu akun dari antrian dan memprosesnya secara berurutan.
    Worker tidak akan mengambil akun baru sebelum akun sebelumnya selesai diproses.
    """
    while True:
        try:
            original_index, account = queue.get_nowait()
        except asyncio.QueueEmpty:
            break
        account_label = f"Worker-{worker_id} Account-{original_index+1}"
        await process_account(account, original_index, account_label, timefar, config)
        queue.task_done()
    timefar.log(f"Worker-{worker_id} finished processing all assigned accounts.", Fore.CYAN)


async def main():
    timefar = timefarm()  
    config = timefar.load_config()
    all_accounts = timefar.query_list
    num_threads = config.get("thread", 1)  # Jumlah worker sesuai konfigurasi

    if config.get("proxy", False):
        proxies = timefar.load_proxies()

    timefar.log(
        "🎉 [LIVEXORDS] === Welcome to Time Farm Automation === [LIVEXORDS]", Fore.YELLOW
    )
    timefar.log(f"📂 Loaded {len(all_accounts)} accounts from query list.", Fore.YELLOW)

    while True:
        # Buat queue baru dan masukkan semua akun (dengan index asli)
        queue = asyncio.Queue()
        for idx, account in enumerate(all_accounts):
            queue.put_nowait((idx, account))

        # Buat task worker sesuai dengan jumlah thread yang diinginkan
        workers = [
            asyncio.create_task(worker(i + 1, timefar, config, queue))
            for i in range(num_threads)
        ]

        # Tunggu hingga semua akun di queue telah diproses
        await queue.join()

        # Opsional: batalkan task worker (agar tidak terjadi tumpang tindih)
        for w in workers:
            w.cancel()

        timefar.log("🔁 All accounts processed. Restarting loop.", Fore.CYAN)
        delay_loop = config.get("delay_loop", 30)
        timefar.log(
            f"⏳ Sleeping for {Fore.WHITE}{delay_loop}{Fore.CYAN} seconds before restarting.",
            Fore.CYAN,
        )
        await asyncio.sleep(delay_loop)


if __name__ == "__main__":
    asyncio.run(main())
