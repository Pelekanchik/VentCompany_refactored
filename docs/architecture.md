# Архітектура системи

## Загальна структура

```
ventilation_company/
├── main.py                 # Точка входу GUI
├── main_cli.py             # Точка входу CLI
├── setup.py                # Конфігурація пакету
├── requirements.txt        # Залежності
├── README.md               # Документація
├── LICENSE                 # Ліцензія MIT
├── .gitignore             # Ігнорування файлів Git
│
├── ventilation_company/    # Основний пакет
│   ├── __init__.py
│   ├── config.py           # Конфігурація
│   ├── database.py         # Робота з SQLite
│   ├── gui.py              # Графічний інтерфейс
│   ├── cad_editor.py       # CAD-редактор
│   ├── camduct_editor.py   # Розкрій листа
│   ├── detail_calculator.py # Калькулятор виробів
│   │
│   ├── project_builder/    # Модуль 1: Побудова проєкту
│   │   ├── project.py
│   │   ├── components.py
│   │   ├── specifications.py
│   │   └── export.py
│   │
│   ├── calculations/       # Модуль 2: Розрахунки
│   │   ├── cost_calculator.py
│   │   ├── salary_calculator.py
│   │   ├── expenses.py
│   │   └── pricing.py
│   │
│   ├── archive/            # Модуль 3: Архів та аналітика
│   │   ├── storage.py
│   │   ├── analytics.py
│   │   ├── statistics.py
│   │   └── reports.py
│   │
│   └── utils/              # Утиліти
│       ├── validators.py
│       ├── helpers.py
│       └── archive_manager.py
│
├── tests/                  # Модульні тести
│   ├── test_project.py
│   └── test_calculations.py
│
└── docs/                   # Документація
    └── architecture.md
```

## Модулі

### 1. project_builder
- **project.py** — клас `Project`, управління проєктом
- **components.py** — каталог компонентів, розрахунок повітропроводів
- **specifications.py** — формування специфікацій
- **export.py** — експорт у JSON, TXT, ZIP

### 2. calculations
- **cost_calculator.py** — розрахунок вартості проєкту
- **salary_calculator.py** — зарплатний фонд з податками
- **expenses.py** — облік витрат та аналіз собівартості
- **pricing.py** — методи ціноутворення

### 3. archive
- **storage.py** — архівування проєктів
- **analytics.py** — фінансова аналітика
- **statistics.py** — статистика виробництва
- **reports.py** — генерація звітів

### 4. utils
- **validators.py** — валідація даних
- **helpers.py** — допоміжні функції
- **archive_manager.py** — робота з ZIP-архівами

## База даних

SQLite (`data/company.db`) містить таблиці:
- `projects` — проєкти
- `project_components` — компоненти
- `project_materials` — матеріали
- `project_works` — роботи
- `calculations` — розрахунки
- `employees` — співробітники
- `payroll` — зарплатний фонд
- `production` — виробництво
- `archive` — архіви

## Запуск

```bash
# GUI режим
python main.py

# CLI режим
python main.py --cli

# Або через встановлений пакет
pip install -e .
vent-firm      # CLI
vent-firm-gui  # GUI
```

## Тестування

```bash
python -m unittest discover tests
```
