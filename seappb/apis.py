import requests


def get_cidades_paraiba():
    """Consulta a API para obter as cidades da Paraíba."""
    url = 'https://brasilapi.com.br/api/ibge/municipios/v1/PB'
    response = requests.get(url)

    print(f"Status Code: {response.status_code}")
    print(f"Response Text: {response.text}")

    if response.status_code == 200:
        cidades_data = response.json()
        return [(cidade['nome'], cidade['nome']) for cidade in cidades_data]
    else:
        return []  # Retorna uma lista vazia caso haja erro na requisição


# Testar a função para garantir que está funcionando corretamente
get_cidades_paraiba()
