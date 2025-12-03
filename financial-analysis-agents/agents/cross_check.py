"""Agente di verifica incrociata tramite Finviz e Web Search."""
import json
import datetime
from typing import Dict, Any, List, Optional
from ddgs import DDGS # type: ignore
from .ai_provider import AIProvider
from .finviz import FinvizAgent  # <--- Usiamo il nuovo agente

class CrossCheckAgent:
    """
    Agente Investigativo Ibrido.
    1. Consulta Finviz (Dati strutturati affidabili).
    2. Se necessario, consulta il Web generico (DDGS).
    """
    def __init__(self, api_key: Optional[str] = None):
        self.provider = AIProvider(api_key)
        self.model = self.provider.get_model(json_mode=True)
        self.finviz = FinvizAgent() # <--- Init Finviz

    def cross_check_fields(self, ticker: str, original_data: Dict[str, Any], fields_to_check: List[str]) -> Dict[str, Any]:
        """Validazione incrociata dei campi specificati nei dati finanziari."""
        if not fields_to_check:
            return {}

        print(f"🕵️‍♂️ CrossCheckAgent: Validazione dati per {ticker} su {len(fields_to_check)} campi...")
        
        corrections = {}
        
        # --- FASE 1: CONSULTAZIONE FINVIZ ---
        finviz_data = self.finviz.get_fundamental_data(ticker)
        finviz_context = ""
        
        if finviz_data:
            print("   ✅ Dati Finviz acquisiti con successo.")
            # Convertiamo il dizionario Finviz in una stringa leggibile per l'AI
            # Selezioniamo solo chiavi rilevanti per risparmiare token
            relevant_keys = ['P/E', 'Forward P/E', 'Sales', 'Income', 'Debt/Eq', 'LT Debt/Eq', 
                             'Total Debt', 'Book/sh', 'Cash/sh', 'Dividend', 'Dividend %']
            
            finviz_subset = {k: finviz_data.get(k, 'N/A') for k in relevant_keys}
            finviz_context = f"DATI UFFICIALI FINVIZ (Fonte Primaria):\n{json.dumps(finviz_subset, indent=2)}"
        else:
            print("   ⚠️ Finviz non disponibile, procedo solo con Web Search.")

        # --- FASE 2: WEB SEARCH (Fallback / Integrazione) ---
        # Se mancano dati critici o per conferma ulteriore
        web_context = ""
        search_tool = DDGS()
        current_year = datetime.date.today().year
        
        # Cerchiamo solo se Finviz non ha risposto o per campi molto specifici non in tabella
        if not finviz_data or "long_term_debt" in fields_to_check:
            query = f"{ticker} total long term debt {current_year} is debt free balance sheet"
            print(f"   🌐 Query Web Integrativa: '{query}'")
            try:
                results = list(search_tool.text(keywords=query, max_results=2)) # pyright: ignore
                web_context = "\n\n".join([f"Web Snippet: {r.get('body', '')}" for r in results])
            except Exception: # pylint: disable=broad-exception-caught
                pass

        # --- FASE 3: ARBITRAGGIO AI ---
        suspicious_data_subset = {k: original_data.get(k) for k in fields_to_check}

        prompt = f"""
        Sei un Revisore Contabile. Valida i dati di {ticker}.
        
        DATI DA VERIFICARE (Estratti dai report):
        {json.dumps(suspicious_data_subset, indent=2)}

        FONTI DI VERITÀ:
        1. {finviz_context}
        2. DATI WEB SUPPLEMENTARI:
           {web_context}

        REGOLE DI VALIDAZIONE:
        1. **Finviz è l'autorità**. Se Finviz dice 'LT Debt/Eq' = 0.00, allora 'long_term_debt' è 0 o trascurabile.
        2. **Mapping Finviz**:
           - 'Income' -> Net Income
           - 'Sales' -> Sales / Revenue
           - 'Total Debt' (se presente) o dedotto da Debt/Eq -> Long Term Debt
        3. **GME Case**: Se Finviz o Web confermano "Debt Free" o debiti minimi, correggi long_term_debt a 0.0.
        4. **Date**: I dati Finviz sono "Current/TTM". Usali per correggere dati vecchi.

        OUTPUT JSON:
        Restituisci un dizionario con i valori corretti.
        {{
            "long_term_debt": 0.0,
            "net_income": 15000000.0
        }}
        """

        try:
            response = self.model.generate_content(prompt)
            if not response or not hasattr(response, 'text'): 
                return {}

            corrections_json = json.loads(response.text)
            
            for k, v in corrections_json.items():
                if k not in fields_to_check: 
                    continue
                
                orig = original_data.get(k, 0)
                # Calcola diff solo se entrambi sono numeri
                try:
                    diff_pct = abs(v - orig) / (abs(orig) + 1)
                except TypeError:
                    diff_pct = 1.0 # Force update se tipi diversi

                if (orig == 0 and v != 0) or diff_pct > 0.1:
                    source = "Finviz" if finviz_data else "Web"
                    print(f"   ✅ CORRETTO {k}: {orig:,.0f} -> {v:,.0f} (Fonte: {source})")
                    corrections[k] = v
                else:
                    # print(f"   🆗 CONFERMATO {k}") # Verbose off
                    pass

        except Exception as e: # pylint: disable=broad-exception-caught
            print(f"⚠️ Errore Arbitraggio AI: {e}")
        
        return corrections