import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QTabWidget,
    QPushButton, QLabel, QLineEdit, QFileDialog, QComboBox, QCheckBox, QGroupBox,
    QToolBar, QStyle, QSpacerItem, QSizePolicy, QMessageBox, QListWidget,
    QDialog, QTableWidget, QTableWidgetItem, QHeaderView, QSlider, QFrame, QDockWidget
)
from PySide6 import QtWidgets
from PySide6.QtGui import QIcon, QAction
from PySide6.QtCore import Qt, QUrl, QSettings
import os
import traceback
import logging
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cleanvid import VidCleaner, SUBTITLE_DEFAULT_LANG, VIDEO_DEFAULT_PARAMS, AUDIO_DEFAULT_PARAMS


class CleanVidGUI(QMainWindow):

    def handle_play(self):
        logging.info("Play button pressed")
        try:
            self.video_player.play()
            logging.info("Playback started")
        except Exception as e:
            logging.exception("Failed to start playback: %s", e)


    def show_subtitle_editor(self):
        # Avoid re-adding the editor if already shown
        if getattr(self, '_subtitle_editor_shown', False):
            return
        # Stop live subtitle updates while editing (guard against deleted widgets)
        try:
            if getattr(self, '_live_connected', False):
                self.video_player.positionChanged.disconnect(self.update_live_subtitle)
                self._live_connected = False
        except Exception:
            pass
        # Clear main area (remove widgets and nested layouts)
        try:
            self._clear_layout(self.main_area)
        except Exception:
            pass


        # Push the checkbox down so it sits directly above the subtitle table
        try:
            self.main_area.addStretch(1)
        except Exception:
            pass
        # 'Show only muted' checkbox (placed just above the table)
        self.show_only_muted_chk = QCheckBox("Show only muted matches")
        self.show_only_muted_chk.stateChanged.connect(self.filter_subtitle_table)
        self.main_area.addWidget(self.show_only_muted_chk)

        # Subtitle Table/Grid
        self.subtitle_table = QTableWidget()
        self.subtitle_table.setColumnCount(6)
        self.subtitle_table.setHorizontalHeaderLabels([
            "Id", "Start", "End", "Original Text", "Replacement Text", "Mute"
        ])
        from PySide6.QtWidgets import QHeaderView
        header = self.subtitle_table.horizontalHeader()
        # Make Id, Start, End, and Mute auto-size to contents and allow user resizing.
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        # Original and Replacement should take remaining space but remain adjustable
        # Make Original and Replacement interactive so we can set sensible starting widths
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        # Reduce subtitle table height so it doesn't take too much space
        self.subtitle_table.setMaximumHeight(220)
        self.main_area.addWidget(self.subtitle_table)

        # Mark editor as shown
        self._subtitle_editor_shown = True

        # Load subtitles immediately from the global top-level `self.subs_file`.
        # Keep connection on the top-level field so further changes auto-update.
        try:
            # connect the top-level subs field to reload while editor is open
            if hasattr(self, 'subs_file'):
                self.subs_file.textChanged.connect(self.load_subtitles_to_table)
            # Trigger initial load to populate the table right away
            self.load_subtitles_to_table()
        except Exception:
            logging.debug("Failed to load subtitles on entering subtitle editor")

    def filter_subtitle_table(self):
        show_only_muted = self.show_only_muted_chk.isChecked()
        for row in range(self.subtitle_table.rowCount()):
            mute_chk = self.subtitle_table.cellWidget(row, 5)
            if mute_chk is not None and isinstance(mute_chk, QCheckBox):
                self.subtitle_table.setRowHidden(row, show_only_muted and not mute_chk.isChecked())

    def load_subtitles_to_table(self):
        import pysrt
        import re
        # Prefer editor field if present, otherwise use top-level subs field
        editor_field = getattr(self, 'subs_file_edit', None)
        if editor_field is not None:
            srt_path = editor_field.text().strip()
        else:
            srt_path = self.subs_file.text().strip() if hasattr(self, 'subs_file') else ""
        if not srt_path or not os.path.isfile(srt_path):
            self.subtitle_table.setRowCount(0)
            return
        # Load swears
        swears_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'swears.txt')
        swears = {}
        with open(swears_path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                parts = line.split('|')
                swears[parts[0].lower()] = parts[1] if len(parts) > 1 else "*****"
        # Build regex using word boundaries
        pattern = r'\b(' + '|'.join(re.escape(k) for k in swears.keys()) + r')\b'
        replacer = re.compile(pattern, re.IGNORECASE) if swears else None

        subs = pysrt.open(srt_path)
        self.subtitle_table.setRowCount(len(subs))
        for i, sub in enumerate(subs):
            orig = sub.text
            repl = orig
            matched = False
            if replacer:
                def replace_func(m):
                    matched_word = m.group(0).lower()
                    matched = True
                    return swears.get(matched_word, "*****")
                # Find and replace all matches
                if replacer.search(orig):
                    repl = replacer.sub(lambda m: swears[m.group(0).lower()], orig)
                    matched = True
            self.subtitle_table.setItem(i, 0, QTableWidgetItem(str(sub.index)))
            self.subtitle_table.setItem(i, 1, QTableWidgetItem(str(sub.start)))
            self.subtitle_table.setItem(i, 2, QTableWidgetItem(str(sub.end)))
            self.subtitle_table.setItem(i, 3, QTableWidgetItem(orig))
            # Editable replacement text
            repl_item = QTableWidgetItem(repl)
            # Highlight replaced cells so muted matches are obvious
            if repl != orig:
                from PySide6.QtGui import QColor
                repl_item.setBackground(QColor("yellow"))
            self.subtitle_table.setItem(i, 4, repl_item)
            # Mute checkbox: mark if replacement differs from original
            mute_chk = QCheckBox()
            if repl != orig:
                mute_chk.setChecked(True)
            self.subtitle_table.setCellWidget(i, 5, mute_chk)

        # After populating, compute sensible starting widths.
        try:
            from PySide6.QtGui import QFontMetrics
            fm = QFontMetrics(self.subtitle_table.font())
            # compute pixel width of the longest original and replacement text
            max_orig_px = 0
            max_repl_px = 0
            for row in range(self.subtitle_table.rowCount()):
                orig_item = self.subtitle_table.item(row, 3)
                repl_item = self.subtitle_table.item(row, 4)
                if orig_item:
                    max_orig_px = max(max_orig_px, fm.horizontalAdvance(orig_item.text()))
                if repl_item:
                    max_repl_px = max(max_repl_px, fm.horizontalAdvance(repl_item.text()))
            padding = 80
            # Small columns: Id, Start, End (keep sizes) and Mute (ensure visible)
            self.subtitle_table.setColumnWidth(0, 60)
            self.subtitle_table.setColumnWidth(1, 120)
            self.subtitle_table.setColumnWidth(2, 120)
            # Ensure mute checkbox column has enough room to show the checkbox
            mute_col_w = 80
            self.subtitle_table.setColumnWidth(5, mute_col_w)
            # Text columns: start with max content width (capped) but enforce sensible minima
            max_allowed = 1400
            min_text_w = 300
            orig_w = min(max_orig_px + padding, max_allowed)
            repl_w = min(max_repl_px + padding, max_allowed)
            self.subtitle_table.setColumnWidth(3, max(min_text_w, orig_w))
            self.subtitle_table.setColumnWidth(4, max(min_text_w, repl_w))
            # Allow horizontal scrolling for very narrow windows
            try:
                # Use ScrollPerPixel if available; fall back to ScrollPerItem
                mode = getattr(QtWidgets.QAbstractItemView, 'ScrollPerPixel', None) or getattr(QtWidgets.QAbstractItemView, 'ScrollPerItem', None)
                if mode is not None:
                    self.subtitle_table.setHorizontalScrollMode(mode)
            except Exception:
                pass
        except Exception:
            pass
        # Restore saved widths if present
        try:
            self.load_subtitle_column_widths()
        except Exception:
            pass
        # Connect resize signal to save widths when the user adjusts columns
        try:
            self.subtitle_table.horizontalHeader().sectionResized.connect(self._on_subtitle_section_resized)
        except Exception:
            pass

    def pick_file(self, line_edit, file_filter, must_exist=False):
        # Always use getOpenFileName for picking files (never getSaveFileName)
        file, _ = QFileDialog.getOpenFileName(self, "Select File", "", file_filter)
        if file:
            line_edit.setText(file)
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CleanVid - HandBrake Style")
        self.setMinimumSize(900, 600)
        self.setStyleSheet("""
            QMainWindow { background: #f4f4f4; }
            QLabel, QCheckBox, QComboBox, QPushButton, QLineEdit {
                color: #222;
                font-size: 14px;
            }
            QTabWidget::pane { border: 1px solid #bbb; }
            QTabBar::tab { background: #eaeaea; color: #222; padding: 8px; }
            QTabBar::tab:selected { background: #d0d0d0; }
            QToolBar { background: #eaeaea; border: none; }
        """)
        self.init_ui()
        # Track whether subtitle editor is currently shown to avoid duplicates
        self._subtitle_editor_shown = False

    def init_ui(self):
        # Toolbar
        toolbar = QToolBar()
        toolbar.setMovable(False)
        self.addToolBar(toolbar)
        # Main View action in toolbar (Home button first)
        main_view_action = QAction(QIcon.fromTheme("go-home"), "Main View", self)
        main_view_action.triggered.connect(self.show_main_view)
        toolbar.addAction(main_view_action)

        open_action = QAction(QIcon.fromTheme("document-open"), "Open Source", self)
        open_action.triggered.connect(self.open_source)
        toolbar.addAction(open_action)

        # Edit Subtitles action in toolbar
        edit_subs_action = QAction(QIcon.fromTheme("document-edit"), "Edit Subtitles", self)
        edit_subs_action.triggered.connect(self.show_subtitle_editor)
        toolbar.addAction(edit_subs_action)

        # queue feature removed

        # Central widget and main layout
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QtWidgets.QVBoxLayout(central)

        # --- Persistent Source/Subs fields at top ---
        filebar = QHBoxLayout()
        filebar.addWidget(QLabel("Source:"))
        self.source_file = QLineEdit()
        self.source_file.setPlaceholderText("Select source video file...")
        self.source_file_btn = QPushButton("...")
        self.source_file_btn.clicked.connect(lambda: self.pick_file(self.source_file, "Video Files (*.mp4 *.mkv *.avi *.mov)", True))
        filebar.addWidget(self.source_file)
        filebar.addWidget(self.source_file_btn)
        filebar.addWidget(QLabel("Subtitles:"))
        self.subs_file = QLineEdit()
        self.subs_file.setPlaceholderText("Select subtitle file...")
        self.subs_file_btn = QPushButton("...")
        self.subs_file_btn.clicked.connect(lambda: self.pick_file(self.subs_file, "Subtitle Files (*.srt *.ass)", True))
        filebar.addWidget(self.subs_file)
        filebar.addWidget(self.subs_file_btn)
        filebar.addStretch()
        main_layout.addLayout(filebar)

        # Main area (below filebar)
        content_layout = QHBoxLayout()

        # queue UI removed

        # Main area (right) - placeholder for future controls
        self.main_area = QtWidgets.QVBoxLayout()
        # Reduce default spacing so controls are closer together
        self.main_area.setSpacing(6)
        self.main_area.setContentsMargins(6, 6, 6, 6)
        main_area_widget = QWidget()
        main_area_widget.setLayout(self.main_area)
        content_layout.addWidget(main_area_widget, 4)

        main_layout.addLayout(content_layout)

        # --- Video preview widget below filebar ---
        from PySide6.QtMultimediaWidgets import QVideoWidget
        from PySide6.QtMultimedia import QMediaPlayer
        self.video_player = QMediaPlayer()
        self.video_widget = QVideoWidget()
        self.video_player.setVideoOutput(self.video_widget)
        # Make video widget larger and allow it to expand
        self.video_widget.setMinimumHeight(420)
        self.video_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.main_area.addWidget(self.video_widget, 10)

        # Playback controls with standard icons
        controls_layout = QHBoxLayout()
        self.play_btn = QPushButton()
        self.play_btn.setIcon(QIcon.fromTheme("media-playback-start"))
        self.pause_btn = QPushButton()
        self.pause_btn.setIcon(QIcon.fromTheme("media-playback-pause"))
        self.stop_btn = QPushButton()
        self.stop_btn.setIcon(QIcon.fromTheme("media-playback-stop"))
        self.backward_btn = QPushButton()
        self.backward_btn.setIcon(QIcon.fromTheme("media-seek-backward"))
        self.forward_btn = QPushButton()
        self.forward_btn.setIcon(QIcon.fromTheme("media-seek-forward"))
        self.seek_slider = QSlider(Qt.Orientation.Horizontal)
        self.seek_slider.setMinimum(0)
        self.seek_slider.setMaximum(100)
        controls_layout.addWidget(self.backward_btn)
        controls_layout.addWidget(self.play_btn)
        controls_layout.addWidget(self.pause_btn)
        controls_layout.addWidget(self.stop_btn)
        controls_layout.addWidget(self.forward_btn)
        controls_layout.addWidget(self.seek_slider)
        self.main_area.addLayout(controls_layout)

        # Route playback through handler for logging and safety
        self.play_btn.clicked.connect(self.handle_play)
        self.pause_btn.clicked.connect(self.video_player.pause)
        self.stop_btn.clicked.connect(self.video_player.stop)
        self.backward_btn.clicked.connect(lambda: self.seek_relative(-5000))
        self.forward_btn.clicked.connect(lambda: self.seek_relative(5000))
        self.seek_slider.sliderMoved.connect(self.seek_video)
        self.video_player.positionChanged.connect(self.update_seek_slider)
        self.video_player.durationChanged.connect(self.update_seek_range)

        # Live subtitle display in a smaller, bordered field
        from PySide6.QtWidgets import QFrame, QVBoxLayout
        sub_frame = QFrame()
        sub_frame.setFrameShape(QFrame.Shape.Box)
        sub_frame.setLineWidth(1)
        sub_layout = QVBoxLayout(sub_frame)
        self.live_sub_label = QLabel("")
        # Smaller subtitle box and font
        self.live_sub_label.setStyleSheet("font-size: 12px; color: #222; background: #f9f9f9; padding: 4px;")
        self.live_sub_label.setMaximumHeight(40)
        sub_layout.addWidget(self.live_sub_label)
        # Give the subtitle frame a smaller max height too
        sub_frame.setMaximumHeight(60)
        self.main_area.addWidget(sub_frame)
        self.video_player.positionChanged.connect(self.update_live_subtitle)
        # Track live connection
        self._live_connected = True

        # Subtitles Offset removed per user request.

        # Connect source file change to load video and subtitles for live view
        self.source_file.textChanged.connect(self.load_video_preview)
        self.subs_file.textChanged.connect(self.load_subtitles_for_live)

        # Live subtitles cache
        self.live_subs = []

    def seek_relative(self, ms):
        pos = self.video_player.position() + ms
        pos = max(0, min(pos, self.video_player.duration()))
        self.video_player.setPosition(pos)
    def seek_video(self, value):
        duration = self.video_player.duration()
        if duration > 0:
            pos = int(duration * value / 100)
            self.video_player.setPosition(pos)

    def update_seek_slider(self, pos):
        duration = self.video_player.duration()
        if duration > 0:
            self.seek_slider.blockSignals(True)
            self.seek_slider.setValue(int(pos * 100 / duration))
            self.seek_slider.blockSignals(False)

    def update_seek_range(self, duration):
        self.seek_slider.setEnabled(duration > 0)

    def load_subtitles_for_live(self):
        import pysrt
        srt_path = self.subs_file.text().strip()
        self.live_subs = []
        if srt_path and os.path.isfile(srt_path):
            subs = pysrt.open(srt_path)
            # If edited subtitles exist, use them
            # Otherwise, use original
            self.live_subs = [(sub.start.ordinal, sub.end.ordinal, sub.text) for sub in subs]

    def _clear_layout(self, layout):
        """Recursively remove all items from a QLayout, including nested layouts and widgets.
        This ensures layouts added with addLayout() are removed, preventing duplicate
        controls when switching views.
        """
        try:
            while layout.count():
                item = layout.takeAt(0)
                if item is None:
                    continue
                w = item.widget()
                if w is not None:
                    w.setParent(None)
                else:
                    child = item.layout()
                    if child is not None:
                        self._clear_layout(child)
        except Exception:
            pass

    def update_live_subtitle(self, pos):
        # Show the current subtitle line based on video position
        if not getattr(self, 'live_subs', None):
            return
        for start, end, text in self.live_subs:
            if start <= pos <= end:
                lbl = getattr(self, 'live_sub_label', None)
                if lbl:
                    try:
                        lbl.setText(text)
                    except Exception:
                        logging.debug("Live subtitle label deleted while setting text; disconnecting")
                        try:
                            if getattr(self, '_live_connected', False):
                                self.video_player.positionChanged.disconnect(self.update_live_subtitle)
                                self._live_connected = False
                        except Exception:
                            pass
                break
        else:
            lbl = getattr(self, 'live_sub_label', None)
            if lbl:
                try:
                    lbl.setText("")
                except Exception:
                    logging.debug("Live subtitle label deleted while clearing text; disconnecting")
                    try:
                        if getattr(self, '_live_connected', False):
                            self.video_player.positionChanged.disconnect(self.update_live_subtitle)
                            self._live_connected = False
                    except Exception:
                        pass

    def show_main_view(self):
        # Clear non-video widgets from main area and show main controls
        try:
            # Clear reference to live_sub_label so we can reliably recreate it
            try:
                self.live_sub_label = None
            except Exception:
                pass
            # Remove all widgets and nested layouts from the main area so we
            # don't leave behind layouts (addLayout) that cause duplicates.
            self._clear_layout(self.main_area)
        except Exception:
            logging.exception("Error while clearing main area")
        # Ensure video_widget is present exactly once
        try:
            if self.main_area.indexOf(self.video_widget) == -1:
                self.main_area.addWidget(self.video_widget)
        except Exception:
            # indexOf may not be available on some layouts; fall back safely
            if not getattr(self.video_widget, 'parent', None):
                self.main_area.addWidget(self.video_widget)
        # Recreate live subtitle frame/label if missing
        try:
            if not getattr(self, 'live_sub_label', None):
                # recreate the live subtitle frame
                from PySide6.QtWidgets import QFrame, QVBoxLayout
                sub_frame = QFrame()
                sub_frame.setFrameShape(QFrame.Shape.Box)
                sub_frame.setLineWidth(1)
                sub_layout = QVBoxLayout(sub_frame)
                self.live_sub_label = QLabel("")
                self.live_sub_label.setStyleSheet("font-size: 12px; color: #222; background: #f9f9f9; padding: 4px;")
                self.live_sub_label.setMaximumHeight(40)
                sub_layout.addWidget(self.live_sub_label)
                sub_frame.setMaximumHeight(60)
                self.main_area.addWidget(sub_frame)
        except Exception:
            logging.exception("Failed to recreate live subtitle frame")
        # Offset widget is persistent and lives outside `main_area`.
        # Reset subtitle editor shown flag
        try:
            self._subtitle_editor_shown = False
        except Exception:
            pass
        # Reconnect live subtitle updates (avoid multiple connects)
        try:
            if not getattr(self, '_live_connected', False):
                self.video_player.positionChanged.connect(self.update_live_subtitle)
                self._live_connected = True
        except Exception:
            pass

    # Persist and restore subtitle table column widths
    def _on_subtitle_section_resized(self, logicalIndex, oldSize, newSize):
        try:
            self.save_subtitle_column_widths()
        except Exception:
            pass

    def save_subtitle_column_widths(self):
        try:
            if not hasattr(self, 'subtitle_table'):
                return
            widths = []
            for col in range(self.subtitle_table.columnCount()):
                widths.append(self.subtitle_table.columnWidth(col))
            s = QSettings('cleanvid', 'CleanVid')
            s.setValue('subtitle_table/widths', widths)
        except Exception:
            logging.debug('Failed to save subtitle column widths')

    def load_subtitle_column_widths(self):
        try:
            if not hasattr(self, 'subtitle_table'):
                return
            s = QSettings('cleanvid', 'CleanVid')
            val = s.value('subtitle_table/widths')
            if not val:
                return
            # QSettings may return a single string or a list; normalize
            if isinstance(val, str):
                parts = [int(x) for x in val.split(',') if x.strip().isdigit()]
            else:
                parts = [int(x) for x in val]
            for col, w in enumerate(parts[:self.subtitle_table.columnCount()]):
                try:
                    self.subtitle_table.setColumnWidth(col, int(w))
                except Exception:
                    pass
        except Exception:
            logging.debug('Failed to load subtitle column widths')

    def load_video_preview(self):
        video_path = self.source_file.text().strip()
        if video_path and os.path.isfile(video_path):
            qurl = QUrl.fromLocalFile(video_path)
            logging.info("Loading video preview: %s", video_path)
            try:
                self.video_player.setSource(qurl)
            except Exception as e:
                logging.exception("setSource failed: %s", e)
            # Do not auto-start playback; user must press Play explicitly.

    # queue methods removed
    # --- Subtitle Editor Controls ---
    def add_subtitle_editor_button(self):
        self.edit_subs_btn = QPushButton("Edit Subtitles")
        self.edit_subs_btn.clicked.connect(self.show_subtitle_editor)
        self.main_area.addWidget(self.edit_subs_btn)
    # queue removed: add_to_queue

    # queue removed: process_queue

        # Preview Subtitles Button
        preview_btn = QPushButton("Preview Subtitles")
        preview_btn.clicked.connect(self.preview_subtitles)
        self.statusBar().addPermanentWidget(preview_btn)
    def preview_subtitles(self):
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView
        import pysrt
        import re
        # Get subtitle file path
        subs_path = self.source_file.text().strip()
        if not subs_path:
            QMessageBox.warning(self, "Preview Subtitles", "No source file selected.")
            return
        # Try to auto-locate .srt file
        srt_path = os.path.splitext(subs_path)[0] + ".srt"
        if not os.path.isfile(srt_path):
            QMessageBox.warning(self, "Preview Subtitles", f"Subtitle file not found: {srt_path}")
            return
        # Load swears
        swears_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'swears.txt')
        swears = {}
        with open(swears_path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                parts = line.split('|')
                swears[parts[0].lower()] = parts[1] if len(parts) > 1 else "*****"
        # Build regex
        pattern = r'\b(' + '|'.join(re.escape(k) for k in swears.keys()) + r')\b'
        replacer = re.compile(pattern, re.IGNORECASE) if swears else None
        # Load subtitles
        subs = pysrt.open(srt_path)
        # Dialog
        dlg = QDialog(self)
        dlg.setWindowTitle("Subtitle Preview")
        dlg.resize(900, 500)
        layout = QtWidgets.QVBoxLayout(dlg)
        table = QTableWidget()
        table.setColumnCount(5)
        table.setHorizontalHeaderLabels(["Id", "Start", "End", "Original Text", "Replacement Text"])
            # Offset row removed from editor; offset is a persistent control in main UI
        layout.addWidget(table)
        dlg.setLayout(layout)
        dlg.exec()

        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QtWidgets.QVBoxLayout(central)

        # Source and Preset
        source_layout = QHBoxLayout()
        source_label = QLabel("Source:")
        self.source_file = QLineEdit()
        open_btn = QPushButton("Open Source")
        open_btn.clicked.connect(self.open_source)
        source_layout.addWidget(source_label)
        source_layout.addWidget(self.source_file)
        source_layout.addWidget(open_btn)
        source_layout.addStretch()
        main_layout.addLayout(source_layout)

        preset_layout = QHBoxLayout()
        preset_label = QLabel("Preset:")
        self.preset_combo = QComboBox()
        self.preset_combo.addItems([
            "Official > General > Fast 1080p30",
            "Official > General > Fast 720p30",
            "Custom"
        ])
        preset_layout.addWidget(preset_label)
        preset_layout.addWidget(self.preset_combo)
        preset_layout.addStretch()
        main_layout.addLayout(preset_layout)

        # Tabs
        tabs = QTabWidget()
        tabs.addTab(self.create_summary_tab(), "Summary")
        tabs.addTab(QWidget(), "Dimensions")
        tabs.addTab(QWidget(), "Filters")
        tabs.addTab(QWidget(), "Video")
        tabs.addTab(QWidget(), "Audio")
        tabs.addTab(QWidget(), "Subtitles")
        tabs.addTab(QWidget(), "Chapters")
        tabs.addTab(QWidget(), "Tags")
        main_layout.addWidget(tabs)

        # Save As
        save_layout = QHBoxLayout()
        save_label = QLabel("Save As:")
        self.save_file = QLineEdit("New Video.mp4")
        save_btn = QPushButton("...")
        save_btn.clicked.connect(self.save_as)
        save_layout.addWidget(save_label)
        save_layout.addWidget(self.save_file)
        save_layout.addWidget(save_btn)
        save_layout.addStretch()
        main_layout.addLayout(save_layout)

        # Destination and When Done
        dest_layout = QHBoxLayout()
        dest_label = QLabel("To:")
        self.dest_folder = QLineEdit("Videos")
        dest_btn = QPushButton("...")
        dest_btn.clicked.connect(self.select_dest)
        when_done_label = QLabel("When Done:")
        self.when_done_combo = QComboBox()
        self.when_done_combo.addItems(["Do Nothing", "Shut Down", "Sleep"])
        dest_layout.addWidget(dest_label)
        dest_layout.addWidget(self.dest_folder)
        dest_layout.addWidget(dest_btn)
        dest_layout.addWidget(when_done_label)
        dest_layout.addWidget(self.when_done_combo)
        dest_layout.addStretch()
        main_layout.addLayout(dest_layout)

    def create_summary_tab(self):
        tab = QWidget()
        layout = QtWidgets.QVBoxLayout(tab)
        format_group = QGroupBox("Format:")
        format_layout = QHBoxLayout(format_group)
        self.format_combo = QComboBox()
        self.format_combo.addItems(["MPEG-4 (avformat)", "Matroska (mkv)", "WebM"])
        format_layout.addWidget(self.format_combo)
        layout.addWidget(format_group)
        self.web_opt = QCheckBox("Web Optimized")
        self.align_av = QCheckBox("Align A/V Start")
        self.ipod_support = QCheckBox("iPod 5G Support")
        self.passthru_metadata = QCheckBox("Passthru Common Metadata")
        self.align_av.setChecked(True)
        self.passthru_metadata.setChecked(True)
        layout.addWidget(self.web_opt)
        layout.addWidget(self.align_av)
        layout.addWidget(self.ipod_support)
        layout.addWidget(self.passthru_metadata)
        layout.addStretch()
        return tab

    def open_source(self):
        file, _ = QFileDialog.getOpenFileName(self, "Open Source Video", filter="Video Files (*.mp4 *.mkv *.avi *.mov)")
        if file:
            # Try to set the correct QLineEdit depending on which panel is visible
            # Always set the main persistent source field; subtitle editor no longer has its own "File:" field
            target_edit = self.source_file if hasattr(self, 'source_file') else None
            if target_edit:
                target_edit.setText(file)
            # Suggest output file name if main panel is visible
            if hasattr(self, 'save_file'):
                out_path = os.path.splitext(file)[0] + "_clean" + os.path.splitext(file)[1]
                self.save_file.setText(out_path)

    def save_as(self):
        file, _ = QFileDialog.getSaveFileName(self, "Save As", filter="Video Files (*.mp4 *.mkv *.avi *.mov)")
        if file:
            self.save_file.setText(file)


    def select_dest(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Destination Folder")
        if folder:
            self.dest_folder.setText(folder)

    def run_cleanvid(self):
        src = self.source_file.text().strip()
        out = self.save_file.text().strip()
        swears = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'swears.txt')
        subs = None  # Let cleanvid auto-detect or download
        lang = SUBTITLE_DEFAULT_LANG
        pad = 0.0
        embedSubs = False
        fullSubs = False
        subsOnly = False
        edl = False
        jsonDump = False
        reEncodeVideo = False
        reEncodeAudio = False
        hardCode = False
        vParams = VIDEO_DEFAULT_PARAMS
        audioStreamIdx = None
        aParams = AUDIO_DEFAULT_PARAMS
        aDownmix = False
        threadsInput = None
        threadsEncoding = None
        plexAutoSkipJson = ""
        plexAutoSkipId = ""
        subsOut = ""
        # Validate input/output
        if not src or not out:
            QMessageBox.warning(self, "CleanVid", "Please select both input and output files.")
            return
        try:
            cleaner = VidCleaner(
                src,
                subs,
                out,
                subsOut,
                swears,
                pad,
                embedSubs,
                fullSubs,
                subsOnly,
                edl,
                jsonDump,
                lang,
                reEncodeVideo,
                reEncodeAudio,
                hardCode,
                vParams,
                audioStreamIdx,
                aParams,
                aDownmix,
                threadsInput,
                threadsEncoding,
                plexAutoSkipJson,
                plexAutoSkipId,
            )
            cleaner.CreateCleanSubAndMuteList()
            cleaner.MultiplexCleanVideo()
            QMessageBox.information(self, "CleanVid", "Processing complete!")
        except Exception as e:
            tb = traceback.format_exc()
            QMessageBox.critical(self, "CleanVid Error", f"Error: {e}\n\n{tb}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CleanVidGUI()
    window.show()
    sys.exit(app.exec())
