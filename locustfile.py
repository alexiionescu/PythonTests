from locust import HttpUser, task, between

class MyLocustUser(HttpUser):
    wait_time = between(0.5, 3)
    host = "http://alex-laptop.poltys.com:9081"

    @task
    def short_page(self):
        self.client.get(self.host + "/short.html")

    # @task
    # def medium_page(self):
    #     self.client.get("/medium.html")
