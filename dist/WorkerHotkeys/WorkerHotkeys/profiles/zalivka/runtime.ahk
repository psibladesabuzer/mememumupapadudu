#Requires AutoHotkey v2.0
#SingleInstance Force
#UseHook True
#Warn

; ==== DPI FIX (Per-Monitor v2) ====

try {
    DllCall("SetThreadDpiAwarenessContext", "ptr", -4, "ptr")
} catch {
    try {
        DllCall("SetThreadDpiAwarenessContext", "ptr", -3, "ptr")
    } catch {
    }
}
CoordMode "Mouse", "Screen"
CoordMode "Pixel", "Screen"
CoordMode "ToolTip", "Screen"

; =================

; ====== PATHS (profile-aware) ======
BASE_DIR := A_AppData "\WorkerHotkeys"
ACTIVE_PROFILE_FILE := BASE_DIR "\active_profile.txt"

active := "index"
try {
    if FileExist(ACTIVE_PROFILE_FILE) {
        profVal := Trim(FileRead(ACTIVE_PROFILE_FILE, "UTF-8"))
        if (profVal = "index" || profVal = "zalivka")
            active := profVal
    }
} catch {
}

PROFILE_DIR := BASE_DIR "\profiles\" active
DirCreate(PROFILE_DIR)

; APP_DIR = папка профиля (всё профильное хранится тут)
APP_DIR := PROFILE_DIR
; ===================================
; ====== LOGGING (daily files) ======
LOG_DIR := BASE_DIR "\logs"
DirCreate(LOG_DIR)

LogWrite(line) {
    global LOG_DIR
    t := FormatTime(, "HH:mm:ss")
    d := FormatTime(, "dd_MM_yyyy")
    logFile := LOG_DIR "\log_" d ".txt"
    FileAppend(line " " t "`n", logFile, "UTF-8")
}

; Build a nice line for generated Ctrl+1..4 hotkeys using toast_state.txt (written by the app)
LogGeneratedHotkey(hkN, tplN) {
    stateFile := GENERATED_DIR "\..\toast_state.txt"
    pickType := ""
    pickLang := ""
    pickSubtype := ""

    try {
        if FileExist(stateFile) {
            txt := FileRead(stateFile, "UTF-8")
            if RegExMatch(txt, "type=(.+)", &m1)
                pickType := Trim(m1[1])
            if RegExMatch(txt, "lang=(.+)", &m2)
                pickLang := Trim(m2[1])
            if RegExMatch(txt, "subtype=(.*)", &m3)
                pickSubtype := Trim(m3[1])
        }
    } catch {
    }

    ; Action name by template number (tplN)
    action := ""
    if (tplN = 1)
        action := "ZALIV"
    else if (tplN = 2)
        action := "ROLLBACK"
    else if (tplN = 3)
        action := "SITEMAP"
    else if (tplN = 4)
        action := "HIDE"
    else
        action := "HK" tplN

    scope := ""
    if (pickType != "" && pickSubtype != "")
        scope := pickType "/" pickSubtype
    else if (pickType != "")
        scope := pickType

    dirNum := GetCurrentDirNum()
    if (dirNum = "")
        dirNum := "None"
    dirNumPart := " DIRNUM-" dirNum

    if (pickLang = "")
        LogWrite("HOTKEY" dirNumPart)
    else if (scope != "")
        LogWrite("^" hkN " " scope " " action " " pickLang dirNumPart)
    else
        LogWrite("^" hkN " " action " " pickLang dirNumPart)
}



; ===== Generated templates: copy+paste HK1..HK4 =====
GENERATED_DIR := APP_DIR "\generated_templates"

CopyFileToClipboardAndPaste(filePath) {
    try {
        if !FileExist(filePath) {
            ToolTip("Нет файла: " filePath)
            SetTimer(() => ToolTip(), -1200)
            return
        }

        txt := FileRead(filePath, "UTF-8")

        dn := GetCurrentDirNum()
        if (dn != "") {
            txt := StrReplace(txt, "__DIR_NUM__", dn)
        }

        if Trim(txt) = "" {
            ToolTip("Файл пустой: " filePath)
            SetTimer(() => ToolTip(), -1200)
            return
        }

        A_Clipboard := ""
        A_Clipboard := txt
        ClipWait 1
        Send "^v"
        Sleep 50
        Send "^{Home}"
    } catch as e {
        ToolTip("Ошибка: " e.Message)
        SetTimer(() => ToolTip(), -1500)
    }
}
; ===== end generated templates =====


; ===== DIR_NUM queue (profile-aware) =====
GetDirNumOverride() {
    f := APP_DIR "\dirnum_override.txt"
    try {
        if FileExist(f) {
            v := Trim(FileRead(f, "UTF-8"))
            return v
        }
    } catch {
        ; ignore
    }
    return ""
}

GetDirNumFromQueue() {
    qf := APP_DIR "\dirnum_queue.txt"
    if !FileExist(qf)
        return ""

    nums := []
    for line in StrSplit(FileRead(qf, "UTF-8"), "`n") {
        v := Trim(StrReplace(line, "`r"))
        if v != ""
            nums.Push(v)
    }
    if (nums.Length = 0)
        return ""

    idxFile := APP_DIR "\dirnum_queue_index.txt"
    idx := 1

    if FileExist(idxFile) {
        raw := Trim(FileRead(idxFile, "UTF-8"))
        if RegExMatch(raw, "^\d+$")
            idx := raw + 0
    }

    if (idx < 1 || idx > nums.Length)
        idx := 1

    return nums[idx]
}

GetCurrentDirNum() {
    ov := GetDirNumOverride()
    if (ov != "")
        return ov
    return GetDirNumFromQueue()
}

AdvanceDirNum(*) {
    qf := APP_DIR "\dirnum_queue.txt"
    if !FileExist(qf)
        return

    nums := []
    for line in StrSplit(FileRead(qf, "UTF-8"), "`n") {
        v := Trim(StrReplace(line, "`r"))
        if v != ""
            nums.Push(v)
    }
    if (nums.Length = 0)
        return

    idxFile := APP_DIR "\dirnum_queue_index.txt"
    idx := 1

    if FileExist(idxFile) {
        raw := Trim(FileRead(idxFile, "UTF-8"))
        if RegExMatch(raw, "^\d+$")
            idx := raw + 0
    }

    idx := idx + 1
    if (idx > nums.Length)
        idx := 1

    try FileDelete(idxFile)
    FileAppend(idx, idxFile, "UTF-8")

    ToolTip("DIR_NUM -> " nums[idx])
    SetTimer(() => ToolTip(), -700)
}
; ===== end DIR_NUM queue =====

    ; по желанию можно показать подсказку:
    ; ToolTip("D

IsDBMode() {
    ; DB режим = существует HK2.php
    return FileExist(GENERATED_DIR "\HK2.php")
}



; ===== end generated hotkeys =====


; ===== Google file (ОБЩИЙ для всех профилей) =====
GOOGLE_FILE_STORE := BASE_DIR "\google_file.txt"

Global GoogleFileName := ""
Global _LastClipboardText := ""

InitGoogleFile() {
    Global GoogleFileName, BASE_DIR, GOOGLE_FILE_STORE

    DirCreate(BASE_DIR)

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
    Global GoogleFileName, _LastClipboardText, BASE_DIR, GOOGLE_FILE_STORE

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
        DirCreate(BASE_DIR)
        try FileDelete(GOOGLE_FILE_STORE)
        FileAppend(GoogleFileName, GOOGLE_FILE_STORE, "UTF-8")
    }
}

InitGoogleFile()
SetTimer(MaybeUpdateGoogleFileFromClipboard, 350)
; ===== end Google file =====

; ===== DIR_NUM NEXT hotkey (profile) =====
DIRNUM_NEXT_HOTKEY_FILE := APP_DIR "\dirnum_next_hotkey.txt"
Global DirNumNextHotkey := "#m"  ; default Win+M

InitDirnumNextHotkey() {
    global DIRNUM_NEXT_HOTKEY_FILE, DirNumNextHotkey, APP_DIR

    DirCreate(APP_DIR)

    try {
        if FileExist(DIRNUM_NEXT_HOTKEY_FILE) {
            v := Trim(FileRead(DIRNUM_NEXT_HOTKEY_FILE, "UTF-8"))
            if (v != "")
                DirNumNextHotkey := v
        }
    } catch {
    }

    if (DirNumNextHotkey = "")
        DirNumNextHotkey := "#m"

    ; гарантируем, что файл есть
    try FileDelete(DIRNUM_NEXT_HOTKEY_FILE)
    FileAppend(DirNumNextHotkey, DIRNUM_NEXT_HOTKEY_FILE, "UTF-8")
}

RegisterDirnumNextHotkey() {
    global DirNumNextHotkey

    hk := "$*" . DirNumNextHotkey
    try {
        Hotkey(hk, HandleDirnumNextHotkey, "On")
    } catch {
        ; если юзер ввёл фигню — откатим на Win+M
        DirNumNextHotkey := "#m"
        hk := "$*" . DirNumNextHotkey
        Hotkey(hk, HandleDirnumNextHotkey, "On")
    }
}

HandleDirnumNextHotkey(*) {
    global DirNumNextHotkey
    LogWrite("HOTKEY " DirNumNextHotkey " DIRNUM_NEXT")
    AdvanceDirNum()
}


InitDirnumNextHotkey()
RegisterDirnumNextHotkey()
; ===== end DIR_NUM NEXT hotkey =====

; ===== Screenshots (PROFILE: daily folders + custom hotkey + name from clipboard) =====
SCREEN_ROOT := APP_DIR "\Screenshots"
DirCreate(SCREEN_ROOT)

SCREEN_ENABLED_FILE := APP_DIR "\screenshots_enabled.txt"
SCREEN_HOTKEY_FILE  := APP_DIR "\screenshot_hotkey.txt"

Global ScreenshotHotkey := "#n"

IsScreenshotsEnabled() {
    global SCREEN_ENABLED_FILE
    try {
        enabledVal := Trim(FileRead(SCREEN_ENABLED_FILE, "UTF-8"))
        return (enabledVal != "0")
    } catch {
        return true
    }
}

InitScreenshotHotkey() {
    global SCREEN_HOTKEY_FILE, ScreenshotHotkey, APP_DIR

    DirCreate(APP_DIR)

    try {
        hotkeyVal := Trim(FileRead(SCREEN_HOTKEY_FILE, "UTF-8"))
        if (hotkeyVal != "")
            ScreenshotHotkey := hotkeyVal
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
    global active

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

    if RegExMatch(clip, "^\S+", &m)
        clip := m[0]

    if (StrLen(clip) > 700)
        return ""

    clipNoProto := RegExReplace(clip, "i)^https?://", "")

    if (active = "zalivka")
        return SanitizeFileNameKeepDots(clipNoProto)

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

; ---- GDI+ startup ONCE (важно, чтобы скрины работали многократно) ----
Global GDIP_TOKEN := 0

TakeScreenshot() {
    if !IsScreenshotsEnabled()
        return

    dayDir := GetTodayScreenDir()

    base := BuildScreenshotBaseNameFromClipboard()
    if (base = "")
        base := "shot"

    shotPath := UniquePngPath(dayDir, base)

    try {
        CaptureVirtualScreenToPng(shotPath)
        LogWrite("HOTKEY " ScreenshotHotkey " SCREENSHOT " shotPath)
    } catch {
        ; ничего не делаем
    }
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

; Запускаем GDI+ один раз
GDIP_TOKEN := Gdip_Startup()

; ===== Screen capture: GDI BitBlt + GDI+ save (no PowerShell, DPI-safe) =====

CaptureVirtualScreenToPng(outPath) {
    mon := GetSelectedMonitor()
    GetMonitorRect(mon, &x, &y, &w, &h)

    if (w <= 0 || h <= 0)
        throw Error("Bad monitor size")

    hdcScreen := DllCall("user32\GetDC", "ptr", 0, "ptr")
    if !hdcScreen
        throw Error("GetDC failed")

    hdcMem := DllCall("gdi32\CreateCompatibleDC", "ptr", hdcScreen, "ptr")
    if !hdcMem {
        DllCall("user32\ReleaseDC", "ptr", 0, "ptr", hdcScreen)
        throw Error("CreateCompatibleDC failed")
    }

    hbm := DllCall("gdi32\CreateCompatibleBitmap", "ptr", hdcScreen, "int", w, "int", h, "ptr")
    if !hbm {
        DllCall("gdi32\DeleteDC", "ptr", hdcMem)
        DllCall("user32\ReleaseDC", "ptr", 0, "ptr", hdcScreen)
        throw Error("CreateCompatibleBitmap failed")
    }

    obm := DllCall("gdi32\SelectObject", "ptr", hdcMem, "ptr", hbm, "ptr")

    ok := DllCall("gdi32\BitBlt"
        , "ptr", hdcMem, "int", 0, "int", 0, "int", w, "int", h
        , "ptr", hdcScreen, "int", x, "int", y
        , "uint", 0x00CC0020) ; SRCCOPY

    DllCall("gdi32\SelectObject", "ptr", hdcMem, "ptr", obm)
    DllCall("gdi32\DeleteDC", "ptr", hdcMem)
    DllCall("user32\ReleaseDC", "ptr", 0, "ptr", hdcScreen)

    if !ok {
        DllCall("gdi32\DeleteObject", "ptr", hbm)
        throw Error("BitBlt failed")
    }

    pBitmap := 0
    if DllCall("gdiplus\GdipCreateBitmapFromHBITMAP", "ptr", hbm, "ptr", 0, "ptr*", &pBitmap) != 0 || !pBitmap {
        DllCall("gdi32\DeleteObject", "ptr", hbm)
        throw Error("GdipCreateBitmapFromHBITMAP failed")
    }

    DllCall("gdi32\DeleteObject", "ptr", hbm)

    Gdip_SaveBitmapToPng(pBitmap, outPath)
    DllCall("gdiplus\GdipDisposeImage", "ptr", pBitmap)
}

Gdip_Startup() {
    static token := 0
    if token
        return token

    si := Buffer(16 + A_PtrSize*2, 0)
    NumPut("uint", 1, si, 0) ; GdiplusVersion = 1

    t := 0
    if DllCall("gdiplus\GdiplusStartup", "ptr*", &t, "ptr", si, "ptr", 0) != 0 || !t
        throw Error("GdiplusStartup failed")

    token := t
    return token
}

Gdip_GetPngClsidBuf() {
    ; PNG encoder CLSID: {557CF406-1A04-11D3-9A73-0000F81EF32E}
    static clsBuf := 0
    if clsBuf
        return clsBuf

    clsBuf := Buffer(16, 0)
    s := "{557CF406-1A04-11D3-9A73-0000F81EF32E}"
    if DllCall("ole32\CLSIDFromString", "wstr", s, "ptr", clsBuf.Ptr) != 0
        throw Error("CLSIDFromString failed for PNG")
    return clsBuf
}

Gdip_SaveBitmapToPng(pBitmap, outPath) {
    cls := Gdip_GetPngClsidBuf()
    if DllCall("gdiplus\GdipSaveImageToFile", "ptr", pBitmap, "wstr", outPath, "ptr", cls.Ptr, "ptr", 0) != 0
        throw Error("GdipSaveImageToFile failed")
}

; ===== end screenshots =====

; ===== Screenshot screen selection =====
GetSelectedMonitor() {
    settingsFile := A_ScriptDir "\screenshot_screen.json"
    mode := "auto"
    idx := ""

    if FileExist(settingsFile) {
        txt := FileRead(settingsFile, "UTF-8")

        if RegExMatch(txt, '"mode"\s*:\s*"([^"]+)"', &m)
            mode := m[1]

        if RegExMatch(txt, '"index"\s*:\s*(\d+)', &n)
            idx := n[1]
    }

    if (mode = "screen" && idx != "") {
        mon := Integer(idx) + 1
        if (mon >= 1 && mon <= MonitorGetCount())
            return mon
    }

    return MonitorGetPrimary()
}

GetMonitorRect(mon, &L, &T, &W, &H) {
    MonitorGet(mon, &left, &top, &right, &bottom)
    L := left
    T := top
    W := right - left
    H := bottom - top
}

GetZalivkaMode() {
    modeFile := APP_DIR "\mode.txt"
    try {
        m := Trim(FileRead(modeFile, "UTF-8"))
        if (m = "db" || m = "html")
            return m
    } catch {
    }
    return "db"
}

HandleGeneratedHotkey(hkN, tplN, *) {
    mode := GetZalivkaMode()

    if (mode = "html" && tplN > 2) {
    ToolTip("HTML: доступны Ctrl+1 и Ctrl+2")
    SetTimer(() => ToolTip(), -700)
    return
    }
    if (mode = "db" && tplN > 4) {
        return
    }

    LogGeneratedHotkey(hkN, tplN)

    CopyFileToClipboardAndPaste(GENERATED_DIR "\HK" tplN ".php")
    ShowToastForGenerated(tplN)
}

ShowInsertToast(text, colorHex := "00FF00", ms := 2000) {
    static gui := 0, lbl := 0

    if !gui {
        gui := Gui("+AlwaysOnTop -Caption +ToolWindow +E0x20") ; E0x20 = click-through
        gui.BackColor := "101826"
        gui.MarginX := 14
        gui.MarginY := 10
        gui.Opt("+LastFound")
        WinSetTransparent(210, gui.Hwnd) ; полупрозрачность (0..255)

        lbl := gui.AddText("vLbl c" colorHex " s12 Bold", text)
    } else {
        lbl.Opt("c" colorHex)
        lbl.Text := text
    }

    ; ---- позиция: низ экрана справа/по центру ----
    w := 10, h := 10
    gui.Show("NA AutoSize")
    gui.GetPos(, , &gw, &gh)

    screenW := A_ScreenWidth
    screenH := A_ScreenHeight
    x := (screenW - gw) // 2
    y := screenH - gh - 40

    gui.Show("NA x" x " y" y)

        SetTimer(HideToastGui.Bind(gui), -ms)
}

HideToastGui(gui) {
    gui.Hide()
}


RegisterGeneratedHotkeys() {
    mode := GetZalivkaMode()

    if (mode = "html") {
        hkMap := Map(1, 1, 2, 2)
    } else {
        hkMap := Map(1, 1, 2, 3, 3, 4, 4, 2)
    }

    for hkN, tplN in hkMap {
        Hotkey("$*^" hkN, HandleGeneratedHotkey.Bind(hkN, tplN), "On")
    }

    ; --- DIR_NUM NEXT HOTKEY ---
    hkFile := APP_DIR "\dirnum_next_hotkey.txt"

    if FileExist(hkFile) {
        hk := Trim(FileRead(hkFile, "UTF-8"))
        try {
            Hotkey("$*" hk, HandleDirnumNextHotkey, "On")
        } catch as e {
            MsgBox("Hotkey register ERROR:`n" e.Message)
        }
    }
}

; ===== Toast notification =====

ShowToastForGenerated(n) {
    stateFile := GENERATED_DIR "\..\toast_state.txt"

    if !FileExist(stateFile)
        return

    pickType := ""
    pickLang := ""
    pickSubtype := ""

    txt := FileRead(stateFile, "UTF-8")

    if RegExMatch(txt, "type=(.+)", &m1)
    pickType := Trim(m1[1])

    if RegExMatch(txt, "lang=(.+)", &m2)
        pickLang := Trim(m2[1])

    if RegExMatch(txt, "subtype=(.*)", &m3)
        pickSubtype := Trim(m3[1])


    ; ---------- Формируем текст ----------
    text := ""
    color := "0xffffff"

    ; Ctrl+1 - заливка (зелёный)
    ; Ctrl+2 - sitemap (синий)
    ; Ctrl+3 - hide (фиолетовый)
    ; Ctrl+4 - rollback (красный)

    prefix := (pickType != "" ? pickType " " : "")
    lang := pickLang

    if (n = 1) {
        text := prefix "Заливка " lang
        color := "0x2e7d32"
    }
    else if (n = 3) {
        text := prefix "Sitemap " lang
        color := "0x1565c0"
    }
    else if (n = 4) {
        text := prefix "Hide " lang
        color := "0x6a1b9a"
    }
    else if (n = 2) {
        text := prefix "Rollback " lang
        color := "0xc62828"
    }
    else {
        text := prefix "HK" n " " lang
        color := "0x999999"
    }


; ---------- Создаём GUI ----------
    toastGui := Gui("+AlwaysOnTop -Caption +ToolWindow +E0x20")
    toastGui.BackColor := "0x111827"

    toastGui.MarginX := 18
    toastGui.MarginY := 12

    toastGui.SetFont("s14 Bold", "Segoe UI")
    txtCtrl := toastGui.AddText("c" color " Center", text)


    toastGui.Show("AutoSize NoActivate")

    WinGetPos(&x, &y, &w, &h, toastGui.Hwnd)
    ; ---- rounded corners ----
    radius := 18
    rgn := DllCall("gdi32\CreateRoundRectRgn"
        , "int", 0, "int", 0, "int", w + 1, "int", h + 1
        , "int", radius, "int", radius
        , "ptr")
    DllCall("user32\SetWindowRgn", "ptr", toastGui.Hwnd, "ptr", rgn, "int", true)

    ; a bit less transparent to feel like an alert
    try WinSetTransparent(245, toastGui.Hwnd)

    screenW := A_ScreenWidth
    screenH := A_ScreenHeight

    posX := (screenW - w) // 2
    posY := screenH - h - 60

    toastGui.Show("x" posX " y" posY " NoActivate")

    SetTimer(() => toastGui.Destroy(), -2000)
}


; ====== PYTHON_BEGIN ======
; ====== AUTOGENERATED HOTKEYS ======
; --- functions ---
HK_1() {
    LogWrite("HOTKEY ^Numpad5 Пароль #3 для шеллов")
    Send("{Tab}")
    Sleep(100)
    Send("lf'nj;tflvbybcnhfnjh")
    Sleep(100)
    Send("{Enter}")
}

HK_2() {
    LogWrite("HOTKEY ^4 Пароль #1 для шеллов")
    Send("{Tab}")
    Sleep(100)
    Send("'nj;tflvbybcnhfnjh")
    Sleep(100)
    Send("{Enter}")
}

HK_3() {
    LogWrite("HOTKEY ^5 Пароль #2 для шеллов")
    Send("{Tab}")
    Sleep(100)
    Send("=ghjcnbnenrf=")
    Sleep(100)
    Send("{Enter}")
}

HK_4() {
    LogWrite("HOTKEY ^q Ввод стандартного логина (wpcore) и пароля (ДЛЯ ВХОДА В АДМИНКУ)")
    Send("wpcore")
    Sleep(200)
    Send("{Tab}")
    Sleep(200)
    Send("1njNNX^H/lq{0MJHkBXRZ*hdz")
    Sleep(200)
    Send("{Enter}")
}

HK_5() {
    LogWrite("HOTKEY ^e Ввод стандартного логина (wpadmin) и пароля (ДЛЯ ВХОДА В АДМИНКУ)")
    Send("wpadmin")
    Sleep(100)
    Send("{Tab}")
    Sleep(100)
    Send("=herjvjqybr=")
    Sleep(100)
    Send("{Enter}")
}

HK_6() {
    LogWrite("HOTKEY ^!#p ^1 ОБЫЧНЫЙ СКРИПТ")
    ; empty ahk_raw body
}

HK_7() {
    LogWrite("HOTKEY ^#!O ^2 СКРИПТ-РОЛЛБЭК")
    ; empty ahk_raw body
}

HK_8() {
    LogWrite("HOTKEY !#^I ^3 СКРИПТ-САЙТМЕП")
    ; empty ahk_raw body
}

HK_9() {
    LogWrite("HOTKEY !#^U ^4 СКРИПТ-ХАЙД")
    ; empty ahk_raw body
}

; --- registration ---
Hotkey("$*^Numpad5", (*) => HK_1(), "On")
Hotkey("$*^4", (*) => HK_2(), "On")
Hotkey("$*^5", (*) => HK_3(), "On")
Hotkey("$*^q", (*) => HK_4(), "On")
Hotkey("$*^e", (*) => HK_5(), "On")
Hotkey("$*^!#p", (*) => HK_6(), "On")
Hotkey("$*^#!O", (*) => HK_7(), "On")
Hotkey("$*!#^I", (*) => HK_8(), "On")
Hotkey("$*!#^U", (*) => HK_9(), "On")
RegisterGeneratedHotkeys()
; ====== END AUTOGENERATED HOTKEYS ======
; ====== PYTHON_END ======

return
