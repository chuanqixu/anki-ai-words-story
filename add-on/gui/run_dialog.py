from aqt import mw

from aqt.browser import Browser
from PyQt6.QtCore import Qt, QSettings
from PyQt6.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit, QDialog, QComboBox

from .prompt_window import PromptConfigDialog
from ..ai.provider import providers
from .provider import *
from ..ankiaddonconfig import ConfigWindow, ConfigManager
from .config_window import conf
from copy import deepcopy


class RunDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(mw)
        # Workaround for dialog error (search: FIXCOL)
        self.par = parent
        self.settings = QSettings('Anki', 'Anki Quick AI')
        self.initUI()

    def initUI(self):
        # Main layout
        layout = QVBoxLayout()
        self.setLayout(layout)
        self.default_provider = mw.addonManager.getConfig(__name__)["ai_config"]["default_provider"]
        self.prompt_dict = mw.addonManager.getConfig(__name__)["prompt"]

        # reload provider config
        provider_name = self.settings.value('ProviderName', self.default_provider)
        self.provider_config = conf.get("ai_config." + provider_name)

        # provider
        provider_layout = QHBoxLayout()
        provider_label = QLabel("Provider:")
        provider_layout.addWidget(provider_label)
        self.provider_box = QComboBox(self)
        self.provider_box.addItems(providers)
        self.provider_box.setCurrentText(provider_name)
        provider_layout.addWidget(self.provider_box)
        self.provider_box.currentIndexChanged.connect(self.provider_changed)
        self.curr_provider_name = self.provider_box.currentText()
        layout.addLayout(provider_layout)

        # Configure Provider
        self.provider_config_button = QPushButton("Configure Provider")
        self.provider_config_button.clicked.connect(self.config_provider)
        layout.addWidget(self.provider_config_button)

        layout.addSpacing(20)

        # reload last prompt name
        prompt_name = self.settings.value('PromptName')

        # prompt
        input_layout = QHBoxLayout()
        note_field_label = QLabel("Prompt:")
        input_layout.addWidget(note_field_label)
        self.prompt_box = QComboBox(self)
        self.prompt_box.addItems(self.prompt_dict.keys())
        if prompt_name:
            self.prompt_box.setCurrentText(prompt_name)
        input_layout.addWidget(self.prompt_box)
        self.prompt_box.currentIndexChanged.connect(self.prompt_changed)
        self.curr_prompt_name = self.prompt_box.currentText()
        layout.addLayout(input_layout)

        # Browse query
        if isinstance(self.par, Browser):
            cards = self.par.selected_cards()
            notesId = []

            for card_id in cards:
                note_id = mw.col.getCard(card_id).note().id
                if note_id not in notesId:
                    notesId.append(note_id)

            if len(notesId) > 0:
                query = " OR ".join([f"nid:{note_id}" for note_id in notesId])
            else:
                query = self.par.form.searchEdit.lineEdit().text()
                if not query:
                    query = "deck:" + mw.col.decks.current()["name"]

        else:
            query = self.prompt_dict[self.curr_prompt_name]["default_query"]

        input_layout = QHBoxLayout()
        query_label = QLabel("Browse Query:")
        input_layout.addWidget(query_label)
        self.input_field_browse_query = QLineEdit(query)
        input_layout.addWidget(self.input_field_browse_query)
        layout.addLayout(input_layout)

        # Configure Prompt 
        self.prompt_config_button = QPushButton("Configure Prompt and Placeholder")
        self.prompt_config_button.clicked.connect(self.config_prompt)
        layout.addWidget(self.prompt_config_button)

        # Label
        instruction_label = QLabel("Configuration only applies this time.\nPlease configure in the configuration page for future usage.")
        layout.addWidget(instruction_label)

        # Run button
        self.run_button = QPushButton("Run")
        # one connect in controller.py
        self.run_button.setFixedSize(100, 40)  # set the size of the button
        layout.addWidget(self.run_button, 0, Qt.AlignmentFlag.AlignCenter)  # align button to the center

        # Cancel button
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.close)
        cancel_button.setFixedSize(100, 40)  # set the size of the button
        layout.addWidget(cancel_button, 0, Qt.AlignmentFlag.AlignCenter)  # align button to the center

    def provider_changed(self, index):
        self.curr_provider_name = self.provider_box.itemText(index)

    def config_provider(self):
        provider_config_dialog = QDialog(self)
        try:
            run_conf = deepcopy(conf)
        except:
            run_conf = ConfigManager()
        config_window = ConfigWindow(run_conf)
        config_window.on_open()
        provider_layout = globals()["ai_config_layout_" + self.provider_box.currentText()](config_window, run_conf)
        provider_config_dialog.setLayout(provider_layout)

        button_layout = QHBoxLayout()
        # save button
        save_button = QPushButton("Save")
        def save():
            self.provider_config = config_window.conf._config["ai_config"][self.curr_provider_name]
            provider_config_dialog.close()
        save_button.clicked.connect(save)
        save_button.setFixedSize(100, 40)  # set the size of the button
        button_layout.addWidget(save_button, 0, Qt.AlignmentFlag.AlignCenter)  # align button to the center

        # Cancel button
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(provider_config_dialog.close)
        cancel_button.setFixedSize(100, 40)  # set the size of the button
        button_layout.addWidget(cancel_button, 0, Qt.AlignmentFlag.AlignCenter)  # align button to the center
        provider_layout.addLayout(button_layout)

        # raise Exception(provider_layout.config_window.conf._config)

        provider_config_dialog.exec()

    def prompt_changed(self, index):
        self.curr_prompt_name = self.prompt_box.itemText(index)

    def config_prompt(self):
        prompt_config_dialog = PromptConfigDialog(config_data=self.prompt_dict[self.curr_prompt_name], in_run_dialog=True)
        prompt_config_dialog.exec()
        if prompt_config_dialog.is_changed:
            self.prompt_dict[self.curr_prompt_name] = prompt_config_dialog.config_data

    def closeEvent(self, event):
        self.settings.setValue('ProviderName', self.curr_provider_name)
        self.settings.setValue('PromptName', self.curr_prompt_name)
        super().closeEvent(event)
