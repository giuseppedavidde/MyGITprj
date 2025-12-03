"""
Modulo per l'interpretazione dei dati finanziari tramite AI.
"""
import json
import os
from dataclasses import asdict
from typing import Optional, Dict, Any
from models.data_schema import FinancialData
from .ai_provider import AIProvider

class DataBuilderAgent:
    """Costruisce un dizionario di dati finanziari da testo grezzo usando l'AI."""
    
    def __init__(self, api_key: Optional[str] = None):
        self.model = None
        try:
            self.provider = AIProvider(api_key)
            self.model = self.provider.get_model(json_mode=True)
        except Exception as e: # pylint: disable=broad-exception-caught
            print(f"⚠️ Attenzione: Inizializzazione AI fallita in DataBuilder: {e}")

    def build_from_text(self, raw_text: str) -> Optional[Dict[str, Any]]:
        """Estrae i dati finanziari dal testo grezzo e li restituisce come dizionario."""
        if not self.model:
            print("❌ Errore: Modello AI non disponibile.")
            return None

        print("🧠 L'Agente Builder sta analizzando i criteri di 'L'Investitore Intelligente'...")

        prompt = f"""
        Sei un esperto analista formato sui libri di Benjamin Graham.
        Estrai i dati dal testo per popolare il JSON.
        
        SCHEMA OUTPUT RICHIESTO:
        {{
            "total_assets": float, "current_assets": float, "current_liabilities": float,
            "inventory": float, "intangible_assets": float, "total_liabilities": float,
            "long_term_debt": float, "preferred_stock": float, "common_stock": float, 
            "surplus": float, "sales": float, "operating_income": float, "net_income": float,
            "interest_charges": float, "preferred_dividends": float, "shares_outstanding": float, 
            "current_market_price": float,
            
            // NUOVI CAMPI STORICI (Stime basate sui dati presenti):
            "eps_3y_avg": float,         // Media utile netto / azioni degli ultimi 3 anni
            "earnings_growth_10y": bool, // True se utili oggi > utili di anni fa (trend positivo)
            "dividend_history_20y": bool // True se sembra pagare dividendi regolarmente
        }}

        REGOLE CRITICHE:
        1. **Debito**: 'long_term_debt' deve essere SOLO il debito finanziario (Bonds/Prestiti). Escludi affitti/fornitori.
        2. **Media 3 Anni**: Per 'eps_3y_avg', guarda la tabella storica nel testo. Fai una media approssimativa degli ultimi 3 anni di Net Income diviso le azioni attuali. Se hai solo TTM, usa quello.
        3. **Dividendi**: Se vedi una storia di dividendi nel testo, imposta 'dividend_history_20y' a true.
        4. **TTM**: Per i dati correnti (sales, income), usa TTM_CALCULATED.

        DOSSIER:
        {raw_text}
        """

        try:
            response = self.model.generate_content(prompt)
            if not response or not hasattr(response, 'text'): return None

            data_dict = json.loads(response.text)
            validated_data = FinancialData(**data_dict)
            return asdict(validated_data)

        except json.JSONDecodeError:
            print("❌ Errore: L'AI non ha prodotto un JSON valido.")
            return None
        except TypeError as e:
            print(f"❌ Errore Schema: Dati non conformi.\n{e}")
            return None
        except Exception as e: # pylint: disable=broad-exception-caught
            print(f"❌ Errore Generico AI in DataBuilder: {e}")
            return None

    def save_to_json(self, data: Dict[str, Any], filename: str):
        """Salva i dati finanziari in un file JSON."""
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        file_path = os.path.join(base_dir, 'data', filename)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)
        print(f"💾 File salvato: {file_path}")