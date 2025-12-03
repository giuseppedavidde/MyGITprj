"""Modulo per la revisione e validazione dei dati finanziari."""
import json
from dataclasses import asdict
from typing import Tuple, List, Optional
from models.data_schema import FinancialData
from .ai_provider import AIProvider

class ReviewAgent:
    """
    Agente Auditor.
    Policy "Zero Trust": Richiede la validazione web su TUTTE le metriche critiche
    per l'analisi di Graham, non solo su quelle anomale.
    """
    def __init__(self, api_key: Optional[str] = None):
        self.provider = AIProvider(api_key)
        self.model = self.provider.get_model(json_mode=True)

    def audit_data(self, ticker: str, data: FinancialData) -> Tuple[str, List[str]]:
        """Esegue un audit sui dati finanziari e restituisce un rapporto e i campi da verificare."""
        print(f"🧐 ReviewAgent sta preparando il piano di validazione per {ticker}...")

        data_dict = asdict(data)
        
        # Definiamo i campi critici che impattano direttamente i calcoli di Graham
        graham_critical_fields = [
            'sales', 'net_income', 'operating_income', 'interest_charges',  # Per P/E e Margini
            'long_term_debt', 'total_liabilities', 'total_assets',          # Per Struttura Capitale
            'current_assets', 'current_liabilities', 'inventory',           # Per Liquidità
            'shares_outstanding', 'current_market_price'                    # Per EPS e Valutazione
        ]
        
        formatted_data = "\n".join([f"- {k}: {data_dict.get(k, 0):,.2f}" for k in graham_critical_fields])

        prompt = f"""
        Sei un Senior Auditor. Stiamo preparando i dati di {ticker} per un'analisi fondamentale rigorosa.
        Non possiamo permetterci errori o allucinazioni dell'AI sui numeri.

        DATI ESTRATTI (Da Validare):
        {formatted_data}

        COMPITO:
        Devi selezionare i campi che necessitano di una CONFERMA ESTERNA.
        Vista l'importanza dell'analisi, devi includere nella lista 'suspicious_fields' **TUTTI** i campi critici 
        sopra elencati, a meno che tu non sia matematicamente certo della loro correttezza interna 
        (es. Total Assets = Liabilities + Equity verificato al centesimo).
        
        In particolare, richiedi SEMPRE la verifica per:
        - long_term_debt (Spesso confuso con lease o total liabilities)
        - net_income (Spesso confuso con l'annuale vecchio invece del TTM)
        - interest_charges (Spesso ignorato se nel cash flow)
        - shares_outstanding (Cambia spesso con i buyback)

        OUTPUT RICHIESTO (JSON):
        {{
            "report_text": "Breve commento sulla qualità apparente dei dati pre-verifica.",
            "suspicious_fields": ["long_term_debt", "net_income", "sales", ...] 
        }}
        """

        try:
            response = self.model.generate_content(prompt)
            result = json.loads(response.text)
            
            report = result.get("report_text", "Audit completato.")
            # Se l'AI è pigra, forziamo noi la verifica dei campi vitali se la lista è vuota
            fields = result.get("suspicious_fields", [])
            if not fields:
                fields = ['long_term_debt', 'net_income', 'sales', 'interest_charges']
            
            return report, fields

        except Exception as e: # pylint: disable=broad-exception-caught
            return f"Errore Audit: {e}", []