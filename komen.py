import os
import re
import json
import requests
import uuid
import base64, time
from rich import print as prints

ew = "[reset]"
dG = "[bold #00fe00]"
RW = "[bold #ff0b50]"

def login_facebook(cookie):
    try:
        response = requests.get(
            "https://business.facebook.com/business_locations",
            headers={
                "user-agent": "Mozilla/5.0 (Linux; Android 8.1.0; MI 8 Build/OPM1.171019.011) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.86 Mobile Safari/537.36", 
                "cookie": cookie
            }
        )
        token = re.search("(EAAG\\w+)", response.text)
        if token:
            prints(f"[INFO] Login Berhasil!")
            return token.group(1)
        else:
            prints(f"[INFO] Login Gagal, Cookie Tidak Valid.")
            return None
    except requests.exceptions.RequestException:
        prints(f"[INFO] Koneksi Internet Bermasalah.")
        return None

def GetDate(req):
    if not req:
        print("❌ ERROR: Response kosong atau tidak valid!")
        return None

    def extract(pattern, text, default=None):
        match = re.search(pattern, text)
        return match.group(1) if match else default

    return {
        "av": extract(r'"actorID":"(\d+)"', req, "Tidak ditemukan"),
        "__aaid": "0",
        "__user": extract(r'"actorID":"(\d+)"', req, "Tidak ditemukan"),
        "__a": "1",
        "__req": "25",
        "__hs": extract(r'"haste_session":"(.*?)"', req, "Tidak ditemukan"),
        "dpr": "1",
        "__ccg": extract(r'"connectionClass":"(.*?)"', req, "Tidak ditemukan"),
        "__rev": extract(r'"__spin_r":(\d+)', req, "Tidak ditemukan"),
        "__s": extract(r'"__s":"(\d+)"', req, "Tidak ditemukan"),
        "__hsi": extract(r'"hsi":"(\d+)"', req, "Tidak ditemukan"),
        "__dyn": extract(r'"__dyn":"(\d+)"', req, "Tidak ditemukan"),
        "__hsdp": extract(r'"__hsdp":"(\d+)"', req, "Tidak ditemukan"),
        "__hblp": extract(r'"__hblp":"(\d+)"', req, "Tidak ditemukan"),
        "__csr": extract(r'"__csr":"(\d+)"', req, "Tidak ditemukan"),
        "__comet_req": extract(r'__comet_req=(\d+)', req, "Tidak ditemukan"),
        "fb_dtsg": extract(r'"DTSGInitData",\[\],{"token":"(.*?)",', req, "Tidak ditemukan"),
        "jazoest": extract(r'jazoest=(\d+)', req, "Tidak ditemukan"),
        "lsd": extract(r'"LSD",\[\],{"token":"(.*?)"', req, "Tidak ditemukan"),
        "__spin_r": extract(r'"__spin_r":(\d+)', req, "Tidak ditemukan"),
        "__spin_b": extract(r'"__spin_b":"(.*?)"', req, "Tidak ditemukan"),
        "__spin_t": extract(r'"__spin_t":(\d+)', req, "Tidak ditemukan"),
    }

def extract_feedback_id(url):
    match = re.search(r'fbid=(\d+)', url)
    if not match:
        match = re.search(r'videos/(\d+)', url)
    if not match:
        match = re.search(r'posts/(\d+)', url)
    if not match:
        match = re.search(r'(pfbid[0-9a-zA-Z]+)', url)
    if not match:
        match = re.search(r'reel/(\d+)', url)
    if match:
        return match.group(1) if len(match.groups()) > 0 else match.group(0)
    print(f"Gagal mengekstrak ID dari URL: {url}")
    return None

def encode_feedback_id(feedback_id):
    raw_string = f"feedback:{feedback_id}"
    encoded_bytes = base64.b64encode(raw_string.encode("utf-8"))
    return encoded_bytes.decode("utf-8")  # Decode ke string

class Facebook:
    def __init__(self, cookie):
        self.r = requests.Session()
        self.cok = cookie
        self.req = None
        self.uid = None
        self.client = None
        self.profile_ganda = []
    
    def getuid(self):
        try:
            headers = {
                'accept': '*/*',
                'accept-language': 'en-US,en;q=0.9,id;q=0.8',
                'content-type': 'application/x-www-form-urlencoded',
                'origin': 'https://www.facebook.com',
                'priority': 'u=1, i',
                'sec-ch-prefers-color-scheme': 'dark',
                'sec-ch-ua': '"Chromium";v="134", "Not:A-Brand";v="24", "Google Chrome";v="134"',
                'sec-ch-ua-full-version-list': '"Chromium";v="134.0.6998.89", "Not:A-Brand";v="24.0.0.0", "Google Chrome";v="134.0.6998.89"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-model': '""',
                'sec-ch-ua-platform': '"Windows"',
                'sec-ch-ua-platform-version': '"10.0.0"',
                'sec-fetch-dest': 'empty',
                'sec-fetch-mode': 'cors',
                'sec-fetch-site': 'same-origin',
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36',
                'x-asbd-id': '359341',
                'x-fb-friendly-name': 'CometSettingsDropdownTriggerQuery',
            }
            self.req = self.r.get("https://www.facebook.com/me", headers=headers, cookies={"cookie": self.cok}).text
            data = GetDate(self.req)
            data.update({
                "fb_api_caller_class": "RelayModern",
                "fb_api_req_friendly_name": "CometSettingsDropdownTriggerQuery",
                "variables": json.dumps({
                    "pageManagementNuxId": 8191,
                    "profileSwitcherNuxId": 8150,
                    "coreAppAdminProfileSwitcherNuxId": 8189,
                    "profileSwitcherAdminEducationNuxId": 9348,
                    "showNewToast": True
                }),
                "server_timestamps": "true",
                "doc_id": "6287151654667869"
            })
            response = self.r.post("https://www.facebook.com/api/graphql/", headers=headers, data=data, cookies={"cookie": self.cok})
            if response.status_code != 200:
                prints("[ERROR] Gagal mengambil data profil ganda.")
                return
            json_data = response.json()
            profile_data = json_data.get("data", {}).get("viewer", {}).get("actor", {}).get("profile_switcher_eligible_profiles", {})
            if "nodes" in profile_data:
                prints("[INFO] Kumpulan ID Profile Ganda:")
                for i, profile in enumerate(profile_data["nodes"], start=1):
                    profile_id = profile.get("profile", {}).get("id", "Tidak ditemukan")
                    prints(f"{i}. {profile_id}")
                    self.profile_ganda.append(profile_id)
            else:
                prints("[INFO] Tidak Ada Profil Ganda.")
        except Exception as e:
            prints(f"[ERROR] {e}")

    def switchacc(self, profile_id):
            try:
                headers = {
                    'accept': '*/*',
                    'accept-language': 'en-US,en;q=0.9,id;q=0.8',
                    'content-type': 'application/x-www-form-urlencoded',
                    'origin': 'https://www.facebook.com',
                    'priority': 'u=1, i',
                    'sec-ch-prefers-color-scheme': 'dark',
                    'sec-ch-ua': '"Chromium";v="134", "Not:A-Brand";v="24", "Google Chrome";v="134"',
                    'sec-ch-ua-full-version-list': '"Chrom ium";v="134.0.6998.89", "Not:A-Brand";v="24.0.0.0", "Google Chrome";v="134.0.6998.89"',
                    'sec-ch-ua-mobile': '?0',
                    'sec-ch-ua-model': '""',
                    'sec-ch-ua-platform': '"Windows"',
                    'sec-ch-ua-platform-version': '"10.0.0"',
                    'sec-fetch-dest': 'empty',
                    'sec-fetch-mode': 'cors',
                    'sec-fetch-site': 'same-origin',
                    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36',
                    'x-asbd-id': '359341',
                    'x-fb-friendly-name': 'CometProfileSwitchMutation',
                }
                self.req = self.r.get("https://www.facebook.com/me", headers=headers, cookies={"cookie": self.cok}).text
                data = GetDate(self.req)
                data.update({
                    "fb_api_caller_class": "RelayModern",
                    "fb_api_req_friendly_name": "CometProfileSwitchMutation",
                    "variables": json.dumps({
                        "profile_id": profile_id
                    }),
                    "server_timestamps": "true",
                    "doc_id": "7240611932633722"
                })
                response = self.r.post("https://www.facebook.com/api/graphql/", headers=headers, data=data, cookies={"cookie": self.cok})
                if response.status_code != 200:
                    prints(f"[ERROR] Gagal Login Ke Profil Ganda {profile_id}")
                    return
                prints(f"[SUCCESS] Berhasil Berpindah ke Profil {profile_id}")
            except Exception as e:
                prints(f"[ERROR] Terjadi Kesalahan saat switch ke profil {profile_id}: {e}")

    def komen(self, teks, url):
        feedback_id = extract_feedback_id(url)
        if not feedback_id:
            prints(f"{RW}❌ Gagal mengekstrak feedback_id dari {url}.")
            return
        encoded_feedback_id = encode_feedback_id(feedback_id)
        try:
            headers = {
                'accept': '*/*',
                'accept-language': 'en-US,en;q=0.9,id;q=0.8',
                'content-type': 'application/x-www-form-urlencoded',
                'origin': 'https://www.facebook.com',
                'priority': 'u=1, i',
                'referer': url,
                'sec-ch-prefers-color-scheme': 'dark',
                'sec-ch-ua': '"Chromium";v="134", "Not:A-Brand";v="24", "Google Chrome";v="134"',
                'sec-ch-ua-full-version-list': '"Chromium";v="134.0.6998.89", "Not:A-Brand";v="24.0.0.0", "Google Chrome";v="134.0.6998.89"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-model': '""',
                'sec-ch-ua-platform': '"Windows"',
                'sec-ch-ua-platform-version': '"10.0.0"',
                'sec-fetch-dest': 'empty',
                'sec-fetch-mode': 'cors',
                'sec-fetch-site': 'same-origin',
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36',
                'x-asbd-id': '359341',
                'x-fb-friendly-name': 'useCometUFICreateCommentMutation',
            }
            self.req = self.r.get(url, headers=headers, cookies={"cookie": self.cok}).text
            self.uid = re.search(r'__user=(\d+)',self.req).group(1)
            self.client = re.search('"clientID":"(.*?)"',str(self.req)).group(1)
            data = GetDate(self.req)
            variables = {
                "feedLocation": "PERMALINK",
                "feedbackSource": 2,
                "groupID": None,
                "input": {
                    "client_mutation_id": self.client,
                    "actor_id": self.uid,
                    "attachments": None,
                    "feedback_id": encoded_feedback_id,
                    "formatting_style": None,
                    "message": {"ranges": [], "text": teks},
                    "attribution_id_v2": "CometSinglePostDialogRoot.react,comet.post.single_dialog,via_cold_start,1742357494545,347300,,,",
                    "vod_video_timestamp": None,
                    "is_tracking_encrypted": True,
                    "tracking": [
                        f'{{"assistant_caller":"comet_above_composer","conversation_guide_session_id":"{str(uuid.uuid4())}","conversation_guide_shown":null}}'
                    ],
                    "feedback_source": "OBJECT",
                    "idempotence_token": f"client:{str(uuid.uuid4())}",
                    "session_id": str(uuid.uuid4()),
                    "downstream_share_session_id": str(uuid.uuid4()),
                    "downstream_share_session_origin_uri": url,
                    "downstream_share_session_start_time": "1742357499667",
                },
                "inviteShortLinkKey": None,
                "renderLocation": None,
                "scale": 1,
                "useDefaultActor": False,
                "focusCommentID": None,
                "__relay_internal__pv__IsWorkUserrelayprovider": False,
            }
            data.update({
                "fb_api_caller_class": "RelayModern",
                "fb_api_req_friendly_name": "useCometUFICreateCommentMutation",
                "variables": json.dumps(variables),
                "server_timestamps": "true",
                "doc_id": "9389802714420896"
            })
            cuki = self.r.post("https://www.facebook.com/api/graphql/", headers=headers, data=data, cookies={"cookie": self.cok})
            cuki = cuki.json()
            if "errors" not in cuki:
                prints(f"{dG}✅ Komentar berhasil dikirim ke {url}")
            else:
                prints(f"{RW}❌ Gagal mengirim komentar ke {url}")
            time.sleep(7)
        except Exception as e: print(e)

def main():
    os.system('cls' if os.name == 'nt' else 'clear')

    with open("cok.txt", 'r') as file:
        cookies = [line.strip() for line in file.readlines()]

    with open("url.txt", 'r') as file:
        urls = [line.strip() for line in file.readlines()]

    comment_text = "Ini adalah komentar otomatis."

    for index, cookie in enumerate(cookies, start=1):
        prints(f"[INFO] Mencoba Login Menggunakan Cookie {index}")
        token = login_facebook(cookie)
        if token:
            fb = Facebook(cookie)
            fb.getuid()
            
            if fb.profile_ganda:
                prints("[INFO] Menggunakan ID Utama Untuk Komentar")
                for url in urls:
                    fb.komen(comment_text, url)
                
                for i, profile_id in enumerate(fb.profile_ganda, start=1):
                    prints(f"[INFO] Mencoba Mengganti Akun menggunakan ID Profile {i}: {profile_id}")
                    fb.switchacc(profile_id)
                    
                    prints("[INFO] Menggunakan ID Profil Ganda untuk Komentar")
                    for url in urls:
                        fb.komen(comment_text, url)
            else:
                prints("[INFO] Tidak ada profil ganda untuk digunakan.")
        else:
            prints(f"[INFO] Gagal Login Menggunakan Cookie {index}\n")

if __name__ == "__main__":
    main()