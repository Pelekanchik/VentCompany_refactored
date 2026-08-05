#!/usr/bin/env python3
"""
Модуль інтеграції HTML-редактора креслень через pywebview
"""

import os
import sqlite3
import subprocess
import sys
from pathlib import Path

# ========== ЛОГУВАННЯ ==========
LOG_FILE = Path(__file__).parent / "webview_debug.log"


def log(msg):
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"[{__import__('datetime').datetime.now().isoformat()}] {msg}\n")
    except Exception:
        pass


log("=== СТАРТ drawing_editor.py ===")
log(f"sys.argv = {sys.argv}")
log(f"__file__ = {__file__}")
log(f"cwd = {os.getcwd()}")

# Додаємо батьківську папку до шляху (для імпортів при запуску через subprocess)
editor_dir = Path(__file__).parent.resolve()
parent_dir = editor_dir.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))
log(f"sys.path[0] = {sys.path[0]}")

# Імпортуємо після додавання шляху
try:
    from ventilation_company.config import DB_PATH

    log(f"DB_PATH = {DB_PATH}")
except Exception as e:
    log(f"ПОМИЛКА імпорту config: {e}")
    # Fallback: шукаємо БД поруч зі скриптом
    DB_PATH = str(editor_dir / "ventilation.db")
    log(f"Fallback DB_PATH = {DB_PATH}")

try:
    import webview

    HAS_WEBVIEW = True
    log("pywebview імпортовано успішно")
except ImportError as e:
    HAS_WEBVIEW = False
    webview = None
    log(f"ПОМИЛКА імпорту pywebview: {e}")

HTML_EDITOR_PATH = editor_dir / "assets" / "kreslennya_proektu_pywebview.html"
log(f"HTML_EDITOR_PATH = {HTML_EDITOR_PATH}")


class DrawingApi:
    """API-міст між JavaScript (редактор) і Python (SQLite)"""

    def __init__(self, db_path: str, project_id: int, project_name: str):
        self.db_path = db_path
        self.project_id = project_id
        self.project_name = project_name
        self._window = None
        log(f"DrawingApi створено: pid={project_id}, name={project_name}")

    def set_window(self, window):
        self._window = window

    def get_project_info(self):
        log("get_project_info викликано")
        return {"project_id": self.project_id, "project_name": self.project_name}

    def load_drawing(self, project_id: int):
        log(f"load_drawing викликано для pid={project_id}")
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT drawing_data FROM project_drawings WHERE project_id = ? ORDER BY updated_at DESC LIMIT 1",
                (project_id,),
            )
            row = cursor.fetchone()
            conn.close()
            result = row[0] if row else None
            log(f"load_drawing результат: {'знайдено' if result else 'немає'}")
            return result
        except Exception as e:
            log(f"ПОМИЛКА load_drawing: {e}")
            return None

    def save_drawing(self, project_id: int, drawing_data: str) -> bool:
        log(f"save_drawing викликано для pid={project_id}, дані={len(drawing_data)} символів")
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM project_drawings WHERE project_id = ?", (project_id,))
            row = cursor.fetchone()
            if row:
                cursor.execute(
                    """UPDATE project_drawings
                       SET drawing_data = ?, updated_at = CURRENT_TIMESTAMP
                       WHERE project_id = ?""",
                    (drawing_data, project_id),
                )
            else:
                cursor.execute(
                    """INSERT INTO project_drawings (project_id, drawing_data)
                       VALUES (?, ?)""",
                    (project_id, drawing_data),
                )
            conn.commit()
            conn.close()
            log(f"save_drawing УСПІХ для pid={project_id}")
            return True
        except Exception as e:
            log(f"ПОМИЛКА save_drawing: {e}")
            return False

    def close_editor(self):
        log("close_editor викликано")
        if self._window:
            self._window.destroy()

    def save_file(self, filename: str, data: str, mime_type: str = "text/plain") -> str:
        log(f"save_file викликано: {filename}, mime={mime_type}")
        try:
            save_dir = Path(self.db_path).parent / "exports"
            save_dir.mkdir(exist_ok=True)
            filepath = save_dir / filename
            if mime_type.startswith("image/"):
                import base64

                if "," in data:
                    data = data.split(",", 1)[1]
                raw = base64.b64decode(data)
                filepath.write_bytes(raw)
            else:
                filepath.write_text(data, encoding="utf-8")
            log(f"save_file УСПІХ: {filepath}")
            return str(filepath)
        except Exception as e:
            log(f"ПОМИЛКА save_file: {e}")
            return ""

    def get_save_directory(self) -> str:
        save_dir = Path(self.db_path).parent / "exports"
        save_dir.mkdir(exist_ok=True)
        return str(save_dir)


def open_drawing_editor(
    db_path: str, project_id: int, project_name: str, width: int = 1400, height: int = 900
):
    log(f"open_drawing_editor: db={db_path}, name={project_name}")

    if not HAS_WEBVIEW:
        log("ПОМИЛКА: pywebview не встановлено")
        raise ImportError("pywebview не встановлено. Виконайте: pip install pywebview")

    html_path = HTML_EDITOR_PATH
    if not html_path.exists():
        alt_path = editor_dir / "kreslennya_proektu_pywebview.html"
        if alt_path.exists():
            html_path = alt_path
        else:
            log(f"ПОМИЛКА: HTML не знайдено: {HTML_EDITOR_PATH}")
            raise FileNotFoundError(f"HTML-редактор не знайдено: {HTML_EDITOR_PATH}")

    api = DrawingApi(db_path, project_id, project_name)
    log("Створюємо вікно pywebview...")

    window = webview.create_window(
        title=f"Креслення проєкту — {project_name}",
        url=str(html_path),
        width=width,
        height=height,
        min_size=(1000, 700),
        confirm_close=True,
        js_api=api,
    )

    api.set_window(window)

    # Автоматично відкрити DevTools (F12) після завантаження сторінки
    def on_loaded():
        try:
            window.evaluate_js(
                """
                setTimeout(function(){
                    var e = new KeyboardEvent('keydown', {
                        bubbles: true, cancelable: true, key: 'F12', keyCode: 123, which: 123
                    });
                    document.dispatchEvent(e);
                }, 800);
            """
            )
            log("DevTools відкрито автоматично")
        except Exception as e:
            log("Не вдалося відкрити DevTools: " + str(e))

    window.events.loaded += on_loaded

    log("Запускаємо webview.start()...")
    # http_server=True потрібен для коректної роботи js_api на Windows
    webview.start(debug=True, http_server=True)
    log("webview.start() завершено")


def launch_editor(db_path: str, project_id: int, project_name: str):
    """
    Запускає редактор у окремому процесі через subprocess.
    Помилки записуються у файл webview_debug.log
    """
    log(f"launch_editor: pid={project_id}, name={project_name}")
    editor_path = Path(__file__).resolve()

    # Запускаємо без CREATE_NEW_CONSOLE, але з перенаправленням у файл
    # stderr і stdout підуть у той же лог-файл через наш log()
    subprocess.Popen(
        [sys.executable, str(editor_path), db_path, str(project_id), project_name],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=subprocess.DETACHED_PROCESS,  # не чекаємо завершення, не показуємо консоль
    )
    log("subprocess.Popen виконано")


# ========== ЗАПУСК ЧЕРЕЗ КОМАНДНИЙ РЯДОК ==========
if __name__ == "__main__":
    log("=== __main__ блок ===")
    if len(sys.argv) >= 4:
        db_path = sys.argv[1]
        project_id = int(sys.argv[2])
        project_name = sys.argv[3]
        log(f"Аргументи отримано: db={db_path}, pid={project_id}, name={project_name}")
        try:
            open_drawing_editor(db_path, project_id, project_name)
        except Exception as e:
            log(f"КРИТИЧНА ПОМИЛКА: {e}")
            import traceback

            log(traceback.format_exc())
    else:
        log(
            "Недостатньо аргументів. Очікується: python drawing_editor.py <db_path> <project_id> <project_name>"
        )
