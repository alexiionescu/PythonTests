import logging
import re
import time
import gevent
from locust import User, tag, task, run_single_user
from locust import FastHttpUser
import tomllib
import json
from uuid import UUID, uuid4
import websocket  # pip install websocket-client

from datetime import datetime, timedelta


def datetime_to_excel(dt):
    # Excel's base date
    excel_base_date = datetime(1899, 12, 30)
    delta = dt - excel_base_date
    return float(delta.days) + (float(delta.seconds) / 86400)


def get_toml_cfg(self):
    with open("locustcfg.toml", "rb") as f:
        cfg = tomllib.load(f)
        for k in cfg:
            logging.debug(f"{self.__class__.__name__}.{k}= {cfg[k]}")
            setattr(self, k, cfg[k])


class DCCWebSocket:

    def ws_connect(self, host: str, header=[], **kwargs):
        self.ws = websocket.create_connection(host, header=header, **kwargs)
        self.ws_greenlet = gevent.spawn(self.ws_receive_loop)

    def ws_receive_loop(self):
        while True:
            try:
                message = self.ws.recv()
                logging.debug(f"WSR: {message}")
                self.ws_on_message(message)
            except:
                break

    def ws_send(self, body, name=None, context={}, opcode=websocket.ABNF.OPCODE_TEXT):
        logging.debug(f"WSS: {body}")
        self.ws.send(body, opcode)


class DCCUser(FastHttpUser, DCCWebSocket):
    host = "TEST"
    admin_api_host: str | None = None
    dcc_api_host: str | None = None
    dcc_instance_name: str | None = None
    dcc_instance_guid: str | None = None
    computer_guid: str | None = None
    admin_token_global: str | None = None
    admin_token: str | None = None
    dcc_token: str | None = None
    dcc_user: str | None = None
    dcc_password: str | None = None
    pid: int | None = None
    ws_todo_wait = 60
    ws_todo: int = 0
    ws_sessions: int = 0
    summary_changed = True
    summary_force = 10
    uuid: UUID

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
        self.uuid = uuid4()
        if not self.admin_api_host:
            get_toml_cfg(self)
        if self.admin_api_host:
            logging.debug(f"{self.uuid} REQ PoltysConnect {self.admin_api_host}")
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
                    logging.debug(
                        f"{self.uuid} CHECK Instance {lic.get("Key")} '{lic.get("Name")}'"
                    )
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
            logging.debug(
                f"{self.uuid} REQ ChooseLicense {self.dcc_instance_guid} '{self.dcc_instance_name}'"
            )
            with self.rest(
                "POST",
                f"https://{self.admin_api_host}/api.pts?otype=Admin.MainServer&method=ChooseLicense&token={self.admin_token_global}",
                headers={
                    "Host": self.admin_api_host,
                },
                json={"Token": self.admin_token, "Key": self.dcc_instance_guid},
                name="Admin.MainServer:ChooseLicense",
            ) as resp:
                addr_ssl = resp.json().get("AddressSSL")
                self.dcc_token = resp.json().get("Token")
                self.computer_guid = resp.json().get("ComputerGUID")
                if not self.dcc_api_host:
                    self.dcc_api_host = addr_ssl
                    logging.debug(f"{self.uuid} ChooseLicense AddressSSL {addr_ssl}")

        if self.dcc_token:
            logging.debug(f"{self.uuid} REQ pid")
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
                        self.summary_force_cntdown = self.summary_force
                        logging.info(f"{self.uuid} User Login Successfull")

    def on_stop(self):
        if self.dcc_token:
            logging.debug(f"{self.uuid} REQ Disconnect")
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
                    self.pid = None
                    self.dcc_token = None
                    logging.info(
                        f"{self.uuid} User Logout Successfull. WS sessions: {self.ws_sessions}"
                    )

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
                json={"GUID": self.computer_guid},
                name="Watcher.Server:GetComputerVersion",
            ) as _:
                pass

    @tag("watcher")
    @task(200)
    def watcher_comp_info(self):
        if self.admin_token:
            with self.rest(
                "POST",
                f"https://{self.admin_api_host}/api.pts?otype=Watcher.Server&method=GetComputerInfo&token={self.admin_token}",
                headers={
                    "Host": self.admin_api_host,
                    "Referer": f"{self.host}/",
                },
                json={
                    "GUID": self.computer_guid,
                    "Version": 1,
                    "PackagesDate": datetime_to_excel(datetime.now()),
                    "ProcessID": self.pid,
                    "Updated": True,
                },
                name="Watcher.Server:GetComputerInfo",
            ) as _:
                pass

    @tag("watcher")
    @task(100)
    def watcher_signal_client(self):
        if self.admin_token_global:
            with self.rest(
                "POST",
                f"https://{self.admin_api_host}/api.pts?otype=Admin.MainServer&method=SignalClient&token={self.admin_token_global}",
                headers={
                    "Host": self.admin_api_host,
                    "Referer": f"{self.host}/",
                },
                json={
                    "GUID": self.computer_guid,
                    "Key": self.dcc_instance_guid,
                    "Date": datetime_to_excel(datetime.now()),
                },
                name="Admin.MainServer:SignalClient",
            ) as _:
                pass

    @tag("processinfo")
    @task(100)
    def dcc_proccess_info(self):
        with self.rest(
            "POST",
            f"https://{self.dcc_api_host}/api.pts?otype=Utils.Miscellaneous&method=GetProcessInfo&token={self.dcc_token}",
            headers={
                "Host": self.dcc_api_host,
            },
            json={},
            name="SingleProcessInfo",
        ) as _:
            pass

    @tag("websocket")
    @task
    def dcc_websocket(self):
        if self.dcc_token and self.pid:
            if self.ws_todo == 0:
                self.ws_todo = self.ws_todo_wait
                self.ws_sessions += 1
                logging.info(f"{self.uuid} New websocket connection")
                self.ws_connect(f"wss://{self.dcc_api_host}/api.ws")

                self.ws_send(
                    '{"Type":"ConnectBulk","ConnectionsInfo":'
                    '[{"Cmd::ConnectionInfo":{"ObjectType":"DCC","ObjectName":"Alarms","EventType":"RuntimeSkillsChanged","Connect":true}},'
                    '{"Cmd::ConnectionInfo":{"ObjectType":"Routing","ObjectName":"Activities","EventType":"Created","Connect":true}},'
                    '{"Cmd::ConnectionInfo":{"ObjectType":"Routing","ObjectName":"Activities","EventType":"Closing","Connect":true}},'
                    '{"Cmd::ConnectionInfo":{"ObjectType":"Routing","ObjectName":"Activities","EventType":"StateChanged","Connect":true}},'
                    '{"Cmd::ConnectionInfo":{"ObjectType":"Routing","ObjectName":"Activities","EventType":"SubjectChanged","Connect":true}}]}'
                )

                # update pid, execute this to count the websocket connection count
                with self.rest(
                    "POST",
                    f"https://{self.dcc_api_host}/api.pts?otype=Utils.Miscellaneous&method=GetProcessInfo&token={self.dcc_token}",
                    headers={
                        "Host": self.dcc_api_host,
                    },
                    json={},
                    name="WebSocket:Connect",
                ) as resp:
                    if resp.status_code == 200:
                        self.pid = int(resp.json().get("PID"))

            elif self.ws_todo == 1:
                try:
                    self.ws.close()
                except:
                    pass
                logging.info(f"{self.uuid} End websocket connection")
                self.ws_todo = 0
            else:
                self.ws_todo -= 1

    def ws_on_message(self, message):
        obj = json.loads(message)
        if obj and not obj.get("KeepAlive") and not obj.get("Response"):
            # print(message)
            self.summary_changed = True
        pass

    @tag("devices")
    @task(20)
    def dcc_devices(self):
        if self.dcc_token and self.pid:
            with self.rest(
                "POST",
                f"https://{self.dcc_api_host}/api.pts?otype=Devices.Endpoints&method=Count&token={self.dcc_token}&pid={self.pid}",
                headers={
                    "Host": self.dcc_api_host,
                },
                json={
                    "Condition": "({1} LIKE '%11%' OR {2} LIKE '%11%' OR {13} LIKE '%11%' OR {3} LIKE '%11%' OR {4} LIKE '%11%' OR {5} LIKE '%11%' OR {6} LIKE '%11%' OR {9} LIKE '%11%' OR {10} LIKE '%11%')",
                    "Line": "Sim Residents",
                },
                name="Devices.Endpoints:Count",
            ) as _:
                pass
            with self.rest(
                "POST",
                f"https://{self.dcc_api_host}/api.pts?otype=Devices.Endpoints&method=List&token={self.dcc_token}&pid={self.pid}",
                headers={
                    "Host": self.dcc_api_host,
                },
                json={
                    "Start": 0,
                    "Length": 20,
                    "OrderC": [6, 2],
                    "OrderT": ["ASC", "ASC"],
                    "Condition": "({1} LIKE '%11%' OR {2} LIKE '%11%' OR {13} LIKE '%11%' OR {3} LIKE '%11%' OR {4} LIKE '%11%' OR {5} LIKE '%11%' OR {6} LIKE '%11%' OR {9} LIKE '%11%' OR {10} LIKE '%11%') AND  EndpointTypes.Name != 'LineMaintenance'  AND Lines_.Name = 'Sim Residents'",
                    "Having": "",
                },
                name="Devices.Endpoints:List",
            ) as _:
                pass

    @tag("summary")
    @task(500)
    def dcc_summary(self):
        if self.dcc_token and self.pid:
            if not self.summary_changed:
                self.summary_force_cntdown -= 1
                if self.summary_force_cntdown > 0:
                    return
                else:
                    self.summary_force_cntdown = self.summary_force
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
            ) as _:
                pass
            with self.rest(
                "POST",
                f"https://{self.dcc_api_host}/api.pts?otype=DCC::Alarms&method=GetActiveAlarmsEndpoints&token={self.dcc_token}&pid={self.pid}",
                headers={
                    "Host": self.dcc_api_host,
                },
                json={},
                name="DCC::Alarms:GetActiveAlarmsEndpoints",
            ) as _:
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
            ) as _:
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
            ) as _:
                pass
            self.summary_changed = False

    @tag("history")
    @task(20)
    def dcc_history(self):
        if self.dcc_token and self.pid:
            with self.rest(
                "POST",
                f"https://{self.dcc_api_host}/api.pts?otype=DCC::Alarms&method=Count&token={self.dcc_token}&pid={self.pid}",
                headers={
                    "Host": self.dcc_api_host,
                },
                json={
                    "Condition": "({1} > DATE_SUB(@currTimeUTC, INTERVAL 24 HOUR))",
                    "Having": "(JSON_SEARCH({20}, 'one', '%') IS NULL OR JSON_CONTAINS({20}, '[\"BUILDING\"]')) AND (JSON_SEARCH({21}, 'one', '%') IS NULL OR JSON_CONTAINS({21}, '[\"Caregiver\"]'))",
                    "FromArchive": False,
                },
                name="DCC::Alarms:HistoryCount",
            ) as _:
                pass
            with self.rest(
                "POST",
                f"https://{self.dcc_api_host}/api.pts?otype=DCC::Alarms&method=List&token={self.dcc_token}&pid={self.pid}",
                headers={
                    "Host": self.dcc_api_host,
                },
                json={
                    "Start": 0,
                    "Length": 100,
                    "OrderC": [1],
                    "OrderT": ["DESC"],
                    "Condition": "({1} > DATE_SUB(@currTimeUTC, INTERVAL 24 HOUR))",
                    "Having": "(JSON_SEARCH({20}, 'one', '%') IS NULL OR JSON_CONTAINS({20}, '[\"BUILDING\"]')) AND (JSON_SEARCH({21}, 'one', '%') IS NULL OR JSON_CONTAINS({21}, '[\"Caregiver\"]'))",
                    "FromArchive": False,
                },
                name="DCC::Alarms:HistoryList",
            ) as _:
                pass

    @tag("residents")
    @task(10)
    def dcc_residents(self):
        if self.dcc_token and self.pid:
            with self.rest(
                "POST",
                f"https://{self.dcc_api_host}/api.pts?otype=DCC.Contacts&method=CountResidents&token={self.dcc_token}&pid={self.pid}",
                headers={
                    "Host": self.dcc_api_host,
                },
                json={"Condition": "", "Having": ""},
                name="DCC.Contacts:ResidentsCount",
            ) as _:
                pass
            with self.rest(
                "POST",
                f"https://{self.dcc_api_host}/api.pts?otype=DCC.Contacts&method=ListResidents&token={self.dcc_token}&pid={self.pid}",
                headers={
                    "Host": self.dcc_api_host,
                },
                json={
                    "Start": 0,
                    "Length": 100,
                    "OrderC": [1],
                    "OrderT": ["ASC"],
                    "Condition": "",
                    "Having": "",
                },
                name="DCC.Contacts:ResidentsList",
            ) as _:
                pass

    @tag("employees")
    @task(10)
    def dcc_employees(self):
        if self.dcc_token and self.pid:
            with self.rest(
                "POST",
                f"https://{self.dcc_api_host}/api.pts?otype=DCC.Contacts&method=ListEmployees&token={self.dcc_token}&pid={self.pid}",
                headers={
                    "Host": self.dcc_api_host,
                },
                json={"Condition": "", "Having": ""},
                name="DCC.Contacts:EmployeesCount",
            ) as _:
                pass
            with self.rest(
                "POST",
                f"https://{self.dcc_api_host}/api.pts?otype=DCC.Contacts&method=ListEmployees&token={self.dcc_token}&pid={self.pid}",
                headers={
                    "Host": self.dcc_api_host,
                },
                json={
                    "Start": 0,
                    "Length": 100,
                    "OrderC": [1],
                    "OrderT": ["ASC"],
                    "Condition": "",
                    "Having": "",
                },
                name="DCC.Contacts:EmployeesList",
            ) as _:
                pass


if __name__ == "__main__":
    run_single_user(DCCUser)
