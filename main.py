import streamlit as st
from scholarly import scholarly, ProxyGenerator
import time, random

# --- Configuração de proxy para evitar bloqueios do Google Scholar ---
def setup_scholarly():
    pg = ProxyGenerator()
    # Usa proxies gratuitos (pode ser instável; melhor usar API paga em produção)
    if not pg.FreeProxies(timeout=2, wait_time=60):
        raise RuntimeError("Não foi possível inicializar proxies.")
    scholarly.use_proxy(pg)

# --- Função auxiliar com tentativas de repetição ---
def with_retry(fn, tries=5, base=1.5):
    for i in range(tries):
        try:
            return fn()
        except Exception as e:
            if i == tries - 1:
                raise
            time.sleep((base ** i) + random.random())

# --- Busca de pesquisadores ---
@st.cache_data(ttl=3600)
def fetch_top_researchers_by_area(research_area, max_results=10):
    """
    Busca pesquisadores por área no Google Scholar.
    Tenta primeiro autores; se falhar, retorna vazio.
    """
    setup_scholarly()
    query = scholarly.search_author(research_area)
    top_researchers = []

    while len(top_researchers) < max_results:
        try:
            author = with_retry(lambda: scholarly.fill(next(query)))
            top_researchers.append({
                "name": author.get("name", "N/A"),
                "citations": author.get("citedby", "N/A"),
                "affiliation": author.get("affiliation", "N/A")
            })
        except StopIteration:
            break
        except Exception as e:
            st.error(f"Erro ao processar pesquisador: {e}")
            break

    return top_researchers

# --- Interface no Streamlit ---
st.title("Top Researchers by Research Area")

research_area = st.text_input(
    "Digite a área de pesquisa (ex.: 'machine learning', 'carbon footprint', 'climate change'):",
    placeholder="Escreva aqui a área de pesquisa..."
)

if st.button("Buscar"):
    if research_area.strip():
        with st.spinner("Buscando pesquisadores..."):
            try:
                researchers = fetch_top_researchers_by_area(research_area.strip())
            except Exception as e:
                st.error(f"Erro geral: {e}")
                researchers = []

            if researchers:
                st.success(f"Encontrados {len(researchers)} pesquisadores na área '{research_area}'.")
                for i, r in enumerate(researchers, start=1):
                    with st.expander(f"{i}. {r['name']}"):
                        st.write(f"- **Citações**: {r['citations']}")
                        st.write(f"- **Universidade**: {r['affiliation']}")
            else:
                st.warning(f"Nenhum pesquisador encontrado para '{research_area}'.")
    else:
        st.warning("Por favor, insira uma área válida.")

st.write("---")
st.markdown("**Fonte**: Google Scholar (via biblioteca `scholarly`)")
st.markdown("<p><strong>Ferramenta desenvolvida por Darliane Cunha</strong></p>", unsafe_allow_html=True)



