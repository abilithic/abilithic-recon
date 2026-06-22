"""Main window. Thin UI: gathers input, runs the engine via a worker thread,
and renders a ScanResult. No business logic lives here.
"""
from __future__ import annotations

import os
from html import escape as E

from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QAction, QActionGroup, QIcon, QPixmap
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QPushButton, QComboBox, QFrame, QTableView, QTextBrowser,
    QSplitter, QProgressBar, QPlainTextEdit, QFileDialog, QMessageBox, QDialog,
    QCheckBox, QDialogButtonBox, QHeaderView, QAbstractItemView,
)

from .. import __app_name__, __version__
from ..core.config import load_config, save_config
from ..core.models import ScanState, ScanMode, LiveStatus
from ..core import paths
from ..i18n import Translator
from .. import reports
from .theme import stylesheet, SEV_COLORS, ACCENT, MUTED
from .worker import ScanWorker
from .table_model import AssetTableModel, AssetProxy, COLUMNS


# --- Authorship (kept here AND in EXE version metadata + LICENSE) ---
AUTHOR = "Abil Khosim"
AUTHOR_TITLE = "Cybersecurity Specialist"
LINKEDIN_URL = "https://www.linkedin.com/in/abil-khosim-itsec/"
LINKEDIN_HANDLE = "abil-khosim-itsec"
COPYRIGHT_YEAR = "2026"


def _logo_pixmap(size: int) -> QPixmap:
    for rel in ("assets/abilithic-icon-256.png", "assets/abilithic-icon-1024.png",
                "assets/abilithic-mark-256.png"):
        p = paths.resource_path(rel)
        if os.path.exists(p):
            pm = QPixmap(p)
            if not pm.isNull():
                return pm.scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
    return QPixmap()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.cfg = load_config()
        self.tr = Translator(self.cfg.language)
        self.result = None
        self.worker = None
        self.state = ScanState.IDLE

        ico = _logo_pixmap(64)
        if not ico.isNull():
            self.setWindowIcon(QIcon(ico))

        self._build_ui()
        self._build_menu()
        self.apply_theme(self.cfg.theme)
        self.retranslate()
        self._set_state(ScanState.IDLE)
        self.resize(1180, 760)

    # --------------------------------------------------------------------- #
    def _build_ui(self):
        central = QWidget()
        root = QVBoxLayout(central)
        root.setContentsMargins(16, 12, 16, 8)
        root.setSpacing(10)

        # header
        head = QHBoxLayout()
        self.logo = QLabel()
        pm = _logo_pixmap(44)
        if not pm.isNull():
            self.logo.setPixmap(pm)
        title_box = QVBoxLayout()
        self.title_lbl = QLabel(__app_name__)
        self.title_lbl.setStyleSheet(f"font-size:20px;font-weight:700;color:{ACCENT};")
        self.subtitle_lbl = QLabel("")
        self.subtitle_lbl.setStyleSheet(f"color:{MUTED};font-size:12px;")
        title_box.addWidget(self.title_lbl)
        title_box.addWidget(self.subtitle_lbl)
        head.addWidget(self.logo)
        head.addSpacing(8)
        head.addLayout(title_box)
        head.addStretch(1)
        self.lang_lbl = QLabel("")
        self.lang_combo = QComboBox()
        self.lang_combo.addItem("Bahasa Indonesia", "id")
        self.lang_combo.addItem("English", "en")
        self.lang_combo.setCurrentIndex(0 if self.cfg.language == "id" else 1)
        self.lang_combo.currentIndexChanged.connect(self._on_language_changed)
        head.addWidget(self.lang_lbl)
        head.addWidget(self.lang_combo)
        root.addLayout(head)

        # controls
        ctrl = QHBoxLayout()
        self.domain_edit = QLineEdit()
        self.domain_edit.returnPressed.connect(self.start_scan)
        self.mode_combo = QComboBox()
        self.mode_combo.addItem("", ScanMode.PASSIVE.value)
        self.mode_combo.addItem("", ScanMode.FULL.value)
        self.mode_combo.setCurrentIndex(0 if self.cfg.default_mode == "PASSIVE" else 1)
        self.scan_btn = QPushButton("")
        self.scan_btn.clicked.connect(self._scan_or_cancel)
        ctrl.addWidget(self.domain_edit, 1)
        ctrl.addWidget(self.mode_combo)
        ctrl.addWidget(self.scan_btn)
        root.addLayout(ctrl)

        # wildcard banner
        self.banner = QLabel("")
        self.banner.setWordWrap(True)
        self.banner.setStyleSheet(
            "background:#3a2f12;border:1px solid #ffd166;border-radius:8px;"
            "padding:8px;color:#ffd166;")
        self.banner.hide()
        root.addWidget(self.banner)

        # summary cards
        cards = QHBoxLayout()
        self.cards = {}
        for key in ("subdomains", "alive", "highrisk", "shadow", "risk"):
            frame = QFrame()
            frame.setObjectName("card")
            cl = QVBoxLayout(frame)
            num = QLabel("0")
            num.setObjectName("cardNum")
            lbl = QLabel("")
            lbl.setObjectName("cardLbl")
            cl.addWidget(num)
            cl.addWidget(lbl)
            cards.addWidget(frame, 1)
            self.cards[key] = (num, lbl)
        root.addLayout(cards)

        # splitter: table | detail
        splitter = QSplitter(Qt.Horizontal)
        left = QWidget()
        ll = QVBoxLayout(left)
        ll.setContentsMargins(0, 0, 0, 0)
        self.filter_edit = QLineEdit()
        self.filter_edit.setClearButtonEnabled(True)
        self.filter_edit.textChanged.connect(self._on_filter)
        self.model = AssetTableModel(self.tr)
        self.proxy = AssetProxy()
        self.proxy.setSourceModel(self.model)
        self.table = QTableView()
        self.table.setModel(self.proxy)
        self.table.setSortingEnabled(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.selectionModel().selectionChanged.connect(self._on_select)
        ll.addWidget(self.filter_edit)
        ll.addWidget(self.table)
        self.detail = QTextBrowser()
        self.detail.setOpenExternalLinks(True)
        splitter.addWidget(left)
        splitter.addWidget(self.detail)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)
        root.addWidget(splitter, 1)

        # progress + log
        prog_row = QHBoxLayout()
        self.phase_lbl = QLabel("")
        self.phase_lbl.setStyleSheet(f"color:{MUTED};")
        self.progress = QProgressBar()
        self.progress.setTextVisible(True)
        prog_row.addWidget(self.phase_lbl)
        prog_row.addWidget(self.progress, 1)
        root.addLayout(prog_row)

        self.log = QPlainTextEdit()
        self.log.setReadOnly(True)
        self.log.setMaximumHeight(120)
        root.addWidget(self.log)

        self.setCentralWidget(central)
        self.statusBar().showMessage("")

    def _build_menu(self):
        mb = self.menuBar()
        self.m_file = mb.addMenu("")
        self.a_new = self._action(self.m_file, self.new_scan)
        self.a_open = self._action(self.m_file, self.open_result)
        self.a_save = self._action(self.m_file, self.save_result)
        self.m_export = self.m_file.addMenu("")
        self.a_exp_html = self._action(self.m_export, lambda: self.export("html"))
        self.a_exp_json = self._action(self.m_export, lambda: self.export("json"))
        self.a_exp_csv = self._action(self.m_export, lambda: self.export("csv"))
        self.m_file.addSeparator()
        self.a_exit = self._action(self.m_file, self.close)

        self.m_scan = mb.addMenu("")
        self.a_start = self._action(self.m_scan, self.start_scan)
        self.a_cancel = self._action(self.m_scan, self.cancel_scan)

        self.m_view = mb.addMenu("")
        self.a_theme = self._action(self.m_view, self.toggle_theme)
        self.m_lang = self.m_view.addMenu("")
        grp = QActionGroup(self)
        self.a_lang_id = self._action(self.m_lang, lambda: self.set_language("id"), checkable=True)
        self.a_lang_en = self._action(self.m_lang, lambda: self.set_language("en"), checkable=True)
        grp.addAction(self.a_lang_id)
        grp.addAction(self.a_lang_en)
        (self.a_lang_id if self.cfg.language == "id" else self.a_lang_en).setChecked(True)

        self.m_help = mb.addMenu("")
        self.a_docs = self._action(self.m_help, self.open_docs)
        self.a_disc = self._action(self.m_help, self.show_disclaimer)
        self.a_upd = self._action(self.m_help, self.open_updates)
        self.a_about = self._action(self.m_help, self.show_about)

    def _action(self, menu, slot, checkable=False):
        act = QAction(self)
        act.setCheckable(checkable)
        act.triggered.connect(slot)
        menu.addAction(act)
        return act

    # --------------------------------------------------------------------- #
    def retranslate(self):
        t = self.tr
        self.setWindowTitle(f"{__app_name__} - {t('app.subtitle')}")
        self.subtitle_lbl.setText(t("app.subtitle"))
        self.lang_lbl.setText(t("lang.label") + ":")
        self.domain_edit.setPlaceholderText(t("input.placeholder"))
        self.domain_edit.setToolTip(t("hint.domain"))
        self.mode_combo.setItemText(0, t("mode.passive"))
        self.mode_combo.setItemText(1, t("mode.full"))
        self.mode_combo.setToolTip(t("hint.mode"))
        self.filter_edit.setPlaceholderText(t("col.subdomain") + " ...")
        self.banner.setText(t("wildcard.banner"))
        card_keys = {"subdomains": "card.subdomains", "alive": "card.alive",
                     "highrisk": "card.highrisk", "shadow": "card.shadow", "risk": "card.risk"}
        for k, key in card_keys.items():
            self.cards[k][1].setText(t(key))
        # buttons depend on state
        self._refresh_scan_button()
        # menus
        self.m_file.setTitle(t("menu.file"))
        self.a_new.setText(t("menu.newscan")); self.a_new.setStatusTip(t("hint.newscan")); self.a_new.setToolTip(t("hint.newscan"))
        self.a_open.setText(t("menu.open")); self.a_open.setStatusTip(t("hint.open"))
        self.a_save.setText(t("menu.save")); self.a_save.setStatusTip(t("hint.save"))
        self.m_export.setTitle(t("menu.export"))
        self.a_exp_html.setText(t("menu.exporthtml")); self.a_exp_html.setStatusTip(t("hint.exporthtml"))
        self.a_exp_json.setText(t("menu.exportjson")); self.a_exp_json.setStatusTip(t("hint.exportjson"))
        self.a_exp_csv.setText(t("menu.exportcsv")); self.a_exp_csv.setStatusTip(t("hint.exportcsv"))
        self.a_exit.setText(t("menu.exit"))
        self.m_scan.setTitle(t("menu.scan"))
        self.a_start.setText(t("menu.start")); self.a_start.setStatusTip(t("hint.scan"))
        self.a_cancel.setText(t("menu.cancel")); self.a_cancel.setStatusTip(t("hint.cancel"))
        self.m_view.setTitle(t("menu.view"))
        self.a_theme.setText(t("menu.theme")); self.a_theme.setStatusTip(t("hint.theme"))
        self.m_lang.setTitle(t("menu.language")); self.m_lang.setStatusTip(t("hint.language"))
        self.a_lang_id.setText("Bahasa Indonesia")
        self.a_lang_en.setText("English")
        self.m_help.setTitle(t("menu.help"))
        self.a_docs.setText(t("menu.docs")); self.a_docs.setStatusTip(t("hint.docs"))
        self.a_disc.setText(t("menu.disclaimer")); self.a_disc.setStatusTip(t("hint.disclaimer"))
        self.a_upd.setText(t("menu.updates")); self.a_upd.setStatusTip(t("hint.updates"))
        self.a_about.setText(t("menu.about")); self.a_about.setStatusTip(t("hint.about"))
        # header refresh + detail/cards
        self.model.headerDataChanged.emit(Qt.Horizontal, 0, len(COLUMNS) - 1)
        if self.result:
            self._apply_result(self.result, save=False)
        else:
            self.detail.setHtml(f"<p style='color:{MUTED}'>{E(t('detail.select'))}</p>")
        if self.state == ScanState.IDLE and not self.result:
            self._show_empty()

    # --------------------------------------------------------------------- #
    def _refresh_scan_button(self):
        running = self.state in (ScanState.RUNNING, ScanState.CANCELLING)
        self.scan_btn.setText(self.tr("btn.cancel") if running else self.tr("btn.scan"))
        self.scan_btn.setToolTip(self.tr("hint.cancel") if running else self.tr("hint.scan"))

    def _set_state(self, state: ScanState):
        self.state = state
        running = state in (ScanState.RUNNING, ScanState.CANCELLING)
        self.domain_edit.setEnabled(not running)
        self.mode_combo.setEnabled(not running)
        self.a_start.setEnabled(not running)
        self.a_cancel.setEnabled(running)
        self.a_new.setEnabled(not running)
        self.a_open.setEnabled(not running)
        has_result = self.result is not None
        for a in (self.a_save, self.a_exp_html, self.a_exp_json, self.a_exp_csv):
            a.setEnabled(has_result and not running)
        self._refresh_scan_button()
        msg = {ScanState.IDLE: "status.idle", ScanState.RUNNING: "status.running",
               ScanState.CANCELLING: "status.cancelling", ScanState.DONE: "status.done",
               ScanState.ERROR: "status.error"}[state]
        self.statusBar().showMessage(self.tr(msg))

    # --------------------------------------------------------------------- #
    def _scan_or_cancel(self):
        if self.state in (ScanState.RUNNING, ScanState.CANCELLING):
            self.cancel_scan()
        else:
            self.start_scan()

    def start_scan(self):
        if self.state in (ScanState.RUNNING, ScanState.CANCELLING):
            return
        domain = self.domain_edit.text().strip()
        from ..core.normalize import is_valid_domain
        if not is_valid_domain(domain):
            QMessageBox.warning(self, __app_name__, self.tr("err.invalid_domain"))
            return
        mode = self.mode_combo.currentData()
        if mode == ScanMode.FULL.value and not self._consent():
            return
        self.cfg.language = self.tr.language
        self.log.clear()
        self.banner.hide()
        self.progress.setRange(0, 0)  # busy until first progress
        self.worker = ScanWorker(domain, mode, self.cfg, self.tr)
        self.worker.phase.connect(self._on_phase)
        self.worker.progress.connect(self._on_progress)
        self.worker.log.connect(self._on_log)
        self.worker.finished_ok.connect(self._on_finished)
        self.worker.failed.connect(self._on_failed)
        self._set_state(ScanState.RUNNING)
        self.worker.start()

    def cancel_scan(self):
        if self.worker and self.state == ScanState.RUNNING:
            self.worker.cancel()
            self._set_state(ScanState.CANCELLING)

    def _consent(self) -> bool:
        t = self.tr
        dlg = QDialog(self)
        dlg.setWindowTitle(t("dialog.consent.title"))
        lay = QVBoxLayout(dlg)
        body = QLabel(t("dialog.consent.body"))
        body.setWordWrap(True)
        chk = QCheckBox(t("dialog.consent.check"))
        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        bb.button(QDialogButtonBox.Ok).setText(t("dialog.consent.ok"))
        bb.button(QDialogButtonBox.Cancel).setText(t("dialog.consent.cancel"))
        ok_btn = bb.button(QDialogButtonBox.Ok)
        ok_btn.setEnabled(False)
        chk.toggled.connect(ok_btn.setEnabled)
        bb.accepted.connect(dlg.accept)
        bb.rejected.connect(dlg.reject)
        lay.addWidget(body)
        lay.addWidget(chk)
        lay.addWidget(bb)
        dlg.setMinimumWidth(460)
        return dlg.exec() == QDialog.Accepted

    # --------------------------------------------------------------------- #
    def _on_phase(self, phase):
        self.phase_lbl.setText(self.tr(f"phase.{phase}"))

    def _on_progress(self, done, total):
        if total > 0:
            self.progress.setRange(0, total)
            self.progress.setValue(done)

    def _on_log(self, level, message):
        self.log.appendPlainText(f"[{level}] {message}")

    def _on_failed(self, err):
        self.progress.setRange(0, 1)
        self.progress.setValue(0)
        self._set_state(ScanState.ERROR)
        QMessageBox.critical(self, __app_name__, err)

    def _on_finished(self, result):
        self.result = result
        self.progress.setRange(0, 1)
        self.progress.setValue(1)
        if result.scan_meta.wildcard_detected:
            self.banner.show()
        self._apply_result(result, save=True)
        self._set_state(ScanState.DONE)

    # --------------------------------------------------------------------- #
    def _apply_result(self, result, save=True):
        # compute per-asset severity from findings
        worst = {}
        order = {"INFO": 0, "LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}
        for f in result.findings:
            if not f.asset_ref:
                continue
            cur = worst.get(f.asset_ref, "INFO")
            if order.get(f.severity, 0) > order.get(cur, 0):
                worst[f.asset_ref] = f.severity
        for a in result.assets:
            a._severity = worst.get(a.hostname, "INFO")
        self.model.set_assets(result.assets)
        self.proxy.sort(7, Qt.DescendingOrder)  # by severity

        alive = sum(1 for a in result.assets if a.live_status == LiveStatus.ALIVE.value)
        high = sum(1 for f in result.findings if f.severity in ("HIGH", "CRITICAL"))
        shadow = sum(1 for f in result.findings if f.type in ("SHADOW_IT", "TAKEOVER"))
        self.cards["subdomains"][0].setText(str(len(result.assets)))
        self.cards["alive"][0].setText(str(alive))
        self.cards["highrisk"][0].setText(str(high))
        self.cards["shadow"][0].setText(str(shadow))
        risk_num = self.cards["risk"][0]
        risk_num.setText(f"{result.risk.score}")
        risk_num.setStyleSheet(
            f"font-size:24px;font-weight:800;color:{SEV_COLORS.get(result.risk.grade, ACCENT)};")
        self.detail.setHtml(f"<p style='color:{MUTED}'>{E(self.tr('detail.select'))}</p>")

        if save:
            try:
                stamp = result.scan_meta.started_at.replace(":", "").replace("-", "")[:15]
                path = os.path.join(paths.results_dir(),
                                    f"abilithic-recon_{result.domain_info.domain}_{stamp}.json")
                reports.save_json(result, path)
                self._on_log("INFO", self.tr("export.success").format(path=path))
            except Exception as e:
                self._on_log("ERROR", str(e))

    def _on_select(self, *_):
        idx = self.table.selectionModel().currentIndex()
        if not idx.isValid():
            return
        row = self.proxy.mapToSource(idx).row()
        a = self.model.asset_at(row)
        if a:
            self.detail.setHtml(self._detail_html(a))

    def _detail_html(self, a):
        t = self.tr
        f_by_id = {f.id: f for f in (self.result.findings if self.result else [])}
        finds = []
        for fid in a.findings_ref:
            f = f_by_id.get(fid)
            if not f:
                continue
            c = SEV_COLORS.get(f.severity, MUTED)
            finds.append(
                f"<div style='margin:6px 0'><b style='color:{c}'>[{E(f.severity)}]</b> "
                f"{E(f.title)}<br><span style='color:{MUTED}'>{E(f.detail)}</span><br>"
                f"<span style='color:{ACCENT}'>&#9656; {E(f.recommendation)}</span></div>")
        finds_html = "".join(finds) or f"<span style='color:{MUTED}'>{E(t('detail.none'))}</span>"
        tls = ""
        if a.tls:
            tls = (f"{E(a.tls.issuer)} | {E(a.tls.tls_version)} | "
                   f"days: {a.tls.days_left} | SAN: {E(', '.join(a.tls.san[:8]))}")
        return f"""
        <h3 style='color:{ACCENT}'>{E(a.hostname)}</h3>
        <p><b>{E(t('detail.sources'))}:</b> {E(', '.join(a.sources))}</p>
        <p><b>{E(t('col.resolve'))}:</b> {E(a.resolve_status)} &nbsp; <b>{E(t('col.live'))}:</b> {E(a.live_status)}</p>
        <p><b>IP:</b> {E(', '.join(a.ips)) or '-'} {('<br><b>CNAME:</b> '+E(a.cname)) if a.cname else ''}</p>
        <p><b>{E(t('detail.http'))}:</b> {a.http.status or '-'} | {E(a.http.server)} | {E(a.http.title)}</p>
        <p><b>{E(t('detail.fingerprint'))}:</b> {E(', '.join(a.fingerprint.tech)) or '-'}</p>
        <p><b>{E(t('detail.tls'))}:</b> {tls or '-'}</p>
        <h4>{E(t('detail.findings'))}</h4>{finds_html}
        """

    def _show_empty(self):
        t = self.tr
        self.detail.setHtml(
            f"<div style='color:{MUTED};padding:20px'><h3>{E(t('empty.title'))}</h3>"
            f"<p>{E(t('empty.body'))}</p></div>")

    # --------------------------------------------------------------------- #
    def _on_filter(self, text):
        self.proxy.setFilterFixedString(text)

    def new_scan(self):
        self.result = None
        self.model.set_assets([])
        for k in self.cards:
            self.cards[k][0].setText("0")
        self.banner.hide()
        self.progress.setValue(0)
        self.log.clear()
        self._show_empty()
        self._set_state(ScanState.IDLE)

    def export(self, fmt):
        if not self.result:
            return
        t = self.tr
        domain = self.result.domain_info.domain
        ext = {"html": "html", "json": "json", "csv": "csv"}[fmt]
        default = os.path.join(self.cfg.output_dir or paths.results_dir(),
                               f"abilithic-recon_{domain}.{ext}")
        path, _ = QFileDialog.getSaveFileName(self, t("menu.export"), default,
                                              f"*.{ext}")
        if not path:
            return
        try:
            if fmt == "html":
                reports.save_html(self.result, path, self.tr)
            elif fmt == "json":
                reports.save_json(self.result, path)
            else:
                reports.save_csv(self.result, path)
            self.statusBar().showMessage(t("export.success").format(path=path))
        except Exception as e:
            QMessageBox.critical(self, __app_name__, t("export.fail").format(err=e))

    def save_result(self):
        self.export("json")

    def open_result(self):
        path, _ = QFileDialog.getOpenFileName(self, self.tr("menu.open"),
                                              paths.results_dir(), "*.json")
        if not path:
            return
        try:
            self.result = reports.load_json(path)
            if self.result.scan_meta.wildcard_detected:
                self.banner.show()
            self._apply_result(self.result, save=False)
            self._set_state(ScanState.DONE)
        except Exception as e:
            QMessageBox.critical(self, __app_name__, str(e))

    # --------------------------------------------------------------------- #
    def _on_language_changed(self, idx):
        self.set_language(self.lang_combo.currentData())

    def set_language(self, lang):
        self.tr.set_language(lang)
        self.cfg.language = lang
        save_config(self.cfg)
        self.lang_combo.blockSignals(True)
        self.lang_combo.setCurrentIndex(0 if lang == "id" else 1)
        self.lang_combo.blockSignals(False)
        if hasattr(self, "a_lang_id"):
            self.a_lang_id.setChecked(lang == "id")
            self.a_lang_en.setChecked(lang == "en")
        self.retranslate()

    def apply_theme(self, theme):
        self.cfg.theme = theme
        QApplication.instance().setStyleSheet(stylesheet(theme))

    def toggle_theme(self):
        self.apply_theme("light" if self.cfg.theme == "dark" else "dark")
        save_config(self.cfg)

    def open_docs(self):
        from PySide6.QtGui import QDesktopServices
        from PySide6.QtCore import QUrl
        QDesktopServices.openUrl(QUrl("https://github.com/abilithic/abilithic-recon#readme"))

    def open_updates(self):
        from PySide6.QtGui import QDesktopServices
        from PySide6.QtCore import QUrl
        QDesktopServices.openUrl(QUrl("https://github.com/abilithic/abilithic-recon/releases"))

    def show_disclaimer(self):
        QMessageBox.information(self, self.tr("menu.disclaimer"), self.tr("disclaimer.text"))

    def show_about(self):
        t = self.tr
        dlg = QDialog(self)
        dlg.setWindowTitle(t("menu.about"))
        lay = QVBoxLayout(dlg)
        head = QHBoxLayout()
        pm = _logo_pixmap(56)
        if not pm.isNull():
            lg = QLabel(); lg.setPixmap(pm); head.addWidget(lg)
        ttl = QLabel(f"<b style='font-size:16px'>{__app_name__}</b><br>"
                     f"<span style='color:{MUTED}'>v{__version__} &mdash; {E(t('app.subtitle'))}</span>")
        head.addWidget(ttl); head.addStretch(1)
        lay.addLayout(head)
        body = QLabel(
            f"<p>{E(t('about.devby'))} <b>{AUTHOR}</b><br>"
            f"<span style='color:{MUTED}'>{AUTHOR_TITLE}</span></p>"
            f"<p>LinkedIn: <a href='{LINKEDIN_URL}' style='color:{ACCENT}'>{LINKEDIN_HANDLE}</a></p>"
            f"<p style='color:{MUTED}'>{E(t('about.license'))}<br>"
            f"&copy; {COPYRIGHT_YEAR} {AUTHOR}. All rights reserved.</p>")
        body.setOpenExternalLinks(True)
        body.setWordWrap(True)
        body.setTextFormat(Qt.RichText)
        lay.addWidget(body)
        bb = QDialogButtonBox(QDialogButtonBox.Ok)
        bb.accepted.connect(dlg.accept)
        lay.addWidget(bb)
        dlg.setMinimumWidth(440)
        dlg.exec()

    def closeEvent(self, event):
        if self.worker and self.worker.isRunning():
            self.worker.cancel()
            self.worker.wait(3000)
        save_config(self.cfg)
        super().closeEvent(event)


def main():
    import sys
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    app = QApplication(sys.argv)
    app.setApplicationName(__app_name__)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
