# Перенос v0.8.2 в GitHub

## Почему здесь есть отдельная стадия

В исходном окружении имеется рабочий архив `reels-script-lab-universal-workspace-v0.8.2.zip`, содержащий **75 файлов**. GitHub-коннектор предоставляет операции Git, но не принимает напрямую файл из локального контейнера. Ветку нельзя объявлять импортированной, пока исходники в ней не присутствуют.

**SHA-256 рабочего ZIP:** `893596a6888b78b1b6690654b8ece274e4b828e492171179240a9b357ca1d8d0`

**SHA-256 установочного ZIP:** `86729398cebed2ffa2aaa0f0dd79a2d28241aaaf436e9b7dbcb767a189cab033`

## Способ загрузить без ручного перекладывания 75 файлов

Скачайте рабочий ZIP из исходного диалога ChatGPT, затем локально:

```bash
git clone https://github.com/Vladpryanik11/reels-script-lab.git
cd reels-script-lab
git fetch origin
git switch import/v0.8.2-baseline
python scripts/import_baseline.py "/путь/к/reels-script-lab-universal-workspace-v0.8.2.zip"
python scripts/verify_baseline.py --strict
python -m unittest discover -s tests -p 'test_*.py' -q
git add .
git commit -m "import: restore complete v0.8.2 source baseline unchanged"
git push origin import/v0.8.2-baseline
```

Скрипт копирует **исходные файлы побайтно**, ничего не переписывает и предварительно сверяет SHA архива. Затем открыть PR и дождаться проверок. Если есть изменения в файлах, которые уже есть в ветке, скрипт откажется от перезаписи.

## Статус

Первичная настройка GitHub и сохранение части доступных исторических документов не означает, что все 75 исходных файлов уже загружены. До их появления `verify_baseline --strict` должен возвращать ошибку.
