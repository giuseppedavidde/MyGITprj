"""Agente responsabile del recupero dati da Yahoo Finance."""
from typing import Optional
import yfinance as yf
import pandas as pd
from .data_builder import DataBuilderAgent
from .summary import SummaryAgent

class MarketDataAgent:
    """
    Agente coordinatore (Facade).
    
    Responsabilità:
    1. Scaricare il Dossier Completo (storico) da Yahoo Finance.
    2. Coordinare il SummaryAgent per stampare a video un'overview qualitativa immediata.
    3. Coordinare il DataBuilderAgent per trasformare il testo grezzo in dati strutturati (JSON).
    """
    
    def __init__(self, api_key: Optional[str] = None):
        # Inizializziamo i sotto-agenti.
        # Entrambi useranno internamente AIProvider per configurarsi il modello migliore.
        self.builder = DataBuilderAgent(api_key=api_key)
        self.summarizer = SummaryAgent(api_key=api_key)

    def fetch_from_ticker(self, ticker_symbol: str) -> Optional[dict]:
        """
        Scarica i dati finanziari completi da Yahoo Finance per il ticker specificato.
        """
        print(f"📈 Recupero DOSSIER COMPLETO per {ticker_symbol} da Yahoo Finance...")
        
        try:
            ticker = yf.Ticker(ticker_symbol)
            
            # 1. Scarichiamo i prospetti COMPLETI (senza filtri)
            # Usiamo i DataFrame di Pandas per mantenere la struttura tabellare
            bs = ticker.balance_sheet
            inc = ticker.financials
            cf = ticker.cashflow
            
            # Controllo base di esistenza dati
            if bs.empty or inc.empty:
                print(f"❌ Dati bilancio non disponibili per {ticker_symbol}.")
                return None

            # 2. Dati Addizionali (Dividendi e Info Mercato)
            divs = ticker.dividends.tail(20) # Ultimi ~5 anni
            info = ticker.info

            # 3. Costruzione del Payload "Verboso" per l'AI
            # Pandas .to_string() formatta i dati perfettamente per la lettura da parte dell'LLM
            raw_text_payload = f"""
            === DOSSIER FINANZIARIO PER ANALISI GRAHAM: {ticker_symbol} ===
            Data Estrazione: {pd.Timestamp.now().date()}
            
            *** INFO GENERALI DI MERCATO ***
            Prezzo Corrente: {info.get('currentPrice', info.get('previousClose', 0))}
            Azioni in Circolazione: {info.get('sharesOutstanding', 0)}
            Settore: {info.get('sector', 'N/A')}
            Business Summary: {info.get('longBusinessSummary', 'N/A')}
            
            *** STORICO DIVIDENDI (Ultimi 5 anni) ***
            {divs.to_string() if not divs.empty else "Nessun dividendo recente trovato"}
            
            *** CONTO ECONOMICO (Income Statement - Storico) ***
            {inc.to_string()}
            
            *** STATO PATRIMONIALE (Balance Sheet - Storico) ***
            {bs.to_string()}
            
            *** FLUSSO DI CASSA (Cash Flow - Storico) ***
            NOTA: Utile per trovare interessi pagati o spese non monetarie.
            {cf.to_string()}
            """

            # --- FASE 1: ANALISI QUALITATIVA (Summary) ---
            print("\n" + "="*60)
            print(f" 📜 OVERVIEW STORICA DI {ticker_symbol} (Generata da AI)")
            print("="*60)
            
            # Chiediamo al SummaryAgent di leggere il testo e raccontarci la storia
            summary_text = self.summarizer.summarize_dossier(raw_text_payload)
            print(summary_text)
            print("="*60 + "\n")
            
            # --- FASE 2: ESTRAZIONE QUANTITATIVA (Builder) ---
            print(f"🧠 Passo il dossier di {ticker_symbol} all'Agente Builder per l'estrazione numerica...")
            
            # Chiediamo al DataBuilderAgent di estrarre il JSON rigoroso per i calcoli
            structured_data = self.builder.build_from_text(raw_text_payload)
            
            if structured_data:
                print(f"✅ Dati strutturati e validati per {ticker_symbol}")
                return structured_data
            else:
                return None

        except Exception as e: # pylint: disable=broad-exception-caught
            print(f"❌ Errore critico nel MarketDataAgent: {e}")
            return None

    def save_to_json(self, data: dict, filename: str):
        """Salva i dati su disco delegando al builder (che ha già la logica pronta)"""
        self.builder.save_to_json(data, filename)