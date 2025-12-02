"""Definizione della struttura dati per i valori finanziari standardizzati."""
from dataclasses import dataclass

@dataclass
class FinancialData:
    """
    Struttura dati standardizzata per i valori di bilancio.
    Include validazione automatica post-inizializzazione.
    """
    # Stato Patrimoniale
    total_assets: float
    current_assets: float
    current_liabilities: float
    inventory: float
    intangible_assets: float
    total_liabilities: float
    
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
        """
        Questo metodo viene eseguito automaticamente subito dopo la creazione dell'oggetto.
        Lo usiamo per garantire che i dati siano conformi alle aspettative di Graham.
        """
        # 1. FIX INTERESSI: Graham usa sempre il valore assoluto per la copertura.
        # Se l'AI o Yahoo ci passano un negativo (es. -500), lo rendiamo positivo (500).
        self.interest_charges = abs(self.interest_charges)

        # 2. FIX INTANGIBILI: Non possono essere negativi
        self.intangible_assets = abs(self.intangible_assets)

        # 3. FIX PREZZO: Non può essere negativo
        self.current_market_price = abs(self.current_market_price)

        # 4. FIX AZIONI: Non possono essere negative
        self.shares_outstanding = abs(self.shares_outstanding)