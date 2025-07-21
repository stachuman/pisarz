# 📝 Pisarz - Inteligentny Asystent Pisarza

<div align="center">

**Profesjonalna aplikacja do pisania z zaawansowanym wsparciem AI**

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![PySide6](https://img.shields.io/badge/PySide6-6.5.0%2B-green)
![License](https://img.shields.io/badge/License-MIT-brightgreen)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey)

*Przekształć swoje pisanie dzięki mocy sztucznej inteligencji*

</div>

## ✨ Dlaczego Pisarz?

Pisarz to nie tylko kolejny edytor tekstu - to **kompletne środowisko do twórczego pisania** stworzone z myślą o autorach, którzy chcą skupić się na tworzeniu, a nie na technicznych detalach.

### 🎯 **Kluczowe zalety:**
- **🤖 Zaawansowana integracja AI** - Współpracuj z wieloma modelami LLM (OpenAI, LLaMA, Ollama)
- **📚 Zarządzanie projektami** - Organizuj swoje książki, opowiadania i artykuły w jednym miejscu
- **🎭 Głębokie zarządzanie postaciami i lokacjami** - Twórz bogate światy z konsystentnymi detalami
- **🔍 Inteligentne wyszukiwanie** - Znajdź dowolną informację w swoich projektach błyskawicznie
- **🌍 Wielojęzyczność** - Pełne wsparcie dla polskiego i angielskiego interfejsu
- **🎨 Nowoczesny interfejs** - Przejrzysty, responsywny design oparty na Qt6

## 🚀 Co Pisarz potrafi?

### 📖 **Zarządzanie projektami literackimi**
- Tworzenie i organizowanie projektów książek, opowiadań, artykuł
- Struktura scen z zaawansowanym edytorem RTF
- Automatyczne zapisywanie i historia zmian
- Eksport do różnych formatów

### 🎭 **Inteligentne zarządzanie postaciami**
- Szczegółowe profile postaci z pełną charakterystyką
- Śledzenie relacji między postaciami
- Automatyczne linkowanie postaci do scen
- Wizualizacja powiązań w projekcie

### 🗺️ **Kreowanie światów**
- Tworzenie i zarządzanie lokacjami
- Atmosfera, detale i znaczenie każdego miejsca
- Powiązania między lokacjami a scenami
- Mapa relacji miejsc w opowieści

### 🤖 **Asystent AI dla pisarzy**
- **Kontynuacja scen** - AI pomaga rozwinąć fabułę
- **Poprawa stylu** - Sugestie językowe i stylistyczne
- **Generowanie dialogów** - Naturalne rozmowy postaci
- **Tworzenie opisów** - Bogate opisy lokacji i atmosfery
- **Analiza spójności** - Sprawdzanie konsystencji fabuły

### 🔍 **Zaawansowane wyszukiwanie**
- Pełnotekstowe wyszukiwanie z FTS5
- Filtrowanie według postaci, lokacji, scen
- Szybka nawigacja po projektach
- Inteligentne podpowiedzi

## 📥 Instalacja

### Wymagania systemowe
- **Python 3.8+** (zalecany 3.11+)
- **4GB RAM** (minimum)
- **500MB** wolnego miejsca na dysku
- **Windows 10+, Linux Ubuntu 20.04+, macOS 10.15+**

### Szybka instalacja

```bash
# Klonuj repozytorium
git clone https://github.com/yourusername/pisarz.git
cd pisarz

# Utwórz środowisko wirtualne
python -m venv venv

# Aktywuj środowisko
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Zainstaluj zależności
pip install -r requirements.txt

# Uruchom Pisarz
python main.py
```

### Alternatywnie - instalacja przez pip (wkrótce)
```bash
pip install pisarz-app
pisarz
```

## 🎮 Szybki start

### 1️⃣ **Utwórz pierwszy projekt**
```
Plik → Nowy Projekt → Wpisz nazwę → OK
```

### 2️⃣ **Dodaj pierwszą scenę**
- Kliknij prawym na projekt w drzewie
- Wybierz "Dodaj scenę"
- Zacznij pisać!

### 3️⃣ **Skonfiguruj AI (opcjonalnie)**
- Przejdź do Ustawienia → LLM
- Wybierz provider (OpenAI, Ollama, LLaMA)
- Wprowadź klucz API lub skonfiguruj lokalny model
- Gotowe - masz inteligentnego asystenta!

### 4️⃣ **Wykorzystaj moc AI**
- Zaznacz tekst w scenie
- Kliknij prawym przyciskiem
- Wybierz "Kontynuuj z AI" lub "Popraw styl"
- Zobacz jak AI pomaga w pisaniu!

## 🛠️ Zaawansowane funkcje

### 🎨 **Personalizacja**
- **Motywy kolorystyczne** - Jasny, ciemny i niestandardowe
- **Konfigurowane skróty klawiszowe**
- **Dostosowywalne szablony AI**
- **Elastyczne układy paneli**

### 📊 **Analityka pisania**
- Statystyki słów i znaków
- Tracker postępu dziennego
- Historia zmian i wersjonowanie
- Analiza tempa pisania

### 🔌 **Rozszerzalność**
- Własne szablony promptów dla AI
- Niestandardowe motywy kolorystyczne
- Plugin architecture (w rozwoju)
- API dla integracji zewnętrznych (planowane)

## 🤝 Społeczność i wsparcie

### 💬 **Uzyskaj pomoc**
- 📖 **Dokumentacja**: [Wiki projektu](https://github.com/yourusername/pisarz/wiki)
- 🐛 **Błędy**: [GitHub Issues](https://github.com/yourusername/pisarz/issues)
- 💡 **Pomysły**: [GitHub Discussions](https://github.com/yourusername/pisarz/discussions)
- 📧 **Kontakt**: contact@pisarz.app

### 🌟 **Wesprzyj projekt**
- ⭐ **Zostaw gwiazdkę** na GitHub
- 🐛 **Zgłaszaj błędy** i sugestie
- 💻 **Wnieś swój wkład** - pull requesty mile widziane
- 📢 **Podziel się** z innymi pisarzami

## 🔬 Stack technologiczny

- **🐍 Python 3.8+** - Główny język aplikacji
- **🖼️ PySide6 (Qt6)** - Nowoczesny interfejs użytkownika
- **🗄️ SQLite + FTS5** - Szybka baza danych z pełnotekstowym wyszukiwaniem
- **🤖 Multi-LLM Support** - OpenAI, Anthropic, LLaMA, Ollama
- **🔤 Jinja2** - Silnik szablonów dla promptów AI
- **🌐 i18n** - Pełna internacjonalizacja

## 📈 Roadmapa

### 🎯 **W najbliższym czasie**
- [ ] Export do EPUB/PDF
- [ ] Synchronizacja w chmurze
- [ ] Plugin marketplace
- [ ] Ulepszone motywy

## 📄 Licencja

Projekt udostępniony na licencji **MIT License** - możesz go używać, modyfikować i dystrybuować zgodnie z własnymi potrzebami.

---

<div align="center">

**Gotowy zacząć swoją pisarską przygodę z AI?**

[⬇️ Pobierz Pisarz](https://github.com/yourusername/pisarz/releases) | [📖 Dokumentacja](https://github.com/yourusername/pisarz/wiki) | [🤝 Społeczność](https://github.com/yourusername/pisarz/discussions)

*Stworzono z ❤️ dla społeczności pisarzy*

</div>