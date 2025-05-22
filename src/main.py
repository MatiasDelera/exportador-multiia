
import sys
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

# ─────────────────────────────────────────────
# Asegurar que `src` esté en sys.path
# (útil cuando se ejecuta "python -m src.main")
# ─────────────────────────────────────────────
ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# ─────────────────────────────────────────────
# Importación diferida de la GUI
# ─────────────────────────────────────────────
try:
    from gui.main_window import MainWindow
except ImportError as exc:  # fallback visible
    print("Error: no se pudo importar la GUI:", exc)
    sys.exit(1)


def main() -> None:
    """Inicializa Qt y lanza la ventana."""
    # Alta-densidad (HiDPI) opcional
    # QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)  # No longer needed in recent PySide6

    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
