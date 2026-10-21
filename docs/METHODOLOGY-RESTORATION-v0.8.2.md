# Восстановление методологии — v0.8.2

Дата: 21.10.2026. Исходный v0.8.1 и архивы ранее выданных версий не менялись.
Результат: исходные подробные методологии Hook/Structure/Rehook восстановлены из ранних файлов, без удаления прежних инструментов.

## Список восстановленных источников без изменений

| Архивный оригинал | SHA256 |
|---|---|
| `knowledge/01-hook.md` | `3609a5b5d847159f3f893866953f1a6e6dce0d092ea799adf0167a574c00485e` |
| `review-rules/hook-review.md` | `100e4fbcd53f6aab62d40d331abf4e74d1b7a84b24550077f00bb36550f831f7` |
| `knowledge/02-structure.md` | `6ea729353bab0ebdde3340bf7e8b94d19f380b6a33ff61fc9d93c8e7bac5fab8` |
| `review-rules/structure-review.md` | `52713f918710ffd70c82dd0e80124fbfb5c65e2914e82351fc9dfff0b9770b01` |
| `knowledge/03-rehook.md` | `33a41b0dfb740036c0721a473ac3cf490da56cccf9de62e62ef3084cf2245bbe` |
| `review-rules/rehook-review.md` | `5f80a47ae1e9b67d78a217b52e4d3a723645cdf6df33c282571fa0479d900caa` |

## Конкретные изменения

- Перенесены полный Hook Agent и Hook Reviewer (v0.2), Structure Agent и Structure Reviewer (v0.3.1), Rehook Agent, Reviewer и промпты Orchestrator (v0.4.1); оригиналы сохранены в `methodology-originals/`, активные копии нейтрализованы в части прежних нишевых примеров.
- Главный `SKILL.md` **не переписан с нуля**: добавлены ссылки на восстановленные подробные роли и совместимость хука со структурой до блокировки.
- Script Agent дополнен конкретными требованиями к foreshadow, сюжетным переходам but/therefore, payoff и режиссёрской реализации выбранного SRC-каркаса; ссылки на Jenny Hoyos и Postium проверены.
- CTA Agent получил отдельную методику и Reviewer с одним целевым действием по статье SMMBOT.
- `pipeline_gate.py` отклоняет неизвестные SRC/TR, недостающие fit/reveal/next-beat, отсутствие специализированных полей конструкций, одинаковые narrative_route, ряд пустых заглушек и нарушения очерёдности битов.
- Исторические тестовые данные расширены полями методологии. **Это только контракт JSON**, не доказательство драматургической силы.

## Проверка исторического примера

Сценарий «Не могу найти работу» из v0.8.1 теперь выдаёт `BLOCKED_STRUCTURE` с ошибками `invalid_structure_id`, `missing_reveal_map`, `missing_rehook_technique` и другими. До исправления его ошибочно считали структурно полным.

## Ограничения и незакрытые задачи

- Не существует сервера независимых AI-агентов. Reviewer status `NOT_RUN` остаётся честным; нельзя публиковать отчёт о «независимом PASS».
- Значение `structure_id` и наличие поля `investigation_steps` **не** доказывают, что расследование реально и честно. Нужен редактор, просмотр полного сценария и первоисточников.
- Не настроено гарантированное полное чтение постов Threads и импорт оригинального закрытого каталога пользователя с Telegraph.
- Для `no CTA` инструкции допускают осознанное отсутствие призыва, но нынешний JSON-контракт всё ещё требует текст: необходима будущая целевая миграция, **не сделанная в этой точечной реставрации**.
- Legacy `contract_version=0.7.0` сохранён для совместимости маркировки, но поля на практике стали строже. Старые пакеты требуют миграции.

## Перепроверенные источники

- SMMplanner: https://smmplanner.com/blog/stsienarii-korotkogho-vidieo-idiei-khuki-i-struktury-dlia-reels-shorts-i-vk-klipov/ (21.10.2026 индексная публикация; direct open cache miss)
- Tatam: https://www.tatam.com/blog/hook-rehook-framework-for-influencer-briefing (21.10.2026 полный текст)
- Creator Science/Jenny Hoyos: https://creatorscience.com/podcast/jenny-hoyos/ (21.10.2026 индексированный транскрипт)
- Postium: https://postium.ru/kak-pisat-scenarii-reels/ (21.10.2026 текст открыт)
- SMMBOT Hooks: https://smmbot.net/blog/formula-uspesnogo-huka-kak-privlec-vnimanie-v-socsetah-220.html (21.10.2026 текст открыт)
- SMMBOT Reels 17: https://smmbot.net/blog/kak-nacat-reels-17-idej-instagram-rils-dla-zahvata-vnimania-103.html (21.10.2026 текст открыт)
- SMMBOT CTA: https://smmbot.net/blog/10-prizyvov-k-dejstviu-cta-v-instagram-dla-povysenia-vovlecennosti-137.html (21.10.2026 текст открыт)
- Descript: https://www.descript.com/blog/article/learn-to-read-without-sounding-like-youre-reading (21.10.2026 текст открыт)

Решение по релизу: **skills-only обновление готово к технической установке, к автономной продакшн-работе не готово**.