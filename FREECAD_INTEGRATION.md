# 🏗️ Інтеграція FreeCAD у VentCompany

## Встановлення FreeCAD

### Windows
1. Завантажте FreeCAD з https://www.freecad.org/downloads.php
2. Встановіть у `C:\Program Files\FreeCAD 1.0\`
3. Додайте у **системну змінну оточення PYTHONPATH**:
   ```
   C:\Program Files\FreeCAD 1.0\bin
   C:\Program Files\FreeCAD 1.0\lib
   ```
   (Панель керування → Система → Додаткові параметри системи → Змінні оточення)

### Linux (Ubuntu/Debian)
```bash
sudo apt install freecad
# або
sudo apt install freecad-daily
```

### macOS
```bash
brew install --cask freecad
```

## Перевірка

```bash
python -c "import FreeCAD; print(FreeCAD.Version)"
```

Якщо виводить версію — все добре!

## Файли інтеграції

| Файл | Опис |
|------|------|
| `ventilation_company/freecad_exporter.py` | Експорт CAD-сутностей (оновлено) |
| `ventilation_company/freecad_models.py` | **Новий** — 3D-моделі всіх виробів |
| `ventilation_company/gui/freecad_tab.py` | **Новий** — вкладка FreeCAD у GUI |
| `ventilation_company/gui/main_window.py` | Оновлено — додана вкладка FreeCAD |
| `ventilation_company/gui/products_tab.py` | Оновлено — кнопка експорту у FreeCAD |
| `main.py` | Оновлено — правильний запуск GUI |

## Підтримувані формати

| Формат | Призначення |
|--------|-------------|
| `.FCStd` | Рідний формат FreeCAD (редагований) |
| `.STEP` | Універсальний CAD-формат (SolidWorks, AutoCAD, Fusion) |
| `.STL` | 3D-друк |
| `.OBJ` | Візуалізація |

## 3D-моделі

Підтримуються всі типи виробів:
- ✅ Прямокутні/круглі повітропроводи
- ✅ Прямокутні/круглі фланці з отворами
- ✅ Прямокутні/круглі трійники
- ✅ Прямокутні/круглі переходи
- ✅ Прямокутні/круглі відводи (коліна)
- ✅ Прямокутні/круглі заглушки

## Використання

1. Додайте вироби у вкладці **"📦 Вироби"**
2. Перейдіть у вкладку **"🏗️ FreeCAD 3D"**
3. Натисніть **"Експорт усіх виробів"** або ПКМ на виробі → "Експорт .FCStd"
4. Відкрийте файл у FreeCAD!

## Проблеми?

Якщо FreeCAD не знайдено — програма працюватиме без 3D-функцій.
Всі інші модулі (специфікація, розкрій, БД) працюють незалежно.
