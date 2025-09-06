from dataclasses import dataclass
import random
from urllib3.util.ssl_ import create_urllib3_context
from capmonster_python import CapmonsterClient, TurnstileTask
import requests
import json
from requests.adapters import HTTPAdapter
import urllib3
import time
import re
from urllib.parse import urlparse, parse_qs
from datetime import datetime, timedelta

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class SSLAdapter(HTTPAdapter):
    def __init__(self, ssl_context=None, **kwargs):
        self.ssl_context = ssl_context
        super().__init__(**kwargs)

    def init_poolmanager(self, *args, **kwargs):
        kwargs['ssl_context'] = self.ssl_context
        return super().init_poolmanager(*args, **kwargs)

    def proxy_manager_for(self, proxy, **proxy_kwargs):
        # Ensure the same ssl_context is used when connecting to HTTPS proxies
        proxy_kwargs['ssl_context'] = self.ssl_context
        return super().proxy_manager_for(proxy, **proxy_kwargs)


THEORY_EXAM_TYPE = 'theoryExams'
PRACTICE_EXAM_TYPE = 'practiceExams'

MAX_TURNSTILE_USES = 30
MAX_TURNSTILE_LIFETIME = 300

@dataclass
class Exam:
    id: str
    places: int
    dateStr: str
    date: datetime
    amount: int

class AuthenticationError(Exception):
    pass

class InfoCarSession:
    def __init__(self, capmonster_key, proxies=[]):
        self.session = requests.session()

        ctx = create_urllib3_context()
        # Lower OpenSSL security level to allow smaller DH keys used by legacy servers
        try:
            ctx.set_ciphers('DEFAULT@SECLEVEL=1')
        except Exception:
            # Fallback for environments that don't support @SECLEVEL
            ctx.set_ciphers('DEFAULT')

        # Improve compatibility with legacy TLS servers when available
        _ssl = __import__('ssl')
        ctx.options |= getattr(_ssl, 'OP_LEGACY_SERVER_CONNECT', 0)

        ctx.check_hostname = False
        ctx.verify_mode = _ssl.CERT_NONE

        adapter = SSLAdapter(ssl_context=ctx)
        self.session.mount('https://', adapter)
        self.session.mount('http://', adapter)

        self.session.verify = False

        self.access_token = ""
        self.turnstile_token = ""
        self.turnstile_uses = 0
        self.turnstile_date = None
        self.capmonster = CapmonsterClient(api_key=capmonster_key)
        self.turnstile_solve_count = 0

        self.proxies = proxies

    def login(self, username, password):
        if len(self.proxies) > 0:
            self.session.proxies.update({
                'https': random.choice(self.proxies)
            })

        resp = self.session.get(
            "https://info-car.pl/oauth2/login",
            allow_redirects=True,
        )

        if resp.status_code != 200:
            raise Exception(f"Request failed with status code {resp.status_code}: {resp.text}")

        # Extract CSRF token robustly (supports single/double quotes)
        m = re.search(r'name=[\"\']_csrf[\"\']\s+value=[\"\']([^\"\']+)[\"\']', resp.text)
        if not m:
            raise Exception("Could not find CSRF token on login page")
        csrf = m.group(1)

        resp = self.session.post(
            "https://info-car.pl/oauth2/login",
            data={
                "username": username,
                "_csrf": [
                    csrf,
                    csrf
                ],
                "password": password,
            },
            allow_redirects=False
        )

        if resp.status_code != 302 and resp.status_code != 200:
            raise Exception(f"Login failed with status code {resp.status_code}: {resp.text}")

        loc = resp.headers.get('Location', '')

        if "?error=failure" in loc:
            raise Exception("Invalid credentials to Infocar")

        resp = self.session.get(
            "https://info-car.pl/oauth2/authorize?response_type=id_token%20token&client_id=client&state=am9zY0lXV1ZyY3VrdzlCazRxcVdGTjlIRzQ1NlFxTTdUaFJmbi5LQzZUaU5X&redirect_uri=https%3A%2F%2Finfo-car.pl%2Fnew%2Fassets%2Frefresh.html&scope=openid%20profile%20email%20resource.read&nonce=am9zY0lXV1ZyY3VrdzlCazRxcVdGTjlIRzQ1NlFxTTdUaFJmbi5LQzZUaU5X&prompt=none",
            allow_redirects=False
        )

        if resp.status_code != 302:
            raise Exception(f"Authorize failed with status code {resp.status_code}: {resp.text}")
        
        # Parse access_token from redirect Location (in hash or query)
        loc = resp.headers.get('Location', '')

        parsed = urlparse(loc)
        fragment = parsed.fragment or ''
        # Hash fragment is formatted like: access_token=...&...
        params = parse_qs(fragment)
        if not params.get('access_token'):
            # Sometimes token could be in query
            params = parse_qs(parsed.query)
        token_list = params.get('access_token') or []
        if not token_list:
            raise Exception("Access token not found in authorization redirect")
        self.access_token = token_list[0]

    def solve_turnstile(self):
        task = TurnstileTask(
            websiteURL="https://info-car.pl/new/konto",
            websiteKey="0x4AAAAAABm6HHqkjoB_Yn_a",
        )

        task_id = self.capmonster.create_task(task)
        result = self.capmonster.join_task_result(task_id)

        self.turnstile_solve_count += 1
        return result["token"]

    def ensure_alive_turnstile(self):
        if (
            self.turnstile_token == "" or
            self.turnstile_uses >= MAX_TURNSTILE_USES or
            self.turnstile_date is None or
            (time.time() - self.turnstile_date) >= MAX_TURNSTILE_LIFETIME
        ):
            self.turnstile_token = self.solve_turnstile()
            self.turnstile_uses = 0
            self.turnstile_date = time.time()

    def _to_iso(self, d: datetime) -> str:
        return d.strftime("%Y-%m-%dT%H:%M:%S.000Z")
    
    def is_reschedule_enabled_for_word(self, word_id: str) -> bool:
        if self.access_token == "":
            raise Exception("User is not authenticated")
        
        if len(self.proxies) > 0:
            self.session.proxies.update({
                'https': random.choice(self.proxies)
            })

        resp = self.session.get(
            f"https://info-car.pl/api/word/word-centers/reschedule-enabled/{word_id}",
            headers={
                "Authorization": f"Bearer {self.access_token}",
                "Accept-Language": "pl-PL",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:142.0) Gecko/20100101 Firefox/142.0",
                "Content-Type": "application/json",
                "Origin": "https://info-car.pl",
            },
        )

        if resp.status_code != 200:
            raise Exception(f"Request failed with status code {resp.status_code}: {resp.text}")

        data = resp.json()
        return data.get('rescheduleEnabled', False)

    def get_exams(self, exam_type, word_id, category="B") -> list[Exam]:
        if self.access_token == "":
            raise Exception("User is not authenticated")
 
        if len(self.proxies) > 0:
            self.session.proxies.update({
                'https': random.choice(self.proxies)
            })

        self.ensure_alive_turnstile()
        self.turnstile_uses += 1


        today = datetime.utcnow().date()

        req_data = json.dumps({
            "category": category,
            "endDate": self._to_iso(today + timedelta(days=60)),
            "startDate": self._to_iso(today),
            "wordId": word_id
        })

        resp = self.session.put(
            "https://info-car.pl/api/word/word-centers/exam-schedule",
            headers={
                "Authorization": f"Bearer {self.access_token}",
                "Accept-Language": "pl-PL",
                "X-CF-Turnstile": self.turnstile_token,
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:142.0) Gecko/20100101 Firefox/142.0",
                "Content-Type": "application/json",
                "Origin": "https://info-car.pl",
                "Content-Length": str(len(req_data))
            },
            data=req_data
        )

        if resp.status_code == 401:
            raise AuthenticationError("Access token expired or invalid")

        if resp.status_code != 200:
            raise Exception(f"Request failed with status code {resp.status_code}: {resp.text}")

        if "Request Rejected" in resp.text:
            raise Exception("Request was rejected, likely being an ASP backend error")

        data = resp.json()
        
        schedule = data['schedule']
        scheduled_days = schedule['scheduledDays']
        
        exams = []

        for scheduled_day in scheduled_days:
            for scheduled_hour in scheduled_day['scheduledHours']:
                for exam in scheduled_hour[exam_type]:
                    exams.append(Exam(
                        id=exam['id'],
                        places=exam['places'],
                        dateStr=exam['date'],
                        date=datetime.strptime(exam['date'], "%Y-%m-%dT%H:%M:%S"),
                        amount=exam['amount']
                    ))

        return exams
    
    def get_account_reservations(self):
        if self.access_token == "":
            raise Exception("User is not authenticated")

        if len(self.proxies) > 0:
            self.session.proxies.update({
                'https': random.choice(self.proxies)
            })

        resp = self.session.get(
            "https://info-car.pl/api/word/reservations?limit=10&sort=exam.examDate&direction=DESC",
            headers={
                "Authorization": f"Bearer {self.access_token}",
                "Accept-Language": "pl-PL",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:142.0) Gecko/20100101 Firefox/142.0",
            },
        )

        if resp.status_code != 200:
            raise Exception(f"Request failed with status code {resp.status_code}: {resp.text}")

        data = resp.json()
        return data['items']
    
    def reschedule_exam(self, reservation_id: str, exam_id: str):
        if self.access_token == "":
            raise Exception("User is not authenticated")
        
        if len(self.proxies) > 0:
            self.session.proxies.update({
                'https': random.choice(self.proxies)
            })

        req_data = json.dumps({
            "updatedPracticeId": exam_id,
        })

        resp = self.session.put(
            f"https://info-car.pl/api/word/reservations/{reservation_id}/reschedule",
            headers={
                "Authorization": f"Bearer {self.access_token}",
                "Accept-Language": "pl-PL",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:142.0) Gecko/20100101 Firefox/142.0",
                "Content-Type": "application/json",
                "Origin": "https://info-car.pl",
                "Content-Length": str(len(req_data)),
            },
            data=req_data,
        )

        if resp.status_code not in (200, 201):
            raise Exception(f"Reschedule request failed with status code {resp.status_code}: {resp.text}")

