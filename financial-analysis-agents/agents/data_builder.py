"""Agente responsabile della costruzione di dati finanziari strutturati da testo grezzo."""
from typing import Optional
import json
from dataclasses import asdict
from models.data_schema import FinancialData
from .ai_provider import AIProvider

class DataBuilderAgent:
    """
    Agente responsabile della trasformazione di testo grezzo in dati strutturati.
    Usa AIProvider per ottenere il modello migliore e forza l'output JSON.
    """
    def __init__(self, api_key: Optional[str] = None):
        self.model = None
        try:
            # Chiediamo al Provider un modello ottimizzato per JSON
            self.provider = AIProvider(api_key)
            self.model = self.provider.get_model(json_mode=True)
        except Exception as e: # pylint: disable=broad-exception-caught
            print(f"⚠️ Attenzione: Inizializzazione AI fallita in DataBuilder: {e}")

    def build_from_text(self, raw_text: str) -> Optional[dict]:
        """
        Analizza il testo grezzo e restituisce un dizionario validato.
        """
        if not self.model:
            print("❌ Errore: Modello AI non disponibile.")
            return None

        print("🧠 L'Agente Builder sta interpretando i dati...")

        # Prompt invariato (la logica di business resta qui)
        prompt = f"""
        Sei un esperto analista contabile "Graham-style". 
        Estrai i dati dal testo grezzo per popolare questo JSON rigoroso.
        
        SCHEMA OUTPUT:
        {{
            "total_assets": float, "current_assets": float, "current_liabilities": float,
            "inventory": float, "intangible_assets": float, "total_liabilities": float,
            "preferred_stock": float, "common_stock": float, "surplus": float,
            "sales": float, "operating_income": float, "net_income": float,
            "interest_charges": float, "preferred_dividends": float,
            "shares_outstanding": float, "current_market_price": float
        }}

        REGOLE CRITICHE:
        1. **Interest Charges**: Usa SEMPRE il valore ASSOLUTO (positivo).
        2. **Intangibles**: Somma Goodwill e altri intangibili.
        3. **Notazione**: Converti 4.5e9 in 4500000000.0.
        4. **Date**: Prendi i dati della colonna più recente (Current).
        5. Usa 0.0 per dati mancanti.

        DOSSIER DA ANALIZZARE:
        {raw_text}
        """

        try:
            response = self.model.generate_content(prompt)
            data_dict = json.loads(response.text)
            
            # Validazione (FinancialData correggerà i segni negativi grazie al post_init)
            validated_data = FinancialData(**data_dict)
            return asdict(validated_data)

        except json.JSONDecodeError:
            print("❌ Errore: L'AI non ha prodotto un JSON valido.")
            return None
        except TypeError as e:
            print(f"❌ Errore Schema: Dati non conformi.\n{e}")
            return None
        except Exception as e: # pylint: disable=broad-exception-caught
            print(f"❌ Errore Generico AI: {e}")
            return None

    def save_to_json(self, data: dict, filename: str):
        """Salva su disco UTF-8"""
        import os
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        file_path = os.path.join(base_dir, 'data', filename)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)
        print(f"💾 File salvato: {file_path}")