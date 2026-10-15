"""Auxiliary views: lessons map, progress, mistakes, review, settings,
and an optional Pro-mode free-play console."""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QSlider,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ..config import Settings
from ..memory.store import ProgressStore
from ..theme import Palette
from .widgets import make_label


# --------------------------------------------------------------------------
class SettingsDialog(QDialog):
    def __init__(self, settings: Settings, pal: Palette, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setMinimumWidth(460)
        self.settings = settings
        layout = QVBoxLayout(self)
        layout.addWidget(make_label("Settings - everything is saved on this "
                                    "computer, nothing leaves it."))

        form = QFormLayout()
        self.theme = QComboBox()
        self.theme.addItem("Dark (chill terminal)", "dark")
        self.theme.addItem("Light (paper terminal)", "light")
        self.theme.setCurrentIndex(0 if settings.theme == "dark" else 1)
        form.addRow("Theme", self.theme)

        self.font = QSlider(Qt.Orientation.Horizontal)
        self.font.setRange(11, 24)
        self.font.setValue(settings.font_size)
        self.font_label = QLabel(str(settings.font_size) + " px")
        box = QHBoxLayout()
        box.addWidget(self.font, 1)
        box.addWidget(self.font_label)
        self.font.valueChanged.connect(
            lambda v: self.font_label.setText(str(v) + " px"))
        form.addRow("Text size (Ctrl +/- also works)", box)

        self.reduce = _grow("Reduce motion",
                            "Turn off most animations; things appear calmly at once.",
                            settings.reduce_motion)
        self.pro = _grow("Pro mode",
                         "Reveal a free-play console and the schema browser.",
                         settings.pro_mode)
        self.along = _grow("Type-along ghost text",
                           "Show grey ghost text to type over in early lessons.",
                           settings.type_along)
        form.addRow("", self.reduce)
        form.addRow("", self.pro)
        form.addRow("", self.along)

        self.daily = QSpinBox()
        self.daily.setRange(5, 120)
        self.daily.setValue(settings.daily_session_length)
        self.daily.setSuffix("  minutes")
        form.addRow("Daily session target", self.daily)

        layout.addLayout(form)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save
                                   | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def values(self) -> Settings:
        s = Settings.load()
        s.theme = self.theme.currentData()
        s.font_size = self.font.value()
        s.reduce_motion = self.reduce.isChecked()
        s.pro_mode = self.pro.isChecked()
        s.type_along = self.along.isChecked()
        s.daily_session_length = self.daily.value()
        return s


def _grow(text: str, tip: str, checked: bool):
    from PySide6.QtWidgets import QCheckBox
    box = QCheckBox(text)
    box.setChecked(checked)
    box.setToolTip(tip)
    return box


# --------------------------------------------------------------------------
class LessonsMap(QDialog):
    goto_lesson = Signal(str, int)  # lesson_id, step_index

    def __init__(self, lessons, store: ProgressStore, pal: Palette, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Lessons map")
        self.resize(600, 520)
        self.lessons = lessons
        self.store = store
        self._populated: dict[int, bool] = {}

        self.search = QLineEdit()
        self.search.setPlaceholderText("Search lessons and exercises…")
        self.search.textChanged.connect(self._filter)

        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Lesson", "Steps done"])
        self.tree.itemActivated.connect(self._activate)
        self.tree.itemExpanded.connect(self._on_expanded)
        self.tree.setUniformRowHeights(True)

        self._build_top_level()
        lay = QVBoxLayout(self)
        lay.addWidget(make_label("Type to filter, click a step to jump straight "
                                 "to it. Lessons open when you expand them."))
        lay.addWidget(self.search)
        self.count_lbl = make_label("")
        self.count_lbl.setObjectName("paneTitle")
        lay.addWidget(self.count_lbl)
        lay.addWidget(self.tree, 1)
        self._update_count()

    def _lesson_done(self, lesson) -> str:
        total = len(lesson.steps)
        done = 0
        for step in lesson.steps:
            row = self.store.step_row(lesson.id, step.id)
            if row and row["status"] in ("due", "mastered"):
                done += 1
        return "%d/%d" % (done, total)

    def _build_top_level(self) -> None:
        for lesson in self.lessons:
            text = "%d · %s" % (lesson.order, lesson.title)
            root = QTreeWidgetItem([text, self._lesson_done(lesson)])
            root.setData(0, Qt.ItemDataRole.UserRole, ("lesson", lesson.id))
            # a placeholder child gives the expand arrow without building 40+
            # step rows for every one of hundreds of lessons up-front
            QTreeWidgetItem(root, ["", ""])
            self.tree.addTopLevelItem(root)

    def _on_expanded(self, item) -> None:
        key = id(item)
        if self._populated.get(key):
            return
        data = item.data(0, Qt.ItemDataRole.UserRole)
        if not data or data[0] != "lesson":
            return
        lesson = next((l for l in self.lessons if l.id == data[1]), None)
        if lesson is None:
            return
        item.takeChildren()
        for step in lesson.steps:
            row = self.store.step_row(lesson.id, step.id)
            mark = {"mastered": "★", "due": "✓", "new": "·"}.get(
                (row["status"] if row else "new"), "·")
            child = QTreeWidgetItem(["   %s %s" % (mark, step.title), ""])
            child.setData(0, Qt.ItemDataRole.UserRole, ("step", lesson.id, step.id))
            item.addChild(child)
        self._populated[key] = True

    def _filter(self, text: str) -> None:
        q = (text or "").strip().lower()
        for i in range(self.tree.topLevelItemCount()):
            root = self.tree.topLevelItem(i)
            data = root.data(0, Qt.ItemDataRole.UserRole)
            lesson = next((l for l in self.lessons if l.id == data[1]), None)
            if lesson is None:
                continue
            if not q:
                root.setHidden(False)
                continue
            hay = (lesson.title + " " + " ".join(lesson.concept_tags or [])).lower()
            hit = q in hay or any(
                q in s.title.lower() or q in s.prompt.lower()
                for s in lesson.steps)
            root.setHidden(not hit)
        self._update_count()

    def _update_count(self) -> None:
        shown = sum(1 for i in range(self.tree.topLevelItemCount())
                    if not self.tree.topLevelItem(i).isHidden())
        total_steps = sum(len(l.steps) for l in self.lessons)
        self.count_lbl.setText("%d of %d lessons shown · %d exercises total"
                               % (shown, len(self.lessons), total_steps))

    def _activate(self, item, _col) -> None:
        data = item.data(0, Qt.ItemDataRole.UserRole)
        if not data:
            return
        if data[0] == "step":
            self.goto_lesson.emit(data[1], data[2])
            self.accept()
        elif data[0] == "lesson":
            item.setExpanded(True)



# --------------------------------------------------------------------------
class ProgressView(QDialog):
    def __init__(self, store: ProgressStore, pal: Palette, parent=None):
        super().__init__(parent)
        self.setWindowTitle("My progress")
        self.resize(560, 460)
        lay = QVBoxLayout(self)
        summary = store.progress_summary([])
        info = store.level_info()
        self.info = make_label(
            "Level %d · %s (%d XP)   ·   exercises done: %d   ·   mastered: %d   ·   "
            "streak: %d day%s"
            % (info["level"], info["title"], info["xp"], summary["done"],
               summary["mastered"], store.streak().get("current", 0),
               "s" if store.streak().get("current", 0) != 1 else ""))
        lay.addWidget(self.info)
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(
            ["Step", "Status", "Attempts", "Hinted", "Due"])
        rows = store.conn.execute(
            "SELECT * FROM steps ORDER BY last_seen DESC LIMIT 100").fetchall()
        self.table.setRowCount(len(rows))
        for i, r in enumerate(rows):
            self.table.setItem(i, 0, QTableWidgetItem(r["step_id"]))
            self.table.setItem(i, 1, QTableWidgetItem(r["status"]))
            self.table.setItem(i, 2, QTableWidgetItem(str(r["attempts"])))
            self.table.setItem(i, 3, QTableWidgetItem(str(r["hints_used"])))
            self.table.setItem(i, 4, QTableWidgetItem(str(r["due"] or "")))
        lay.addWidget(self.table)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.accept)
        lay.addWidget(buttons)


# --------------------------------------------------------------------------
class MistakesView(QDialog):
    practice = Signal(str, str)  # lesson_id, step_id

    def __init__(self, store: ProgressStore, pal: Palette, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Mistake notebook")
        self.resize(640, 460)
        self.list = QListWidget()
        for m in store.mistakes():
            text = "%s  (%s) · %d×\n   you: %s\n   answer: %s"
            text = text % (m["step_id"], m["created"], m["repeat_count"],
                           (m["my_sql"] or "(nothing)")[:80],
                           (m["correct_sql"] or "")[:80])
            item = QListWidgetItem(text)
            item.setData(Qt.ItemDataRole.UserRole, (m["lesson_id"], m["step_id"]))
            self.list.addItem(item)
        pal_b = QPushButton("Practice this again")
        pal_b.clicked.connect(self._practice)
        lay = QVBoxLayout(self)
        lay.addWidget(make_label("Every near-miss is saved here so you can "
                                 "revisit it. Asking for hints is never punished."))
        lay.addWidget(self.list)
        lay.addWidget(pal_b)

    def _practice(self) -> None:
        item = self.list.currentItem()
        if item:
            self.practice.emit(*item.data(Qt.ItemDataRole.UserRole))
            self.accept()


# --------------------------------------------------------------------------
class ReviewToday(QDialog):
    practice = Signal(str, str)

    def __init__(self, store: ProgressStore, lessons, pal: Palette, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Review today")
        self.resize(560, 400)
        self.list = QListWidget()
        mapping = {}
        for lesson in lessons:
            for step in lesson.steps:
                mapping[step.id] = (lesson.id, step.id)
        for r in store.due_steps():
            lid, sid = r["lesson_id"], r["step_id"]
            label = "%s  ·  due %s  ·  attempts %s" % (sid, r["due"], r["attempts"])
            item = QListWidgetItem(label)
            item.setData(Qt.ItemDataRole.UserRole, (lid, sid))
            self.list.addItem(item)
        go = QPushButton("Practice this now")
        go.clicked.connect(self._practice)
        lay = QVBoxLayout(self)
        lay.addWidget(make_label("These are the exercises your memory asked to "
                                 "see again today."))
        lay.addWidget(self.list)
        lay.addWidget(go)

    def _practice(self) -> None:
        item = self.list.currentItem()
        if item:
            self.practice.emit(*item.data(Qt.ItemDataRole.UserRole))
            self.accept()


# --------------------------------------------------------------------------
class SchemaRow(QWidget):
    def __init__(self, info, pal: Palette):
        super().__init__()
        cols = ", ".join("%s %s" % (c["name"], c["type"]) for c in info["columns"])
        lay = QVBoxLayout(self)
        head = make_label("%s · %d rows" % (info["name"], info["rows"]))
        head.setObjectName("paneTitle")
        lay.addWidget(head)
        body = make_label(cols or "(no columns)")
        body.setObjectName("paneTitle")
        lay.addWidget(body)


# --------------------------------------------------------------------------
class ProConsole(QDialog):
    """Free-play SQL console for Pro mode (real sandbox, real results)."""

    def __init__(self, sandbox, pal: Palette, schema, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Pro console - free play")
        self.resize(900, 620)
        self.sandbox = sandbox
        lay = QVBoxLayout(self)
        self.editor = QTextEdit()
        self.editor.setPlainText("SELECT * FROM products LIMIT 5;")
        self.editor.setStyleSheet(
            "QTextEdit{background:%s;color:%s;border:1px solid %s;"
            "font-family:'Consolas';font-size:13px;}" % (
                pal.panel_alt, pal.text, pal.border))
        lay.addWidget(self.editor, 1)
        run = QPushButton("Run")
        run.clicked.connect(self._run)
        lay.addWidget(run)
        self.console = QTextEdit()
        self.console.setReadOnly(True)
        self.console.setStyleSheet(
            "QTextEdit{background:%s;color:%s;border:1px solid %s;}" % (
                pal.panel_alt, pal.muted, pal.border))
        self.console.setMaximumHeight(180)
        lay.addWidget(self.console)
        self.schema_tree = QTreeWidget()
        self.schema_tree.setHeaderLabels(["Table / column"])
        for info in schema:
            root = QTreeWidgetItem(["%s (%d rows)" % (info["name"], info["rows"])])
            for c in info["columns"]:
                QTreeWidgetItem(root, ["  %s %s" % (c["name"], c["type"])])
            self.schema_tree.addTopLevelItem(root)
        self.schema_tree.expandAll()
        lay.addWidget(self.schema_tree, 1)

    def _run(self) -> None:
        sql = self.editor.toPlainText()
        res = self.sandbox.run(sql)
        if res.ok:
            lines = ["❯ " + sql, "✓ %s  (%s)" % (res.message, res.kind)]
            self.console.setPlainText("\n".join(lines))
        else:
            self.console.setPlainText("❯ " + sql + "\n⚠ " + res.message)


# --------------------------------------------------------------------------
class WeakSpotsView(QDialog):
    """The exercises that keep going wrong, ready to try again."""

    practice = Signal(str, str)

    def __init__(self, store: ProgressStore, pal: Palette, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Weak spots")
        self.resize(620, 440)
        self.list = QListWidget()
        rows = store.weak_spots(limit=100)
        for r in rows:
            label = ("%s  ·  messed up %s×  ·  last %s"
                     % (r["step_id"], r["lapses"], r["last_seen"]))
            item = QListWidgetItem(label)
            item.setData(Qt.ItemDataRole.UserRole, (r["lesson_id"], r["step_id"]))
            self.list.addItem(item)
        go = QPushButton("Practise this one again")
        go.clicked.connect(self._practice)
        lay = QVBoxLayout(self)
        if rows:
            intro = ("These are the ones that tripped you up. Try them again - "
                     "each clean pass pushes them out of this list.")
        else:
            intro = ("Nothing here yet - that's a good sign! Steps land here "
                     "whenever a query goes wrong, so you can face them again.")
        lay.addWidget(make_label(intro))
        lay.addWidget(self.list, 1)
        lay.addWidget(go)

    def _practice(self) -> None:
        item = self.list.currentItem()
        if item:
            self.practice.emit(*item.data(Qt.ItemDataRole.UserRole))
            self.accept()


# --------------------------------------------------------------------------
class AchievementsView(QDialog):
    """Badges earned, plus a friendly look at the next one to chase."""

    def __init__(self, store: ProgressStore, pal: Palette, parent=None):
        super().__init__(parent)
        from ..memory import achievements as ach
        from ..memory.store import level_info

        self.setWindowTitle("Achievements")
        self.resize(600, 500)
        info = level_info(store.xp())
        stats = store.stats()
        earned = set(store.achievements())
        # evaluate freshly so the badges shown match current progress
        earned |= ach.evaluate(stats)

        lay = QVBoxLayout(self)
        header = make_label(
            "Level %d · %s     %d XP  (next level at %d XP)"
            % (info["level"], info["title"], info["xp"], info["next_at"]))
        header.setObjectName("lessonName")
        lay.addWidget(header)
        progress = make_label(
            "%d / %d XP into this level · %d badges earned of %d"
            % (info["into_level"], info["span"], len(earned), len(ach.ACHIEVEMENTS)))
        progress.setObjectName("paneTitle")
        lay.addWidget(progress)

        self.list = QListWidget()
        for a in ach.ACHIEVEMENTS:
            got = a["id"] in earned
            mark = a["emoji"] if got else "🔒"
            state = "earned" if got else a["hint"]
            item = QListWidgetItem("%s  %s — %s" % (mark, a["title"], state))
            self.list.addItem(item)
        lay.addWidget(self.list, 1)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.accept)
        lay.addWidget(buttons)


# --------------------------------------------------------------------------
REFERENCE = [
    ("SELECT", "Ask for columns.",
     "SELECT name, price FROM products;"),
    ("FROM", "Name the table to read.",
     "SELECT * FROM customers;"),
    ("WHERE", "Keep only rows that pass a test.",
     "SELECT * FROM products WHERE price > 50;"),
    ("ORDER BY", "Sort the result (ASC smallest first, DESC biggest first).",
     "SELECT name FROM products ORDER BY price DESC;"),
    ("LIMIT / OFFSET", "Take only N rows, optionally skipping some.",
     "SELECT * FROM products ORDER BY price DESC LIMIT 5 OFFSET 5;"),
    ("DISTINCT", "Remove duplicate rows.",
     "SELECT DISTINCT city FROM customers;"),
    ("LIKE", "Search text by pattern. % is the 'anything' wildcard.",
     "SELECT * FROM customers WHERE name LIKE 'A%';"),
    ("BETWEEN", "Keep a value inside a range (both ends included).",
     "SELECT * FROM products WHERE price BETWEEN 10 AND 30;"),
    ("IN", "Keep a value that is in a short list.",
     "SELECT * FROM sales WHERE employee_id IN (1, 2, 3);"),
    ("AND / OR / NOT", "Combine or flip tests.",
     "SELECT * FROM products WHERE stock > 0 AND price < 100;"),
    ("COUNT / SUM / AVG / MIN / MAX", "Totals over rows.",
     "SELECT count(*), avg(price) FROM products;"),
    ("GROUP BY", "Make one output row per group (one pile per shared value).",
     "SELECT category_id, count(*) FROM products GROUP BY category_id;"),
    ("HAVING", "Filter the groups after GROUP BY (WHERE filters rows before).",
     "SELECT category_id, count(*) FROM products GROUP BY category_id "
     "HAVING count(*) > 3;"),
    ("JOIN … ON", "Glue two tables by a matching key.",
     "SELECT p.name, c.name FROM products p "
     "JOIN categories c ON p.category_id = c.id;"),
    ("LEFT JOIN", "Keep every left row, even with no match.",
     "SELECT c.name, s.id FROM customers c "
     "LEFT JOIN sales s ON s.customer_id = c.id;"),
    ("Sub-queries", "A question inside a question, wrapped in brackets.",
     "SELECT name FROM products WHERE price > (SELECT avg(price) FROM products);"),
    ("INSERT", "Add a new row.",
     "INSERT INTO suppliers(name, city) VALUES ('New Co', 'Fes');"),
    ("UPDATE", "Change existing rows.",
     "UPDATE products SET stock = stock + 1 WHERE id = 1;"),
    ("DELETE", "Remove rows.",
     "DELETE FROM sales WHERE id = 9999;"),
]


class SqlReference(QDialog):
    """A pocket card of the SQL the course teaches, with tiny examples."""

    def __init__(self, pal: Palette, parent=None):
        super().__init__(parent)
        self.setWindowTitle("SQL reference")
        self.resize(680, 560)
        lay = QVBoxLayout(self)
        lay.addWidget(make_label("The SQL this course teaches, each with one "
                                 "tiny example. Nothing here is a secret."))
        self.search = QLineEdit()
        self.search.setPlaceholderText("Filter the reference…")
        lay.addWidget(self.search)
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Clause", "What it does / example"])
        self.tree.setUniformRowHeights(True)
        self._rows = []
        for name, what, example in REFERENCE:
            root = QTreeWidgetItem([name, what])
            QTreeWidgetItem(root, ["", example])
            self.tree.addTopLevelItem(root)
            self._rows.append((root, (name + " " + what + " " + example).lower()))
        self.tree.expandAll()
        self.search.textChanged.connect(self._filter)
        lay.addWidget(self.tree, 1)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.accept)
        lay.addWidget(buttons)

    def _filter(self, text: str) -> None:
        q = (text or "").strip().lower()
        for root, hay in self._rows:
            root.setHidden(bool(q) and q not in hay)


# --------------------------------------------------------------------------
class SchemaBrowser(QDialog):
    """See the tables, their columns and how they link up."""

    def __init__(self, schema, pal: Palette, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Schema browser")
        self.resize(560, 560)
        lay = QVBoxLayout(self)
        lay.addWidget(make_label("Every table in the practice shop, its columns "
                                 "and the keys that link them."))
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Table / column", "Links to"])
        for info in schema:
            root = QTreeWidgetItem(["%s  (%d rows)" % (info["name"], info["rows"]), ""])
            links = {fk["from"]: "%s.%s" % (fk["table"], fk["to"])
                     for fk in info.get("foreign_keys", [])}
            for c in info["columns"]:
                tag = []
                if c.get("pk"):
                    tag.append("PK")
                if c["name"] in links:
                    tag.append("FK → %s" % links[c["name"]])
                label = "  %s %s%s" % (c["name"], c["type"],
                                       (" [" + ", ".join(tag) + "]") if tag else "")
                QTreeWidgetItem(root, [label, links.get(c["name"], "")])
            self.tree.addTopLevelItem(root)
        self.tree.expandAll()
        lay.addWidget(self.tree, 1)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.accept)
        lay.addWidget(buttons)


# --------------------------------------------------------------------------
class SearchDialog(QDialog):
    """Find any exercise by word, then jump straight to it."""

    chosen = Signal(str, str)  # lesson_id, step_id

    def __init__(self, lessons, pal: Palette, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Search exercises")
        self.resize(640, 480)
        self.lessons = lessons
        self.search = QLineEdit()
        self.search.setPlaceholderText("e.g. orders, count, join, 'A%'…")
        self.search.textChanged.connect(self._run)
        self.results = QListWidget()
        self.results.itemActivated.connect(self._choose)
        self.status = make_label("")
        self.status.setObjectName("paneTitle")
        go = QPushButton("Go to this exercise")
        go.clicked.connect(self._choose_current)
        lay = QVBoxLayout(self)
        lay.addWidget(self.search)
        lay.addWidget(self.status)
        lay.addWidget(self.results, 1)
        lay.addWidget(go)
        self.search.setFocus()

    def _run(self, text: str) -> None:
        from ..lessons.search import search

        self.results.clear()
        if not text.strip():
            self.status.setText("Type a word to search %d exercises."
                                % sum(len(l.steps) for l in self.lessons))
            return
        hits = search(self.lessons, text, limit=200)
        for lesson, step in hits:
            item = QListWidgetItem("%s  ·  %s  —  %s"
                                   % (lesson.id, lesson.title, step.title))
            item.setData(Qt.ItemDataRole.UserRole, (lesson.id, step.id))
            self.results.addItem(item)
        if hits:
            self.status.setText("%d match%s (showing up to 200)."
                                % (len(hits), "" if len(hits) == 1 else "es"))
        else:
            self.status.setText("No exercises matched '%s'." % text.strip())

    def _choose(self, item) -> None:
        data = item.data(Qt.ItemDataRole.UserRole)
        if data:
            self.chosen.emit(data[0], data[1])
            self.accept()

    def _choose_current(self) -> None:
        item = self.results.currentItem()
        if item:
            self._choose(item)


# --------------------------------------------------------------------------
class ChallengeDialog(QDialog):
    """Set up a short adaptive quiz drawn from weak spots, reviews and new
    material."""

    start_requested = Signal(int, str, int)  # count, tag, minutes

    def __init__(self, lessons, pal: Palette, parent=None):
        super().__init__(parent)
        from ..lessons.search import tags

        self.setWindowTitle("Challenge mode")
        self.resize(460, 320)
        lay = QVBoxLayout(self)
        lay.addWidget(make_label(
            "A short quiz built from what will help most: your weak spots, "
            "anything due for review, then a spread of fresh exercises."))
        form = QFormLayout()
        self.count = QSpinBox()
        self.count.setRange(3, 20)
        self.count.setValue(6)
        form.addRow("Number of exercises", self.count)
        self.tag = QComboBox()
        self.tag.addItem("Everything", "")
        for name, _n in tags(lessons).items():
            self.tag.addItem(name, name)
        form.addRow("Focus area", self.tag)
        self.minutes = QSpinBox()
        self.minutes.setRange(1, 60)
        self.minutes.setValue(5)
        self.minutes.setSuffix("  minutes")
        form.addRow("Time limit", self.minutes)
        lay.addLayout(form)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok
                                   | QDialogButtonBox.StandardButton.Cancel)
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText("Start")
        buttons.accepted.connect(self._go)
        buttons.rejected.connect(self.reject)
        lay.addWidget(buttons)

    def _go(self) -> None:
        self.start_requested.emit(self.count.value(), self.tag.currentData() or "",
                                  self.minutes.value())
        self.accept()


# --------------------------------------------------------------------------
class AboutView(QDialog):
    """Who made GRAP-SQL, what it is, and a thank-you for the tools it stands on."""

    def __init__(self, pal: Palette, parent=None):
        from .. import APP_AUTHOR, APP_NAME, APP_TAGLINE, APP_VERSION
        from .logo import logo_pixmap

        super().__init__(parent)
        self.setWindowTitle("About %s" % APP_NAME)
        self.setMinimumWidth(460)
        lay = QVBoxLayout(self)
        lay.setSpacing(10)

        header = QHBoxLayout()
        mark = QLabel()
        mark.setPixmap(logo_pixmap(64, pal))
        mark.setFixedSize(64, 64)
        mark.setScaledContents(True)
        header.addWidget(mark)
        titles = QVBoxLayout()
        name = QLabel("<span style='font-size:16pt;'>%s</span>" % APP_NAME)
        name.setObjectName("lessonName")
        titles.addWidget(name)
        sub = QLabel("%s  ·  version %s" % (APP_TAGLINE, APP_VERSION))
        sub.setObjectName("paneTitle")
        titles.addWidget(sub)
        header.addLayout(titles, 1)
        lay.addLayout(header)

        lay.addWidget(make_label(
            "%s is a calm, offline place to learn SQL from absolute zero. It "
            "runs a real database - not a pretend one - and explains every "
            "query back to you in plain words. Nothing you type ever leaves "
            "your computer." % APP_NAME))

        author = QLabel("<b>Author:</b> %s" % APP_AUTHOR)
        author.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse)
        lay.addWidget(author)

        credits = QLabel(
            "<b>Built with</b> Python and PySide6 (Qt), on top of SQLite. "
            "Lesson explanations are powered by sqlglot.<br>"
            "The half-pen mark, the lessons and the practice shop were made "
            "for this project.")
        credits.setWordWrap(True)
        credits.setObjectName("paneTitle")
        lay.addWidget(credits)

        foot = QLabel("© %s. Made for people who find databases scary."
                      % APP_AUTHOR)
        foot.setObjectName("paneTitle")
        foot.setWordWrap(True)
        lay.addWidget(foot)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.accept)
        buttons.accepted.connect(self.accept)
        lay.addWidget(buttons)
