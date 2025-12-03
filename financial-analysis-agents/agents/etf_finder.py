"""Agente ibrido per trovare ETF che detengono un dato titolo."""
from typing import List, Dict, Any, Optional
import json
import yfinance as yf
from .ai_provider import AIProvider

class ETFFinderAgent:
    """
    Agente ibrido che trova gli ETF che detengono un determinato titolo.
    
    Strategia:
    1. Usa l'AI per dedurre quali ETF contengono probabilmente il titolo (basandosi su settore e fama).
    2. Usa yfinance per scaricare i dati reali di quegli ETF (Total Assets/AUM).
    3. Combina le stime di peso dell'AI con i dati finanziari reali.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.provider = AIProvider(api_key)
        # Usiamo il modello JSON per avere una lista pulita
        self.model = self.provider.get_model(json_mode=True)

    def find_etfs_holding_ticker(self, ticker: str, sector: str = "Unknown") -> List[Dict[str, Any]]:
        """Trova ETF che detengono il titolo specificato."""
        print(f"🔎 ETFFinder sta cercando esposizione ETF per {ticker}...")
        
        # 1. Chiediamo all'AI i candidati
        candidates = self._get_candidates_from_ai(ticker, sector)
        
        if not candidates:
            return []

        results = []
        print(f"   ↳ Analisi dati di mercato per {len(candidates)} ETF candidati...")

        # 2. Arricchiamo con dati reali da Yahoo Finance
        for etf_data in candidates:
            etf_ticker = etf_data.get("ticker")
            
            try:
                # Chiamata a Yahoo Finance
                yf_obj = yf.Ticker(etf_ticker)
                info = yf_obj.info
                
                # Estraiamo Total Assets (AUM)
                # Yahoo a volte usa 'totalAssets', a volte 'assets', a volte manca
                total_assets = info.get("totalAssets", 0)
                
                if total_assets and total_assets > 0:
                    # Formattiamo in Miliardi (B) o Milioni (M)
                    if total_assets > 1_000_000_000:
                        aum_str = f"${total_assets / 1_000_000_000:.2f}B"
                    else:
                        aum_str = f"${total_assets / 1_000_000:.2f}M"
                        
                    results.append({
                        "etf_ticker": etf_ticker,
                        "etf_name": info.get("longName", info.get("shortName", "N/A")),
                        "total_aum": aum_str,
                        "weight_percentage": etf_data.get("estimated_weight", "N/A"),
                        "category": info.get("category", "N/A")
                    })
            except Exception:  # pylint: disable=broad-exception-caught 
                # Se un ETF non viene trovato o Yahoo fallisce, lo saltiamo
                continue

        return results

    def _get_candidates_from_ai(self, ticker: str, sector: str) -> List[Dict]:
        """Chiede all'AI una lista di 5 probabili ETF."""
        prompt = f"""
        Sei un esperto di ETF e Asset Management.
        Identifica 5 principali ETF (Exchange Traded Funds) statunitensi che sicuramente detengono il titolo {ticker} ({sector}).
        
        Includi:
        1. ETF Generali (es. S&P 500) se applicabile.
        2. ETF Settoriali specifici per {sector}.
        
        Restituisci ESCLUSIVAMENTE un JSON con questa struttura:
        [
            {{ "ticker": "SPY", "estimated_weight": "6.5%" }},
            {{ "ticker": "QQQ", "estimated_weight": "8.2%" }}
        ]
        
        Fornisci una stima realistica del peso percentuale (weight) basata sulla tua conoscenza.
        """
        
        try:
            response = self.model.generate_content(prompt)
            data = json.loads(response.text)
            return data if isinstance(data, list) else []
        except Exception as e: # pylint: disable=broad-exception-caught
            print(f"⚠️ Errore AI nel trovare ETF: {e}")
            return []