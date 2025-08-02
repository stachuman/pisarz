# 📝 Pisarz (Lazy Writer) - AI-Powered Writing Assistant

<div align="center">

**Professional writing application with advanced AI integration**

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![PySide6](https://img.shields.io/badge/PySide6-6.5.0%2B-green)
![License](https://img.shields.io/badge/License-MIT-brightgreen)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey)

*Transform your writing with the power of artificial intelligence*

</div>

## ✨ Why Choose Pisarz?

Pisarz isn't just another text editor - it's a **complete creative writing environment** designed for authors who want to focus on creating, not on technical details.

### 🎯 **Key Features:**
- **🤖 Advanced AI Integration** - Collaborate with multiple LLM models (OpenAI, LLaMA, Ollama)
- **📚 Project Management** - Organize your books, stories, and articles in one place
- **🎭 Deep Character & Location Management** - Create rich worlds with consistent details
- **🔍 Intelligent Search** - Find any information in your projects instantly
- **📄 Professional Export System** - Export to PDF, TXT with Polish character support
- **🌍 Multilingual** - Full support for Polish and English interface
- **🎨 Modern Interface** - Clean, responsive design based on Qt6

## 🚀 What Can Pisarz Do?

### 📖 **Literary Project Management**
- Create and organize book, story, and article projects
- Scene structure with advanced RTF editor
- Automatic saving and change history
- Professional export to multiple formats (PDF, TXT)
- Context menus for quick scene and project exports

### 🎭 **Intelligent Character Management**
- Detailed character profiles with full characterization
- Track relationships between characters
- Automatic character linking to scenes
- Visualize connections within projects

### 🗺️ **World Building**
- Create and manage locations
- Atmosphere, details, and significance of each place
- Connections between locations and scenes
- Map relationships of places in your story

### 🤖 **AI Assistant for Writers**
- **Scene Continuation** - AI helps develop your plot
- **Style Improvement** - Language and stylistic suggestions
- **Dialogue Generation** - Natural character conversations
- **Description Creation** - Rich location and atmosphere descriptions
- **Consistency Analysis** - Check plot consistency
- **Extensive Template System** - Customizable AI prompts for every writing need

### 📄 **Professional Export System**
- **PDF Export** - Professional formatting with Unicode font support
- **Text Export** - Clean, formatted plain text
- **Context Menu Integration** - Right-click export from scenes and project tree
- **Flexible Options** - Export all scenes, selected scenes, or full project with metadata

### 🔍 **Advanced Search**
- Full-text search with FTS5
- Filter by characters, locations, scenes
- Quick project navigation
- Intelligent suggestions

## 📥 Installation

### System Requirements
- **Python 3.8+** (recommended 3.11+)
- **4GB RAM** (minimum)
- **500MB** free disk space
- **Windows 10+, Linux Ubuntu 20.04+, macOS 10.15+**

### Quick Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/pisarz.git
cd pisarz

# Create virtual environment
python -m venv venv

# Activate environment
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# For PDF export with Polish characters (Linux):
sudo apt install fonts-dejavu fonts-dejavu-core fonts-dejavu-extra

# Run Pisarz
python main.py
```

## 🎮 Quick Start

### 1️⃣ **Create your first project**
```
File → New Project → Enter name → OK
```

### 2️⃣ **Add your first scene**
- Right-click on project in tree
- Select "Add Scene"
- Start writing!

### 3️⃣ **Configure AI (optional)**
- Go to Settings → LLM
- Choose provider (OpenAI, Ollama, LLaMA)
- Enter API key or configure local model
- Ready - you have an intelligent assistant!

### 4️⃣ **Export your work**
- **Quick Export**: Right-click on scene → Export Scene to PDF/TXT
- **Project Export**: Right-click in empty space → Export Project to PDF/TXT
- **Advanced Export**: File → Export Document... (Ctrl+E)

### 5️⃣ **Harness AI power**
- Select text in scene
- Right-click
- Choose "Continue with AI" or "Improve Style"
- Watch AI help with your writing!

## 🛠️ Advanced Features

### 🎨 **Customization**
- **Color Themes** - Light, dark, and custom themes
- **Configurable Keyboard Shortcuts**
- **Customizable AI Templates** - Create your own prompts
- **Flexible Panel Layouts**

### 📊 **Writing Analytics**
- Word and character statistics
- Daily progress tracking
- Change history and versioning
- Writing pace analysis

### 🔌 **Extensibility**
- Custom prompt templates for AI
- Custom color themes
- Plugin architecture (in development)
- API for external integrations (planned)

## 🤝 Community and Support

### 💬 **Get Help**
- 📖 **Documentation**: [Project Wiki](https://github.com/yourusername/pisarz/wiki)
- 🐛 **Bugs**: [GitHub Issues](https://github.com/yourusername/pisarz/issues)
- 💡 **Ideas**: [GitHub Discussions](https://github.com/yourusername/pisarz/discussions)
- 📧 **Contact**: contact@pisarz.app

### 🌟 **Support the Project**
- ⭐ **Star** on GitHub
- 🐛 **Report bugs** and suggestions
- 💻 **Contribute** - pull requests welcome
- 📢 **Share** with other writers

## 🔬 Tech Stack

- **🐍 Python 3.8+** - Main application language
- **🖼️ PySide6 (Qt6)** - Modern user interface
- **🗄️ SQLite + FTS5** - Fast database with full-text search
- **🤖 Multi-LLM Support** - OpenAI, Anthropic, LLaMA, Ollama
- **📄 ReportLab** - Professional PDF generation
- **🔤 Jinja2** - Template engine for AI prompts
- **🌐 i18n** - Full internationalization

## 📈 Roadmap

### 🎯 **Coming Soon**
- [ ] EPUB export
- [ ] Cloud synchronization
- [ ] Plugin marketplace
- [ ] Enhanced themes
- [ ] DOCX export support

---

# 📝 Pisarz - Inteligentny Asystent Pisarza

<div align="center">

**Profesjonalna aplikacja do pisania z zaawansowanym wsparciem AI**

*Przekształć swoje pisanie dzięki mocy sztucznej inteligencji*

</div>

## ✨ Dlaczego Pisarz?

Pisarz to nie tylko kolejny edytor tekstu - to **kompletne środowisko do twórczego pisania** stworzone z myślą o autorach, którzy chcą skupić się na tworzeniu, a nie na technicznych detalach.

### 🎯 **Kluczowe zalety:**
- **🤖 Zaawansowana integracja AI** - Współpracuj z wieloma modelami LLM (OpenAI, LLaMA, Ollama)
- **📚 Zarządzanie projektami** - Organizuj swoje książki, opowiadania i artykuły w jednym miejscu
- **🎭 Głębokie zarządzanie postaciami i lokacjami** - Twórz bogate światy z konsystentnymi detalami
- **🔍 Inteligentne wyszukiwanie** - Znajdź dowolną informację w swoich projektach błyskawicznie
- **📄 Profesjonalny system eksportu** - Eksport do PDF, TXT z pełnym wsparciem polskich znaków
- **🌍 Wielojęzyczność** - Pełne wsparcie dla polskiego i angielskiego interfejsu
- **🎨 Nowoczesny interfejs** - Przejrzysty, responsywny design oparty na Qt6

## 🚀 Co Pisarz potrafi?

### 📖 **Zarządzanie projektami literackimi**
- Tworzenie i organizowanie projektów książek, opowiadań, artykułów
- Struktura scen z zaawansowanym edytorem RTF
- Automatyczne zapisywanie i historia zmian
- Profesjonalny eksport do wielu formatów (PDF, TXT)
- Menu kontekstowe do szybkiego eksportu scen i projektów

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
- **Rozbudowany system szablonów** - Konfigurowalne prompty AI dla każdej potrzeby pisarskiej

### 📄 **Profesjonalny system eksportu**
- **Eksport PDF** - Profesjonalne formatowanie z wsparciem czcionek Unicode
- **Eksport tekstowy** - Czysty, sformatowany tekst
- **Wsparcie polskich znaków** - Idealne renderowanie ą, ć, ę, ł, ń, ó, ś, ź, ż
- **Integracja z menu kontekstowym** - Eksport prawym klikiem ze scen i drzewa projektu
- **Elastyczne opcje** - Eksport wszystkich scen, wybranych scen lub całego projektu z metadanymi

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
# Sklonuj repozytorium
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

# Dla eksportu PDF z polskimi znakami (Linux):
sudo apt install fonts-dejavu fonts-dejavu-core fonts-dejavu-extra

# Uruchom Pisarz
python main.py
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

### 4️⃣ **Eksportuj swoją pracę**
- **Szybki eksport**: Prawy klik na scenę → Eksportuj scenę do PDF/TXT
- **Eksport projektu**: Prawy klik w pustą przestrzeń → Eksportuj projekt do PDF/TXT
- **Zaawansowany eksport**: Plik → Eksportuj dokument... (Ctrl+E)

### 5️⃣ **Wykorzystaj moc AI**
- Zaznacz tekst w scenie
- Kliknij prawym przyciskiem
- Wybierz "Kontynuuj z AI" lub "Popraw styl"
- Zobacz jak AI pomaga w pisaniu!

## 🛠️ Zaawansowane funkcje

### 🎨 **Personalizacja**
- **Motywy kolorystyczne** - Jasny, ciemny i niestandardowe
- **Konfigurowane skróty klawiszowe**
- **Dostosowywalne szablony AI** - Twórz własne prompty
- **Elastyczne układy paneli**

### 📊 **Analityka pisania**
- Statystyki słów i znaków
- Tracker postępu dziennego
- Historia zmian i wersjonowanie
- Analiza tempa pisania

### 🔌 **Rozszerzalność**
- Własne szablony promptów dla AI
- Niestandardowe motywy kolorystyczne
- Architektura pluginów (w rozwoju)
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
- **📄 ReportLab** - Profesjonalne generowanie PDF
- **🔤 Jinja2** - Silnik szablonów dla promptów AI
- **🌐 i18n** - Pełna internacjonalizacja

## 📈 Roadmapa

### 🎯 **W najbliższym czasie**
- [ ] Eksport do EPUB
- [ ] Synchronizacja w chmurze
- [ ] Marketplace pluginów
- [ ] Ulepszone motywy
- [ ] Wsparcie eksportu DOCX

## 📄 Licencja

Projekt udostępniony na licencji **MIT License** - możesz go używać, modyfikować i dystrybuować zgodnie z własnymi potrzebami.

---

<div align="center">

**Ready to start your writing journey with AI?**

**Gotowy zacząć swoją pisarską przygodę z AI?**

[⬇️ Download Pisarz / Pobierz Pisarz](https://github.com/yourusername/pisarz/releases) | [📖 Documentation / Dokumentacja](https://github.com/yourusername/pisarz/wiki) | [🤝 Community / Społeczność](https://github.com/yourusername/pisarz/discussions)

*Created with ❤️ for the writing community*

*Stworzone z ❤️ dla społeczności pisarzy*

</div>