# app.py
from __future__ import annotations
import sys
import signal
import logging
from pathlib import Path

from PySide6 import QtCore, QtWidgets


# ---- Make package imports work no matter where you run from ----
# Project root assumed: .../MotionSimRepo/src/restructured/
THIS_FILE = Path(__file__).resolve()
APP_ROOT = THIS_FILE.parent
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

# Import MainWindow (widgets/main_window.py)
try:
    from widgets.main_window import MainWindow
except Exception as e:
    msg = (
        "ERROR: Could not import widgets.main_window: "
        f"{e}\nTip: Ensure 'widgets/__init__.py' exists, and run from "
        f"{APP_ROOT} (e.g., 'python app.py')."
    )
    print(msg, file=sys.stderr)
    raise


def parse_args(argv: list[str] | None = None):
    import argparse

    p = argparse.ArgumentParser(description="Motion Simulator UI")
    p.add_argument("--qss", type=str, default="ui/styles.qss",
                   help="Path to a Qt stylesheet (.qss). Use empty string to skip.")
    p.add_argument("--log", type=str, default="INFO",
                   help="Log level: DEBUG/INFO/WARNING/ERROR")
    p.add_argument("--title", type=str, default="Motion Simulator Control",
                   help="Main window title")
    return p.parse_args(argv or sys.argv[1:])


def configure_logging(level_str: str):
    level = getattr(logging, level_str.upper(), logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%H:%M:%S",
    )


def install_sigint_handler(app: QtWidgets.QApplication):
    """Allow Ctrl+C to close the Qt app from a terminal."""
    signal.signal(signal.SIGINT, lambda *_: app.quit())
    timer = QtCore.QTimer()
    timer.start(200)
    timer.timeout.connect(lambda: None)




def try_apply_stylesheet(app: QtWidgets.QApplication, qss_path_str: str):
    """Apply a QSS file if present and valid; never crash the app on QSS errors."""
    if not qss_path_str:
        logging.info("Stylesheet skipped (empty path).")
        return
    qss_path = (APP_ROOT / qss_path_str) if not qss_path_str.startswith("/") else Path(qss_path_str)
    if not qss_path.exists():
        logging.warning(f"Stylesheet not found: {qss_path}")
        return
    try:
        css = qss_path.read_text(encoding="utf-8")
        app.setStyleSheet(css)
        logging.info(f"Applied stylesheet: {qss_path}")
    except Exception as e:
        logging.warning(f"Skipping stylesheet ({qss_path}): {e}")


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    configure_logging(args.log)

    app = QtWidgets.QApplication(sys.argv)
    install_sigint_handler(app)

    # Soft-apply stylesheet (won't crash if invalid)
    try_apply_stylesheet(app, args.qss)

    # Create and show main window
    win = MainWindow()
    win.setWindowTitle(args.title)
    win.show()

    # Execute event loop
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())