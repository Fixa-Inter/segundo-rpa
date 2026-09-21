from extract._extract_all import extract_all
from transform._transform_all import transform_all
from load._load_all import load_all


def main():
    dados_extraidos = extract_all()
    dados_transformados = transform_all(dados_extraidos)
    load_all(dados_transformados)


if __name__ == "__main__":
    main()