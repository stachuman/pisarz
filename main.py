#!/usr/bin/env python3

import sys
from pathlib import Path
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QHBoxLayout, 
                              QSplitter, QStatusBar, QMessageBox, QStackedWidget, QPushButton)
from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence, QShortcut

from core.project import ProjectManager
from core.scene import SceneManager
from ui.widgets import ProjectsView, ProjectTreeView, Workspace, SettingsDialog
from i18n import _


class PisarzApp(QMainWindow):
    """Główne okno aplikacji Pisarz."""
    
    def __init__(self):
        super().__init__()
        self.project_manager = ProjectManager()
        self.current_scene_manager = None
        self.current_project_path = None
        self.current_project_name = ""
        self.current_scene_id = None
        self.focus_mode = False
        
        self.setup_ui()
        self.setup_connections()
        self.setup_shortcuts()
        self.show_projects_view()
        
    def setup_ui(self):
        """Konfiguracja głównego interfejsu."""
        self.setWindowTitle(_("Pisarz - Writing Application"))
        self.setMinimumSize(1200, 800)
        
        # Widget centralny ze stack
        self.main_stack = QStackedWidget()
        self.setCentralWidget(self.main_stack)
        
        # === WIDOK PROJEKTÓW ===
        self.projects_view = ProjectsView()
        self.main_stack.addWidget(self.projects_view)
        
        # === WIDOK PROJEKTU (z nawigacją + workspace) ===
        self.project_widget = QWidget()
        project_layout = QHBoxLayout(self.project_widget)
        project_layout.setContentsMargins(0, 0, 0, 0)
        
        # Splitter dla nawigacji i workspace
        splitter = QSplitter(Qt.Orientation.Horizontal)
        project_layout.addWidget(splitter)
        
        # Drzewko nawigacji w projekcie
        self.project_tree = ProjectTreeView()
        splitter.addWidget(self.project_tree)
        
        # Obszar roboczy
        self.workspace = Workspace()
        splitter.addWidget(self.workspace)
        
        # Proporcje splitter
        splitter.setSizes([300, 900])
        
        self.main_stack.addWidget(self.project_widget)
        
        # Pasek stanu
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage(_("Select project to start"))
        
    def setup_connections(self):
        """Konfiguracja połączeń sygnałów."""
        # Widok projektów
        self.projects_view.projectSelected.connect(self.on_project_selected)
        self.projects_view.newProjectRequested.connect(self.create_new_project)
        self.projects_view.settingsRequested.connect(self.show_settings)
        
        # Drzewko projektu
        self.project_tree.sceneSelected.connect(self.on_scene_selected)
        self.project_tree.categorySelected.connect(self.on_category_selected)
        self.project_tree.newSceneRequested.connect(self.create_new_scene)
        self.project_tree.backToProjectsRequested.connect(self.show_projects_view)
        
        # Workspace
        self.workspace.saveRequested.connect(self.save_scene_content)
        self.workspace.sceneSelectedFromGrid.connect(self.on_scene_selected)
        self.workspace.newSceneRequestedFromGrid.connect(self.create_new_scene)
        self.workspace.focusModeRequested.connect(self.toggle_focus_mode)
        
    def setup_shortcuts(self):
        """Konfiguracja skrótów klawiszowych."""
        # F11 - przełącz tryb fokusu
        self.focus_shortcut = QShortcut(QKeySequence("F11"), self)
        self.focus_shortcut.activated.connect(self.toggle_focus_mode)
        
        # Escape - wyjdź z trybu fokusu (tylko gdy jest aktywny)
        self.escape_shortcut = QShortcut(QKeySequence("Escape"), self)
        self.escape_shortcut.activated.connect(self.exit_focus_mode_if_active)
        
    def exit_focus_mode_if_active(self):
        """Wyjdź z trybu fokusu tylko jeśli jest aktywny."""
        if self.focus_mode:
            self.toggle_focus_mode()
        
    def show_projects_view(self):
        """Pokaż widok projektów."""
        try:
            projects = self.project_manager.list_projects()
            self.projects_view.load_projects(projects)
            self.main_stack.setCurrentIndex(0)
            self.status_bar.showMessage(_("Projects list ({} projects)").format(len(projects)))
        except Exception as e:
            QMessageBox.critical(self, _("Error"), _("Failed to load projects: {}").format(e))
            
    def on_project_selected(self, project_path, project_name):
        """Obsługa wyboru projektu - przejście do widoku projektu."""
        self.current_project_path = project_path
        self.current_project_name = project_name
        self.current_scene_id = None
        self.current_view_state = "welcome"
        self.current_category = None
        
        try:
            # Załaduj dane projektu
            self.current_scene_manager = SceneManager(Path(project_path))
            scenes = self.current_scene_manager.list_scenes()
            
            # Zaktualizuj drzewko nawigacji
            self.project_tree.update_project_name(project_name)
            self.project_tree.load_scenes(scenes, preserve_selection=False)  # Nowy projekt, nie zachowuj selekcji
            
            # Pokaż ekran powitalny w workspace
            self.workspace.show_welcome()
            
            # Przełącz na widok projektu
            self.main_stack.setCurrentIndex(1)
            
            self.status_bar.showMessage(_("Project: {} ({} scenes)").format(project_name, len(scenes)))
            
        except Exception as e:
            QMessageBox.critical(self, _("Error"), _("Failed to load projects: {}").format(e))
            self.show_projects_view()
            
    def on_category_selected(self, category):
        """Obsługa wyboru kategorii - pokaż widok kafelków."""
        if not self.current_scene_manager:
            return
            
        try:
            if category == "scenes":
                scenes = self.current_scene_manager.list_scenes()
                self.workspace.show_scenes_grid(scenes)
                self.status_bar.showMessage(_("Scenes view ({} scenes)").format(len(scenes)))
            else:
                self.workspace.show_welcome()
                self.status_bar.showMessage(_("View {} (function unavailable)").format(category))
        except Exception as e:
            QMessageBox.critical(self, _("Error"), _("Failed to load view: {}").format(e))
            
    def on_scene_selected(self, scene_id, scene_title):
        """Obsługa wyboru sceny."""
        self.current_scene_id = scene_id
        
        try:
            scene_data = self.current_scene_manager.get_scene(scene_id)
            content = scene_data.get("content_rtf", f"<p>{_('Start writing your scene...')}</p>") if scene_data else f"<p>{_('Scene loading error')}</p>"
            
            self.workspace.open_editor_for_scene(content)
            self.status_bar.showMessage(_("Editing scene: {}").format(scene_title))
            
        except Exception as e:
            QMessageBox.critical(self, _("Error"), _("Failed to open scene: {}").format(e))
            
    def save_scene_content(self, content):
        """Zapisz zawartość sceny."""
        if not self.current_scene_manager or not self.current_scene_id:
            return
            
        try:
            success = self.current_scene_manager.update_scene(self.current_scene_id, content_rtf=content)
            if success:
                self.status_bar.showMessage(_("Scene saved successfully"))
                self._refresh_scenes_data()
            else:
                self.status_bar.showMessage(_("Failed to save scene"))
                QMessageBox.warning(self, _("Warning"), _("Failed to save scene"))
        except Exception as e:
            QMessageBox.critical(self, _("Error"), _("Failed to save scene: {}").format(e))
            
    def _refresh_scenes_data(self):
        """Odśwież dane scen zachowując selekcję."""
        try:
            scenes = self.current_scene_manager.list_scenes()
            self.project_tree.load_scenes(scenes, preserve_selection=True)
            
            # Odśwież kafelki jeśli są widoczne
            if hasattr(self.workspace, 'scenes_grid_view') and self.workspace.scenes_grid_view:
                self.workspace.scenes_grid_view.load_scenes(scenes)
                
        except Exception as e:
            QMessageBox.critical(self, _("Error"), _("Failed to load view: {}").format(e))
            
    def create_new_project(self, name):
        """Stwórz nowy projekt."""
        try:
            project_path = self.project_manager.create_project(name)
            self.show_projects_view()  # Odśwież listę projektów
            self.status_bar.showMessage(_("Created project: {}").format(name))
        except Exception as e:
            QMessageBox.critical(self, _("Error"), _("Failed to create project: {}").format(e))
            
    def create_new_scene(self, title):
        """Stwórz nową scenę."""
        if not self.current_scene_manager:
            return
            
        try:
            scene_id = self.current_scene_manager.create_scene(title)
            self._refresh_scenes_data()
            self.status_bar.showMessage(_("Created scene: {}").format(title))
        except Exception as e:
            QMessageBox.critical(self, _("Error"), _("Failed to create scene: {}").format(e))
            
    def show_settings(self):
        """Pokaż dialog ustawień."""
        dialog = SettingsDialog(self)
        dialog.themeChanged.connect(self.on_theme_changed)
        dialog.languageChanged.connect(self.on_language_changed)
        dialog.exec()
        
    def on_theme_changed(self, theme_name):
        """Obsługa zmiany motywu."""
        self.status_bar.showMessage(_("Applied theme: {}").format(theme_name))
        
        # Odśwież kafelki w widokach
        self.projects_view.refresh_theme()
        if hasattr(self.workspace, 'scenes_grid_view') and self.workspace.scenes_grid_view:
            self.workspace.scenes_grid_view.refresh_theme()
            
        # Odśwież ikony w drzewku
        self.project_tree.refresh_icons()
        
        # Jeśli jesteśmy w trybie fokusu, odśwież style trybu fokusu
        if self.focus_mode:
            self._apply_focus_window_style()
            if hasattr(self.workspace, 'current_editor') and self.workspace.current_editor:
                self._apply_focus_mode_style()
                
    def on_language_changed(self, language_code):
        """Obsługa zmiany języka."""
        # Zapisz wybrany język do ustawień
        from PySide6.QtCore import QSettings
        settings = QSettings()
        settings.setValue("language", language_code)
        
        # Informacja o konieczności restartu
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.information(
            self, 
            _("Language Changed"), 
            _("Language has been changed. Please restart the application to see changes.")
        )
        
    def toggle_focus_mode(self):
        """Przełącz tryb fokusu pisania."""
        self.focus_mode = not self.focus_mode
        
        if self.focus_mode:
            # Włącz tryb fokusu
            self.showFullScreen()
            self.status_bar.hide()
            
            # Ukryj nawigację po lewej stronie
            splitter = self.project_widget.findChild(QSplitter)
            if splitter:
                splitter.setSizes([0, 1200])  # Ukryj lewy panel całkowicie
                
            # Zastosuj styl zgodny z motywem do całego okna
            self._apply_focus_window_style()
                
            # Zastosuj styl do edytora
            if hasattr(self.workspace, 'current_editor') and self.workspace.current_editor:
                self._apply_focus_mode_style()
                
        else:
            # Wyłącz tryb fokusu
            self.showNormal()
            self.status_bar.show()
            
            # Przywróć nawigację
            splitter = self.project_widget.findChild(QSplitter)
            if splitter:
                splitter.setSizes([300, 900])  # Przywróć normalny podział
                
            # Przywróć normalny styl okna
            self._remove_focus_window_style()
                
            # Przywróć normalny styl edytora
            if hasattr(self.workspace, 'current_editor') and self.workspace.current_editor:
                self._remove_focus_mode_style()
    
    def _apply_focus_mode_style(self):
        """Zastosuj minimalistyczny styl w trybie fokusu."""
        editor = self.workspace.current_editor
        if not editor:
            return
            
        # Ukryj toolbar w trybie fokusu
        toolbar_widget = None
        for child in editor.findChildren(QWidget):
            if isinstance(child.layout(), QHBoxLayout) and child.findChild(QPushButton):
                toolbar_widget = child
                break
                
        if toolbar_widget:
            toolbar_widget.hide()
            
        # Pobierz kolory z aktualnego motywu
        from ui.styles.themes import ThemeManager
        theme_manager = ThemeManager()
        colors = theme_manager.get_theme_colors()
        
        # Zastosuj minimalistyczny styl zgodny z motywem
        editor.text_edit.setStyleSheet(f"""
            QTextEdit {{
                background-color: {colors["background"]};
                color: {colors["text"]};
                border: none;
                padding: 50px;
                font-size: 14pt;
                line-height: 1.6;
                selection-background-color: {colors["accent"]};
                selection-color: white;
            }}
        """)
        
    def _remove_focus_mode_style(self):
        """Usuń styl trybu fokusu."""
        editor = self.workspace.current_editor
        if not editor:
            return
            
        # Pokaż toolbar
        toolbar_widget = None
        for child in editor.findChildren(QWidget):
            if isinstance(child.layout(), QHBoxLayout) and child.findChild(QPushButton):
                toolbar_widget = child
                break
                
        if toolbar_widget:
            toolbar_widget.show()
            
        # Przywróć normalny styl
        editor.text_edit.setStyleSheet("")
        
    def _apply_focus_window_style(self):
        """Zastosuj styl okna w trybie fokusu."""
        from ui.styles.themes import ThemeManager
        theme_manager = ThemeManager()
        colors = theme_manager.get_theme_colors()
        
        # Zastosuj tło zgodne z motywem
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {colors["background"]};
            }}
            QWidget {{
                background-color: {colors["background"]};
                color: {colors["text"]};
            }}
        """)
        
    def _remove_focus_window_style(self):
        """Usuń styl okna trybu fokusu."""
        # Przywróć domyślny styl
        self.setStyleSheet("")


def main():
    app = QApplication(sys.argv)
    
    # Konfiguracja aplikacji
    app.setApplicationName("Pisarz")
    app.setApplicationVersion("1.0")
    app.setOrganizationName("Pisarz")
    
    # Inicjalizacja i18n - ustaw język z ustawień systemowych lub domyślny
    import i18n
    from PySide6.QtCore import QSettings
    settings = QSettings()
    saved_language = settings.value("language", "en_US")
    i18n.set_language(saved_language)
    
    # Ustaw większą domyślną czcionkę dla całego interfejsu
    from PySide6.QtGui import QFont
    font = QFont()
    font.setPointSize(10)  # Zwiększ z domyślnej 8-9 do 10pt
    app.setFont(font)
    
    # Załaduj i zastosuj zapisany motyw
    from ui.styles.themes import ThemeManager
    theme_manager = ThemeManager()
    theme_manager.set_theme(theme_manager.get_current_theme())
    
    # Stwórz i pokaż główne okno
    window = PisarzApp()
    window.show()
    
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())