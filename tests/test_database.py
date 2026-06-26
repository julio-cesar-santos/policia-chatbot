import requests


def test_get_delegacias_should_return_status_200_when_service_is_up(
    supabase_url, supabase_headers
):
    url = f"{supabase_url}/rest/v1/delegacias?select=id"
    response = requests.get(url, headers=supabase_headers, timeout=5)

    assert response.status_code == 200


def test_search_city_should_return_status_200_when_city_is_valid(
    supabase_url, supabase_headers
):
    url = f"{supabase_url}/rest/v1/delegacias?cidade_busca=eq.belo%20jardim&select=id"
    response = requests.get(url, headers=supabase_headers, timeout=5)

    assert response.status_code == 200


def test_search_city_should_return_non_empty_list_when_city_is_valid(
    supabase_url, supabase_headers
):
    url = f"{supabase_url}/rest/v1/delegacias?cidade_busca=eq.belo%20jardim&select=id"
    response = requests.get(url, headers=supabase_headers, timeout=5)

    assert len(response.json()) > 0


def test_search_city_should_return_correct_address_when_city_is_valid(
    supabase_url, supabase_headers
):
    url = f"{supabase_url}/rest/v1/delegacias?cidade_busca=eq.belo%20jardim&select=endereco"
    response = requests.get(url, headers=supabase_headers, timeout=5)
    returned_address = response.json()[0].get("endereco", "")

    assert "Av. Sebastião Rodrigues" in returned_address


def test_search_city_should_return_status_200_when_city_is_invalid(
    supabase_url, supabase_headers
):
    url = f"{supabase_url}/rest/v1/delegacias?cidade_busca=eq.gotham_city&select=id"
    response = requests.get(url, headers=supabase_headers, timeout=5)

    assert response.status_code == 200


def test_search_city_should_return_empty_list_when_city_is_invalid(
    supabase_url, supabase_headers
):
    url = f"{supabase_url}/rest/v1/delegacias?cidade_busca=eq.gotham_city&select=id"
    response = requests.get(url, headers=supabase_headers, timeout=5)

    assert len(response.json()) == 0