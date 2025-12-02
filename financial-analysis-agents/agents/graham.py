"""Agente di analisi finanziaria basato sui principi di Benjamin Graham."""
from dataclasses import dataclass
from models.data_schema import FinancialData

@dataclass
class GrahamAnalysisResult:
    """Struttura per i risultati dell'analisi di Graham."""
    value: float
    verdict: str
    graham_ref: str  # Riferimento al principio del libro

class GrahamAgent:
    """
    Analista avanzato basato su 'Leggere e capire i bilanci'.
    Implementa il 'Metodo dei Multipli' descritto nella Parte Seconda del libro.
    """
    def __init__(self, data: FinancialData):
        self.d = data
        # Assicuriamoci che gli oneri siano positivi per i calcoli dei rapporti
        self.d.interest_charges = abs(self.d.interest_charges)

    def analyze(self) -> str:
        """Esegue l'analisi completa stile 'Parte Seconda' del libro."""
        
        # --- CALCOLI FONDAMENTALI (Basati sui capitoli del libro) ---

        # 1. Margine di Profitto (Margin of Profit)
        # Rif: [cite: 928] "Reddito operativo diviso per le vendite"
        profit_margin = 0.0
        if self.d.sales > 0:
            profit_margin = (self.d.operating_income / self.d.sales) * 100

        # 2. Indice di Copertura Interessi (Times Interest Charges Earned)
        # Rif: [cite: 940] "Totale ricavi diviso per gli interessi"
        # Graham richiede > 2.5x per la media, > 3x per industriali sicure [cite: 942]
        int_coverage = 0.0
        # Usiamo Reddito Operativo come proxy di "Totale Ricavi" (disponibili per oneri)
        if self.d.interest_charges > 0:
            int_coverage = self.d.operating_income / self.d.interest_charges
        else:
            int_coverage = 999.0  # Nessun debito, sicurezza massima

        # 3. Indice di Liquidità (Current Ratio)
        # Rif: [cite: 1004] "Attivo corrente diviso per passivo corrente"
        # Standard minimo industriali: 2 a 1 
        curr_ratio = 0.0
        if self.d.current_liabilities > 0:
            curr_ratio = self.d.current_assets / self.d.current_liabilities

        # 4. Indice di Liquidità Immediata (Quick/Acid Test)
        # Rif: [cite: 1008] "(Attivo corrente - scorte) / Passivo corrente"
        # Obiettivo: 1 a 1 [cite: 1009]
        quick_assets = self.d.current_assets - self.d.inventory
        quick_ratio = 0.0
        if self.d.current_liabilities > 0:
            quick_ratio = quick_assets / self.d.current_liabilities

        # 5. Valore Contabile Tangibile per Azione (Book Value)
        # Rif: [cite: 1010, 1012] "Escludere attivi intangibili (avviamento, brevetti)"
        equity = self.d.common_stock + self.d.surplus
        tangible_equity = equity - self.d.intangible_assets
        bv_share = 0.0
        if self.d.shares_outstanding > 0:
            bv_share = tangible_equity / self.d.shares_outstanding

        # 6. Rapporto Prezzo/Valore Contabile (Price to Book)
        # Non esplicitato come formula unica ma discusso nel cap. 21 [cite: 656-658]
        pb_ratio = 0.0
        if bv_share > 0:
            pb_ratio = self.d.current_market_price / bv_share
        
        # 7. Struttura del Capitale (Capitalization)
        # Rif: [cite: 985-997] Rapporto tra Obbligazioni e Capitale Totale
        # "Una normale azienda industriale non dovrebbe avere molto più del 25-30% in obbligazioni" [cite: 998]
        total_capitalization = self.d.total_liabilities + equity # Approx Debito + Equity
        debt_ratio = 0.0
        if total_capitalization > 0:
            # Usiamo total_liabilities come proxy del debito finanziato per prudenza
            debt_ratio = (self.d.total_liabilities / total_capitalization) * 100

        # 8. P/E Ratio
        # Rif: [cite: 1015] "Prezzo diviso utili per azione"
        # Graham nota: < 15 per aziende stabili, > 15 sconta crescita futura [cite: 868]
        eps = 0.0
        pe_ratio = 0.0
        if self.d.shares_outstanding > 0:
            eps = (self.d.net_income - self.d.preferred_dividends) / self.d.shares_outstanding
        if eps > 0:
            pe_ratio = self.d.current_market_price / eps

        # 9. Earnings Yield (Rendimento degli Utili)
        # Rif: [cite: 1191] "Rapporto tra utile annuo e prezzo (inverso del P/E)"
        # Utile per confrontare l'azione con un'obbligazione
        earnings_yield = 0.0
        if self.d.current_market_price > 0:
            earnings_yield = (eps / self.d.current_market_price) * 100

        # --- GENERAZIONE REPORT ---
        
        return f"""
        === ANALISI APPROFONDITA BENJAMIN GRAHAM ===
        Data source: Bilancio Aziendale
        
        [SEZIONE A: SICUREZZA E SOLIDITÀ]
        
        1. COPERTURA INTERESSI (Interest Coverage) [cite: 940]
           Valore: {int_coverage:.2f}x
           Graham: "Minimo 3 volte per industriali sicure" 
           Giudizio: {"ECCELLENTE" if int_coverage > 5 else "ADEGUATO" if int_coverage > 3 else "RISCHIOSO"}
           
        2. CAPITALE CIRCOLANTE (Liquidità)
           Current Ratio: {curr_ratio:.2f} (Target Graham > 2.0) 
           Quick Ratio:   {quick_ratio:.2f} (Target Graham > 1.0) [cite: 1009]
           Giudizio: {"SOLIDO" if curr_ratio >= 1.5 else "TIRATO - L'azienda opera con poca cassa rispetto ai debiti brevi"}
           *Nota: Aziende moderne efficienti possono operare sotto 2.0, ma Graham predilige ampi margini di sicurezza.
        
        3. STRUTTURA DEL CAPITALE [cite: 998]
           Incidenza del Debito Totale: {debt_ratio:.1f}%
           Graham: "Non molto più del 25-30% in obbligazioni/debiti"
           
        ------------------------------------------------
        
        [SEZIONE B: REDDITIVITÀ E PREZZO]
        
        4. PERFORMANCE OPERATIVA
           Margine di Profitto: {profit_margin:.2f}% [cite: 928]
           (Indica l'efficienza gestionale: {profit_margin:.2f} centesimi guadagnati per ogni dollaro di vendite)
           
        5. VALUTAZIONE DI MERCATO
           Prezzo Attuale:   ${self.d.current_market_price:.2f}
           EPS (Utile/Az):   ${eps:.2f}
           P/E Ratio:        {pe_ratio:.2f}x
           Earnings Yield:   {earnings_yield:.2f}% (Rendimento teorico se l'azienda distribuisse tutto l'utile) [cite: 1191]
           
           Graham sul P/E:
           - P/E < 15: Tipico di aziende stabili o sottovalutate [cite: 868]
           - P/E > 15: Il mercato sconta una forte crescita futura (Speculativo) [cite: 868]
           
        6. ANALISI ASSET TANGIBILI (Book Value)
           Valore Contabile Tangibile: ${bv_share:.2f} per azione
           Prezzo su Book Value:       {pb_ratio:.2f}x
           
           Analisi Intangibili:
           L'azienda ha ${self.d.intangible_assets:,.0f} in intangibili (Avviamento, Brevetti).
           Graham avverte: "Dare poco o nessun peso alle cifre degli attivi immateriali".
           Il premio pagato sul Book Value ({pb_ratio:.2f}x) rappresenta la fiducia del mercato nel brand e nella crescita futura.
        """