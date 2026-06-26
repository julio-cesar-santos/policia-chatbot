import pytest
from unittest.mock import patch, MagicMock
from bot_logic import ServicoTriagemIA, IAIntegrationError

@pytest.fixture
@patch('bot_logic.FAISS.load_local')
@patch('bot_logic.HuggingFaceEmbeddings')
def ia_service_mocked(mock_embeddings, mock_faiss):
    return ServicoTriagemIA()

@patch('bot_logic.requests.post')
def test_analyze_report_should_include_transbordo_tag_when_crime_is_severe(mock_post, ia_service_mocked):
    mock_response = MagicMock()
    mock_response.json.return_value = {
        'choices': [{'message': {'content': 'Este é um crime grave. Dirija-se à delegacia. [TRANSBORDO]'}}]
    }
    mock_response.raise_for_status = MagicMock()
    mock_post.return_value = mock_response

    resposta = ia_service_mocked.analisar_relato("Fui assaltado agora, o indivíduo estava armado!")

    assert "[TRANSBORDO]" in resposta
    mock_post.assert_called_once()


@patch('bot_logic.requests.post')
def test_analyze_report_should_not_include_transbordo_tag_when_crime_is_mild(mock_post, ia_service_mocked):
    mock_response = MagicMock()
    mock_response.json.return_value = {
        'choices': [{'message': {'content': 'Você pode registrar o boletim online no portal da SDS.'}}]
    }
    mock_response.raise_for_status = MagicMock()
    mock_post.return_value = mock_response

    resposta = ia_service_mocked.analisar_relato("Perdi meu documento na rua.")

    assert "[TRANSBORDO]" not in resposta


@patch('bot_logic.requests.post')
def test_analyze_report_should_raise_exception_when_api_fails(mock_post, ia_service_mocked):
    import requests
    mock_post.side_effect = requests.RequestException("API fora do ar")

    with pytest.raises(IAIntegrationError) as erro_info:
        ia_service_mocked.analisar_relato("Preciso de ajuda")
    
    assert "Falha de comunicação com o LLM" in str(erro_info.value)