"""Modulo AI Provider per la selezione dinamica del modello Gemini."""
from typing import Optional, List
import os
import re
import time
import requests
from bs4 import BeautifulSoup
import google.generativeai as genai
from google.api_core.exceptions import ResourceExhausted, ServiceUnavailable, InternalServerError

class SmartModelWrapper:
    """
    Wrapper intelligente che gestisce i Rate Limits (Errore 429).
    I messaggi di switching sono nascosti a meno che il debug non sia attivo.
    """
    def __init__(self, provider, json_mode: bool):
        self.provider = provider
        self.json_mode = json_mode
        self._refresh_underlying_model()

    def _refresh_underlying_model(self):
        config = None
        if self.json_mode:
            config = genai.types.GenerationConfig( # pyright: ignore[reportPrivateImportUsage]
                response_mime_type="application/json"
            )
        
        self.real_model = genai.GenerativeModel( # pyright: ignore[reportPrivateImportUsage]
            model_name=self.provider.current_model_name,
            generation_config=config
        )

    def generate_content(self, prompt):
        """
        Genera contenuto gestendo i Rate Limits con tentativi di fallback.
        """
        max_retries = 5
        attempts = 0

        while attempts < max_retries:
            try:
                return self.real_model.generate_content(prompt)

            except ResourceExhausted:
                # Logga solo se in DEBUG mode
                self.provider.log_debug(f"⚠️ Quota esaurita per {self.provider.current_model_name} (429).")
                
                if self.provider.downgrade_model():
                    # Logga solo se in DEBUG mode
                    self.provider.log_debug(f"🔄 Switching automatico al prossimo modello: {self.provider.current_model_name}")
                    
                    self._refresh_underlying_model()
                    attempts += 1
                    time.sleep(1)
                else:
                    print("❌ Errore: Nessun altro modello disponibile per il fallback.")
                    raise

            except (ServiceUnavailable, InternalServerError):
                self.provider.log_debug("⚠️ Errore server Google. Attendo 5s...")
                time.sleep(5)
                attempts += 1
                
            except Exception as e: # pylint: disable=broad-exception-caught
                raise e
        
        raise RuntimeError("Impossibile generare contenuto dopo i tentativi di fallback.")


class AIProvider:
    """
    Gestore centralizzato AI con supporto Debug Mode.
    """
    
    DOCS_URL = "https://ai.google.dev/gemini-api/docs/models?hl=it"

    FALLBACK_ORDER = [
        "gemini-2.5-flash",
        "gemini-2.5-flash-lite",
        "gemini-2.0-flash",
        "gemini-2.0-flash-lite"
    ]

    def __init__(self, api_key: Optional[str] = None):
        """
        Inizializza l'AI Provider con API Key e modalità debug.
        """
        # --- CONFIGURAZIONE API KEY
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("Google API Key mancante.")
        
        # --- CONFIGURAZIONE DEBUG ---
        # Legge la variabile d'ambiente. Default: False (Silenzioso)
        debug_env = os.getenv("AI_DEBUG", "false").lower()
        self.debug_mode = debug_env in ("true", "1", "yes", "on")
        # ----------------------------

        genai.configure(api_key=self.api_key) # pyright: ignore[reportPrivateImportUsage]
        
        # Scraping silenzioso (logga solo se debug è True)
        self.available_models_chain = self._build_model_chain()
        
        if not self.available_models_chain:
            raise ValueError("Nessun modello Gemini utilizzabile trovato.")

        self.current_model_index = 0
        self.current_model_name = self.available_models_chain[0]
        
        self.log_debug(f"🤖 AI Provider pronto. Modello iniziale: {self.current_model_name}")

    def log_debug(self, message: str):
        """Stampa il messaggio solo se la modalità debug è attiva."""
        if self.debug_mode:
            print(message)

    def downgrade_model(self) -> bool:
        """Passa al modello successivo nella catena di fallback, se disponibile."""
        if self.current_model_index + 1 < len(self.available_models_chain):
            self.current_model_index += 1
            self.current_model_name = self.available_models_chain[self.current_model_index]
            return True
        return False

    def get_model(self, json_mode: bool = False):
        """Restituisce un wrapper modello intelligente per il tipo di output desiderato."""
        return SmartModelWrapper(provider=self, json_mode=json_mode)

    def _build_model_chain(self) -> List[str]:
        """Costruisce la catena di modelli utilizzabili basata sulla priorità dinamica."""
        priority_list = self._scrape_dynamic_priority()
        
        try:
            my_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods] # pyright: ignore[reportPrivateImportUsage]
        except Exception: # pylint: disable=broad-exception-caught
            return [f"models/{m}" if not m.startswith("models/") else m for m in self.FALLBACK_ORDER]

        usable_chain = []
        for desired in priority_list:
            for real in my_models:
                if desired in real and real not in usable_chain:
                    usable_chain.append(real)
        
        for m in my_models:
            if ("pro" in m or "flash" in m) and "vision" not in m and m not in usable_chain:
                usable_chain.append(m)
                
        return usable_chain

    def _scrape_dynamic_priority(self) -> List[str]:
        """Scarica e analizza la lista modelli Gemini da Google per priorità dinamica."""
        self.log_debug("🌐 Scarico lista modelli da Google...")
        try:
            response = requests.get(self.DOCS_URL, timeout=3)
            if response.status_code != 200: 
                return self.FALLBACK_ORDER

            soup = BeautifulSoup(response.text, 'html.parser')
            text = soup.get_text()
            candidates = set(re.findall(r"(gemini-[a-zA-Z0-9\-\.]+)", text))
            
            valid = [m for m in candidates if "gemini" in m and not m.endswith("-vision") and "google" not in m]
            if not valid: 
                return self.FALLBACK_ORDER

            def sort_key(name):
                match = re.search(r"(\d+(?:\.\d+)?)", name)
                ver = float(match.group(1)) if match else 0.0
                tier = 4 if "ultra" in name else 3 if "pro" in name else 2 if "flash" in name else 1
                preview = 1 if "preview" in name or "exp" in name else 0
                return (ver, tier, preview)

            return sorted(valid, key=sort_key, reverse=True)

        except Exception: # pylint: disable=broad-exception-caught
            return self.FALLBACK_ORDER
        
