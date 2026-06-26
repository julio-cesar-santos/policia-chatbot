import os
from langchain_community.document_loaders import PyPDFDirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

def ingerir_documentos():
    pasta_conhecimento = "conhecimento"
    
    print(f"[1/4] Lendo PDFs e textos da pasta '{pasta_conhecimento}'...")
    
    carregador_pdf = PyPDFDirectoryLoader(pasta_conhecimento, glob="**/*.pdf")
    documentos = carregador_pdf.load()
    
    for raiz, _, arquivos in os.walk(pasta_conhecimento):
        for arquivo in arquivos:
            if arquivo.endswith(".txt"):
                caminho_txt = os.path.join(raiz, arquivo)
                documentos.extend(TextLoader(caminho_txt, encoding='utf-8').load())

    if not documentos:
        print("Nenhum documento encontrado. Coloque os PDFs na pasta 'conhecimento/'.")
        return

    print(f"[2/4] Fatiando {len(documentos)} páginas em pedaços menores...")
    separador = RecursiveCharacterTextSplitter(
        chunk_size=800,      
        chunk_overlap=150,   
        length_function=len
    )
    pedacos = separador.split_documents(documentos)

    print("[3/4] Gerando vetores (Isso pode demorar alguns minutos na primeira vez)...")
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    )

    print("[4/4] Salvando o banco de dados vetorial FAISS...")
    banco_vetorial = FAISS.from_documents(pedacos, embeddings)
    
    banco_vetorial.save_local("faiss_index")
    
    print("\n Ingestão concluída com sucesso! O cérebro do robô está atualizado.")

if __name__ == "__main__":
    ingerir_documentos()