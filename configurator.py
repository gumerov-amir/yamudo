#!/usr/bin/env python3

from getpass import getpass
import json
import os

import requests

CLIENT_ID = "23cabbbdc6cd418abb4b39c32c41195d"
CLIENT_SECRET = "53bc75238f0c4d08a118e51fe9203300"
USER_AGENT = "Yandex-Music-API"
HEADERS = {
    "X-Yandex-Music-Client": "YandexMusicAndroid/23020251",
    "USER_AGENT": USER_AGENT,
}
url = "https://oauth.yandex.ru/token"


def get_token(
    username, password, grant_type="password", x_captcha_answer=None, x_captcha_key=None
):
    data = {
        "grant_type": grant_type,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "username": username,
        "password": password,
    }
    if x_captcha_answer and x_captcha_key:
        data.update(
            {"x_captcha_answer": x_captcha_answer, "x_captcha_key": x_captcha_key}
        )
    try:
        resp = requests.request("post", url, data=data, headers=HEADERS)
    except requests.RequestException as e:
        raise NetworkError(e)
    if not (200 <= resp.status_code <= 299):
        raise SystemError("Error")
    json_data = json.loads(resp.content.decode("utf-8"))
    return json_data["access_token"]


def main():
    cfg: Dict[str, str] = {"links_file": "links.txt", "target_dir": "music", "token": ""}
    if input("You don't have config, do you want to create it? y or n")[0] == "n":
        return
    login = ""
    password = ""
    try:
        print("For using this tool you should have Yandex music token")
        print()
        print("Enter your Yandex credentials to continue")
        while not login:
            login = input("email or  login: ")
        while not password:
            password = getpass("Password: ")
        token = get_token(login, password)
        cfg["token"] = token
        with open("config.json", "w") as f:
            json.dump(cfg, f, indent=4, ensure_ascii=False)
        print("Config was created. started using default config values, to configure it open config.json")
    except Exception as e:
        print(e)
    input("Press enter to continue")
