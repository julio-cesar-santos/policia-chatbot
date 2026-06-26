import concurrent.futures
import requests


def test_post_webhook_should_return_status_200_when_payload_is_valid(
    flask_webhook_url, authorized_number
):
    payload = {
        "event": "message",
        "payload": {"from": authorized_number, "body": "Ping"},
    }
    response = requests.post(flask_webhook_url, json=payload, timeout=5)

    assert response.status_code == 200


def test_post_webhook_should_return_ok_status_in_json_when_payload_is_valid(
    flask_webhook_url, authorized_number
):
    payload = {
        "event": "message",
        "payload": {"from": authorized_number, "body": "Ping"},
    }
    response = requests.post(flask_webhook_url, json=payload, timeout=5)

    assert response.json().get("status") == "ok"


def test_post_webhook_should_return_status_200_when_sender_is_unauthorized(
    flask_webhook_url,
):
    payload = {
        "event": "message",
        "payload": {"from": "5511999999999@c.us", "body": "Invasor"},
    }
    response = requests.post(flask_webhook_url, json=payload, timeout=5)

    assert response.status_code == 200


def test_post_webhook_should_return_ignored_status_when_sender_is_unauthorized(
    flask_webhook_url,
):
    payload = {
        "event": "message",
        "payload": {"from": "5511999999999@c.us", "body": "Invasor"},
    }
    response = requests.post(flask_webhook_url, json=payload, timeout=5)

    assert response.json().get("status") == "ignorado"


def test_post_webhook_should_return_status_200_when_event_is_not_message(
    flask_webhook_url,
):
    payload = {"event": "message.ack", "payload": {"id": "123", "status": "READ"}}
    response = requests.post(flask_webhook_url, json=payload, timeout=5)

    assert response.status_code == 200


def test_get_webhook_should_return_status_405_when_method_is_not_allowed(
    flask_webhook_url,
):
    response = requests.get(flask_webhook_url, timeout=5)

    assert response.status_code == 405


def test_post_webhook_should_return_status_200_when_body_is_only_spaces(
    flask_webhook_url, authorized_number
):
    payload = {
        "event": "message",
        "payload": {"from": authorized_number, "body": "    "},
    }
    response = requests.post(flask_webhook_url, json=payload, timeout=5)

    assert response.status_code == 200


def test_post_webhook_should_return_status_200_when_media_has_no_text(
    flask_webhook_url, authorized_number
):
    payload = {
        "event": "message",
        "payload": {"from": authorized_number, "type": "image", "body": ""},
    }
    response = requests.post(flask_webhook_url, json=payload, timeout=5)

    assert response.status_code == 200


def test_post_webhook_should_return_status_200_when_text_is_massive(
    flask_webhook_url, authorized_number
):
    payload = {
        "event": "message",
        "payload": {"from": authorized_number, "body": "A" * 5000},
    }
    response = requests.post(flask_webhook_url, json=payload, timeout=10)

    assert response.status_code == 200


def test_post_webhook_should_survive_concurrent_requests(flask_webhook_url):
    def send_request(i):
        payload = {
            "event": "message",
            "payload": {"from": f"11999900{i}@c.us", "body": "Stress"},
        }
        return requests.post(flask_webhook_url, json=payload, timeout=5)

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(send_request, range(10)))

    assert all(res.status_code == 200 for res in results)