import requests

def test_get_delegacias_should_return_status_200_when_service_is_up(
    supabase_url, supabase_headers
):
    url = f"{supabase_url}?select=descricao"
    response = requests.get(url, headers=supabase_headers, timeout=5)
    assert response.status_code == 200

def test_search_city_should_return_status_200_when_city_is_valid(
    supabase_url, supabase_headers
):
    url = f"{supabase_url}?endereco=ilike.*janga*&select=endereco"
    response = requests.get(url, headers=supabase_headers, timeout=5)
    assert response.status_code == 200

def test_search_city_should_return_non_empty_list_when_city_is_valid(
    supabase_url, supabase_headers
):
    url = f"{supabase_url}?endereco=ilike.*janga*&select=endereco"
    response = requests.get(url, headers=supabase_headers, timeout=5)
    assert len(response.json()) > 0

def test_search_city_should_return_correct_address_when_city_is_valid(
    supabase_url, supabase_headers
):
    url = f"{supabase_url}?endereco=ilike.*janga*&select=endereco"
    response = requests.get(url, headers=supabase_headers, timeout=5)
    returned_address = response.json()[0].get("endereco", "").lower()
    
    assert "janga" in returned_address

def test_search_city_should_return_status_200_when_city_is_invalid(
    supabase_url, supabase_headers
):
    url = f"{supabase_url}?endereco=ilike.*cidade_falsa_gotham*&select=descricao"
    response = requests.get(url, headers=supabase_headers, timeout=5)
    assert response.status_code == 200

def test_search_city_should_return_empty_list_when_city_is_invalid(
    supabase_url, supabase_headers
):
    url = f"{supabase_url}?endereco=ilike.*cidade_falsa_gotham*&select=descricao"
    response = requests.get(url, headers=supabase_headers, timeout=5)
    assert len(response.json()) == 0