"""
Modulo per l'interpretazione dei dati finanziari tramite AI.
"""
import json
from dataclasses import asdict
from typing import Optional, Dict, Any
from models.data_schema import FinancialData
from .ai_provider import AIProvider

class DataBuilderAgent:
    """
    Agente Builder con istruzioni raffinate sul Debito Finanziario.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.model = None
        try:
            self.provider = AIProvider(api_key)
            self.model = self.provider.get_model(json_mode=True)
        except Exception as e: # pylint: disable=broad-exception-caught
            print(f"⚠️ Init DataBuilder fallita: {e}")

    def build_from_text(self, raw_text: str) -> Optional[Dict[str, Any]]:
        """Costruisce un dizionario di dati finanziari da testo grezzo."""
        if not self.model:
            return None

        print("🧠 L'Agente Builder sta isolando il Debito Finanziario dai dati...")

        prompt = f"""
        Sei un esperto analista contabile "Graham-style". 
        Estrai i dati TTM e Balance Sheet (MRQ).
        
        SCHEMA OUTPUT:
        {{
            "total_assets": float, "current_assets": float, "current_liabilities": float,
            "inventory": float, "intangible_assets": float, "total_liabilities": float,
            "long_term_debt": float,  // NUOVO CAMPO CRUCIALE
            "preferred_stock": float, "common_stock": float, "surplus": float,
            "sales": float, "operating_income": float, "net_income": float,
            "interest_charges": float, "preferred_dividends": float,
            "shares_outstanding": float, "current_market_price": float
        }}

        REGOLE ESTRAZIONE:
        1. **long_term_debt**: Cerca "Long Term Debt" o "Long Term Debt excluding Current Portion". 
           NON includere "Total Liabilities". Se l'azienda è "Debt Free", metti 0.0.
           (Nota: Leases/Affitti vanno in liabilities ma idealmente non in Long Term Debt finanziario, se separabili).
        2. **total_liabilities**: Questa invece è la somma di TUTTO (Fornitori, Debiti, Affitti).
        3. **Interest Charges**: Sempre valore assoluto.
        4. **TTM**: Priorità ai dati TTM_CALCULATED per Income Statement.

        DOSSIER:
        {raw_text}
        """

        try:
            response = self.model.generate_content(prompt)
            if not response or not hasattr(response, 'text'): return None

            data_dict = json.loads(response.text)
            validated_data = FinancialData(**data_dict)
            return asdict(validated_data)

        except Exception as e: # pylint: disable=broad-exception-caught
            print(f"❌ Errore DataBuilder: {e}")
            return None

    def save_to_json(self, data: Dict[str, Any], filename: str):
        """Salva i dati finanziari in un file JSON."""
        # (Codice salvataggio invariato...)
        import os
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        file_path = os.path.join(base_dir, 'data', filename)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)
        print(f"💾 File salvato: {file_path}")