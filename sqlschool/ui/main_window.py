"""The main window: three panes, top/bottom bars, menu, keyboard, welcome."""
from __future__ import annotations

from PySide6.QtCore import QEvent, QTimer, Qt
from PySide6.QtGui import QColor, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from .. import APP_NAME, APP_VERSION
from ..config import Settings
from ..engine.session import LessonSession
from ..lessons.model import Lesson
from ..memory.store import ProgressStore
from ..theme import Palette
from .editor import TerminalEditor
from .logo import logo_icon
from .output import OutputPane
from .teacher import TeacherPane
from .views import (
    AboutView,
    AchievementsView,
    ChallengeDialog,
    LessonsMap,
    MistakesView,
    ProConsole,
    ProgressView,
    ReviewToday,
    SchemaBrowser,
    SearchDialog,
    SettingsDialog,
    SqlReference,
    WeakSpotsView,
)
from .welcome import WelcomeDialog


class MainWindow(QMainWindow):
    def __init__(self, settings: Settings, lessons: list[Lesson],
                 sandbox, store: ProgressStore, pal: Palette,
                 zoom_cb=None, data_hook=None):
        super().__init__()
        self.settings = settings
        self.lessons = lessons
        self.sandbox = sandbox
        self.store = store
        self.pal = pal
        self.zoom_cb = zoom_cb
        self.data_hook = data_hook  # for smoke tests: (sandbox, settings)
        self.lesson_index = max(0, min(len(lessons) - 1, settings.last_lesson - 1))
        self.step_index = settings.last_step
        self._total_steps = sum(max(0, lesson.step_count) for lesson in lessons)
        self.passed_this_step = False
        self.finished = False
        self._typewriter: QTimer | None = None
        self.challenge: Lesson | None = None
        self.challenge_remaining = 0
        self._challenge_timer: QTimer | None = None

        self.session = LessonSession(
            self.current_lesson(), sandbox, store,
            type_along=settings.type_along,
            reduce_motion=settings.reduce_motion,
        )

        self._build_window()
        self._build_menus_and_shortcuts()
        self._welcome_if_needed()
        self._load_current_lesson()
        self._restore_geometry()

    # -- lesson helpers ----------------------------------------------------
    def current_lesson(self) -> Lesson:
        if self.challenge is not None:
            return self.challenge
        return self.lessons[self.lesson_index]

    def _load_current_lesson(self) -> None:
        lesson = self.current_lesson()
        self.session.__init__(
            lesson, self.sandbox, self.store,
            type_along=self.settings.type_along,
            reduce_motion=self.settings.reduce_motion,
        )
        self.step_index = max(0, min(self.step_index, lesson.step_count - 1))
        self.session.load_step(self.step_index)
        self.render_step()

    # -- window building ----------------------------------------------------
    def _build_window(self) -> None:
        self.setWindowTitle(APP_NAME)
        self.setWindowIcon(logo_icon(self.pal))
        self.setMinimumSize(960, 640)
        self.resize(self.settings.window_w, self.settings.window_h)

        central = QWidget()
        layout = QVBoxLayout(central)
        layout.setContentsMargins(6, 4, 6, 4)
        layout.setSpacing(5)

        # top bar
        top = QHBoxLayout()
        top.setSpacing(8)
        menu_btn = QPushButton("☰  Menu")
        menu_btn.setObjectName("ghost")
        menu_btn.setToolTip("Open the menu (Esc)")
        menu_btn.clicked.connect(self.show_menu)
        top.addWidget(menu_btn)
        self.lesson_lbl = QLabel("")
        self.lesson_lbl.setObjectName("lessonName")
        top.addWidget(self.lesson_lbl)
        top.addStretch(1)
        self.progress = QProgressBar()
        self.progress.setTextVisible(True)
        self.progress.setFixedWidth(150)
        self.progress.setToolTip("How much of the whole course you've passed.")
        top.addWidget(self.progress)
        self.level_lbl = QLabel("")
        self.level_lbl.setObjectName("paneTitle")
        top.addWidget(self.level_lbl)
        self.step_lbl = QLabel("")
        self.step_lbl.setObjectName("paneTitle")
        top.addWidget(self.step_lbl)
        self.streak_lbl = QLabel("")
        self.streak_lbl.setObjectName("streak")
        top.addWidget(self.streak_lbl)
        layout.addLayout(top)

        # three panes
        self.teacher = TeacherPane(self.pal)
        self.teacher.slow_down_requested.connect(self.slow_down)

        # - type here pane
        self.editor_pane = _Pane("3 · Type here")
        self.editor = TerminalEditor(self.pal)
        self.editor.setFont(self._mono_font())
        self.editor.setMinimumHeight(70)
        self.editor.installEventFilter(self)
        self.editor_pane.addWidget(self.editor, 1)
        btnrow = QHBoxLayout()
        self.run_btn = QPushButton("Run ▶")
        self.run_btn.setObjectName("primary")
        self.run_btn.setToolTip("Run your query (Ctrl+Enter)")
        self.run_btn.clicked.connect(self.run_query)
        btnrow.addWidget(self.run_btn)
        self.hint_btn = QPushButton("Hint")
        self.hint_btn.setToolTip("A nudge in the right direction (F1)")
        self.hint_btn.clicked.connect(self.show_hint)
        btnrow.addWidget(self.hint_btn)
        self.paste_btn = QPushButton("Type it for me")
        self.paste_btn.setToolTip("Show and type the answer for me (Ctrl+P)")
        self.paste_btn.clicked.connect(self.type_it_for_me)
        btnrow.addWidget(self.paste_btn)
        btnrow.addStretch(1)
        self.next_btn = QPushButton("Next →")
        self.next_btn.setEnabled(False)
        self.next_btn.setToolTip("Finish this exercise to unlock "
                                 "(or press Ctrl+L)")
        self.next_btn.clicked.connect(self._next_step)
        btnrow.addWidget(self.next_btn)
        self.editor_pane.addLayout(btnrow)
        self.mode_lbl = QLabel("")
        self.mode_lbl.setObjectName("paneTitle")
        self.editor_pane.addWidget(self.mode_lbl)

        # - output
        self.output = OutputPane(self.pal)
        self.output.reset_requested.connect(self.reset_shop)

        right = QSplitter(Qt.Orientation.Vertical)
        right.addWidget(self.editor_pane)
        right.addWidget(self.output)
        right.setChildrenCollapsible(False)
        right.setStretchFactor(0, 3)
        right.setStretchFactor(1, 3)

        horizontal = QSplitter(Qt.Orientation.Horizontal)
        horizontal.addWidget(self.teacher)
        horizontal.addWidget(right)
        horizontal.setChildrenCollapsible(False)
        horizontal.setStretchFactor(0, 3)
        horizontal.setStretchFactor(1, 4)
        layout.addWidget(horizontal, 1)

        # bottom bar
        bottom = QLabel(
            "Ctrl+Enter run · F1 hint · Ctrl+P show answer · Ctrl+L next · "
            "Ctrl+R reset · Esc menu · Ctrl+/- text size")
        bottom.setObjectName("bottombar")
        bottom.setToolTip("Handy shortcuts - the same things as the buttons above.")
        layout.addWidget(bottom)

        self.setCentralWidget(central)
        self.teacher_horizontal = horizontal
        self.right_splitter = right

    def _mono_font(self):
        from ..theme import mono_family
        from PySide6.QtGui import QFont
        font = QFont(mono_family())
        font.setPointSize(self.settings.font_size)
        return font

    def _restore_geometry(self) -> None:
        try:
            if len(self.settings.vsplit) == 2:
                self.teacher_horizontal.setSizes(self.settings.vsplit)
            if len(self.settings.hsplit) == 2:
                self.right_splitter.setSizes(self.settings.hsplit)
        except Exception:
            pass

    # -- menus / keyboard ---------------------------------------------------
    def _build_menus_and_shortcuts(self) -> None:
        def sc(seq, fn):
            s = QShortcut(QKeySequence(seq), self)
            s.activated.connect(fn)
            return s
        sc("Ctrl+Return", self.run_query)
        sc("Ctrl+Enter", self.run_query)
        sc("F1", self.show_hint)
        sc("Ctrl+L", self._next_step)
        sc("Ctrl+R", self.reset_shop)
        sc("Ctrl+=", lambda: self.zoom_cb(+1) if self.zoom_cb else None)
        sc("Ctrl+-", lambda: self.zoom_cb(-1) if self.zoom_cb else None)
        sc("Ctrl+P", self.type_it_for_me)
        sc("Esc", self.show_menu)

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Escape,):
            self.show_menu()
            return
        super().keyPressEvent(event)

    def show_menu(self) -> None:
        dialog = QDialog(self)
        dialog.setWindowTitle("Menu")
        dialog.setMinimumWidth(340)
        dialog.setMinimumHeight(480)
        lay = QVBoxLayout(dialog)
        lay.setSpacing(8)

        name = self.store.learner_name()
        greet = QLabel("Hi%s!" % (" " + name if name else ""))
        greet.setObjectName("lessonName")
        lay.addWidget(greet)

        stats = self.store.stats()
        done = min(self.store.passed_count(), self._total_steps)
        summary = QLabel(
            "Lv %d · %s · %d XP   ·   🔥 %d-day streak   ·   %d/%d done"
            % (stats["level"], self.store.level_info()["title"], stats["xp"],
               stats["streak_current"], done, self._total_steps))
        summary.setObjectName("paneTitle")
        summary.setWordWrap(True)
        lay.addWidget(summary)

        menu = QListWidget()
        entries = [
            ("section", "Learn"),
            ("item", "Lessons map", self.open_map),
            ("item", "Search exercises", self.open_search),
            ("item", "Challenge mode", self.open_challenge),
            ("item", "Review today", self.open_review),
            ("item", "Weak spots", self.open_weakspots),
            ("section", "Tools & reference"),
            ("item", "SQL reference", self.open_reference),
            ("item", "Schema browser", self.open_schema),
            ("item", "Mistake notebook", self.open_mistakes),
            ("item", "Pro console", self.open_pro_console),
            ("section", "Your progress"),
            ("item", "My progress", self.open_progress),
            ("item", "Achievements", self.open_achievements),
            ("section", "Settings & data"),
            ("item", "Settings", self.open_settings),
            ("item", "Export progress", self.export_progress),
            ("item", "Import progress", self.import_progress),
            ("item", "Reset practice data", self.reset_practice_data),
            ("section", "About"),
            ("item", "About %s" % APP_NAME, self.open_about),
        ]
        for entry in entries:
            if entry[0] == "section":
                head = QListWidgetItem(entry[1].upper())
                head.setFlags(Qt.ItemFlag.NoItemFlags)
                head.setForeground(QColor(self.pal.muted))
                menu.addItem(head)
            else:
                item = QListWidgetItem(entry[1])
                item.setData(Qt.ItemDataRole.UserRole, entry[2])
                menu.addItem(item)

        def activate(it):
            callback = it.data(Qt.ItemDataRole.UserRole)
            if not callback:
                return
            dialog.accept()
            callback()

        menu.itemActivated.connect(activate)
        menu.itemClicked.connect(activate)
        lay.addWidget(menu, 1)

        spacer = QLabel("A quiet place to learn SQL.\nEverything runs on this "
                        "computer - nothing is sent anywhere.")
        spacer.setObjectName("paneTitle")
        spacer.setWordWrap(True)
        lay.addWidget(spacer)
        dialog.exec()

    # -- welcome ------------------------------------------------------------
    def _welcome_if_needed(self) -> None:
        if self.settings.onboarded:
            return
        welcome = WelcomeDialog(self.pal, self)
        if welcome.exec():
            self.store.set_learner_name(welcome.learner_name)
            self.settings.learner_name = welcome.learner_name
            self.settings.onboarded = True
            self.settings.save()

    # -- rendering a step ---------------------------------------------------
    def render_step(self) -> None:
        step = self.session.step
        lesson = self.current_lesson()
        if self.challenge is not None:
            self.lesson_lbl.setText("⚡ %s" % lesson.title)
        else:
            self.lesson_lbl.setText("%d · %s" % (lesson.order, lesson.title))
        step_pos = self.step_index + 1
        self.step_lbl.setText("step %d of %d" % (step_pos, lesson.step_count))
        self._refresh_level()
        streak = self.store.streak().get("current", 0)
        flame = "🔥" if streak > 0 else "✻"
        self.streak_lbl.setText("%s %d" % (flame, streak) if streak else "✻ start your streak")
        self.streak_lbl.setToolTip("Day streak: %d (best %d)"
                                   % (streak, self.store.streak().get("best", 0)))

        fragments = []
        for para in step.prompt.split("\n"):
            para = para.strip()
            if para:
                fragments.append(("line", para))
        if step.real_life:
            fragments.append(("real", step.real_life))
        if step.task:
            fragments.append(("task", step.task))
        if step.memory_trick and step.kind == "answer":
            fragments.append(("trick", step.memory_trick))
        self.teacher.show_fragments(fragments)

        prep = self.session.prepare_editor(step)
        self.editor.set_ghost(prep["ghost"], prep["mode"])
        self.editor.setPlainText(prep.get("text") or "")
        mode_note = {
            "type": "type-along ghost text is on · type the query yourself",
            "fill": "fill in the blanks ___",
            "fix": "fix the broken query",
            "answer": "type your answer here (no SQL needed)",
        }.get(prep["mode"], "")
        self.mode_lbl.setText(mode_note)
        self.passed_this_step = False
        self._set_next_enabled(False)
        self.next_btn.setText("Next →")
        self.output.clear_messages()
        known = self._known_names()
        self.editor.set_known_names(known)
        self.paste_btn.setVisible(prep["mode"] in ("type", "fill", "fix"))
        if not self.settings.reduce_motion:
            self.editor.setFocus()
            self.editor.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def _known_names(self) -> set[str]:
        names = set()
        for table in self.sandbox.schema:
            names.add(table["name"])
            for c in table["columns"]:
                names.add(c["name"])
        return names

    def _refresh_level(self) -> None:
        info = self.store.level_info()
        self.level_lbl.setText("Lv %d · %s · %d XP"
                               % (info["level"], info["title"], info["xp"]))
        self.level_lbl.setToolTip(
            "%d of %d XP towards level %d.\n%d XP left to go."
            % (info["into_level"], info["span"], info["level"] + 1,
               info["to_next"]))
        self._refresh_progress()

    def _refresh_progress(self) -> None:
        total = self._total_steps or 1
        done = min(self.store.passed_count(), total)
        self.progress.setMaximum(total)
        self.progress.setValue(done)
        self.progress.setFormat("%v/%m done")
        self.progress.setToolTip(
            "%d of %d exercises passed (%.0f%%)."
            % (done, self._total_steps, 100.0 * done / total))

    def _set_next_enabled(self, enabled: bool) -> None:
        self.next_btn.setEnabled(enabled)
        self.next_btn.setObjectName("primary" if enabled else "")
        style = self.next_btn.style()
        style.unpolish(self.next_btn)
        style.polish(self.next_btn)

    def eventFilter(self, obj, event):  # noqa: N802
        if obj is self.editor:
            if event.type() == QEvent.Type.FocusIn:
                self.editor_pane.set_active(True)
                self.output.set_active(False)
            elif event.type() == QEvent.Type.FocusOut:
                self.editor_pane.set_active(False)
        return super().eventFilter(obj, event)

    def _announce_achievements(self, ids: list[str]) -> None:
        if not ids:
            return
        from ..memory import achievements as ach

        for aid in ids:
            a = ach.describe(aid)
            self.output.append_line(
                "%s Achievement unlocked: %s — %s"
                % (a.get("emoji", "🏆"), a["title"], a["hint"] or ""), kind="ok")

    # -- running -------------------------------------------------------------
    def run_query(self) -> None:
        self.teacher.skip_typing()
        self.output.set_active(True)
        self.editor_pane.set_active(False)
        sql = self.editor.toPlainText()
        step = self.session.step
        self.output.clear_messages()
        self.output.append_line(sql or "(your answer)", kind="accent")
        self.output.show_thinking()

        outcome = self.session.run(sql)

        if not outcome.result.ok and outcome.result.message:
            self.output.append_line(outcome.result.message, kind="err")
        else:
            self.output.append_line(outcome.result.message, kind="ok")
        did = outcome.result.kind
        if did == "select" and outcome.result.columns:
            note = "✓ %s" % outcome.result.message
            self.output.show_result_table(
                outcome.result.columns, outcome.result.rows,
                row_note=note, truncated=outcome.result.truncated)
        elif did == "modify":
            self.output.show_status("✓ " + outcome.result.message)
        if outcome.passed:
            self.passed_this_step = True
            self._set_next_enabled(True)
            self.next_btn.setText("Next → ✻")
        elif outcome.verdict:
            self.output.append_line(outcome.verdict.detail, kind="warn")

        # Teacher: line-by-line explanation of the learner's actual query
        lines = [l for l in outcome.teacher_lines if l.strip()]
        fragments = [("ok" if outcome.passed else "line", l) for l in lines]
        self.teacher.show_fragments(fragments)

        self._refresh_level()
        self._announce_achievements(getattr(outcome, "new_achievements", []))

        if not outcome.passed:
            self.editor.setFocus()

    # -- actions ---------------------------------------------------------------
    def show_hint(self) -> None:
        self.teacher.skip_typing()
        hint = self.session.next_hint()
        if hint:
            self.output.append_line(hint, kind="warn")
            self.teacher.show_fragments(
                self.teacher.current_fragments + [("hint", hint)])
        else:
            solution = self.session.preview_solution()
            if solution:
                self.output.append_line(
                    "No more hints. The answer was: %s" % solution, kind="warn")
            else:
                self.output.append_line("You've seen every hint - you've got "
                                        "this. Try your best guess!", kind="warn")

    def type_it_for_me(self) -> None:
        step = self.session.step
        solution = step.reference_solution()
        if not solution:
            self.output.append_line("There's no ready-made answer for this "
                                    "one - it's yours to build.", kind="warn")
            return
        self.editor.clear()
        self._typewrite_text(solution)

    def _typewrite_text(self, text: str) -> None:
        self._typewriter_pos = 0
        full = text

        def tick():
            self._typewriter_pos += 2
            self.editor.setPlainText(full[: self._typewriter_pos])
            if self._typewriter_pos >= len(full):
                self.editor.setPlainText(full)
                self._typewriter.stop()

        self._typewriter = QTimer(self)
        self._typewriter.setInterval(8 if not self.settings.reduce_motion else 1)
        self._typewriter.timeout.connect(tick)
        self._typewriter.start()

    def _next_step(self) -> None:
        if not self.passed_this_step:
            self.output.append_line("Finish the current step first - one tiny "
                                    "triumph at a time!", kind="warn")
            return
        self.teacher.skip_typing()
        self.step_index += 1
        if self.step_index >= self.current_lesson().step_count:
            if self.challenge is not None:
                self._finish_challenge()
                return
            # lesson complete -> next lesson (with a pat on the back)
            finished_title = self.current_lesson().title
            if self.lesson_index + 1 < len(self.lessons):
                self.lesson_index += 1
                self.step_index = 0
                self._load_current_lesson()
                self.output.append_line(
                    "✓ Lesson finished: %s! On to the next one." % finished_title,
                    kind="ok")
            else:
                self.finished = True
                self.lesson_index = 0
                self.step_index = 0
                self._load_current_lesson()
                self.output.append_line(
                    "🎉 You finished the whole course! Reset it anytime and "
                    "play again, or open Pro console for free play.", kind="ok")
            return
        self.session.load_step(self.step_index)
        self.render_step()

    def reset_shop(self) -> None:
        self.sandbox.reset()
        self.output.append_line("✓ Practice shop back to original - you're "
                                "safe to experiment again.", kind="ok")

    def slow_down(self) -> None:
        self.teacher.skip_typing()
        step = self.session.step
        base = step.prompt.replace("\n", " ")
        simpler = {
            1: "Here's the whole idea in one breath.",
        }
        fragments = [("line", base)]
        fragments.append(("trick", "The only new word in this step is what's "
                                   "written in the typing box. Everything else "
                                   "you already know."))
        self.teacher.show_fragments(fragments)
        self.output.append_line("🐢 Slowing down: I re-stated that in the "
                                "simplest way I know.", kind="info")

    # -- menu actions ----------------------------------------------------------
    def open_map(self) -> None:
        dlg = LessonsMap(self.lessons, self.store, self.pal, self)
        dlg.goto_lesson.connect(self.jump_to)
        dlg.exec()

    def open_progress(self) -> None:
        ProgressView(self.store, self.pal, self).exec()

    def open_review(self) -> None:
        dlg = ReviewToday(self.store, self.lessons, self.pal, self)
        dlg.practice.connect(self.jump_to)
        dlg.exec()

    def open_mistakes(self) -> None:
        dlg = MistakesView(self.store, self.pal, self)
        dlg.practice.connect(self.jump_to)
        dlg.exec()

    def open_pro_console(self) -> None:
        if not self.settings.pro_mode:
            QMessageBox.information(
                self, "Pro mode",
                "The free-play console and schema browser appear when you "
                "turn on Pro mode in Settings.")
            return
        ProConsole(self.sandbox, self.pal, self.sandbox.schema, self).exec()

    def open_search(self) -> None:
        dlg = SearchDialog(self.lessons, self.pal, self)
        dlg.chosen.connect(self.jump_to)
        dlg.exec()

    def open_reference(self) -> None:
        SqlReference(self.pal, self).exec()

    def open_schema(self) -> None:
        SchemaBrowser(self.sandbox.schema, self.pal, self).exec()

    def open_achievements(self) -> None:
        AchievementsView(self.store, self.pal, self).exec()
        self._refresh_level()

    def open_weakspots(self) -> None:
        dlg = WeakSpotsView(self.store, self.pal, self)
        dlg.practice.connect(self.jump_to)
        dlg.exec()

    def open_challenge(self) -> None:
        dlg = ChallengeDialog(self.lessons, self.pal, self)
        dlg.start_requested.connect(self.start_challenge)
        dlg.exec()

    # -- challenge mode -----------------------------------------------------
    def start_challenge(self, count: int, tag: str, minutes: int) -> None:
        from ..lessons import challenge as _challenge

        lesson = _challenge.make_challenge(self.lessons, self.store,
                                           count=count, tag=tag or None)
        if not lesson.steps:
            self.output.append_line("I couldn't find exercises for that focus - "
                                    "try 'Everything'.", kind="warn")
            return
        self.challenge = lesson
        self.step_index = 0
        self.challenge_remaining = max(1, minutes) * 60
        self._start_challenge_timer()
        self._load_current_lesson()
        self.output.append_line(
            "⚡ Challenge started: %d exercises, %d minute%s. Good luck!"
            % (len(lesson.steps), minutes, "" if minutes == 1 else "s"), kind="ok")

    def _start_challenge_timer(self) -> None:
        if self._challenge_timer is not None:
            self._challenge_timer.stop()
        self._challenge_timer = QTimer(self)
        self._challenge_timer.setInterval(1000)
        self._challenge_timer.timeout.connect(self._challenge_tick)
        self._challenge_timer.start()

    def _challenge_tick(self) -> None:
        self.challenge_remaining -= 1
        if self.challenge_remaining <= 0:
            self._end_challenge_timer()
            self.output.append_line(
                "⏰ Time's up! Finish this exercise if you like, then open the "
                "menu to start another challenge.", kind="warn")
            return
        mins, secs = divmod(self.challenge_remaining, 60)
        self.step_lbl.setText("⏱ %d:%02d · step %d of %d"
                              % (mins, secs, self.step_index + 1,
                                 self.current_lesson().step_count))

    def _end_challenge_timer(self) -> None:
        if self._challenge_timer is not None:
            self._challenge_timer.stop()
            self._challenge_timer = None

    def _finish_challenge(self) -> None:
        self._end_challenge_timer()
        self.challenge = None
        self.step_index = 0
        self._load_current_lesson()
        self.output.append_line("🎉 Challenge complete - nice work!", kind="ok")

    def open_settings(self) -> None:
        dlg = SettingsDialog(self.settings, self.pal, self)
        if not dlg.exec():
            return
        # Update the *existing* settings object in place. Replacing it would
        # leave the theme/zoom callback (created in app.make_window) pointing
        # at the old object, so theme changes would only take effect after a
        # restart.
        values = dlg.values()
        for field in ("theme", "font_size", "reduce_motion", "pro_mode",
                      "type_along", "daily_session_length"):
            setattr(self.settings, field, getattr(values, field))
        self.settings.save()
        self.session.type_along = self.settings.type_along
        self.session.reduce_motion = self.settings.reduce_motion
        if self.zoom_cb:
            self.zoom_cb(0)
        else:
            from ..theme import PALETTES
            self.pal = PALETTES.get(self.settings.theme, PALETTES["dark"])
            self.apply_palette()
        self.set_font_size(self.settings.font_size)
        self.output.append_line("✓ Settings saved.", kind="ok")

    def open_about(self) -> None:
        AboutView(self.pal, self).exec()

    def export_progress(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, "Export your progress", "sql-progress.json",
            "JSON files (*.json)")
        if not path:
            return
        try:
            payload = self.store.export_json()
        except Exception as exc:
            QMessageBox.warning(self, "Export", "Something went wrong writing "
                                "the export: %s" % exc)
            return
        try:
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(payload)
            self.output.append_line("✓ Progress exported to %s" % path, "ok")
        except OSError as exc:
            QMessageBox.warning(self, "Export", "I couldn't save that file: %s" % exc)

    def import_progress(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Import progress", "", "JSON files (*.json)")
        if not path:
            return
        try:
            payload = open(path, encoding="utf-8").read()
            counts = self.store.import_json(payload)
        except Exception as exc:
            QMessageBox.warning(self, "Import", "That file didn't import "
                                "cleanly: %s" % exc)
            return
        self.output.append_line("✓ Imported %d exercises, %d mistakes"
                                % (counts["steps"], counts["mistakes"]), "ok")

    def reset_practice_data(self) -> None:
        answer = QMessageBox.question(
            self, "Reset practice data",
            "This clears all progress, streaks and mistakes on this computer.\n"
            "Your lessons themselves are untouched - you'd simply restart "
            "from Lesson 1.\n\nContinue?")
        if answer == QMessageBox.StandardButton.Yes:
            self.store.reset_practice_data()
            self.lesson_index = 0
            self.step_index = 0
            self._load_current_lesson()
            self.output.append_line("✓ Practice data reset. Fresh start it is!",
                                    "ok")

    # -- navigation helper -------------------------------------------------------
    def jump_to(self, lesson_id: str, step_id: str) -> None:
        self._end_challenge_timer()
        self.challenge = None
        for idx, lesson in enumerate(self.lessons):
            if lesson.id == lesson_id:
                self.lesson_index = idx
                for sidx, step in enumerate(lesson.steps):
                    if step.id == step_id:
                        self.step_index = sidx
                        self._load_current_lesson()
                        return
        self.output.append_line("I couldn't find that exercise - maybe it was "
                                "skipped because of a bad file.", kind="warn")

    # -- finish ----------------------------------------------------------------
    def apply_palette(self) -> None:
        self.setWindowIcon(logo_icon(self.pal))
        self.teacher.pal = self.pal
        self.teacher.sync_theme()
        self.output.pal = self.pal
        self.output.sync_with_theme()

    def set_font_size(self, size: int) -> None:
        self.settings.font_size = size
        self.editor.setFont(self._mono_font())

    def closeEvent(self, event):  # noqa: N802
        self._end_challenge_timer()
        self.settings.last_lesson = self.lesson_index + 1
        self.settings.last_step = self.step_index
        self.settings.window_w = self.width()
        self.settings.window_h = self.height()
        try:
            self.settings.vsplit = list(self.teacher_horizontal.sizes())
            self.settings.hsplit = list(self.right_splitter.sizes())
        except Exception:
            pass
        self.settings.save()
        self.store.close()
        try:
            self.sandbox.close()
        except Exception:
            pass
        super().closeEvent(event)

    def save_state_now(self) -> None:
        # non-destructive save for smoke tests
        try:
            self.settings.vsplit = list(self.teacher_horizontal.sizes())
        except Exception:
            pass


# ---------------------------------------------------------------------------
class _Pane(QWidget):
    """A plain rounded panel that can glow when active."""

    def __init__(self, title: str):
        super().__init__()
        from PySide6.QtWidgets import QFrame

        self._frame = QFrame(self)
        self._frame.setObjectName("pane")
        box = QVBoxLayout(self)
        box.setContentsMargins(0, 0, 0, 0)
        box.addWidget(self._frame)
        f = QVBoxLayout(self._frame)
        f.setContentsMargins(6, 4, 6, 4)
        title_lbl = QLabel(title.upper())
        title_lbl.setObjectName("paneTitle")
        f.addWidget(title_lbl)
        self.content_layout = f

    def layoutFor(self):
        return self.content_layout

    def addWidget(self, w, *args):
        self.content_layout.addWidget(w, *args)

    def addLayout(self, l, *args):
        self.content_layout.addLayout(l, *args)

    def set_active(self, active: bool) -> None:
        self._frame.setObjectName("paneActive" if active else "pane")
        style = self._frame.style()
        style.unpolish(self._frame)
        style.polish(self._frame)