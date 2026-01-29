Сводка проекта WorkerHotkeys (коротко)
Цель

Windows-only приложение (Win10/Win11) для сотрудников:

UI на PySide6 для управления хоткеями

Глобальные хоткеи работают через AutoHotkey v2 (AutoHotkeyUX.exe)

Python генерирует %APPDATA%\WorkerHotkeys\runtime.ahk из шаблона ahk/runner_template.ahk

Настройки/данные хранятся в %APPDATA%\WorkerHotkeys\

Структура проекта (важное)
project_root/
  app/
    main.py
    ui/
      main_window.py
      hotkeys_dialog.py
    core/
      ahk_manager.py
      hotkeys_store.py
      paths.py
      templates.py
  ahk/
    runner_template.ahk
  assets/
    appicona.ico
    templates/
      index_php.tpl
    (иконки кнопок png: add/edit/delete/apply/folder/keyboard и т.д.)
  AutoHotkeyUX.exe

Runtime-файлы (создаются на ПК пользователя)
%APPDATA%\WorkerHotkeys\
  config.json
  runtime.ahk
  google_file.txt
  screenshots_enabled.txt
  screenshot_hotkey.txt
  Screenshots\
    YYYY-MM-DD\
      shot_HH-mm-ss.png

Главное про AHK-генерацию

В runner_template.ahk есть маркеры:

; ====== PYTHON_BEGIN ======

; ====== PYTHON_END ======

Python (кнопка Применить) вставляет туда автогенерируемые функции HK_1()... и строки регистрации:

Hotkey("$*{combo}", (*) => HK_1(), "On")

Для action=ahk_raw: в payload хранится только тело хоткея (без ^x::).

Трей

Закрытие окна прячет приложение в трей, хоткеи продолжают работать

Двойной клик по трею — открыть

Меню: Открыть / Выход (реальный выход)

Скриншоты

Скриншоты делаются хоткеем из файла:

%APPDATA%\WorkerHotkeys\screenshot_hotkey.txt (по умолчанию #n)

Включение/выключение:

%APPDATA%\WorkerHotkeys\screenshots_enabled.txt (1/0)

Сохраняются по дням:

%APPDATA%\WorkerHotkeys\Screenshots\YYYY-MM-DD\shot_HH-mm-ss.png

UI: кнопки

Добавить / Редактировать / Удалить / Применить

Скриншоты (открыть папку)

Скрин: Вкл/Выкл (переключатель)

Хоткей: #n (кнопка изменения хоткея скрина)

Сборка EXE (PowerShell)

Установить:

pip install pyinstaller pillow


Сборка “папкой” (рекомендовано):

pyinstaller --noconfirm --clean --windowed --name WorkerHotkeys --icon assets\appicona.ico --add-data "assets;assets" --add-data "ahk;ahk" --add-binary "AutoHotkeyUX.exe;." app\main.py


Результат:

dist\WorkerHotkeys\WorkerHotkeys.exe


Если ругается WinError 5 (Access denied):

закрыть WorkerHotkeys.exe и AutoHotkeyUX.exe

выполнить:

taskkill /F /IM WorkerHotkeys.exe 2>$null
taskkill /F /IM AutoHotkeyUX.exe 2>$null


удалить dist/ build/ .spec и пересобрать

Передача коллегам

Отдавать архивом всю папку:

dist\WorkerHotkeys\


Коллега: распаковал → запустил WorkerHotkeys.exe.