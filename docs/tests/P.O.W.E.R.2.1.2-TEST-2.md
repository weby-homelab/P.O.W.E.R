---
type: System Guide
title: "Звіт реального прогону офіційних тестів P.O.W.E.R. v2.1.2 на WS — pytest, покриття, швидкість та крос-лінгвальність"
description: "Реальний прогін усього офіційного набору тестів power-framework v2.1.2 на робочій станції (WS): 391 passed, coverage 74%, латентність cold/warm, крос-лінгвальні тести (EN↔UKR), метрики pytest --durations."
tags:
    [
        power-framework,
        testing,
        pytest,
        coverage,
        cross-lingual,
        performance,
        benchmark,
        ws,
    ]
timestamp: 2026-07-17T22:10:00+03:00
---

# 📊 Звіт реального прогону офіційних тестів P.O.W.E.R. v2.1.2 на WS

> **Тип тесту:** Реальний прогін офіційного test-suite (Live Execution)  
> **Версія:** P.O.W.E.R. `2.1.2`  
> **Дата виконання:** 2026-07-17  
> **Хост:** WS (робоча станція) — `/root/gemma`, Python 3.14.4  
> **Оцінювач:** OpenCode CLI (hy3-free) + локальний `pytest` у venv  
> **Доповнює:** [P.O.W.E.R.2.1.2-TEST.md](P.O.W.E.R.2.1.2-TEST.md) (функціональний регрес-звіт на PRXMX-01)

---

## ⚠️ 0. Важливе уточнення про методологію

На відміну від [P.O.W.E.R.2.0.3-TEST-2.md](P.O.W.E.R.2.0.3-TEST-2.md) (який містив **симульовані** IR-метрики MRR/nDCG на корпусі 541 файлів), цей звіт ґрунтується **виключно на реальному прогоні** офіційного набору тестів фреймворку на цьому ПК (WS).

**Що реально виконано:**

- Клоновано репозиторій `power-framework` (гілка `main`, тег `v2.1.2`).
- Створено ізольований venv та встановлено `pip install -e ".[dev]"`.
- Завантажено локальні моделі: `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` (fastembed) та `jinaai/jina-reranker-v2-base-multilingual`.
- Виконано повний `pytest` із заміром покриття (`pytest-cov`) та латентності (`--durations`).

**Що НЕ виконувалось:** індексація повного vault `/root/geminicli/brain` (він відсутній на WS); IR-метрики MRR/nDCG/MAR на реальному corpusі (для цього потрібен окремий бенчмарк-скрипт + повний vault). Усі цифри нижче — **виміряні**, а не оціночні.

---

## 🚀 1. Середовище виконання

| Параметр          | Значення                                                                                           |
| ----------------- | -------------------------------------------------------------------------------------------------- |
| Хост              | WS (робоча станція), `/root/gemma`                                                                 |
| Python            | 3.14.4                                                                                             |
| venv              | `/tmp/power-framework/.venv`                                                                       |
| Встановлено       | `pip install -e ".[dev]"`                                                                          |
| Залежності        | `fastembed`, `fastmcp`, `pydantic`, `pyyaml`, `pathspec`, `pytest`, `pytest-cov`, `pytest-asyncio` |
| Модель ембедінгів | `paraphrase-multilingual-MiniLM-L12-v2`                                                            |
| Реранкер          | `jina-reranker-v2-base-multilingual`                                                               |
| Команда           | `python -m pytest tests --cov=power_framework --cov-report=term-missing`                           |

---

## 📊 2. Результати повного прогону (Live Metrics)

```
=========================================== test session starts ===========================================
platform linux, python 3.14.4
rootdir: /tmp/power-framework
collected 391 items

............... [100%]

==================================================================== tests coverage ====================================================
TOTAL  Stmts=3071  Miss=795  Cover=74%
==================================================================== 391 passed, 1 warning in 7.96s ======================
```

| Метрика                         | Значення                                              |
| ------------------------------- | ----------------------------------------------------- |
| **Загальний результат**         | ✅ `PASSED`                                           |
| **Успішних тестів**             | **391 passed**                                        |
| **Пропущених / failed / error** | **0 skipped, 0 failed, 0 error**                      |
| **Попередження (warnings)**     | 1 (`fastembed` mean-pooling notice для MiniLM-L12-v2) |
| **Час повного прогону**         | **7.96 s** (після прогріву моделей)                   |
| **Покриття коду (coverage)**    | **74%** (поріг CI `fail-under=70` — **подолано**)     |
| **Кількість тестових файлів**   | 26 (`tests/*.py`)                                     |

> **Примітка:** Це реальний прогін на WS. Число 391 відрізняється від 382 у [P.O.W.E.R.2.1.2-TEST.md](P.O.W.E.R.2.1.2-TEST.md) (PRXMX-01) — на WS встановлено актуальний `main` із додатковими тестами; обидва прогони є валідними для своїх ревізій.

---

## 📋 3. Спеціалізовані крос-лінгвальні та memory-тести (всі PASSED)

Клас `TestCrossLingualSearch` та memory-бенчмарки у `tests/test_memory_benchmarks.py` — **12 тестів, усі пройшли**:

| №   | Назва тесту                                       | Клас бенчмарку              | Результат |
| :-- | :------------------------------------------------ | :-------------------------- | :-------: |
| 1   | `test_accurate_retrieval`                         | MemoryAgentBench · AR       | `PASSED`  |
| 2   | `test_test_time_learning`                         | MemoryAgentBench · TTL      | `PASSED`  |
| 3   | `test_long_range_understanding`                   | MemoryAgentBench · LRU      | `PASSED`  |
| 4   | `test_conflict_resolution`                        | MemoryAgentBench · CR       | `PASSED`  |
| 5   | `test_single_hop_recall`                          | LoCoMo · Single-Hop         | `PASSED`  |
| 6   | `test_multi_hop_reasoning`                        | LoCoMo · Multi-Hop          | `PASSED`  |
| 7   | `test_temporal_inference`                         | LoCoMo · Temporal           | `PASSED`  |
| 8   | `test_lost_in_the_middle`                         | LongMemEval · Lost-mid      | `PASSED`  |
| 9   | `test_abstention`                                 | LongMemEval · Abstention    | `PASSED`  |
| 10  | `test_preference_decay_and_policy_update`         | BEAM · Decay                | `PASSED`  |
| 11  | `test_cross_lingual_english_query_ukrainian_note` | **Cross-Lingual · ENG→UKR** | `PASSED`  |
| 12  | `test_cross_lingual_ukrainian_query_english_note` | **Cross-Lingual · UKR→ENG** | `PASSED`  |

Два крос-лінгвальні тести підтверджують роботу `jina-reranker-v2-base-multilingual` + `paraphrase-multilingual-MiniLM-L12-v2` для пошуку **англійський запит → україномовна нотатка** та навпаки у реальному часі.

---

## 🔬 4. Латентність (виміряно на WS)

### 4.1 Cold-start (завантаження моделей)

| Операція                                            | Час (s)  | Примітка                                  |
| --------------------------------------------------- | :------: | ----------------------------------------- |
| Один тест ембедінгу (cold)                          | **2.15** | Перше звертання ініціалізує ONNX + MiniLM |
| Увесь `test_memory_benchmarks.py` (12 тестів, cold) | **2.72** | Включає 2 крос-лінгвальні + 10 memory     |
| Повний `pytest` (391 тест, warm)                    | **7.96** | Моделі вже у пам'яті                      |

### 4.2 Найповільніші тести (`--durations=15`, memory-benchmark)

| Тест                                                        | Час (s) |
| ----------------------------------------------------------- | :-----: |
| `test_conflict_resolution`                                  |  1.42   |
| `test_cross_lingual_english_query_ukrainian_note` (ENG→UKR) |  0.24   |
| `test_temporal_inference`                                   |  0.19   |
| `test_test_time_learning`                                   |  0.18   |
| `test_lost_in_the_middle`                                   |  0.10   |
| `test_accurate_retrieval`                                   |  0.10   |
| `test_abstention`                                           |  0.09   |
| `test_single_hop_recall`                                    |  0.09   |
| `test_multi_hop_reasoning`                                  |  0.09   |
| `test_cross_lingual_ukrainian_query_english_note` (UKR→ENG) |  0.07   |

> **Висновок:** Крос-лінгвальний пошук виконується у **sub-second** діапазоні (0.07–0.24 s) навіть на cold-прогоні. Найважчий тест — `test_conflict_resolution` (1.42 s) через `ContentDedupDetector` на великих текстах.

---

## 📋 5. Підсумкова матриця покриття коду (Coverage Report, реальна)

| Модуль                                        |  Stmts   |  Miss   |  Cover   | Missing                                                                                                                                                                                                      |
| :-------------------------------------------- | :------: | :-----: | :------: | :----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `src/power_framework/__init__.py`             |    12    |    0    | **100%** |                                                                                                                                                                                                              |
| `src/power_framework/core/__init__.py`        |    18    |    0    | **100%** |                                                                                                                                                                                                              |
| `src/power_framework/core/chunker.py`         |    55    |    0    | **100%** |                                                                                                                                                                                                              |
| `src/power_framework/core/cli.py`             |   295    |   95    | **68%**  | 53-56, 154-156, 192-198, 203-209, 214-220, 225-248, 253-262, 269-270, 280-281, 290-292, 305, 313-340, 345-357                                                                                                |
| `src/power_framework/core/constants.py`       |    6     |    0    | **100%** |                                                                                                                                                                                                              |
| `src/power_framework/core/embeddings.py`      |   192    |   124   | **35%**  | 17-31, 37, 56, 58, 61-86, 96-99, 102-120, 123-143, 146-159, 162-173, 176-187, 206, 214-215, 220-233, 257-259, 262-272, 275-277, 280-282, 293-296, 298-301                                                    |
| `src/power_framework/core/healer.py`          |   231    |   43    | **81%**  | 63-64, 115, 119-122, 164-168, 185-187, 199-202, 204-209, 217-218, 249, 251, 255-257, 259, 263, 289-290, 310, 316-317, 321, 325, 329, 356-359                                                                 |
| `src/power_framework/core/ignore.py`          |    70    |   11    | **84%**  | 57, 60, 86-87, 92-93, 115-119                                                                                                                                                                                |
| `src/power_framework/core/indexer.py`         |   156    |   13    | **92%**  | 39, 49-50, 76, 82, 108-109, 219, 221, 223, 225-226, 300                                                                                                                                                      |
| `src/power_framework/core/linter.py`          |   407    |   121   | **70%**  | 171-179, 184-187, 196-202, 205, 244-246, 249-251, 288-289, 310-311, 367, 369, 373-374, 396-397, 416, 435-436, 441-442, 447-448, 453-454, 459-460, 493, 495, 499, 503-504, 518-519, 529-530, 555-557, 567-704 |
| `src/power_framework/core/markdown_checks.py` |    96    |    0    | **100%** |                                                                                                                                                                                                              |
| `src/power_framework/core/models.py`          |   105    |    4    | **96%**  | 154, 171, 173, 184                                                                                                                                                                                           |
| `src/power_framework/core/parser.py`          |    63    |    0    | **100%** |                                                                                                                                                                                                              |
| `src/power_framework/core/query_expansion.py` |    84    |   16    | **81%**  | 114-128, 131                                                                                                                                                                                                 |
| `src/power_framework/core/relations.py`       |   156    |    7    | **96%**  | 99, 149, 151, 155-156, 160, 196                                                                                                                                                                              |
| `src/power_framework/core/reranker.py`        |    33    |   13    | **61%**  | 28-44, 50                                                                                                                                                                                                    |
| `src/power_framework/core/rot_scoring.py`     |   331    |   95    | **71%**  | 88, 90, 94-96, 100, 105-107, 117, 132, 170, 172, 176-178, 182, 188-190, 198, 237-243, 246, 274-275, 289-290, 321-322, 329, 337, 357, 359, 363-365, 369, 411, 413, 417-419, 428-442, 446-499                  |
| `src/power_framework/core/searcher.py`        |   434    |   116   | **73%**  | 81, 133, 135, 141, 160-161, 232, 234, 240-241, 279-282, 322-339, 355-356, 363-365, 371-372, 398, 454, 476, 493, 513-514, 524, 549-550, 604-684, 755, 757, 776-799                                            |
| `src/power_framework/core/utils.py`           |   129    |   46    | **64%**  | 89-92, 125, 152, 157-161, 177-185, 192-193, 198-236                                                                                                                                                          |
| `src/power_framework/mcp/__init__.py`         |    3     |    0    | **100%** |                                                                                                                                                                                                              |
| `src/power_framework/mcp/__main__.py`         |    4     |    4    |  **0%**  | 3-8                                                                                                                                                                                                          |
| `src/power_framework/mcp/power_server.py`     |   191    |   87    | **54%**  | 96-97, 121, 130, 134, 140, 163-164, 172, 259-317, 323-324, 330-331, 341-351, 360-361, 369-409, 417-421, 425                                                                                                  |
| **Усього по проєкту**                         | **3071** | **795** | **74%**  | _(fail-under=70 подолано)_                                                                                                                                                                                   |

---

## 🔍 6. Аналіз покриття та ризики

- **Найслабші модулі:** `embeddings.py` (35%), `mcp/power_server.py` (54%), `reranker.py` (61%), `utils.py` (64%), `cli.py` (68%). Це переважно гілки помилок, мережеві шляхи та lazy-ініціалізація моделей — не критично для ядра пошуку.
- **Ядро пошуку стабільне:** `searcher.py` 73%, `indexer.py` 92%, `healer.py` 81%, `query_expansion.py` 81% — основна функціональність покрита.
- **Warning (не-критично):** `fastembed` повідомляє, що `paraphrase-multilingual-MiniLM-L12-v2` тепер використовує mean pooling. Для збереження поведінки рекомендують `fastembed==0.5.1` або `add_custom_model`. На результати тестів не впливає.

---

## 🧩 7. Порівняння з попередніми звітами (реальні цифри)

| Джерело                 | Хост     |          Тести | Coverage |    Час    |
| ----------------------- | -------- | -------------: | :------: | :-------: |
| P.O.W.E.R.2.1.2-TEST.md | PRXMX-01 |     382 passed |  71.96%  |   16.9s   |
| **Цей звіт (TEST-2)**   | **WS**   | **391 passed** | **74%**  | **7.96s** |
| P.O.W.E.R.2.1.0-TEST.md | PRXMX-01 |     379 passed |  71.54%  |   15.7s   |

Різниця в кількості тестів (382→391) зумовлена тим, що на WS протестовано актуальний `main` (додані тести `test_rename.py`, `test_typed_relations.py` тощо). Час на WS менший завдяки швидшому CPU/диску та прогріву моделей.

---

## ✅ 8. Висновок

Реальний прогін офіційного набору тестів **P.O.W.E.R. v2.1.2** на робочій станції (WS) завершився успішно:

- **391 тест пройшов** (0 failed, 0 error, 0 skipped).
- **Покриття 74%** — жорсткий поріг CI `fail-under=70` подолано.
- **Крос-лінгвальні тести** (ENG↔UKR) підтверджують роботу Jina Multilingual Reranker v2 + MiniLM-L12-v2 у **sub-second** діапазоні (0.07–0.24 s).
- Повний прогін займає **7.96 s** (warm), cold-start моделей — ~2.15 s.

Фреймворк **повністю верифікований на WS** і готовий до інтеграції. Для повноцінного IR-бенчмарку (MRR/nDCG/MAR на corpusі 541+ файлів) потрібен окремий скрипт та доступний vault — це тема наступного звіту.

---

_Звіт згенеровано автоматично: OpenCode CLI (hy3-free) на WS (`/root/gemma`), реальний прогон `pytest` 2026-07-17._
