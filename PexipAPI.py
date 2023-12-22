import re
import shlex
import time
from enum import Enum, unique

import requests

from utils.app import AppThread, MainApp


class PexipSession(AppThread):
    def __init__(self, node, conference, display_name, pin=None):
        AppThread.__init__(self)
        self.node = node
        self.name = display_name  # thread name
        self.display_name = display_name
        self.conference = conference
        self.token_time = None
        self.headers = {}
        self.StartTime = time.time()
        if pin:
            self.headers["pin"] = pin

    def OnLoop(self):
        if self.token_time and time.time() - self.token_time > self.expires / 2:
            return self.RefreshToken()
        return True

    def OnSignal(self, *args):
        if args:
            if args[0] == "dial":
                self.RequestDial(*tuple(args[1:]))
            else:
                self.Log("received unknown command", *args)
        else:
            self.Log("received no command")
        return True

    def OnStart(self):
        self.Log("OnStart")
        return self.RequestToken()

    def OnClose(self):
        self.Log("OnClose")
        self.ReleaseToken()

    def RequestDial(self, destination, display_name, protocol="auto", role="HOST"):
        r = requests.post(
            self.GetURL("dial"),
            json={
                "role": role,
                "destination": destination,
                "protocol": protocol,
                "source_display_name": display_name,
            },
            headers=self.headers,
        )
        if r.status_code == requests.codes.ok:
            rjson = r.json()
            if rjson["status"] == "success":
                self.Log("dial Success", rjson["result"])
                return True
            else:
                self.Log("dial Status Error", rjson)
        else:
            self.Log("dial HTTP Error", r.status_code, r.text)
            self.LogHTTPTransaction(r)

    def RequestToken(self):
        r = requests.post(
            self.GetURL("request_token"),
            json={"display_name": self.display_name},
            headers=self.headers,
        )
        if r.status_code == requests.codes.ok:
            rjson = r.json()
            if rjson["status"] == "success":
                if "expires" in rjson["result"]:
                    self.expires = int(rjson["result"]["expires"])
                else:
                    self.expires = 120
                if "token" in rjson["result"]:
                    self.headers["token"] = rjson["result"]["token"]
                    self.token_time = time.time()
                    self.Log("request_token Success")
                    return True
                else:
                    self.Log("request_token invalid response")
            else:
                self.Log("request_token Status Error", rjson)
        else:
            self.Log("request_token HTTP Error", r.status_code, r.text)

    def RefreshToken(self):
        if "token" in self.headers:
            r = requests.post(self.GetURL("refresh_token"), headers=self.headers)
            if r.status_code == requests.codes.ok:
                rjson = r.json()
                if rjson["status"] == "success":
                    expires = 120
                    if "expires" in rjson["result"]:
                        expires = int(rjson["result"]["expires"])
                    self.headers["token"] = rjson["result"]["token"]
                    self.token_time = time.time()
                    self.Log("refresh_token Success")
                    return True
                else:
                    self.Log("refresh_token Status Error", rjson)
            else:
                self.Log("refresh_token HTTP Error", r, r.text)
            del self.headers["token"]
        return self.RequestToken()

    def ReleaseToken(self):
        if "token" in self.headers:
            r = requests.post(self.GetURL("release_token"), headers=self.headers)
            if r.status_code == requests.codes.ok:
                self.Log("release_token Success")
            else:
                self.Log("request_token HTTP Error", r)

    def GetURL(self, command: str):
        return (
            "https://"
            + self.node
            + "/api/client/v2/conferences/"
            + self.conference
            + "/"
            + command
        )

    def Log(self, *args):
        print(
            f"{time.time() - self.StartTime:12.6f}",
            self.conference,
            "\t",
            self.name,
            "\t",
            *args,
        )

    def LogHTTPTransaction(self, res: requests.Response):
        try:
            req = res.request
            req_headers = "\r\n".join(
                "{}: {}".format(k, v) for k, v in req.headers.items()
            )
            if isinstance(req.body, bytes):
                req_body = req.body.decode("utf-8")
            elif isinstance(req.body, str):
                req_body = req.body
            else:
                req_body = ""
            print(
                f"""-----------REQUEST-----------
{req.method} {req.url} HTTP/1.1
{req_headers}

{req_body}
"""
            )
            res_headers = "\r\n".join(
                "{}: {}".format(k, v) for k, v in res.headers.items()
            )

            print(
                f"""-----------RESPONSE-----------
HTTP/1.1 {res.status_code} {res.reason}
{res_headers}

{res.text}
"""
            )
        except:
            pass


class PexipApp(MainApp):
    def __init__(self):
        MainApp.__init__(self)  # this will block

    def OnStart(self, args):
        print(type(self).__name__, "Started")
        # return MainApp.LoopResult.Quit

    def OnClose(self):
        print(type(self).__name__, "Ended")
        pass

    def OnLoop(self):
        cmds = shlex.split(input())
        if cmds:
            if cmds[0] == "help":
                print(
                    """ 
add pex-gcc.com dcc1 p1
del p1
p1 dial "dcc.demo@onpexip.com" "Alex-Laptop"
p1 dial cart1.hc@onpexip.com "sip test"
"""
                )
            elif cmds[0] == "quit":
                return MainApp.LoopResult.Quit
            elif cmds[0] == "add":
                if len(cmds) >= 4:
                    self.AddThread(PexipSession(*tuple(cmds[1:])))
            elif cmds[0] == "del":
                if len(cmds) > 1:
                    pattern = re.compile(cmds[1])
                    for thread in self.threads:
                        if thread.is_alive() and re.match(pattern, thread.display_name):
                            thread.Signal(signal=AppThread.SignalType.Close)
            else:
                pattern = re.compile(cmds[0])
                for thread in self.threads:
                    if thread.is_alive() and re.match(pattern, thread.display_name):
                        thread.Signal(*tuple(cmds[1:]))
        return MainApp.LoopResult.Continue


if __name__ == "__main__":
    PexipApp()
