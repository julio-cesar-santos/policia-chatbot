import pytest
from bot_logic import processar_ia

def test_processar_ia_should_include_transbordo_tag_when_crime_is_severe():    
    resposta = processar_ia("123", "Fui assaltado agora, o indivíduo estava armado e levou o meu carro!")
    
    assert "[TRANSBORDO]" in resposta

def test_processar_ia_should_not_include_transbordo_tag_when_crime_is_mild():    
    resposta = processar_ia("123", "Perdi o meu documento na rua.")
    
    assert "[TRANSBORDO]" not in resposta