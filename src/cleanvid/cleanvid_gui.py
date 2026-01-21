import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QTabWidget,
    QPushButton, QLabel, QLineEdit, QFileDialog, QComboBox, QCheckBox, QGroupBox,
    QToolBar, QStyle, QSpacerItem, QSizePolicy, QMessageBox, QListWidget,
    QDialog, QTableWidget, QTableWidgetItem, QHeaderView, QSlider, QFrame, QDockWidget, QProgressBar
)
from PySide6 import QtWidgets
from PySide6.QtGui import QIcon, QAction
from PySide6.QtCore import Qt, QUrl, QSettings, QTimer
from PySide6.QtCore import QThread, QObject, Signal
from PySide6.QtGui import QPainter, QColor, QPen


# Simple spinner widget (no external assets) to indicate work in progress
class Spinner(QWidget):
    def __init__(self, parent=None, diameter=16):
        super().__init__(parent)
        self._angle = 0
        self._timer = QTimer(self)
        self._timer.setInterval(80)
        self._timer.timeout.connect(self._on_timeout)
        self._diameter = diameter
        self.setFixedSize(diameter + 4, diameter + 4)

    def _on_timeout(self):
        self._angle = (self._angle + 30) % 360
        self.update()

    def start(self):
        self._timer.start()

    def stop(self):
        try:
            self._timer.stop()
        except Exception:
            pass

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect()
        cx = rect.center().x()
        cy = rect.center().y()
        radius = min(rect.width(), rect.height()) / 2 - 2
        pen = QPen(QColor(100, 100, 100))
        pen.setWidth(2)
        painter.setPen(pen)
        for i in range(12):
            alpha = (i * 20) % 255
            color = QColor(70, 130, 180)
            color.setAlphaF((i + 1) / 12.0)
            painter.setPen(QPen(color, 2))
            angle = (self._angle + i * 30) * 3.14159 / 180.0
            x1 = cx + (radius - 4) * 0.7 * (1) * 0.0
            y1 = cy
            # draw short line segments around circle
            x1 = cx + (radius - 4) * 0.6 * __import__('math').cos(angle)
            y1 = cy + (radius - 4) * 0.6 * __import__('math').sin(angle)
            x2 = cx + radius * __import__('math').cos(angle)
            y2 = cy + radius * __import__('math').sin(angle)
            painter.drawLine(int(x1), int(y1), int(x2), int(y2))
import os
import time
import traceback
import logging
import tempfile
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

    def show_skip_editor(self):
        # Avoid re-adding the editor if already shown
        if getattr(self, '_skip_editor_shown', False):
            return
        # Stop live subtitle updates while editing
        try:
            if getattr(self, '_live_connected', False):
                self.video_player.positionChanged.disconnect(self.update_live_subtitle)
                self._live_connected = False
        except Exception:
            pass
        # Clear main area
        try:
            self._clear_layout(self.main_area)
        except Exception:
            pass

        # Ensure skip ranges list exists
        if not hasattr(self, '_skip_ranges') or self._skip_ranges is None:
            self._skip_ranges = []

        # Reuse the main video widget and controls
        try:
            self.main_area.addWidget(self.video_widget, 10)
        except Exception:
            pass
        try:
            if getattr(self, 'controls_widget', None) is not None:
                self.main_area.addWidget(self.controls_widget)
        except Exception:
            pass

        # Controls for recording skip ranges
        ctrl_layout = QHBoxLayout()
        self.start_skip_btn = QPushButton("Start Skip")
        self.stop_skip_btn = QPushButton("Stop Skip")
        self.clear_last_skip_btn = QPushButton("Clear Last")
        self.clear_all_skips_btn = QPushButton("Clear All")
        ctrl_layout.addWidget(self.start_skip_btn)
        ctrl_layout.addWidget(self.stop_skip_btn)
        ctrl_layout.addWidget(self.clear_last_skip_btn)
        ctrl_layout.addWidget(self.clear_all_skips_btn)
        self.main_area.addLayout(ctrl_layout)

        # Table of skip ranges
        self.skip_table = QTableWidget()
        self.skip_table.setColumnCount(4)
        self.skip_table.setHorizontalHeaderLabels(["Id", "Start", "End", "Duration(s)"])
        from PySide6.QtWidgets import QHeaderView
        header = self.skip_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.skip_table.setMaximumHeight(200)
        self.main_area.addWidget(self.skip_table)

        # Wire up buttons
        self.start_skip_btn.clicked.connect(self._on_start_skip)
        self.stop_skip_btn.clicked.connect(self._on_stop_skip)
        self.clear_last_skip_btn.clicked.connect(self._on_clear_last_skip)
        self.clear_all_skips_btn.clicked.connect(self._on_clear_all_skips)

        self._skip_editor_shown = True
        try:
            self._refresh_skip_table()
        except Exception:
            pass

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

        # Skip Scenes action in toolbar
        skip_scenes_action = QAction(QIcon.fromTheme("media-skip-forward"), "Skip Scenes", self)
        skip_scenes_action.triggered.connect(self.show_skip_editor)
        toolbar.addAction(skip_scenes_action)

        # Encode / Run action in toolbar
        encode_action = QAction(QIcon.fromTheme("media-record"), "Encode", self)
        encode_action.setToolTip("Run CleanVid to process the current source/output settings")
        encode_action.triggered.connect(self.start_encode_with_estimate)
        toolbar.addAction(encode_action)

        # Threads override control (small spinbox) so users can set encoding threads
        try:
            threads_label = QLabel("Threads:")
            toolbar.addWidget(threads_label)
            self.threads_spin = QtWidgets.QSpinBox()
            max_threads = max(1, (os.cpu_count() or 1))
            default_threads = max(1, (os.cpu_count() or 1) - 2)
            self.threads_spin.setRange(1, max_threads)
            self.threads_spin.setValue(default_threads)
            self.threads_spin.setToolTip("Override ffmpeg -threads (default: all-but-2 cores)")
            toolbar.addWidget(self.threads_spin)
        except Exception:
            self.threads_spin = None

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
        # Playback controls are placed inside a persistent container widget
        # so they can be removed from the layout and re-added later without
        # losing signal/slot connections or widget state.
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
        # Create a container widget so we can re-add the entire controls block
        # to `main_area` after the subtitle editor clears the layout.
        controls_container = QWidget()
        controls_container.setLayout(controls_layout)
        self.controls_widget = controls_container
        self.main_area.addWidget(self.controls_widget)

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
        # Prefer an exported temporary subs file (from the editor) when present
        tmp = getattr(self, '_temp_subs_path', None)
        if tmp and os.path.isfile(tmp):
            srt_path = tmp
        else:
            srt_path = self.subs_file.text().strip()
        self.live_subs = []
        if srt_path and os.path.isfile(srt_path):
            subs = pysrt.open(srt_path)
            # If edited subtitles exist, use them
            # Otherwise, use original
            self.live_subs = [(sub.start.ordinal, sub.end.ordinal, sub.text) for sub in subs]

    def _export_edited_table_to_temp_srt(self):
        """Export the currently-edited subtitle table to a temporary .srt and
        also export any recorded skip ranges to a JSON alongside it.
        Returns (temp_srt_path, mute_filter_list, skip_ranges) or (None, None, None) on failure.
        """
        try:
            import pysrt
            # Determine source srt used to align timing
            editor_field = getattr(self, 'subs_file_edit', None)
            if editor_field is not None:
                srt_path = editor_field.text().strip()
            else:
                srt_path = self.subs_file.text().strip() if hasattr(self, 'subs_file') else ""
            if not srt_path or not os.path.isfile(srt_path):
                return None, None, None
            orig_subs = pysrt.open(srt_path)
            new_subs = pysrt.SubRipFile()
            mute_filters = []
            for row in range(self.subtitle_table.rowCount()):
                # Use original timing, but replacement text if present
                if row >= len(orig_subs):
                    continue
                orig = orig_subs[row]
                repl_item = self.subtitle_table.item(row, 4)
                text = repl_item.text() if (repl_item and repl_item.text()) else orig.text
                new_item = pysrt.SubRipItem(index=orig.index, start=orig.start, end=orig.end, text=text)
                new_subs.append(new_item)
                # Mute checkbox
                try:
                    mute_chk = self.subtitle_table.cellWidget(row, 5)
                except Exception:
                    mute_chk = None
                if mute_chk is not None and isinstance(mute_chk, QCheckBox) and mute_chk.isChecked():
                    def _tsecs(t):
                        tt = t.to_time()
                        return (tt.hour * 3600) + (tt.minute * 60) + tt.second + (tt.microsecond / 1000000.0)

                    lineStart = _tsecs(orig.start)
                    lineEnd = _tsecs(orig.end)
                    # next start (peek) for fade-in window
                    if (row + 1) < len(orig_subs):
                        next_start = _tsecs(orig_subs[row + 1].start)
                    else:
                        next_start = lineEnd + 0.1
                    mute_filters.append(
                        "afade=enable='between(t," + format(lineStart, '.3f') + "," + format(lineEnd, '.3f') +")':t=out:st=" + format(lineStart, '.3f') + ":d=10ms"
                    )
                    mute_filters.append(
                        "afade=enable='between(t," + format(lineEnd, '.3f') + "," + format(next_start, '.3f') +")':t=in:st=" + format(lineEnd, '.3f') + ":d=10ms"
                    )

            # Create temp file in same directory as source srt for relative paths
            try:
                dirpath = os.path.dirname(srt_path) or None
            except Exception:
                dirpath = None
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.srt', prefix='cleanvid_edit_', dir=dirpath)
            tmp_path = tmp.name
            tmp.close()
            new_subs.save(tmp_path)
            # Export skip ranges (if any) to a JSON file next to the temp SRT
            skip_ranges = getattr(self, '_skip_ranges', []) or []
            try:
                import json
                skips_path = os.path.splitext(tmp_path)[0] + '_skips.json'
                with open(skips_path, 'w') as sf:
                    json.dump(skip_ranges, sf)
                # store path for cleanup
                self._temp_skips_path = skips_path
            except Exception:
                # ignore JSON export failures
                self._temp_skips_path = None
            return tmp_path, mute_filters, skip_ranges
        except Exception:
            logging.exception("Failed to export edited subtitle table to temp srt")
            return None, None, None

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

    def _ms_to_timestr(self, ms):
        try:
            s = int(ms // 1000)
            ms_r = int(ms % 1000)
            h, r = divmod(s, 3600)
            m, sec = divmod(r, 60)
            return f"{h:02d}:{m:02d}:{sec:02d}.{ms_r:03d}"
        except Exception:
            return "00:00:00.000"

    def _on_start_skip(self):
        # Record current player position as start (ms)
        try:
            pos = int(self.video_player.position())
            self._current_skip_start = pos
        except Exception:
            self._current_skip_start = None

    def _on_stop_skip(self):
        # Record current player position as end and append range
        try:
            end = int(self.video_player.position())
            start = getattr(self, '_current_skip_start', None)
            if start is None:
                return
            if end <= start:
                return
            # ensure skip ranges list
            if not hasattr(self, '_skip_ranges') or self._skip_ranges is None:
                self._skip_ranges = []
            # ensure id counter
            if not hasattr(self, '_skip_next_id'):
                self._skip_next_id = 1
            rid = self._skip_next_id
            self._skip_next_id += 1
            rng = {"id": rid, "start_ms": start, "end_ms": end, "created_at": time.time()}
            self._skip_ranges.append(rng)
            # clear current start
            self._current_skip_start = None
            self._refresh_skip_table()
        except Exception:
            logging.exception("Failed to record skip range")

    def _on_clear_last_skip(self):
        try:
            if getattr(self, '_skip_ranges', None):
                self._skip_ranges.pop()
                self._refresh_skip_table()
        except Exception:
            pass

    def _on_clear_all_skips(self):
        try:
            self._skip_ranges = []
            self._refresh_skip_table()
        except Exception:
            pass

    def _refresh_skip_table(self):
        try:
            rows = getattr(self, '_skip_ranges', []) or []
            self.skip_table.setRowCount(len(rows))
            for i, r in enumerate(rows):
                sid = QTableWidgetItem(str(r.get('id')))
                start_it = QTableWidgetItem(self._ms_to_timestr(r.get('start_ms', 0)))
                end_it = QTableWidgetItem(self._ms_to_timestr(r.get('end_ms', 0)))
                dur_s = (r.get('end_ms', 0) - r.get('start_ms', 0)) / 1000.0
                dur_it = QTableWidgetItem(f"{dur_s:.3f}")
                self.skip_table.setItem(i, 0, sid)
                self.skip_table.setItem(i, 1, start_it)
                self.skip_table.setItem(i, 2, end_it)
                self.skip_table.setItem(i, 3, dur_it)
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
            # If an edited subtitle table was open, export it to a temp SRT so
            # the live preview and subsequent processing use the edited text.
            try:
                if getattr(self, '_subtitle_editor_shown', False) and hasattr(self, 'subtitle_table') and (self.subtitle_table.rowCount() > 0):
                    edited_clean_subs, edited_mute_list, edited_skip_ranges = self._export_edited_table_to_temp_srt()
                    if edited_clean_subs:
                        self._temp_subs_path = edited_clean_subs
                        self._temp_skips = edited_skip_ranges
                        # Reload live subtitles from the exported temp file immediately
                        try:
                            self.load_subtitles_for_live()
                        except Exception:
                            pass
            except Exception:
                pass
            # If skip editor was open, export skip ranges to a temp JSON so
            # they are available for preview/encode even if subtitles weren't edited.
            try:
                if getattr(self, '_skip_editor_shown', False) and getattr(self, '_skip_ranges', None):
                    import json
                    tmp_sk = tempfile.NamedTemporaryFile(delete=False, suffix='_skips.json', prefix='cleanvid_skips_')
                    try:
                        tmp_sk.write(json.dumps(self._skip_ranges).encode('utf-8'))
                        tmp_sk_path = tmp_sk.name
                    finally:
                        tmp_sk.close()
                    self._temp_skips_path = tmp_sk_path
                    self._temp_skips = list(self._skip_ranges)
            except Exception:
                pass
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
        # Ensure playback controls are present (re-add persistent widget)
        try:
            if getattr(self, 'controls_widget', None) is not None:
                try:
                    if self.main_area.indexOf(self.controls_widget) == -1:
                        self.main_area.addWidget(self.controls_widget)
                except Exception:
                    # fallback when indexOf isn't available
                    if not getattr(self.controls_widget, 'parent', None):
                        self.main_area.addWidget(self.controls_widget)
        except Exception:
            pass
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
            try:
                self._skip_editor_shown = False
            except Exception:
                pass
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
        # Allow missing `save_file` widget by falling back to a sensible default
        if hasattr(self, 'save_file') and getattr(self, 'save_file') is not None:
            out = self.save_file.text().strip()
        else:
            out = os.path.splitext(src)[0] + "_clean" + os.path.splitext(src)[1] if src else ""
        swears = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'swears.txt')
        subs = None  # Let cleanvid auto-detect or download
        lang = SUBTITLE_DEFAULT_LANG
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
        threadsEncoding = max(1, (os.cpu_count() or 1) - 2)  # Set default threadsEncoding to all but 2 cores
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
                            threadsEncoding,
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
                    max(1, (os.cpu_count() or 1) - 2),  # Set default threadsEncoding to all but 2 cores
                plexAutoSkipJson,
                plexAutoSkipId,
            )
            cleaner.CreateCleanSubAndMuteList()
            cleaner.MultiplexCleanVideo()
            QMessageBox.information(self, "CleanVid", "Processing complete!")
        except Exception as e:
            tb = traceback.format_exc()
            QMessageBox.critical(self, "CleanVid Error", f"Error: {e}\n\n{tb}")

    # ----- Background encode worker and progress estimation -----
    class _EncodeWorker(QObject):
        finished = Signal(bool, str)
        # emits a dict with keys like 'percent', 'out_time_ms', 'duration', 'eta'
        progress = Signal(dict)

        def __init__(self, src, subs, out, edited_clean_subs=None, edited_mute_list=None, threadsEncoding=None, parent=None):
            super().__init__(parent)
            self.src = src
            self.subs = subs
            self.out = out
            # If provided, these are the GUI-exported cleaned subtitle file and precomputed mute filters.
            self.edited_clean_subs = edited_clean_subs
            self.edited_mute_list = edited_mute_list or []
            # Optional override for ffmpeg encoding threads
            self.threadsEncoding = threadsEncoding

            # Smoothing / throttling state
            self._start_time = None
            self._last_emit_time = 0
            self._ema_percent = None

        def run(self):
            try:
                self._start_time = time.time()
                swears = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'swears.txt')
                subs = None
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
                # Use override if present, otherwise default all-but-2 cores
                threadsEncoding = self.threadsEncoding if (self.threadsEncoding is not None) else max(1, (os.cpu_count() or 1) - 2)
                plexAutoSkipJson = ""
                plexAutoSkipId = ""
                subsOut = ""
                cleaner = VidCleaner(
                    self.src,
                    self.subs,
                    self.out,
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

                # Fetch duration if possible
                try:
                    from cleanvid.cleanvid import GetFormatAndStreamInfo
                    info = GetFormatAndStreamInfo(self.src) or {}
                    duration = float((info.get('format') or {}).get('duration') or 0) or None
                except Exception:
                    duration = None

                # Exponential smoothing + throttled emit
                alpha = 0.25
                min_interval = 0.20  # seconds (5 Hz)

                def _emit_progress(d):
                    now = time.time()
                    # Throttle frequent updates
                    if (now - self._last_emit_time) < min_interval:
                        return
                    try:
                        out_time_ms = int(d.get('out_time_ms', '0'))
                    except Exception:
                        out_time_ms = 0
                    # ffmpeg '-progress' reports out_time_ms as microseconds (us),
                    # so convert to seconds by dividing by 1_000_000.
                    out_s = out_time_ms / 1000000.0
                    raw_percent = None
                    if duration and duration > 0:
                        try:
                            raw_percent = (out_s / duration) * 100.0
                        except Exception:
                            raw_percent = None

                    # Update EMA
                    if raw_percent is not None:
                        if self._ema_percent is None:
                            self._ema_percent = raw_percent
                        else:
                            self._ema_percent = self._ema_percent + alpha * (raw_percent - self._ema_percent)

                    # Parse speed (ffmpeg reports like '8.18x')
                    speed = None
                    try:
                        sp = d.get('speed')
                        if isinstance(sp, str) and sp.endswith('x'):
                            speed = float(sp.rstrip('x'))
                        elif sp is not None:
                            speed = float(sp)
                    except Exception:
                        speed = None

                    eta = None
                    if duration and speed and (duration > out_s):
                        try:
                            eta = int(max(0, (duration - out_s) / speed))
                        except Exception:
                            eta = None

                    payload = {
                        'percent': int(self._ema_percent) if self._ema_percent is not None else (int(raw_percent) if raw_percent is not None else None),
                        'smoothed_percent': self._ema_percent,
                        'out_time_ms': out_time_ms,
                        'duration': duration,
                        'eta': eta,
                        'raw': d,
                    }
                    try:
                        self.progress.emit(payload)
                        self._last_emit_time = now
                    except Exception:
                        pass

                # If the GUI exported an edited cleaned subtitle file, use that and
                # pre-populate the mute filter list, skipping the normal CreateCleanSubAndMuteList
                # which would overwrite the provided cleaned subtitles.
                if self.edited_clean_subs:
                    cleaner.cleanSubsFileSpec = self.edited_clean_subs
                    cleaner.muteTimeList = list(self.edited_mute_list)
                    cleaner.MultiplexCleanVideo(progress_callback=_emit_progress)
                else:
                    cleaner.CreateCleanSubAndMuteList()
                    cleaner.MultiplexCleanVideo(progress_callback=_emit_progress)
                self.finished.emit(True, "")
            except Exception as e:
                import traceback as _tb
                self.finished.emit(False, _tb.format_exc())

    def start_encode_with_estimate(self):
        # Validate inputs
        src = self.source_file.text().strip()
        if hasattr(self, 'save_file') and getattr(self, 'save_file') is not None:
            out = self.save_file.text().strip()
        else:
            out = os.path.splitext(src)[0] + "_clean" + os.path.splitext(src)[1] if src else ""
        if not src or not out:
            QMessageBox.warning(self, "CleanVid", "Please select both input and output files.")
            return

        # If the user has an edited subtitle table, export it to a temp .srt
        edited_clean_subs = None
        edited_mute_list = None
        edited_skip_ranges = None
        try:
            if hasattr(self, 'subtitle_table') and (self.subtitle_table.rowCount() > 0):
                edited_clean_subs, edited_mute_list, edited_skip_ranges = self._export_edited_table_to_temp_srt()
                # remember temp path for cleanup later
                if edited_clean_subs:
                    self._temp_subs_path = edited_clean_subs
                    self._temp_skips = edited_skip_ranges
        except Exception:
            edited_clean_subs = None
            edited_mute_list = None

        # Worker thread
        try:
            with open('/tmp/cleanvid_debug.log', 'a') as _d:
                _d.write('STARTING encode: src=%s out=%s\n' % (src, out))
        except Exception:
            pass
        self._encode_thread = QThread()
        # Determine subtitle file: explicit field, guessed .srt, or try auto-extract (offline)
        subs_path = None
        try:
            candidate = self.subs_file.text().strip() if hasattr(self, 'subs_file') else ''
            if candidate and os.path.isfile(candidate):
                subs_path = candidate
            else:
                guess = os.path.splitext(src)[0] + '.srt'
                if os.path.isfile(guess):
                    subs_path = guess
                else:
                    # don't attempt network downloads here; require explicit .srt
                    subs_path = None
        except Exception:
            subs_path = None

        if not subs_path:
            QMessageBox.warning(self, "CleanVid", "Subtitle file not found. Please select a subtitle (.srt) file.")
            return

        threads_override = None
        try:
            if getattr(self, 'threads_spin', None):
                threads_override = int(self.threads_spin.value())
        except Exception:
            threads_override = None
        self._encode_worker = self._EncodeWorker(src, subs_path, out, edited_clean_subs=edited_clean_subs, edited_mute_list=edited_mute_list, threadsEncoding=threads_override)
        # Connect progress and finished handlers before moving worker to thread
        try:
            self._encode_worker.progress.connect(self._on_encode_progress)
        except Exception:
            pass
        self._encode_worker.finished.connect(self._on_encode_finished)
        self._encode_worker.finished.connect(self._encode_thread.quit)
        self._encode_thread.finished.connect(self._encode_thread.deleteLater)
        # Pause any playback to avoid race conditions with multimedia pipeline
        try:
            if getattr(self, 'video_player', None):
                try:
                    self.video_player.pause()
                except Exception:
                    pass
        except Exception:
            pass
        self._encode_worker.moveToThread(self._encode_thread)
        self._encode_thread.started.connect(self._encode_worker.run)
        # Show a small animated "working" indicator in the status bar
        try:
            self._spinner_widget = Spinner(self, diameter=16)
            self.statusBar().addPermanentWidget(self._spinner_widget)
            self._spinner_widget.start()
        except Exception:
            self._spinner_widget = None
        # Add a progress bar to the status bar and hook it to worker progress
        try:
            self._progress_bar = QProgressBar(self)
            self._progress_bar.setRange(0, 100)
            self._progress_bar.setValue(0)
            self.statusBar().addPermanentWidget(self._progress_bar)
        except Exception:
            self._progress_bar = None
        except Exception:
            self._progress_bar = None

        # Start worker thread
        self._encode_thread.start()

    def _on_encode_finished(self, success, message):
        try:
            if getattr(self, '_spinner_widget', None):
                try:
                    self._spinner_widget.stop()
                except Exception:
                    pass
                try:
                    self.statusBar().removeWidget(self._spinner_widget)
                except Exception:
                    pass
        except Exception:
            pass

        try:
            if getattr(self, '_progress_bar', None):
                try:
                    self.statusBar().removeWidget(self._progress_bar)
                except Exception:
                    pass
                self._progress_bar = None
        except Exception:
            pass
        if success:
            QMessageBox.information(self, "CleanVid", "Processing complete!")
        else:
            QMessageBox.critical(self, "CleanVid Error", message)
        # Clean up temp exported subtitle file if present
        try:
            if getattr(self, '_temp_subs_path', None):
                try:
                    os.remove(self._temp_subs_path)
                except Exception:
                    pass
                self._temp_subs_path = None
        except Exception:
            pass

    def _on_encode_progress(self, payload):
        try:
            if not getattr(self, '_progress_bar', None):
                return
            percent = payload.get('percent')
            out_time_ms = payload.get('out_time_ms', 0)
            duration = payload.get('duration')
            eta = payload.get('eta')
            if percent is not None:
                try:
                    v = max(0, min(100, int(percent)))
                    self._progress_bar.setValue(v)
                    if eta is not None:
                        # Show percent + ETA
                        m, s = divmod(int(eta), 60)
                        if m:
                            eta_str = f" ETA {m}m{s}s"
                        else:
                            eta_str = f" ETA {s}s"
                        try:
                            self._progress_bar.setFormat(f"{v}%{eta_str}")
                        except Exception:
                            pass
                    else:
                        try:
                            self._progress_bar.setFormat(f"{v}%")
                        except Exception:
                            pass
                except Exception:
                    pass
            else:
                # show running time / duration if available
                try:
                    out_s = int(out_time_ms) // 1000
                    if duration:
                        try:
                            self._progress_bar.setFormat(f"{out_s}s/{int(duration)}s")
                        except Exception:
                            pass
                    else:
                        try:
                            self._progress_bar.setFormat(f"{out_s}s")
                        except Exception:
                            pass
                except Exception:
                    pass
        except Exception:
            pass


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CleanVidGUI()
    window.show()
    sys.exit(app.exec())
