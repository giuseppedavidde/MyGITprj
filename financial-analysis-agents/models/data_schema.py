"""Definizione della struttura dati per i valori finanziari standardizzati."""
from dataclasses import dataclass

@dataclass
class FinancialData:
    """
    Struttura dati standardizzata per i valori di bilancio.
    Include distinzione tra Passività Totali e Debito Finanziario.
    """
    # Stato Patrimoniale
    total_assets: float
    current_assets: float
    current_liabilities: float
    inventory: float
    intangible_assets: float
    total_liabilities: float
    long_term_debt: float  # Solo debiti finanziari (Bonds, Mutui), esclusi fornitori/affitti
    
    # Capitale
    preferred_stock: float
    common_stock: float
    surplus: float
    
    # Conto Economico
    sales: float
    operating_income: float
    net_income: float
    interest_charges: float
    preferred_dividends: float
    
    # Mercato
    shares_outstanding: float
    current_market_price: float

    def __post_init__(self):
        """Validazione e pulizia automatica."""
        # Fix segni
        self.interest_charges = abs(self.interest_charges)
        self.intangible_assets = abs(self.intangible_assets)
        self.current_market_price = abs(self.current_market_price)
        self.shares_outstanding = abs(self.shares_outstanding)
        self.long_term_debt = abs(self.long_term_debt) 