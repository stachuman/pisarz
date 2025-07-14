"""Internationalization module for Pisarz."""

import os
import gettext
from pathlib import Path
from typing import Optional

# Dostępne języki
AVAILABLE_LANGUAGES = {
    'en_US': 'English',
    'pl_PL': 'Polski'
}

# Aktualny język (domyślnie angielski)
_current_language = 'en_US'
_translator = None

def get_locales_dir() -> Path:
    """Zwróć ścieżkę do katalogu z tłumaczeniami."""
    return Path(__file__).parent / "locales"

def get_available_languages() -> dict:
    """Zwróć słownik dostępnych języków."""
    return AVAILABLE_LANGUAGES.copy()

def get_current_language() -> str:
    """Zwróć aktualny język."""
    return _current_language

def set_language(language_code: str) -> bool:
    """Ustaw język aplikacji."""
    global _current_language, _translator
    
    if language_code not in AVAILABLE_LANGUAGES:
        return False
    
    try:
        locales_dir = get_locales_dir()
        if language_code == 'en_US':
            # Angielski - użyj domyślnych stringów
            _translator = gettext.NullTranslations()
        else:
            # Inne języki - załaduj tłumaczenia
            _translator = gettext.translation(
                'pisarz', 
                localedir=locales_dir, 
                languages=[language_code]
            )
        
        _current_language = language_code
        return True
        
    except FileNotFoundError:
        print(f"Warning: Translation file for {language_code} not found")
        return False

def _(text: str) -> str:
    """Funkcja tłumaczenia - główna funkcja używana w kodzie."""
    if _translator is None:
        return text
    return _translator.gettext(text)

# Zainicjalizuj domyślny język
set_language('en_US')