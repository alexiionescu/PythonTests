import logging
from locust import tag, task, run_single_user
from locust import FastHttpUser
import tomllib


def get_toml_cfg(self):
    with open("locustcfg.toml", "rb") as f:
        cfg = tomllib.load(f)
        for k in cfg:
            logging.debug(f"{self.__class__.__name__}.{k}= {cfg[k]}")
            setattr(self, k, cfg[k])


class DCCUser(FastHttpUser):
    host = "TEST"
    admin_api_host: str | None = None
    dcc_api_host: str | None = None
    dcc_instance_name: str | None = None
    dcc_instance_guid: str | None = None
    admin_token_global: str | None = None
    admin_token: str | None = None
    dcc_token: str | None = None
    dcc_user: str | None = None
    dcc_password: str | None = None
    pid: int | None = None

    default_headers = {
        "Accept": "application/json, text/plain, */*",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Accept-Language": "en-US,en;q=0.9,fr-CA;q=0.8,fr;q=0.7",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-site",
        "Origin": host,
        "Pragma": "no-cache",
        "Referer": f"{host}/",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "sec-ch-ua": '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "macOS",
    }

    def on_start(self):
        if not self.admin_api_host:
            get_toml_cfg(self)
        if self.admin_api_host:
            logging.debug(f"REQ PoltysConnect {self.admin_api_host}")
            with self.rest(
                "POST",
                f"https://{self.admin_api_host}/api.pts?otype=Admin.Users&method=PoltysConnect&token=null",
                headers={
                    "Host": self.admin_api_host,
                },
                json={
                    "Email": self.dcc_user,
                    "MD5Password": self.dcc_password,
                    "Product": "DCC",
                },
                name="Admin.Users:PoltysConnect",
            ) as resp:
                self.admin_token_global = resp.json().get("TokenGlobal")
                self.admin_token = resp.json().get("Token")
                for lic_obj in resp.json().get("Licenses"):
                    lic = lic_obj.get("Admin::LicensesKey")
                    logging.debug(f"CHECK Instance {lic.get("Key")} '{lic.get("Name")}'")
                    if self.dcc_instance_name and self.dcc_instance_name == lic.get(
                        "Name"
                    ):
                        self.dcc_instance_guid = lic.get("Key")
                        break
                    if self.dcc_instance_guid and self.dcc_instance_guid == lic.get(
                        "Key"
                    ):
                        self.dcc_instance_name = lic.get("Name")
                        break

        if self.dcc_instance_guid and self.admin_token_global and self.admin_token:
            logging.debug(f"REQ ChooseLicense {self.dcc_instance_guid} '{self.dcc_instance_name}'")
            with self.rest(
                "POST",
                f"https://{self.admin_api_host}/api.pts?otype=Admin.MainServer&method=ChooseLicense&token={self.admin_token_global}",
                headers={
                    "Host": self.admin_api_host,
                },
                json={"Token": self.admin_token, "Key": self.dcc_instance_guid},
                name="Admin.MainServe:ChooseLicense",
            ) as resp:
                addr_ssl = resp.json().get("AddressSSL")
                self.dcc_token = resp.json().get("Token")
                if not self.dcc_api_host:
                    self.dcc_api_host = addr_ssl
                    logging.debug(f"ChooseLicense AddressSSL {addr_ssl}")

        if self.dcc_token:
            logging.debug("REQ pid")
            with self.rest(
                "POST",
                f"https://{self.dcc_api_host}/api.pts?otype=Utils.Miscellaneous&method=GetProcessInfo&token={self.dcc_token}",
                headers={
                    "Host": self.dcc_api_host,
                },
                json={},
                name="Utils.Miscellaneous:GetProcessInfo",
            ) as resp:
                if resp.status_code == 200:
                    self.pid = int(resp.json().get("PID"))
                    if self.pid:
                        logging.info("User Login Successfull")

    def on_stop(self):
        if self.dcc_token:
            logging.debug(f"REQ Disconnect")
            with self.rest(
                "POST",
                f"https://{self.admin_api_host}/api.pts?otype=Admin.Users&method=Disconnect&token={self.admin_token_global}",
                headers={
                    "Host": self.admin_api_host,
                },
                json={"Password": None},
                name="Admin.Users:Disconnect",
            ) as resp:
                if resp.status_code == 200:
                    logging.info("User Logout Successfull")

    @tag("about")
    @task
    def admin_about(self):
        if self.admin_token:
            with self.rest(
                "POST",
                f"https://{self.admin_api_host}/api.pts?otype=Watcher.Server&method=GetComputerVersion&token={self.admin_token}",
                headers={
                    "Host": self.admin_api_host,
                    "Referer": f"{self.host}/",
                },
                json={"GUID": "19424eb7-e5c6-4f4a-a077-b9d058eb56d9"},
                name="Watcher.Server:GetComputerVersion",
            ) as resp:
                pass

    @tag("summary")
    @task(50)
    def dcc_summary(self):
        if self.dcc_token and self.pid:
            with self.rest(
                "POST",
                f"https://{self.dcc_api_host}/api.pts?otype=DCC::Alarms&method=ActiveCount&token={self.dcc_token}&pid={self.pid}",
                headers={
                    "Host": self.dcc_api_host,
                },
                json={
                    "Condition": "",
                    "Having": "(JSON_SEARCH({15}, 'one', '%') IS NULL OR JSON_CONTAINS({15}, '[\"BUILDING\"]') OR JSON_CONTAINS({15}, '[\"Special\"]')) AND (JSON_SEARCH({16}, 'one', '%') IS NULL OR JSON_CONTAINS({16}, '[\"Caregiver\"]'))",
                    "Version": 1,
                },
                name="DCC::Alarms:ActiveCount",
            ) as resp:
                pass
            with self.rest(
                "POST",
                f"https://{self.dcc_api_host}/api.pts?otype=DCC::Alarms&method=GetActiveAlarmsEndpoints&token={self.dcc_token}&pid={self.pid}",
                headers={
                    "Host": self.dcc_api_host,
                },
                json={},
                name="DCC::Alarms:GetActiveAlarmsEndpoints",
            ) as resp:
                pass
            with self.rest(
                "POST",
                f"https://{self.dcc_api_host}/api.pts?otype=DCC::Alarms&method=ActiveList&token={self.dcc_token}&pid={self.pid}",
                headers={
                    "Host": self.dcc_api_host,
                },
                json={
                    "Version": 1,
                    "Start": 0,
                    "Length": 300,
                    "OrderC": [],
                    "OrderT": [],
                    "Condition": "",
                    "Having": "(JSON_SEARCH({15}, 'one', '%') IS NULL OR JSON_CONTAINS({15}, '[\"BUILDING\"]') OR JSON_CONTAINS({15}, '[\"Special\"]')) AND (JSON_SEARCH({16}, 'one', '%') IS NULL OR JSON_CONTAINS({16}, '[\"Caregiver\"]'))",
                },
                name="DCC::Alarms:ActiveList",
            ) as resp:
                pass
            with self.rest(
                "POST",
                f"https://{self.dcc_api_host}/api.pts?otype=DCC::Logins&method=AvailableList&token={self.dcc_token}&pid={self.pid}",
                headers={
                    "Host": self.dcc_api_host,
                },
                json={
                    "Locations": ["<empty>", "BUILDING", "Special"],
                    "Competences": ["<empty>", "Caregiver"],
                    "Shift": "Day",
                },
                name="DCC::Logins:AvailableList",
            ) as resp:
                pass
            with self.rest(
                "POST",
                f"https://{self.dcc_api_host}/api.pts?otype=DCC::Checkins&method=ActiveList&token={self.dcc_token}&pid={self.pid}",
                headers={
                    "Host": self.dcc_api_host,
                },
                json={
                    "Start": 0,
                    "Length": 300,
                    "OrderC": [1],
                    "OrderT": ["ASC"],
                    "Condition": "",
                    "Having": "(JSON_SEARCH({6}, 'one', '%') IS NULL OR JSON_CONTAINS({6}, '[\"BUILDING\"]') OR JSON_CONTAINS({6}, '[\"Special\"]'))",
                },
                name="DCC::Checkins:ActiveList",
            ) as resp:
                pass


if __name__ == "__main__":
    run_single_user(DCCUser)
