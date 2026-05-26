import requests
import unicodedata

def remover_acentos(texto):
    # Remove acentos e converte para minúsculo (Ideal para a cidade_busca)
    texto_sem_acento = ''.join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')
    return texto_sem_acento.lower()

def gerar_sql():
    print(" Buscando municípios de Pernambuco no IBGE...")
    url = "https://servicodados.ibge.gov.br/api/v1/localidades/estados/PE/municipios"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        municipios = response.json()
    except requests.exceptions.RequestException as e:
        print(f"Erro ao acessar a API do IBGE: {e}")
        return

    sql_lines = ["INSERT INTO delegacias (cidade_busca, cidade_exibicao, endereco) VALUES"]
    valores = []

    for mun in municipios:
        nome = mun['nome']
        
        # Omitindo Fernando de Noronha conforme a regra de negócio
        if nome == "Fernando de Noronha":
            continue
        
        cidade_busca = remover_acentos(nome)
        # Endereço placeholder temporário
        endereco = "Endereço em atualização. Verifique no site oficial da PCPE."
        
        # Prepara a linha SQL escapando aspas simples caso existam no nome da cidade
        nome_escapado = nome.replace("'", "''")
        busca_escapada = cidade_busca.replace("'", "''")
        
        valores.append(f"('{busca_escapada}', '{nome_escapado}', '{endereco}')")

    # Junta todas as linhas com vírgula e finaliza com ponto e vírgula
    sql_lines.append(",\n".join(valores) + ";")

    # Salva o arquivo SQL
    with open("inserir_cidades.sql", "w", encoding="utf-8") as f:
        f.write("\n".join(sql_lines))

    print(f" Sucesso! Arquivo 'inserir_cidades.sql' gerado com {len(valores)} cidades.")

if __name__ == "__main__":
    gerar_sql()