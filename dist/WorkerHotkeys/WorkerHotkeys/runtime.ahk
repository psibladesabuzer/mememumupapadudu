#Requires AutoHotkey v2.0
#SingleInstance Force
#UseHook True
#Warn

APP_DIR := A_AppData "\WorkerHotkeys"
GOOGLE_FILE_STORE := APP_DIR "\google_file.txt"

Global GoogleFileName := ""
Global _LastClipboardText := ""

InitGoogleFile() {
    Global GoogleFileName, APP_DIR, GOOGLE_FILE_STORE

    DirCreate(APP_DIR)

    if FileExist(GOOGLE_FILE_STORE) {
        try {
            GoogleFileName := Trim(FileRead(GOOGLE_FILE_STORE, "UTF-8"))
        } catch {
            GoogleFileName := ""
        }
    }

    if (GoogleFileName = "") {
        GoogleFileName := "google9288ce023100f138.html"
        try FileDelete(GOOGLE_FILE_STORE)
        FileAppend(GoogleFileName, GOOGLE_FILE_STORE, "UTF-8")
    }
}

NormalizeGoogleFile(s) {
    s := Trim(s)

    if InStr(s, "`n") || InStr(s, "`r")
        return ""

    if (StrLen(s) > 60)
        return ""

    if RegExMatch(s, "i)^google[0-9a-z]+$")
        return s ".html"

    if RegExMatch(s, "i)^google[0-9a-z]+\.html$")
        return s

    return ""
}

MaybeUpdateGoogleFileFromClipboard() {
    Global GoogleFileName, _LastClipboardText, APP_DIR, GOOGLE_FILE_STORE

    try {
        clip := A_Clipboard
    } catch {
        return
    }

    if (clip = "" || clip = _LastClipboardText)
        return

    _LastClipboardText := clip

    newVal := NormalizeGoogleFile(clip)
    if (newVal = "")
        return

    if (newVal = GoogleFileName)
        return

    res := MsgBox(
        "Найден новый google verification файл в буфере:`n`n"
        . newVal . "`n`n"
        . "Заменить текущее значение?`n"
        . "(Текущее: " . GoogleFileName . ")",
        "Worker Hotkeys",
        "YesNo Icon?"
    )

    if (res = "Yes") {
        GoogleFileName := newVal
        DirCreate(APP_DIR)
        try FileDelete(GOOGLE_FILE_STORE)
        FileAppend(GoogleFileName, GOOGLE_FILE_STORE, "UTF-8")
    }
}

InitGoogleFile()
SetTimer(MaybeUpdateGoogleFileFromClipboard, 350)

; ===== Screenshots (daily folders + custom hotkey + name from clipboard) =====
SCREEN_ROOT := APP_DIR "\Screenshots"
DirCreate(SCREEN_ROOT)

SCREEN_ENABLED_FILE := APP_DIR "\screenshots_enabled.txt"
SCREEN_HOTKEY_FILE  := APP_DIR "\screenshot_hotkey.txt"

Global ScreenshotHotkey := "#n"

IsScreenshotsEnabled() {
    global SCREEN_ENABLED_FILE
    try {
        v := Trim(FileRead(SCREEN_ENABLED_FILE, "UTF-8"))
        return (v != "0")
    } catch {
        return true
    }
}

InitScreenshotHotkey() {
    global SCREEN_HOTKEY_FILE, ScreenshotHotkey, APP_DIR

    DirCreate(APP_DIR)

    try {
        v := Trim(FileRead(SCREEN_HOTKEY_FILE, "UTF-8"))
        if (v != "")
            ScreenshotHotkey := v
    } catch {
    }

    if (ScreenshotHotkey = "")
        ScreenshotHotkey := "#n"

    try FileDelete(SCREEN_HOTKEY_FILE)
    FileAppend(ScreenshotHotkey, SCREEN_HOTKEY_FILE, "UTF-8")
}

GetTodayScreenDir() {
    global SCREEN_ROOT
    day := FormatTime(, "yyyy-MM-dd")
    dayDir := SCREEN_ROOT "\" day
    DirCreate(dayDir)
    return dayDir
}

SanitizeFileNameKeepDots(s) {
    s := Trim(s)
    s := RegExReplace(s, "i)^https?://", "")
    s := StrReplace(s, "\", "_")
    s := StrReplace(s, "/", "_")
    s := StrReplace(s, "?", "_")
    s := StrReplace(s, "&", "_")
    s := StrReplace(s, "=", "_")
    s := StrReplace(s, ":", "_")
    s := StrReplace(s, "*", "_")
    s := StrReplace(s, Chr(34), "_") ; "
    s := StrReplace(s, "<", "_")
    s := StrReplace(s, ">", "_")
    s := StrReplace(s, "|", "_")
    s := RegExReplace(s, "\s+", "_")
    s := RegExReplace(s, "_{2,}", "_")
    s := Trim(s, "_")
    if (StrLen(s) > 160)
        s := SubStr(s, 1, 160)
    return s
}

BuildScreenshotBaseNameFromClipboard() {
    clip := ""
    try {
        clip := A_Clipboard
    } catch {
        return ""
    }

    clip := StrReplace(clip, "`r", " ")
    clip := StrReplace(clip, "`n", " ")
    clip := StrReplace(clip, "`t", " ")
    clip := RegExReplace(clip, "\s{2,}", " ")
    clip := Trim(clip)

    if (clip = "")
        return ""

    ; Excel иногда тащит мусор после URL — берём только первое "слово"
    if RegExMatch(clip, "^\S+", &m)
        clip := m[0]

    if (StrLen(clip) > 700)
        return ""

    clipNoProto := RegExReplace(clip, "i)^https?://", "")

    domain := clipNoProto
    if RegExMatch(clipNoProto, "i)^([^/]+)", &m1)
        domain := m1[1]

    feed := ""
    if RegExMatch(clipNoProto, "i)(?:\?|&)?feed=([^&\s#]+)", &m2)
        feed := m2[1]

    if (feed != "") {
        base := domain "_feed_" feed
        return SanitizeFileNameKeepDots(base)
    }

    pathPart := ""
    if RegExMatch(clipNoProto, "i)^[^/]+/(.+)$", &mp)
        pathPart := mp[1]

    if (pathPart != "") {
        pathPart := RegExReplace(pathPart, "\?.*$", "")
        pathPart := RegExReplace(pathPart, "\#.*$", "")

        lowPath := StrLower(pathPart)
        if InStr(lowPath, "sitemap") || RegExMatch(pathPart, "i)\.xml$") {
            base := domain "_" pathPart
            return SanitizeFileNameKeepDots(base)
        }
    }

    return SanitizeFileNameKeepDots(domain "_sitemap")
}


UniquePngPath(dayDir, baseName) {
    p := dayDir "\" baseName ".png"
    if !FileExist(p)
        return p

    i := 2
    loop {
        p2 := dayDir "\" baseName "_" i ".png"
        if !FileExist(p2)
            return p2
        i += 1
        if (i > 999)
            return dayDir "\shot.png"
    }
}

TakeScreenshot() {
    if !IsScreenshotsEnabled()
        return

    dayDir := GetTodayScreenDir()

    base := BuildScreenshotBaseNameFromClipboard()
    if (base = "")
        base := "shot"

    shotPath := UniquePngPath(dayDir, base)

    ps :=
        "Add-Type -AssemblyName System.Windows.Forms; "
      . "Add-Type -AssemblyName System.Drawing; "
      . "$b=[System.Windows.Forms.Screen]::PrimaryScreen.Bounds; "
      . "$bmp=New-Object System.Drawing.Bitmap $b.Width,$b.Height; "
      . "$g=[System.Drawing.Graphics]::FromImage($bmp); "
      . "$g.CopyFromScreen($b.Location,[System.Drawing.Point]::Empty,$b.Size); "
      . "$bmp.Save('" shotPath "',[System.Drawing.Imaging.ImageFormat]::Png); "
      . "$g.Dispose(); $bmp.Dispose();"

    RunWait('powershell -NoProfile -ExecutionPolicy Bypass -Command "' ps '"', , "Hide")
}

RegisterScreenshotHotkey() {
    global ScreenshotHotkey
    hk := "$*" . ScreenshotHotkey

    try {
        Hotkey(hk, (*) => TakeScreenshot(), "On")
    } catch {
        ScreenshotHotkey := "#n"
        hk := "$*" . ScreenshotHotkey
        Hotkey(hk, (*) => TakeScreenshot(), "On")
    }
}

InitScreenshotHotkey()
RegisterScreenshotHotkey()
; ===== end screenshots =====

; ====== PYTHON_BEGIN ======
; ====== AUTOGENERATED HOTKEYS ======
; --- functions ---
HK_1() {
    oldClip := ClipboardAll()
    
    clip := ""
    try {
        clip := A_Clipboard
    } catch {
        clip := ""
    }
    
    clip := StrReplace(clip, "`r", " ")
    clip := StrReplace(clip, "`n", " ")
    clip := StrReplace(clip, "`t", " ")
    clip := RegExReplace(clip, "\s{2,}", " ")
    sitemap := Trim(clip)
    
    if RegExMatch(sitemap, "^\S+", &m)
        sitemap := m[0]
    
    if (sitemap = "") {
        MsgBox("Буфер пуст. Скопируй sitemap URL и повтори.")
        A_Clipboard := oldClip
        return
    }
    
    tplPath := A_AppData "\WorkerHotkeys\index_php.tpl"
    if !FileExist(tplPath) {
        MsgBox("Не найден шаблон: " tplPath)
        A_Clipboard := oldClip
        return
    }
    
    phpTemplate := FileRead(tplPath, "UTF-8")
    phpText := StrReplace(phpTemplate, "__SITEMAP__", sitemap)
    phpText := StrReplace(phpText, "__GOOGLE_FILE__", GoogleFileName)
    
    A_Clipboard := phpText
    ClipWait 1
    Send("^v")
    Sleep 120
    A_Clipboard := oldClip
}

HK_2() {
    Send("/options-general.php?page=wp-promtools-pro")
    Sleep(100)
    Send("{Enter}")
}

HK_3() {
    oldClip := ClipboardAll()
    
    text :=
        "User-agent: Baiduspider`n"
      . "Disallow: /`n"
      . "User-agent: AhrefsBot`n"
      . "Disallow: /`n"
      . "User-agent: MJ12bot`n"
      . "Disallow: /`n"
      . "User-agent: BLEXBot`n"
      . "Disallow: /`n"
      . "User-agent: DotBot`n"
      . "Disallow: /`n"
      . "User-agent: SemrushBot`n"
      . "Disallow: /`n"
      . "User-agent: YandexBot`n"
      . "Disallow: /`n"
      . "User-agent: *`n"
      . "Allow: /`n"
      . "Sitemap: "
    
    A_Clipboard := text
    ClipWait 1
    Send("^v")
    Sleep 120
    A_Clipboard := oldClip
}

HK_4() {
    Send("{Tab}")
    Sleep(100)
    Send("lf'nj;tflvbybcnhfnjh")
    Sleep(100)
    Send("{Enter}")
}

HK_5() {
    Send("{Tab}")
    Sleep(100)
    Send("'nj;tflvbybcnhfnjh")
    Sleep(100)
    Send("{Enter}")
}

HK_6() {
    Send("{Tab}")
    Sleep(100)
    Send("=ghjcnbnenrf=")
    Sleep(100)
    Send("{Enter}")
}

HK_7() {
    Send("sitemap11.xml")
}

HK_8() {
    Send("wpcore")
    Sleep(200)
    Send("{Tab}")
    Sleep(200)
    Send("1njNNX^H/lq{0MJHkBXRZ*hdz")
    Sleep(200)
    Send("{Enter}")
}

HK_9() {
    oldClip := ClipboardAll()  ; Сохраняем текущий буфер обмена
    
    meta := ""  ; Инициализируем переменную
    Try {
        meta := A_Clipboard  ; Пробуем захватить текст из буфера
    } Catch {
        meta := ""  ; Если не удалось — пустая строка
    }
    
    meta := Trim(meta)  ; Убираем пробелы по краям
    
    if (meta = "" || InStr(meta, "`n") || InStr(meta, "`r")) {
        MsgBox("Скопируй meta-тег (одна строка) и повтори.")
        return
    }
    
    ; Не создаем переменную APP_DIR заново
    tplPath := APP_DIR "\meta_inject.tpl"
    
    if !FileExist(tplPath) {
        MsgBox("Не найден шаблон meta_inject.tpl:`n" . tplPath . "`nНажми «Применить» в приложении.")
        return
    }
    
    tpl := FileRead(tplPath, "UTF-8")
    
    metaSafe := StrReplace(meta, "\", "\\")
    metaSafe := StrReplace(metaSafe, "'", "\'")
    
    text := StrReplace(tpl, "__META__", metaSafe)
    
    A_Clipboard := text  ; Вставляем новый контент в буфер обмена
    ClipWait 1
    Send("^v")  ; Вставляем в приложение
    Sleep 120
    A_Clipboard := oldClip  ; Восстанавливаем старый буфер обмена
}

HK_10() {
    Send("wpadmin")
    Sleep(100)
    Send("{Tab}")
    Sleep(100)
    Send("=herjvjqybr=")
    Sleep(100)
    Send("{Enter}")
}

HK_11() {
    oldClip := ClipboardAll()
    
    text := "
    (
    $document_root = $_SERVER['DOCUMENT_ROOT'];
    
    $old_name = $document_root . '/sitemap1803.xml';
    $new_name = $document_root . '/sitemap11.xml';
    
    if (file_exists($old_name)) {
        if (rename($old_name, $new_name)) {
            echo "Файл успешно переименован в sitemap11.xml";
        } else {
            echo "Ошибка при переименовании файла";
        }
    } else {
        echo "Файл sitemap.xml не найден";
    }
    )"
    
    A_Clipboard := text
    ClipWait 1
    Send "^v"
    Sleep 120
    A_Clipboard := oldClip
}

; --- registration ---
Hotkey("$*^1", (*) => HK_1(), "On")
Hotkey("$*^3", (*) => HK_2(), "On")
Hotkey("$*^2", (*) => HK_3(), "On")
Hotkey("$*^Numpad5", (*) => HK_4(), "On")
Hotkey("$*^4", (*) => HK_5(), "On")
Hotkey("$*^5", (*) => HK_6(), "On")
Hotkey("$*^d", (*) => HK_7(), "On")
Hotkey("$*^q", (*) => HK_8(), "On")
Hotkey("$*^7", (*) => HK_9(), "On")
Hotkey("$*^e", (*) => HK_10(), "On")
Hotkey("$*^b", (*) => HK_11(), "On")
; ====== END AUTOGENERATED HOTKEYS ======
; ====== PYTHON_END ======

return
