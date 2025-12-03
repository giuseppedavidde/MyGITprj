"""
Modulo per l'analisi fondamentale secondo i principi di Benjamin Graham.
"""
from dataclasses import dataclass
from models.data_schema import FinancialData

@dataclass
class GrahamAnalysisResult:
    """Classe di supporto per i risultati."""
    value: float
    verdict: str
    graham_ref: str

class GrahamAgent:
    """
    Analista avanzato. Implementa il 'Metodo dei Multipli' (Parte Seconda del libro).
    """
    def __init__(self, data: FinancialData):
        self.d = data

    def analyze(self) -> str:
        """Esegue l'analisi completa con logica Debt-Free corretta."""
        
        # 1. Margine di Profitto
        profit_margin = 0.0
        if self.d.sales > 0:
            profit_margin = (self.d.operating_income / self.d.sales) * 100

        # 2. Copertura Interessi (Logic Smart)
        int_coverage_str = "N/A"
        if self.d.interest_charges > 0:
            int_cov_val = self.d.operating_income / self.d.interest_charges
            int_coverage_str = f"{int_cov_val:.2f}x"
            int_judgement = "ECCELLENTE" if int_cov_val > 5 else "ADEGUATO" if int_cov_val > 3 else "RISCHIOSO"
        else:
            # Se interessi sono 0, controlliamo se c'è debito
            if self.d.long_term_debt == 0:
                int_coverage_str = "∞ (Debt Free)"
                int_judgement = "ECCELLENTE (Nessun Debito Finanziario)"
            else:
                # Debito c'è ma interessi 0? Strano, ma matematicamente ∞
                int_coverage_str = "∞ (Interessi Zero)"
                int_judgement = "DA VERIFICARE"

        # 3. Current Ratio
        curr_ratio = 0.0
        if self.d.current_liabilities > 0:
            curr_ratio = self.d.current_assets / self.d.current_liabilities

        # 4. Quick Ratio
        quick_assets = self.d.current_assets - self.d.inventory
        quick_ratio = 0.0
        if self.d.current_liabilities > 0:
            quick_ratio = quick_assets / self.d.current_liabilities

        # 5. Book Value (Tangibile)
        equity = self.d.common_stock + self.d.surplus
        tangible_equity = equity - self.d.intangible_assets
        bv_share = 0.0
        if self.d.shares_outstanding > 0:
            bv_share = tangible_equity / self.d.shares_outstanding

        pb_ratio = 0.0
        if bv_share > 0:
            pb_ratio = self.d.current_market_price / bv_share
        
        # 6. Struttura del Capitale (CORRETTA)
        # Graham Cap. 27: Obbligazioni / (Obbligazioni + Equity)
        # Usiamo Long Term Debt invece di Total Liabilities per escludere i fornitori.
        capitalization_base = self.d.long_term_debt + equity
        debt_ratio = 0.0
        if capitalization_base > 0:
            debt_ratio = (self.d.long_term_debt / capitalization_base) * 100

        # 7. P/E Ratio
        eps = 0.0
        pe_ratio = 0.0
        if self.d.shares_outstanding > 0:
            eps = (self.d.net_income - self.d.preferred_dividends) / self.d.shares_outstanding
        if eps > 0:
            pe_ratio = self.d.current_market_price / eps

        # 8. Earnings Yield
        earnings_yield = 0.0
        if self.d.current_market_price > 0:
            earnings_yield = (eps / self.d.current_market_price) * 100

        return f"""
        === ANALISI BENJAMIN GRAHAM (Refined) ===
        
        [SICUREZZA FINANZIARIA]
        0. MARGINE DI PROFITTO [cite: 920]
           Valore: {profit_margin:.2f}%
           Giudizio: {('BUONO' if profit_margin > 10 else 'ADEGUATO' if profit_margin > 5 else 'BASSO')}
        
        1. COPERTURA INTERESSI [cite: 940]
           Valore: {int_coverage_str}
           Giudizio: {int_judgement}
           
        2. STRUTTURA DEL CAPITALE (Debito Finanziario) [cite: 986]
           Incidenza Bonds/Debito Lungo: {debt_ratio:.1f}%  <-- (Ora esclude debiti operativi)
           Graham: "Ottimale sotto il 25-30% per industriali"
           Valore Debito LP: ${self.d.long_term_debt:,.0f}
           
        3. LIQUIDITÀ (Capitale Circolante) [cite: 1003]
           Current Ratio: {curr_ratio:.2f} (Target > 2.0)
           Quick Ratio:   {quick_ratio:.2f} (Target > 1.0)
           
        [VALUTAZIONE PREZZO]
        4. P/E RATIO (TTM) [cite: 1015]
           Valore: {pe_ratio:.2f}x
           Utile per Azione (EPS): ${eps:.2f}
           Earnings Yield: {earnings_yield:.2f}%
           Graham: "Sopra 15x si paga un premio per la crescita futura"
           
        5. ASSET TANGIBILI [cite: 1010]
           Book Value Tangibile: ${bv_share:.2f}
           Prezzo/Book Value:    {pb_ratio:.2f}x
           
        Note:
        - Il calcolo del debito esclude ora le passività correnti (fornitori) conformemente al cap. 22.
        - L'EPS è basato sui dati TTM (ultimi 12 mesi).
        """