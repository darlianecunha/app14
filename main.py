import streamlit as st
from scholarly import scholarly
import time

# Função para buscar os principais pesquisadores por área de pesquisa
def fetch_top_researchers_by_area(research_area, max_results=10):
    """
    Busca os principais pesquisadores em uma área específica no Google Scholar.
    
    Args:
        research_area (str): A área de pesquisa a ser consultada.
        max_results (int): Número máximo de pesquisadores a buscar.
    
    Returns:
        list: Lista de dicionários com informações dos pesquisadores.
    """
    try:
        search_query = scholarly.search_keyword(research_area)
        top_researchers = []
        
        for _ in range(max_results):
            try:
                researcher = next(search_query)
                researcher = scholarly.fill(researcher)  # Carrega o perfil completo
                
                # Extrai as informações relevantes
                name = researcher.get("name", "Nome não disponível")
                citations = researcher.get("citedby", "Citações não disponíveis")
                affiliation = researcher.get("affiliation", "Afiliação não disponível")
                
                top_researchers.append({
                    "name": name,
                    "citations": citations,
                    "affiliation": affiliation
                })
            except StopIteration:
                break  # Não há mais pesquisadores disponíveis
            except Exception as inner_error:
                st.error(f"Erro ao processar um pesquisador: {inner_error}")
        
        return top_researchers
    
    except Exception as e:
        st.error(f"Erro ao buscar dados no Google Scholar: {e}")
        return []

# Interface do Streamlit
st.title("Top Researchers by Research Area")

# Input para a área de pesquisa
research_area = st.text_input(
    "Enter a search area (e.g. 'machine learning', 'carbon footprint', 'climate change'):",
    placeholder="Digite aqui a área de pesquisa..."
)

# Busca dos resultados ao clicar no botão
if st.button("Search"):
    if research_area.strip():  # Valida o input
        with st.spinner("Seeking Researchers..."):
           


