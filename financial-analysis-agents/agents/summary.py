"""Agente responsabile della generazione di riassunti qualitativi da dossier finanziari grezzi."""
from typing import Optional
from .ai_provider import AIProvider

class SummaryAgent:
    """
    Agente "Narratore". 
    Usa AIProvider per ottenere un modello e generare riassunti qualitativi.
    """
    def __init__(self, api_key: Optional[str] = None):
        self.model = None
        try:
            # Chiediamo al Provider un modello standard (testo libero)
            self.provider = AIProvider(api_key)
            self.model = self.provider.get_model(json_mode=False)
        except Exception as e: # pylint: disable=broad-exception-caught
            print(f"⚠️ Attenzione: Inizializzazione AI fallita in SummaryAgent: {e}")

    def summarize_dossier(self, raw_text_dossier: str) -> str:
        """
        Genera un riassunto discorsivo focalizzato sui principi di Graham.
        """
        if not self.model:
            return "⚠️ Impossibile generare riassunto: Modello AI non disponibile."

        print("📜 Il SummaryAgent sta analizzando la storia aziendale...")

        prompt = f"""
        Sei un assistente analista finanziario (Metodo Graham).
        Analizza questo Dossier Finanziario (bilanci 4 anni, flussi, dividendi).

        Scrivi un RIASSUNTO DISCORSIVO (max 12 righe) su:
        1. **Business**: Cosa fa l'azienda?
        2. **Trend Utili**: Stabili, in crescita o calo? (Fondamentale per Graham).
        3. **Dividendi**: Regolari? In crescita?
        4. **Salute Finanziaria**: Debito eccessivo o sotto controllo?
        5. **Note**: Eventuali perdite o anomalie recenti.

        DOSSIER GREZZO:
        {raw_text_dossier}
        """

        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e: # pylint: disable=broad-exception-caught
            return f"Errore nella generazione del riassunto: {e}"