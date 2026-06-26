from locust import HttpUser, task, between

class WahaWebhookUser(HttpUser):
    wait_time = between(1, 3)

    @task
    def test_load_webhook_endpoint(self):
        payload = {
            "event": "message",
            "payload": {
                "from": "5581999999999@c.us",
                "body": "Teste de stress",
                "type": "text"
            }
        }
        
        with self.client.post("/webhook", json=payload, catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Failed with status code {response.status_code}")