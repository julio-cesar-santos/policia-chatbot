import pytest
from unittest.mock import MagicMock
from app import OrquestradorDeTriagem, sessoes, WahaOutboundAdapter
from bot_logic import DelegaciaRepository, ServicoTriagemIA

@pytest.fixture(autouse=True)
def clear_sessions():
    sessoes.clear()
    yield

@pytest.fixture
def orquestrador_mock():
    mock_waha = MagicMock(spec=WahaOutboundAdapter)
    mock_repo = MagicMock(spec=DelegaciaRepository)
    mock_ia = MagicMock(spec=ServicoTriagemIA)
    return OrquestradorDeTriagem(waha=mock_waha, repo=mock_repo, ia=mock_ia)

def test_initial_state_creates_session(orquestrador_mock):
    chat_id = "5511999999999@c.us"
    orquestrador_mock.executar_ciclo(chat_id, "Olá")
    
    assert chat_id in sessoes
    assert sessoes[chat_id]['estado'] == 'menu'
    assert sessoes[chat_id]['primeiro_acesso'] is False
    orquestrador_mock.waha.enviar.assert_called()

def test_state_machine_routes_to_busca(orquestrador_mock):
    chat_id = "5511999999999@c.us"
    sessoes[chat_id] = {'estado': 'menu', 'historico': []}
    
    orquestrador_mock.executar_ciclo(chat_id, "2")
    
    assert sessoes[chat_id]['estado'] == 'busca_delegacias'
    orquestrador_mock.waha.enviar.assert_called_with(chat_id, 'Por favor, me informe o seu bairro e a sua cidade para que eu possa localizar a delegacia mais próxima no meu sistema. Mande exatamente: "BAIRRO, CIDADE"')

def test_global_interceptor_aborts_flow(orquestrador_mock):
    chat_id = "5511999999999@c.us"
    sessoes[chat_id] = {'estado': 'busca_delegacias', 'historico': []}
    
    orquestrador_mock.executar_ciclo(chat_id, "Menu")
    
    assert sessoes[chat_id]['estado'] == 'menu'

def test_feedback_handles_invalid_input_gracefully(orquestrador_mock):
    chat_id = "5511999999999@c.us"
    sessoes[chat_id] = {'estado': 'feedback_busca', 'historico': []}
    
    orquestrador_mock.executar_ciclo(chat_id, "Eu achei ótimo!")
    
    assert sessoes[chat_id]['estado'] == 'feedback_busca'
    orquestrador_mock.waha.enviar.assert_called_with(chat_id, "Por favor, responda com o número 1 para Sim ou 2 para Não.")

def test_footer_is_shown_only_on_first_access(orquestrador_mock):
    """Test UX: Ensure the 'Voltar' instruction is not spammed to the user."""
    chat_id = "5511999999999@c.us"
    sessoes[chat_id] = {'estado': 'novo', 'historico': [], 'primeiro_acesso': True}
    
    orquestrador_mock._enviar_menu_principal(chat_id)
    first_call_args = orquestrador_mock.waha.enviar.call_args[0][1]
    assert 'Para voltar ao menu, digite "Menu" ou "Voltar".' in first_call_args
    assert sessoes[chat_id]['primeiro_acesso'] is False
    
    orquestrador_mock._enviar_menu_principal(chat_id)
    second_call_args = orquestrador_mock.waha.enviar.call_args[0][1]
    assert 'Para voltar ao menu, digite "Menu" ou "Voltar".' not in second_call_args