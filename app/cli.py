import sys
import traceback


def _show_startup_error(title: str, message: str) -> None:
    try:
        from PySide6.QtWidgets import QApplication, QMessageBox

        app = QApplication.instance()
        created = False
        if app is None:
            app = QApplication(sys.argv)
            created = True
        QMessageBox.critical(None, title, message)
        if created:
            app.processEvents()
    except Exception:
        pass


def _validate_runtime_environment() -> None:
    from app.core.paths import RESOURCES_DIR

    required_resources = [
        RESOURCES_DIR,
        RESOURCES_DIR / "icon.png",
        RESOURCES_DIR / "hero_image.png",
    ]
    missing_resources = [
        str(path)
        for path in required_resources
        if not path.exists()
    ]
    if missing_resources:
        missing = "\n".join(missing_resources)
        raise RuntimeError(f"Missing packaged resource(s):\n{missing}")


def main() -> int:
    try:
        from PySide6.QtWidgets import QApplication

        from app.main_window import MainWindow

        _validate_runtime_environment()

        application = QApplication(sys.argv)
        application.setApplicationName("Image Vectorizer")

        window = MainWindow()
        window.show()
        return application.exec()
    except ImportError as error:
        msg = (
            f"Failed to start Image Vectorizer: missing dependency ({error}).\n\n"
            "Please ensure all dependencies are installed correctly."
        )
        print(msg, file=sys.stderr)
        _show_startup_error("Dependency Error", msg)
        return 1
    except Exception as error:
        print(f"Failed to start Image Vectorizer: {error}", file=sys.stderr)
        traceback.print_exc()

        _show_startup_error(
            "Startup Error",
            f"Image Vectorizer could not start:\n{error}",
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())
