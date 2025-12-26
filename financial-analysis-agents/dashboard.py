"""
Dashboard interattiva Streamlit per Graham AI Analyst.
Supporta visualizzazione mobile, grafici e selezione multi-provider.
"""
import os
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import yfinance as yf
from dotenv import load_dotenv

from agents import MarketDataAgent, AIProvider, GrahamAgent, ETFFinderAgent
from agents.ai_provider import OLLAMA_AVAILABLE
from utils.cache_manager import CacheManager
from models import FinancialData

OLLAMA_INSTALLED = OLLAMA_AVAILABLE


# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(
    page_title="Graham AI",
    page_icon="🧐",
    layout="wide",
    initial_sidebar_state="collapsed"
)

load_dotenv()

# --- FUNZIONI UTILITY ---

def get_ollama_models_list():
    """
    Recupera la lista dei modelli locali installati su Ollama.
    Gestisce errori di connessione se Ollama non è attivo.
    """
    return AIProvider.get_ollama_models()

def plot_price_chart(ticker_symbol):
    """Crea un grafico a candele interattivo usando Plotly."""
    try:
        df = yf.Ticker(ticker_symbol).history(period="1y")
        if df.empty:
            return None
        
        chart_fig = go.Figure(data=[go.Candlestick(
            x=df.index,
            open=df['Open'], high=df['High'],
            low=df['Low'], close=df['Close']
        )])
        
        chart_fig.update_layout(
            title=f"Trend {ticker_symbol} (1 Anno)",
            xaxis_rangeslider_visible=False,
            margin={"l": 20, "r": 20, "t": 40, "b": 20},
            height=350
        )
        return chart_fig
    except Exception: # pylint: disable=broad-exception-caught
        return None

# --- SIDEBAR: CONFIGURAZIONE ---

st.sidebar.header("🧠 Cervello AI")

# Selezione Provider
provider_options = ["Google Gemini", "Groq (Veloce)", "DeepSeek (Economico)", "Ollama (Locale)"]
# Usiamo index=0 (Gemini) come default
provider_selection = st.sidebar.radio("Scegli Provider:", provider_options, index=0)

api_key = None
selected_model = None
provider_code = "gemini"

# Logica specifica per ogni provider
# Logica specifica per ogni provider
# Wrapper Caching per Streamlit (evita chiamate API ad ogni rerun)
@st.cache_data(ttl=3600, show_spinner=False)
def get_cached_gemini_models(api_key):
    return AIProvider.get_gemini_models(api_key)

@st.cache_data(ttl=3600, show_spinner=False)
def get_cached_groq_models(api_key):
    return AIProvider.get_groq_models(api_key)
    
if "Gemini" in provider_selection:
    provider_code = "gemini"
    env_key = os.getenv("GOOGLE_API_KEY")
    user_key = st.sidebar.text_input("Gemini API Key", value=env_key or "", type="password")
    api_key = user_key if user_key else None
    
    if api_key:
        try:
            gemini_models = get_cached_gemini_models(api_key)
            if gemini_models:
                # Trova indice default solo se non c'è già una selezione nello state
                # Ma st.selectbox gestisce lo stato se la lista è stabile (che ora è cacheata)
                default_ix = 0
                for i, m in enumerate(gemini_models):
                    if "1.5-flash" in m and "latest" not in m: 
                         default_ix = i
                         break
                
                # Usa key univoca per persistenza
                selected_model = st.sidebar.selectbox("Scegli Modello Gemini:", gemini_models, index=default_ix, key="gemini_model_select")
            else:
                 st.sidebar.warning("Nessun modello Gemini trovato o Key invalida.")
        except Exception as e:
             st.sidebar.error(f"Errore recupero modelli: {e}")

elif "Groq" in provider_selection:
    provider_code = "groq"
    env_key = os.getenv("GROQ_API_KEY")
    user_key = st.sidebar.text_input("Groq API Key", value=env_key or "", type="password")
    api_key = user_key if user_key else None
    
    if api_key:
        try:
            groq_models = get_cached_groq_models(api_key)
            if groq_models:
                # Default a llama-3 se c'è
                default_ix = 0
                for i, m in enumerate(groq_models):
                    if "llama-3.3" in m:
                        default_ix = i
                        break
                selected_model = st.sidebar.selectbox("Scegli Modello Groq:", groq_models, index=default_ix, key="groq_model_select")
            else:
                st.sidebar.warning("Nessun modello Groq trovato.")
        except Exception:
            st.sidebar.caption("Err lista modelli.")

elif "DeepSeek" in provider_selection:
    provider_code = "deepseek"
    selected_model = "deepseek-chat"
    env_key = os.getenv("DEEPSEEK_API_KEY")
    user_key = st.sidebar.text_input("DeepSeek API Key", value=env_key or "", type="password")
    api_key = user_key if user_key else None

elif "Ollama" in provider_selection:
    provider_code = "ollama"
    if OLLAMA_INSTALLED:
        # Recupero dinamico dei modelli
        local_models = get_ollama_models_list()
        
        if local_models:
            selected_model = st.sidebar.selectbox("Scegli Modello Locale:", local_models)
            st.sidebar.success(f"Pronto: {selected_model}")
        else:
            st.sidebar.error("Nessun modello trovato o Ollama spento.")
            st.sidebar.info("1. Assicurati che Ollama sia in esecuzione.")
            st.sidebar.info("2. Esegui `ollama pull llama3` nel terminale.")
    else:
        st.sidebar.error("Libreria 'ollama' mancante.")

# --- GESTIONE CACHE ---
with st.sidebar.expander("🗑️ Gestione Cache", expanded=False):
    cm = CacheManager()
    all_keys = cm.get_all_keys()
    
    # Raggruppa per Ticker
    tickers_in_cache = sorted(list(set([k.split('_')[0] for k in all_keys if "_" in k])))
    
    if not tickers_in_cache:
        st.caption("Nessun dato in cache.")
    else:
        st.caption(f"Trovati dati per {len(tickers_in_cache)} ticker.")
        # Multiselect per cancellazione
        to_delete = st.multiselect("Seleziona da cancellare:", tickers_in_cache)
        
        if st.button("Svuota Cache Selezionati"):
            keys_to_del = []
            for t in to_delete:
                # Trova tutte le chiavi che iniziano con questo ticker
                keys_to_del.extend([k for k in all_keys if k.startswith(f"{t}_")])
            
            if keys_to_del:
                cm.delete_keys(keys_to_del)
                st.success(f"Rimossi dati per: {', '.join(to_delete)}")
                st.rerun() # Ricarica per aggiornare lista


st.sidebar.divider()
st.sidebar.header("🎛️ Opzioni Analisi")
audit_mode_ui = st.sidebar.radio(
    "Livello Audit Dati:",
    ["🚀 Rapido (Token Saver)", "🛡️ Completo (Massima Precisione)"],
    index=0,
    help="Rapido: Verifica solo errori evidenti.\nCompleto: Verifica web aggressiva su più campi."
)

# --- INTERFACCIA PRINCIPALE ---

st.title("🧐 Graham AI Analyst")
st.caption(f"Analisi fondamentale potenziata da **{provider_code.title()}**")

# Input Ticker e Bottone
col_input, col_btn = st.columns([3, 1])
with col_input:
    ticker_input = st.text_input(
        "Ticker", 
        placeholder="Es. AAPL, GME, NVDA...", 
        label_visibility="collapsed"
    ).upper()
    
with col_btn:
    run_btn = st.button("Analizza", type="primary", use_container_width=True)

# Logica di Esecuzione
if run_btn:
    # Controlli preliminari
    if not ticker_input:
        st.warning("Inserisci un simbolo azionario.")
    elif provider_code != "ollama" and not api_key:
        st.error(f"🔑 API Key mancante per {provider_code}. Inseriscila nella sidebar.")
    elif provider_code == "ollama" and not selected_model:
        st.error("❌ Nessun modello locale selezionato o disponibile.")
    else:
        # Avvio Processo
        status_box = st.status("🕵️‍♂️ Analisi in corso...", expanded=True)
        
        try:
            # 1. Setup Agente
            model_disp = selected_model or 'Auto'
            status_box.write(f"1️⃣ Connessione a {provider_code.title()} ({model_disp})...")
            
            market_agent = MarketDataAgent(
                api_key=api_key,
                provider=provider_code,
                model=selected_model
            )
            
            # 2. Recupero Dati (Cache o AI)
            status_box.write(f"2️⃣ Recupero dati ({audit_mode_ui})...")
            
            # Mappatura UI -> Parametro
            audit_param = "full" if "Completo" in audit_mode_ui else "quick"
            
            result_package = market_agent.fetch_from_ticker(
                ticker_input, 
                audit_mode=audit_param,
                callback=status_box.write
            )
            
            if result_package:
                financial_data = result_package.get("financials")
                summary_text = result_package.get("summary")
                
                status_box.write("3️⃣ Applicazione formule di Benjamin Graham...")
                
                # Creazione oggetti modello
                fin_obj = FinancialData(**financial_data)
                graham_agent = GrahamAgent(fin_obj)
                report_text = graham_agent.analyze()
                
                # Completamento
                status_box.update(label="✅ Analisi Completata!", state="complete", expanded=False)
                
                # --- DASHBOARD VISUALIZZAZIONE ---
                
                # A. KPI Metrics
                st.markdown("### ⚡ Indicatori Chiave (TTM)")
                m1, m2, m3 = st.columns(3)
                
                m1.metric("Prezzo", f"${fin_obj.current_market_price}")
                
                pe_ratio = 0.0
                if fin_obj.net_income > 0:
                    pe_ratio = fin_obj.current_market_price / (fin_obj.net_income / fin_obj.shares_outstanding)
                m2.metric("P/E Ratio", f"{pe_ratio:.1f}x")
                
                debt_str = f"${fin_obj.long_term_debt / 1_000_000:.0f}M"
                m3.metric("Debito LP", debt_str)
                
                # B. Contenuto a Schede
                tab_main, tab_story, tab_chart, tab_raw = st.tabs(
                    ["📝 Report Graham", "📜 Storia & Business", "📉 Grafico & ETF", "🔢 Dati Grezzi"]
                )
                
                with tab_main:
                    if "SOTTOVALUTATA" in report_text:
                        st.success("💎 VERDETTO: Titolo SOTTOVALUTATO secondo i criteri.")
                    elif "DA VERIFICARE" in report_text:
                        st.warning("⚠️ VERDETTO: Segnali MISTI. Richiede attenzione.")
                    
                    st.text_area("Report Dettagliato", report_text, height=600)
                    
                with tab_story:
                    st.markdown("### 🏢 Profilo Aziendale")
                    if summary_text:
                        st.info(summary_text)
                    else:
                        st.warning("Riassunto non disponibile.")
                        
                with tab_chart:
                    price_chart = plot_price_chart(ticker_input)
                    if price_chart:
                        st.plotly_chart(price_chart, width="stretch")
                    
                    st.markdown("#### 🏦 Esposizione ETF")
                    # Istanziamo un ETF finder dedicato per la UI se necessario
                    etf_finder = ETFFinderAgent(api_key=api_key, provider=provider_code, model=selected_model)
                    etf_list = etf_finder.find_etfs_holding_ticker(ticker_input)
                    
                    if etf_list:
                        st.dataframe(pd.DataFrame(etf_list), hide_index=True, width="stretch")
                    else:
                        st.caption("Nessun dato ETF rilevante trovato.")
                        
                with tab_raw:
                    st.markdown("### 📊 Confronto Dati Estratti vs Finviz")
                    
                    finviz_data_raw = result_package.get("finviz", {})
                    
                    # Mappa chiavi Finviz -> Chiavi Nostre
                    FV_MAP = {
                        'Price': 'current_market_price',
                        'P/E': 'pe_ratio', # Calcolato
                        'Income': 'net_income',
                        'Sales': 'sales',
                        'Shs Outstand': 'shares_outstanding',
                        'LTDebt/Eq': None, # Non diretto
                        'Dividend %': 'dividend_yield'
                    }
                    
                    # Creiamo confronto
                    comparison_rows = []
                    for k, v in financial_data.items():
                        finviz_val = "N/A"
                        # Cerca reverse mapping o match diretto
                        # Semplificazione: cerchiamo se c'è una chiave Finviz che mappa a k
                        found_fv_key = next((fk for fk, mk in FV_MAP.items() if mk == k), None)
                        
                        if found_fv_key and finviz_data_raw:
                            finviz_val = finviz_data_raw.get(found_fv_key, "N/A")
                        elif k == "long_term_debt" and finviz_data_raw:
                             # Finviz spesso non ha Long Term Debt esplicito in tabella snapshot principale se non come ratio
                             # Ma proviamo a vedere se c'è qualcosa di simile o se il cross-check lo ha preso da altrove
                             finviz_val = finviz_data_raw.get('Long Term Debt', "N/A") # A volte non c'è
                        
                        comparison_rows.append({"Campo": k, "Valore AI": v, "Valore Finviz": str(finviz_val)})
                        
                    st.dataframe(
                        pd.DataFrame(comparison_rows).set_index("Campo"),
                        width="stretch"
                    )
                    
                    if finviz_data_raw:
                        with st.expander("Vedi dati grezzi Finviz completi"):
                            st.json(finviz_data_raw)

            else:
                status_box.update(label="❌ Errore Dati", state="error")
                st.error("Impossibile recuperare o strutturare i dati. Controlla la console.")
        
        except Exception as e: # pylint: disable=broad-exception-caught
            status_box.update(label="❌ Errore Critico", state="error")
            st.error(f"Si è verificato un errore imprevisto: {e}")