"""Internationalization manager for consistent text handling."""

from typing import Dict, Optional
from PySide6.QtCore import QSettings, QLocale, QTranslator, QCoreApplication
from PySide6.QtWidgets import QApplication
import os
from pathlib import Path

from i18n import _


class I18nManager:
    """Manager for internationalization and localization."""
    
    def __init__(self):
        self.settings = QSettings()
        self.translator = QTranslator()
        self.current_locale = self.get_current_locale()
        self.available_locales = self.get_available_locales()
        
    def get_current_locale(self) -> str:
        """Get the current locale."""
        saved_locale = self.settings.value("locale", "")
        if saved_locale:
            return saved_locale
        
        # Use system locale as fallback
        system_locale = QLocale.system().name()
        return system_locale
    
    def get_available_locales(self) -> Dict[str, str]:
        """Get available locales from the i18n directory."""
        locales = {}
        i18n_dir = Path(__file__).parent.parent.parent / "i18n" / "locales"
        
        if i18n_dir.exists():
            for locale_dir in i18n_dir.iterdir():
                if locale_dir.is_dir():
                    locale_code = locale_dir.name
                    mo_file = locale_dir / "LC_MESSAGES" / "pisarz.mo"
                    if mo_file.exists():
                        # Map locale codes to display names
                        display_name = self.get_locale_display_name(locale_code)
                        locales[locale_code] = display_name
        
        # Add default English if not present
        if "en_US" not in locales:
            locales["en_US"] = "English (US)"
            
        return locales
    
    def get_locale_display_name(self, locale_code: str) -> str:
        """Get display name for a locale code."""
        locale_names = {
            "en_US": "English (US)",
            "en_GB": "English (UK)",
            "pl_PL": "Polski",
            "de_DE": "Deutsch",
            "fr_FR": "Français",
            "es_ES": "Español",
            "it_IT": "Italiano",
            "pt_PT": "Português",
            "ru_RU": "Русский",
            "zh_CN": "中文 (简体)",
            "zh_TW": "中文 (繁體)",
            "ja_JP": "日本語",
            "ko_KR": "한국어",
        }
        
        return locale_names.get(locale_code, locale_code)
    
    def set_locale(self, locale_code: str) -> bool:
        """Set the application locale."""
        if locale_code not in self.available_locales:
            return False
        
        # Save to settings
        self.settings.setValue("locale", locale_code)
        self.current_locale = locale_code
        
        # Load translation
        success = self.load_translation(locale_code)
        
        if success:
            # Notify that locale changed
            app = QApplication.instance()
            if app:
                app.installTranslator(self.translator)
        
        return success
    
    def load_translation(self, locale_code: str) -> bool:
        """Load translation for the specified locale."""
        i18n_dir = Path(__file__).parent.parent.parent / "i18n" / "locales"
        translation_file = i18n_dir / locale_code / "LC_MESSAGES" / "pisarz.qm"
        
        if translation_file.exists():
            return self.translator.load(str(translation_file))
        
        # Try to load from .mo file if .qm doesn't exist
        mo_file = i18n_dir / locale_code / "LC_MESSAGES" / "pisarz.mo"
        if mo_file.exists():
            return self.translator.load(str(mo_file))
        
        return False
    
    def get_text(self, key: str, context: Optional[str] = None) -> str:
        """Get translated text for a key."""
        if context:
            return QCoreApplication.translate(context, key)
        else:
            return _(key)
    
    def get_common_texts(self) -> Dict[str, str]:
        """Get commonly used translated texts."""
        return {
            # Common actions
            "save": _("Save"),
            "cancel": _("Cancel"),
            "close": _("Close"),
            "open": _("Open"),
            "new": _("New"),
            "edit": _("Edit"),
            "delete": _("Delete"),
            "create": _("Create"),
            "update": _("Update"),
            "refresh": _("Refresh"),
            "search": _("Search"),
            "filter": _("Filter"),
            "sort": _("Sort"),
            "export": _("Export"),
            "import": _("Import"),
            "copy": _("Copy"),
            "paste": _("Paste"),
            "cut": _("Cut"),
            "undo": _("Undo"),
            "redo": _("Redo"),
            "select_all": _("Select All"),
            "find": _("Find"),
            "replace": _("Replace"),
            "find_next": _("Find Next"),
            "find_previous": _("Find Previous"),
            
            # Common UI elements
            "ok": _("OK"),
            "yes": _("Yes"),
            "no": _("No"),
            "apply": _("Apply"),
            "reset": _("Reset"),
            "default": _("Default"),
            "settings": _("Settings"),
            "preferences": _("Preferences"),
            "help": _("Help"),
            "about": _("About"),
            "exit": _("Exit"),
            "quit": _("Quit"),
            
            # Common status messages
            "loading": _("Loading..."),
            "saving": _("Saving..."),
            "saved": _("Saved"),
            "error": _("Error"),
            "warning": _("Warning"),
            "info": _("Information"),
            "success": _("Success"),
            "ready": _("Ready"),
            "processing": _("Processing..."),
            "complete": _("Complete"),
            "failed": _("Failed"),
            
            # Common placeholders
            "enter_name": _("Enter name..."),
            "enter_text": _("Enter text..."),
            "search_placeholder": _("Search..."),
            "no_results": _("No results found"),
            "empty_list": _("No items to display"),
            "select_item": _("Select an item"),
            "untitled": _("Untitled"),
            
            # Time and date
            "today": _("Today"),
            "yesterday": _("Yesterday"),
            "tomorrow": _("Tomorrow"),
            "now": _("Now"),
            "never": _("Never"),
            
            # File operations
            "file": _("File"),
            "folder": _("Folder"),
            "path": _("Path"),
            "name": _("Name"),
            "size": _("Size"),
            "type": _("Type"),
            "modified": _("Modified"),
            "created": _("Created"),
            
            # Application specific
            "project": _("Project"),
            "projects": _("Projects"),
            "scene": _("Scene"),
            "scenes": _("Scenes"),
            "character": _("Character"),
            "characters": _("Characters"),
            "location": _("Location"),
            "locations": _("Locations"),
            "note": _("Note"),
            "notes": _("Notes"),
            "description": _("Description"),
            "title": _("Title"),
            "content": _("Content"),
            "summary": _("Summary"),
            "draft": _("Draft"),
            "published": _("Published"),
            "word_count": _("Word Count"),
            "page_count": _("Page Count"),
            "chapter": _("Chapter"),
            "chapters": _("Chapters"),
            "outline": _("Outline"),
            "timeline": _("Timeline"),
            "relationship": _("Relationship"),
            "relationships": _("Relationships"),
        }
    
    def get_error_messages(self) -> Dict[str, str]:
        """Get common error messages."""
        return {
            "file_not_found": _("File not found"),
            "file_exists": _("File already exists"),
            "permission_denied": _("Permission denied"),
            "invalid_input": _("Invalid input"),
            "required_field": _("This field is required"),
            "save_failed": _("Failed to save"),
            "load_failed": _("Failed to load"),
            "connection_failed": _("Connection failed"),
            "timeout": _("Operation timed out"),
            "unknown_error": _("Unknown error occurred"),
            "invalid_format": _("Invalid file format"),
            "corrupted_file": _("File is corrupted"),
            "disk_full": _("Disk space full"),
            "network_error": _("Network error"),
            "invalid_characters": _("Contains invalid characters"),
            "too_long": _("Text is too long"),
            "too_short": _("Text is too short"),
            "already_exists": _("Already exists"),
            "not_found": _("Not found"),
            "access_denied": _("Access denied"),
        }
    
    def get_confirmation_messages(self) -> Dict[str, str]:
        """Get common confirmation messages."""
        return {
            "delete_confirm": _("Are you sure you want to delete this item?"),
            "unsaved_changes": _("You have unsaved changes. Do you want to save them?"),
            "overwrite_confirm": _("File already exists. Do you want to overwrite it?"),
            "reset_confirm": _("Are you sure you want to reset all settings?"),
            "clear_confirm": _("Are you sure you want to clear all data?"),
            "exit_confirm": _("Are you sure you want to exit?"),
            "restart_required": _("Restart required for changes to take effect. Restart now?"),
            "discard_changes": _("Are you sure you want to discard all changes?"),
            "permanent_action": _("This action cannot be undone. Continue?"),
            "delete_multiple": _("Are you sure you want to delete {count} items?"),
        }
    
    def format_message(self, template: str, **kwargs) -> str:
        """Format a message template with variables."""
        return template.format(**kwargs)
    
    def get_units(self) -> Dict[str, str]:
        """Get translated units."""
        return {
            "words": _("words"),
            "characters": _("characters"),
            "pages": _("pages"),
            "lines": _("lines"),
            "paragraphs": _("paragraphs"),
            "sentences": _("sentences"),
            "bytes": _("bytes"),
            "kb": _("KB"),
            "mb": _("MB"),
            "gb": _("GB"),
            "seconds": _("seconds"),
            "minutes": _("minutes"),
            "hours": _("hours"),
            "days": _("days"),
            "weeks": _("weeks"),
            "months": _("months"),
            "years": _("years"),
        }
    
    def pluralize(self, count: int, singular: str, plural: str) -> str:
        """Return singular or plural form based on count."""
        if count == 1:
            return f"{count} {singular}"
        else:
            return f"{count} {plural}"
    
    def format_time_ago(self, minutes_ago: int) -> str:
        """Format time ago string."""
        if minutes_ago < 1:
            return _("just now")
        elif minutes_ago < 60:
            return self.pluralize(minutes_ago, _("minute ago"), _("minutes ago"))
        elif minutes_ago < 1440:  # 24 hours
            hours = minutes_ago // 60
            return self.pluralize(hours, _("hour ago"), _("hours ago"))
        else:
            days = minutes_ago // 1440
            return self.pluralize(days, _("day ago"), _("days ago"))
    
    def format_file_size(self, size_bytes: int) -> str:
        """Format file size in human readable format."""
        if size_bytes < 1024:
            return f"{size_bytes} {_('bytes')}"
        elif size_bytes < 1024 * 1024:
            kb = size_bytes / 1024
            return f"{kb:.1f} {_('KB')}"
        elif size_bytes < 1024 * 1024 * 1024:
            mb = size_bytes / (1024 * 1024)
            return f"{mb:.1f} {_('MB')}"
        else:
            gb = size_bytes / (1024 * 1024 * 1024)
            return f"{gb:.1f} {_('GB')}"