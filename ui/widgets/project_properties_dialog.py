"""Project properties dialog for editing project metadata and settings."""

from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
                              QTabWidget, QWidget, QLabel, QLineEdit, QTextEdit,
                              QComboBox, QSpinBox, QCheckBox, QDateEdit, QPushButton,
                              QMessageBox, QGroupBox, QScrollArea)
from PySide6.QtCore import Qt, Signal, QDate
from PySide6.QtGui import QFont

from ui.base.base_dialog import BaseDialog
from ui.base.enhanced_theme_manager import EnhancedThemeManager
from i18n import _


class ProjectPropertiesDialog(BaseDialog):
    """Dialog for editing project properties and settings."""
    
    # Signal emitted when project properties are saved
    properties_saved = Signal(dict)  # project_data
    
    def __init__(self, project_data=None, parent=None):
        self.project_data = project_data or {}
        
        super().__init__(
            title=_("Project Properties"),
            width=600,
            height=500,
            modal=True,
            parent=parent
        )
        
        self.setup_ui()
        self.load_project_data()
        
    def setup_ui(self):
        """Setup the project properties dialog UI."""
        
        # Create tab widget for organizing properties
        self.tab_widget = QTabWidget()
        self.add_content_widget(self.tab_widget)
        
        # Create tabs
        self.create_general_tab()
        self.create_writing_tab()
        self.create_publishing_tab()
        self.create_settings_tab()
        
        # Button layout using BaseDialog functionality
        self.add_button_stretch()
        
        self.cancel_btn = self.create_custom_button(_("Cancel"), self.reject, "secondary")
        self.add_button(self.cancel_btn)
        
        self.save_btn = self.create_custom_button(_("Save"), self.save_properties, "primary")
        self.save_btn.setDefault(True)
        self.add_button(self.save_btn)
        
    def create_general_tab(self):
        """Create the general information tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Scroll area for the form
        scroll = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QFormLayout(scroll_widget)
        
        # Core Information Group
        core_group = QGroupBox(_("Core Information"))
        core_layout = QFormLayout(core_group)
        
        # Project Name (read-only, shows directory name)
        self.name_label = QLabel()
        self.name_label.setStyleSheet("color: #666; font-style: italic;")
        core_layout.addRow(_("Project Name:"), self.name_label)
        
        # Display Title
        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText(_("Enter project title..."))
        core_layout.addRow(_("Display Title:"), self.title_edit)
        
        # Author
        self.author_edit = QLineEdit()
        self.author_edit.setPlaceholderText(_("Enter author name..."))
        core_layout.addRow(_("Author:"), self.author_edit)
        
        # Genre
        self.genre_combo = QComboBox()
        self.genre_combo.setEditable(True)
        self.genre_combo.addItems([
            _("Novel"),
            _("Short Story"),
            _("Poetry"),
            _("Non-fiction"),
            _("Biography"),
            _("Science Fiction"),
            _("Fantasy"),
            _("Mystery"),
            _("Romance"),
            _("Thriller"),
            _("Historical Fiction"),
            _("Literary Fiction"),
            _("Children's Book"),
            _("Young Adult"),
            _("Memoir"),
            _("Other")
        ])
        core_layout.addRow(_("Genre:"), self.genre_combo)
        
        # Language
        self.language_combo = QComboBox()
        self.language_combo.addItems([
            ("en", _("English")),
            ("pl", _("Polish")),
            ("de", _("German")),
            ("fr", _("French")),
            ("es", _("Spanish")),
            ("it", _("Italian")),
            ("pt", _("Portuguese")),
            ("ru", _("Russian")),
            ("other", _("Other"))
        ])
        core_layout.addRow(_("Language:"), self.language_combo)
        
        scroll_layout.addWidget(core_group)
        
        # Description Group
        desc_group = QGroupBox(_("Description"))
        desc_layout = QVBoxLayout(desc_group)
        
        self.description_edit = QTextEdit()
        self.description_edit.setPlaceholderText(_("Enter project description or synopsis..."))
        self.description_edit.setMaximumHeight(120)
        desc_layout.addWidget(self.description_edit)
        
        scroll_layout.addWidget(desc_group)
        
        # Tags Group
        tags_group = QGroupBox(_("Tags"))
        tags_layout = QVBoxLayout(tags_group)
        
        self.tags_edit = QLineEdit()
        self.tags_edit.setPlaceholderText(_("Enter tags separated by commas..."))
        tags_layout.addWidget(self.tags_edit)
        
        tags_help = QLabel(_("Use tags to categorize and organize your projects"))
        tags_help.setFont(QFont("Arial", 8))
        tags_help.setStyleSheet("color: #666;")
        tags_layout.addWidget(tags_help)
        
        scroll_layout.addWidget(tags_group)
        
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)
        
        self.tab_widget.addTab(tab, _("General"))
        
    def create_writing_tab(self):
        """Create the writing details tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Scroll area for the form
        scroll = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QFormLayout(scroll_widget)
        
        # Writing Progress Group
        progress_group = QGroupBox(_("Writing Progress"))
        progress_layout = QFormLayout(progress_group)
        
        # Status
        self.status_combo = QComboBox()
        self.status_combo.addItems([
            (_("Draft"), "draft"),
            (_("In Progress"), "in_progress"),
            (_("First Draft Complete"), "first_draft"),
            (_("Revision"), "revision"),
            (_("Editing"), "editing"),
            (_("Final Draft"), "final_draft"),
            (_("Completed"), "completed"),
            (_("Published"), "published"),
            (_("On Hold"), "on_hold"),
            (_("Abandoned"), "abandoned")
        ])
        progress_layout.addRow(_("Status:"), self.status_combo)
        
        # Target Word Count
        self.target_word_count_spin = QSpinBox()
        self.target_word_count_spin.setRange(0, 1000000)
        self.target_word_count_spin.setValue(50000)
        self.target_word_count_spin.setSuffix(_(" words"))
        progress_layout.addRow(_("Target Word Count:"), self.target_word_count_spin)
        
        scroll_layout.addWidget(progress_group)
        
        # Writing Goals Group
        goals_group = QGroupBox(_("Writing Goals"))
        goals_layout = QFormLayout(goals_group)
        
        # Daily Word Goal
        self.daily_word_goal_spin = QSpinBox()
        self.daily_word_goal_spin.setRange(0, 10000)
        self.daily_word_goal_spin.setValue(500)
        self.daily_word_goal_spin.setSuffix(_(" words/day"))
        goals_layout.addRow(_("Daily Word Goal:"), self.daily_word_goal_spin)
        
        # Weekly Word Goal
        self.weekly_word_goal_spin = QSpinBox()
        self.weekly_word_goal_spin.setRange(0, 70000)
        self.weekly_word_goal_spin.setValue(3500)
        self.weekly_word_goal_spin.setSuffix(_(" words/week"))
        goals_layout.addRow(_("Weekly Word Goal:"), self.weekly_word_goal_spin)
        
        scroll_layout.addWidget(goals_group)
        
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)
        
        self.tab_widget.addTab(tab, _("Writing"))
        
    def create_publishing_tab(self):
        """Create the publishing information tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Scroll area for the form
        scroll = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QFormLayout(scroll_widget)
        
        # Publishing Information Group
        pub_group = QGroupBox(_("Publishing Information"))
        pub_layout = QFormLayout(pub_group)
        
        # Publisher
        self.publisher_edit = QLineEdit()
        self.publisher_edit.setPlaceholderText(_("Enter publisher name..."))
        pub_layout.addRow(_("Publisher:"), self.publisher_edit)
        
        # ISBN
        self.isbn_edit = QLineEdit()
        self.isbn_edit.setPlaceholderText(_("Enter ISBN..."))
        pub_layout.addRow(_("ISBN:"), self.isbn_edit)
        
        # Publication Date
        self.publication_date_edit = QDateEdit()
        self.publication_date_edit.setDate(QDate.currentDate())
        self.publication_date_edit.setCalendarPopup(True)
        self.publication_date_edit.setSpecialValueText(_("Not set"))
        pub_layout.addRow(_("Publication Date:"), self.publication_date_edit)
        
        scroll_layout.addWidget(pub_group)
        
        # Copyright Group
        copyright_group = QGroupBox(_("Copyright"))
        copyright_layout = QVBoxLayout(copyright_group)
        
        self.copyright_edit = QTextEdit()
        self.copyright_edit.setPlaceholderText(_("Enter copyright information..."))
        self.copyright_edit.setMaximumHeight(80)
        copyright_layout.addWidget(self.copyright_edit)
        
        scroll_layout.addWidget(copyright_group)
        
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)
        
        self.tab_widget.addTab(tab, _("Publishing"))
        
    def create_settings_tab(self):
        """Create the project settings tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Scroll area for the form
        scroll = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        
        # Editor Settings Group
        editor_group = QGroupBox(_("Editor Settings"))
        editor_layout = QVBoxLayout(editor_group)
        
        # Default Scene Template
        template_label = QLabel(_("Default Scene Template:"))
        editor_layout.addWidget(template_label)
        
        self.scene_template_edit = QTextEdit()
        self.scene_template_edit.setPlaceholderText(_("Enter default RTF template for new scenes..."))
        self.scene_template_edit.setMaximumHeight(100)
        editor_layout.addWidget(self.scene_template_edit)
        
        scroll_layout.addWidget(editor_group)
        
        # Backup Settings Group
        backup_group = QGroupBox(_("Backup Settings"))
        backup_layout = QVBoxLayout(backup_group)
        
        self.auto_backup_check = QCheckBox(_("Enable automatic backups"))
        self.auto_backup_check.setChecked(True)
        backup_layout.addWidget(self.auto_backup_check)
        
        backup_help = QLabel(_("Automatically create backups of your project"))
        backup_help.setFont(QFont("Arial", 8))
        backup_help.setStyleSheet("color: #666;")
        backup_layout.addWidget(backup_help)
        
        scroll_layout.addWidget(backup_group)
        
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)
        
        self.tab_widget.addTab(tab, _("Settings"))
        
    def load_project_data(self):
        """Load project data into the form fields."""
        if not self.project_data:
            return
            
        # General tab
        self.name_label.setText(self.project_data.get('name') or '')
        self.title_edit.setText(self.project_data.get('title') or '')
        self.author_edit.setText(self.project_data.get('author') or '')
        
        # Genre
        genre = self.project_data.get('genre') or ''
        if genre:
            index = self.genre_combo.findText(genre)
            if index >= 0:
                self.genre_combo.setCurrentIndex(index)
            else:
                self.genre_combo.setCurrentText(genre)
        
        # Language
        language = self.project_data.get('language') or 'en'
        for i in range(self.language_combo.count()):
            if self.language_combo.itemData(i) == language:
                self.language_combo.setCurrentIndex(i)
                break
        
        self.description_edit.setPlainText(self.project_data.get('description') or '')
        self.tags_edit.setText(self.project_data.get('tags') or '')
        
        # Writing tab
        status = self.project_data.get('status') or 'draft'
        for i in range(self.status_combo.count()):
            if self.status_combo.itemData(i) == status:
                self.status_combo.setCurrentIndex(i)
                break
        
        self.target_word_count_spin.setValue(self.project_data.get('target_word_count') or 50000)
        self.daily_word_goal_spin.setValue(self.project_data.get('daily_word_goal') or 500)
        self.weekly_word_goal_spin.setValue(self.project_data.get('weekly_word_goal') or 3500)
        
        # Publishing tab
        self.publisher_edit.setText(self.project_data.get('publisher') or '')
        self.isbn_edit.setText(self.project_data.get('isbn') or '')
        
        # Publication date
        pub_date = self.project_data.get('publication_date') or ''
        if pub_date:
            try:
                date = QDate.fromString(pub_date, Qt.DateFormat.ISODate)
                self.publication_date_edit.setDate(date)
            except:
                pass
        
        self.copyright_edit.setPlainText(self.project_data.get('copyright') or '')
        
        # Settings tab
        self.scene_template_edit.setPlainText(self.project_data.get('default_scene_template') or '')
        auto_backup = self.project_data.get('auto_backup_enabled')
        self.auto_backup_check.setChecked(auto_backup if auto_backup is not None else True)
        
    def save_properties(self):
        """Save the project properties."""
        # Validate required fields
        if not self.title_edit.text().strip():
            QMessageBox.warning(self, _("Validation Error"), 
                              _("Display title cannot be empty."))
            self.title_edit.setFocus()
            return
            
        # Collect all the data
        properties = {
            'title': self.title_edit.text().strip(),
            'author': self.author_edit.text().strip(),
            'genre': self.genre_combo.currentText().strip(),
            'language': self.language_combo.currentData() or 'en',
            'description': self.description_edit.toPlainText().strip(),
            'tags': self.tags_edit.text().strip(),
            'status': self.status_combo.currentData() or 'draft',
            'target_word_count': self.target_word_count_spin.value(),
            'daily_word_goal': self.daily_word_goal_spin.value(),
            'weekly_word_goal': self.weekly_word_goal_spin.value(),
            'publisher': self.publisher_edit.text().strip(),
            'isbn': self.isbn_edit.text().strip(),
            'publication_date': self.publication_date_edit.date().toString(Qt.DateFormat.ISODate),
            'copyright': self.copyright_edit.toPlainText().strip(),
            'default_scene_template': self.scene_template_edit.toPlainText().strip(),
            'auto_backup_enabled': self.auto_backup_check.isChecked()
        }
        
        # Emit signal with the properties
        self.properties_saved.emit(properties)
        self.accept()