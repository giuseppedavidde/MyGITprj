"""Module providing a function printing python version."""
import os
from dotenv import load_dotenv
from utils import load_company_data
# Importiamo la classe dati per convertire il dict in oggetto
from models import FinancialData
# Importiamo tutti gli agent necessari
from agents import GrahamAgent, DataBuilderAgent, MarketDataAgent

# Carica le variabili dal file .env all'avvio dello script
load_dotenv()

def mode_analysis():
    """Logica per l'analisi di Graham su file locali esistenti"""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(base_dir, 'data')
    
    if not os.path.exists(data_dir):
        print(f"Cartella {data_dir} non trovata.")
        return

    files = [f for f in os.listdir(data_dir) if f.endswith('.json')]
    
    if not files:
        print("Nessun file JSON trovato in /data.")
        return

    print("\nFile disponibili:")
    for i, f in enumerate(files):
        print(f"{i+1}. {f}")
    
    choice = input("\nScegli il numero del file da analizzare: ")
    try:
        selected_file = files[int(choice)-1]
        file_path = os.path.join(data_dir, selected_file)
        
        financial_data = load_company_data(file_path)
        if financial_data:
            print(f"\n--- Esecuzione Agent: Benjamin Graham su {selected_file} ---")
            agent = GrahamAgent(financial_data)
            print(agent.analyze())
    except (ValueError, IndexError):
        print("Selezione non valida.")

def mode_builder():
    """Logica per creare dati manualmente incollando testo grezzo"""
    print("\n--- MODALITÀ CREAZIONE DATI MANUALE (AI - Gemini) ---")
    
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("⚠️  ERRORE: Google API Key non trovata nel file .env")
        return

    print("Incolla qui sotto il testo grezzo del bilancio.")
    print("Premi ENTER due volte per terminare l'inserimento.")
    
    lines = []
    while True:
        line = input()
        if not line: break
        lines.append(line)
    raw_text = "\n".join(lines)
    
    if len(raw_text) < 10:
        print("Testo troppo breve.")
        return

    builder = DataBuilderAgent(api_key=api_key)
    structured_data = builder.build_from_text(raw_text)
    
    if structured_data:
        print("\nDati estratti con successo.")
        # Chiediamo se salvare
        confirm = input("Vuoi salvare questo file per analisi future? (s/n): ")
        if confirm.lower() == 's':
            filename = input("Nome del file (es. azienda_x.json): ")
            if not filename.endswith('.json'):
                filename += ".json"
            builder.save_to_json(structured_data, filename)
            
            # Opzionale: Analisi immediata
            analyze_now = input("Vuoi eseguire l'analisi di Graham ora? (s/n): ")
            if analyze_now.lower() == 's':
                f_data = FinancialData(**structured_data)
                graham = GrahamAgent(f_data)
                print(graham.analyze())

def mode_ticker():
    """
    Logica per scaricare dati da Yahoo Finance, strutturarli con AI
    e lanciare l'analisi di Graham.
    """
    print("\n--- MODALITÀ TICKER (Yahoo Finance + AI) ---")
    
    # Controllo API Key (MarketDataAgent usa DataBuilderAgent che usa Gemini)
    if not os.getenv("GOOGLE_API_KEY"):
        print("⚠️  ERRORE: Google API Key non trovata nel file .env")
        return

    ticker = input("Inserisci il simbolo del Ticker (es. GME, AAPL, TSLA): ").upper().strip()
    
    if not ticker:
        return

    # 1. Istanziamo l'agent di mercato
    market_agent = MarketDataAgent()
    
    # 2. Recuperiamo i dati (Questo usa internamente l'AI per mappare i campi)
    data_dict = market_agent.fetch_from_ticker(ticker)
    
    if data_dict:
        print(f"\n✅ Dati recuperati e strutturati per {ticker}.")
        print(f"   Prezzo rilevato: ${data_dict['current_market_price']}")
        print(f"   Utile Netto:     ${data_dict['net_income']:,.0f}")
        
        # 3. Salvataggio
        save = input("\nVuoi salvare i dati in locale (data/)? (s/n): ")
        if save.lower() == 's':
            filename = f"{ticker}.json"
            market_agent.save_to_json(data_dict, filename)
        
        # 4. Analisi di Graham
        run_now = input("Vuoi eseguire l'analisi di Graham ora? (s/n): ")
        if run_now.lower() == 's':
            print(f"\n--- Analisi Graham su {ticker} ---")
            
            # Convertiamo il dizionario (JSON) in Oggetto FinancialData
            financial_data_obj = FinancialData(**data_dict)
            
            # Passiamo l'oggetto all'Agente di Graham
            graham = GrahamAgent(financial_data_obj)
            print(graham.analyze())
    else:
        print("❌ Impossibile recuperare o strutturare i dati per questo ticker.")

def main():
    """Codice principale per selezionare la modalità operativa."""
    print("=== Financial Analysis Multi-Agent System ===")
    print("1. Analizza un file locale esistente")
    print("2. Crea dati da testo grezzo (Copia/Incolla)")
    print("3. Analizza da Ticker (Yahoo Finance -> AI -> Graham)") # <--- NUOVA OPZIONE
    
    mode = input("\nScegli modalità (1, 2 o 3): ")
    
    if mode == "1":
        mode_analysis()
    elif mode == "2":
        mode_builder()
    elif mode == "3":
        mode_ticker()
    else:
        print("Scelta non valida.")

if __name__ == "__main__":
    main()