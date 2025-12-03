"""Agente responsabile del recupero dati da Yahoo Finance."""
from typing import Optional
from dataclasses import asdict
import yfinance as yf
import pandas as pd
from models.data_schema import FinancialData            
from .data_builder import DataBuilderAgent
from .summary import SummaryAgent
from .review import ReviewAgent
from .etf_finder import ETFFinderAgent
from .cross_check import CrossCheckAgent

class MarketDataAgent:
    """
    Agente coordinatore (Facade).
    Gestisce il flusso: Download -> Summary -> Build -> Review.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.builder = DataBuilderAgent(api_key=api_key)
        self.summarizer = SummaryAgent(api_key=api_key)
        self.reviewer = ReviewAgent(api_key=api_key)
        self.etf_finder = ETFFinderAgent(api_key=api_key)
        self.cross_checker = CrossCheckAgent(api_key=api_key)

    def fetch_from_ticker(self, ticker_symbol: str) -> Optional[dict]:
        """Recupera e processa i dati finanziari per il ticker specificato."""
        print(f"📈 Recupero DOSSIER COMPLETO (TTM) per {ticker_symbol}...")
        
        try:
            ticker = yf.Ticker(ticker_symbol)
            
            # --- 1. DATI TRIMESTRALI (Per calcolo TTM) ---
            q_inc = ticker.quarterly_financials
            q_cf = ticker.quarterly_cashflow
            q_bs = ticker.quarterly_balance_sheet # Per lo stato patrimoniale serve l'ultimo, non la somma
            
            if q_inc.empty:
                print(f"❌ Dati trimestrali non disponibili per {ticker_symbol}. Impossibile calcolare TTM.")
                return None

            # --- 2. COSTRUZIONE TTM (Trailing Twelve Months) ---
            # Sommiamo le ultime 4 colonne disponibili (4 trimestri) per il Conto Economico
            # Se ci sono meno di 4 colonne, sommiamo quelle che ci sono
            cols_to_sum = q_inc.columns[:4] 
            
            # Calcolo TTM per Income Statement (Somma)
            ttm_income = q_inc[cols_to_sum].sum(axis=1).to_frame(name="TTM_CALCULATED")
            
            # Calcolo TTM per Cash Flow (Somma)
            ttm_cashflow = q_cf[q_cf.columns[:4]].sum(axis=1).to_frame(name="TTM_CALCULATED")
            
            # Per il Balance Sheet NON si somma, si prende l'ultimo disponibile (MRQ - Most Recent Quarter)
            mrq_balance_sheet = q_bs.iloc[:, 0].to_frame(name="MRQ_LATEST_SNAPSHOT")

            # --- 3. Dati Mercato e Dividendi ---
            divs = ticker.dividends.tail(20)
            info = ticker.info
            sector = info.get('sector', 'Unknown')
            current_price = info.get('currentPrice', info.get('previousClose', 0))

            # --- 4. COSTRUZIONE PAYLOAD ---
            # Creiamo un testo che forza l'AI a guardare la colonna TTM
            raw_text_payload = f"""
            === DOSSIER FINANZIARIO AGGIORNATO (TTM): {ticker_symbol} ===
            Data Analisi: {pd.Timestamp.now().date()}
            
            *** INFO MERCATO ***
            Prezzo Attuale: {current_price}
            Azioni in Circolazione: {info.get('sharesOutstanding', 0)}
            Settore: {sector}
            
            *** ISTRUZIONI PER L'AI ***
            IMPORTANTE: Per 'Net Income', 'Sales', 'EBIT', usa la colonna 'TTM_CALCULATED' qui sotto.
            Questa colonna rappresenta la somma degli ultimi 4 trimestri ed è fondamentale per un P/E corretto.
            
            *** CONTO ECONOMICO (Income Statement - TTM & Storico Trimestrale) ***
            {ttm_income.to_string()}
            --- Dettaglio Trimestrale ---
            {q_inc.iloc[:, :4].to_string()}
            
            *** STATO PATRIMONIALE (Balance Sheet - Ultimo Trimestre MRQ) ***
            NOTA: Usa questi valori per Assets, Liabilities, Debt.
            {mrq_balance_sheet.to_string()}
            
            *** FLUSSO DI CASSA (Cash Flow - TTM) ***
            {ttm_cashflow.to_string()}
            
            *** DIVIDENDI RECENTI ***
            {divs.to_string() if not divs.empty else "Nessun dividendo recente"}
            """

            # --- FASE 1: SUMMARY ---
            print("\n" + "="*60)
            print("📜 OVERVIEW (Focus su TTM/Trend Recenti)")
            print("="*60)
            print(self.summarizer.summarize_dossier(raw_text_payload))
            print("="*60 + "\n")
            
            # --- FASE 1.5: ETF FINDER ---
            print("\n" + "-"*60)
            print("🏦 ANALISI ESPOSIZIONE ETF")
            print("-"*60)
            etf_list = self.etf_finder.find_etfs_holding_ticker(ticker_symbol, sector)
            if etf_list:
                print(f"{'ETF Ticker':<10} {'AUM':<15} {'Peso Stimato':<15} {'Nome ETF'}")
                print("-" * 70)
                for etf in etf_list:
                    print(f"{etf['etf_ticker']:<10} {etf['total_aum']:<15} {etf['weight_percentage']:<15} {etf['etf_name'][:30]}...")
            else:
                print("Nessun ETF principale rilevato.")
            print("-" * 60 + "\n")

            # --- FASE 2: BUILDER ---
            print("🧠 Estrazione dati TTM in corso...")
            structured_data_dict = self.builder.build_from_text(raw_text_payload)
            
            if not structured_data_dict: 
                return None

            fin_data_obj = FinancialData(**structured_data_dict)

            # --- FASE 3: REVISIONE & AUTO-CORREZIONE ---
            print("\n" + "-"*60)
            print("🧐 AUDIT AUTOMATICO")
            
            # Il ReviewAgent ora ci dice COSA non va
            audit_report, suspicious_fields = self.reviewer.audit_data(ticker_symbol, fin_data_obj)
            print(f"\nREPORT: {audit_report}")
            
            if suspicious_fields:
                print(f"⚠️ Rilevate anomalie in: {suspicious_fields}. Avvio Cross-Check Web...")
                
                # Chiamiamo l'agente investigativo
                corrections = self.cross_checker.cross_check_fields(
                    ticker_symbol, 
                    asdict(fin_data_obj), 
                    suspicious_fields
                )
                
                if corrections:
                    # Applichiamo le correzioni al dizionario
                    print("🛠️ Applicazione correzioni web ai dati finali...")
                    structured_data_dict.update(corrections)
                    # Ricreiamo l'oggetto pulito
                    fin_data_obj = FinancialData(**structured_data_dict)
            else:
                print("✅ Nessuna anomalia critica rilevata che richieda web search.")
                
            print("-" * 60 + "\n")

            return asdict(fin_data_obj)

        except Exception as e: # pylint: disable=broad-exception-caught
            print(f"❌ Errore critico nel MarketDataAgent: {e}")
            return None

    def save_to_json(self, data: dict, filename: str):
        """Salva i dati strutturati in un file JSON."""
        self.builder.save_to_json(data, filename)