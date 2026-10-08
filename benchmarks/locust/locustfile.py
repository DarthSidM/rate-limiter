from locust import HttpUser, between, task


class RateLimiterUser(HttpUser):
    wait_time = between(0.01, 0.1)

    @task
    def test_endpoint(self):
        self.client.get("/api/test")