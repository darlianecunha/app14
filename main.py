import os
import time
import random
import requests
import streamlit as st
from typing import List, Dict, Tuple

# scholarly é opcional se você optar por usar só SerpAPI
try:
    from scholarly import scholarly, ProxyGenerator
    HAS_SCHOLARLY = True
except Exception:
    HAS_SCHOLARLY = False


# -------------- Configurações da Página --------------
st.set_page_config(page_title="Top Researchers by Research Area", layout="wide")
st.title("Top Researchers by Research Area")

# -------------- Utilitários --------------
def jitter_sleep(base_low=0.7, base_high=1.4):
    time.sleep(random.uniform(base_low, base_high))

def setup_scholarly(use_proxies: bool) -> Tuple[bool, str]:
    """
    Tenta configurar proxies grátis. Retorna (ok, msg).
    """
    if not HAS_SCHOLARLY:
        return False, "Biblioteca 'scholarly' não disponível (import falhou)."
    if not use_proxies:
        return True, "Sem proxies (modo direto)."
    try:
        pg = ProxyGenerator()
        ok = pg.FreeProxies(timeout=2, wait_time=60)
        if ok:
            scholarly.use_proxy(pg)
            return True, "Proxies gratuitos habilitados."
        else:
            return False, "Falha ao obter proxies gratuitos."
    except Exception as e:
        return False, f"Erro ao configurar proxies: {e}"

def scholarly_fetch_authors(area: str, max_results: int, use_proxies: bool) -> List[Dict]:
    """
    Busca autores via scholarly.search_author(area).
    Tenta contornar bloqueios com pequenas pausas e captura de erros.
    """
    ok_proxy, proxy_msg = setup_scholarly(use_proxies)
    results: List[Dict] = []
    if not HAS_SCHOLARLY:
        st.info("Pulei scholarly: não está instalado/operante. Use SerpAPI (recomendado) ou instale a lib.")
        return results

    try:
        q = scholarly.search_author(area)
    except Exception as e:
        st.error(f"Falha ao iniciar pesquisa no scholarly: {e}")
        return results

    consecutive_errors = 0
    while len(results) < max_results:
        try:
            author = next(q)              # pode falhar se bloqueado/sem mais resultados
            author = scholarly.fill(author)  # carrega detalhes do perfil
            results.append({
                "name": author.get("name", "N/A"),
                "citations": author.get("citedby", "N/A"),
                "affiliation": author.get("affiliation", "N/A")
            })
            consecutive_errors = 0
            jitter_sleep(0.8, 1.8)  # pequena pausa entre requisições
        except StopIteration:
            break
        except Exception as e:
            consecutive_errors += 1
            st.warning(f"Erro ao buscar/ler autor (tentativa {consecutive_errors}): {e}")
            # backoff simples
            time.sleep(min(6, 1.5 ** consecutive_errors))
            if consecutive_errors >= 3 and len(results) == 0:
                # provavelmente bloqueado; abandona cedo para permitir fallback
                break
            continue

    # Feedback de proxy
    st.caption(f"Estado dos proxies scholarly: {proxy_msg}")
    return results


def serpapi_fetch_authors(area: str, max_results: int, api_key: str) -> List[Dict]:
    """
    Usa SerpAPI (engine google_scholar_author) – solução estável para produção.
    """
    url = "https://serpapi.com/search"
    params = {
        "engine": "google_scholar_author",
        "q": area,
        "api_key": api_key,
    }
    try:
        r = requests.get(url, params=params, timeout=30)
        r.raise_for_status()
        data = r.json()
        out = []
        for item in (data.get("authors") or [])[:max_results]:
            out.append({
                "name": item.get("name", "N/A"),
                "citations": (item.get("cited_by") or {}).get("table", [{}])[0].get("citations", "N/A")
                             if isinstance(item.get("cited_by"), dict) else item.get("cited_by"),
                "affiliation": item.get("affiliations", "N/A"),
            })
        return out
    except Exception as e:
        st.error(f"Erro na SerpAPI: {e}")
        return []


# -------------- Interface (opções) --------------
with st.sidebar:
    st.header("Configurações")
    max_results = st.number_input("Qtd. pesquisadores", min_value=1, max_value=50, value=10, step=1)
    engine = st.selectbox(
        "Engine",
        options=["Auto (SerpAPI se houver chave, senão Scholarly)", "Apenas SerpAPI", "Apenas Scholarly"]
    )
    use_proxies = st.checkbox("Usar proxies gratuitos (scholarly)", value=True)
    serpapi_key = st.text_input("SERPAPI_KEY (opcional)", type="password", value=os.getenv("SERPAPI_KEY", ""))

area = st.text_input("Área de pesquisa (ex.: 'machine learning', 'carbon footprint', 'climate change')",
                     placeholder="Digite a área...")

if st.button("Buscar"):
    if not area.strip():
        st.warning("Informe uma área de pesquisa válida.")
    else:
        with st.spinner("Buscando pesquisadores..."):
            results: List[Dict] = []

            # Seleção do mecanismo
            use_serpapi = (engine in ["Apenas SerpAPI"]) or \
                          (engine.startswith("Auto") and bool(serpapi_key))

            if use_serpapi:
                results = serpapi_fetch_authors(area.strip(), max_results, serpapi_key)
                if not results and engine.startswith("Auto"):
                    st.info("SerpAPI não retornou resultados. Tentando scholarly como fallback...")
                    results = scholarly_fetch_authors(area.strip(), max_results, use_proxies)
            else:
                results = scholarly_fetch_authors(area.strip(), max_results, use_proxies)

        # Exibição
        if results:
            st.success(f"Encontrados {len(results)} pesquisadores para '{area}'.")
            for i, r in enumerate(results, start=1):
                with st.expander(f"{i}. {r.get('name','N/A')}"):
                    st.write(f"- **Citações**: {r.get('citations','N/A')}")
                    st.write(f"- **Universidade**: {r.get('affiliation','N/A')}")
        else:
            st.warning("Nenhum resultado. Dicas:\n"
                       "• Ative proxies (scholarly) ou use SERPAPI_KEY\n"
                       "• Tente palavras-chave mais gerais\n"
                       "• Reduza a quantidade de resultados inicialmente")

st.write("---")
st.markdown("**Fontes**: Google Scholar (via `scholarly`) e/ou SerpAPI.")
st.caption("Dica: para produção, prefira SerpAPI pela estabilidade e políticas de uso.")
