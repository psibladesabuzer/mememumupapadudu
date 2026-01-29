#Requires AutoHotkey v2.0
#SingleInstance Force
#UseHook True
#Warn

; ==== DPI FIX (Per-Monitor v2) ====
try DllCall("SetThreadDpiAwarenessContext", "ptr", -4, "ptr")
catch {
    try DllCall("SetThreadDpiAwarenessContext", "ptr", -3, "ptr")
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
    x := DllCall("user32\GetSystemMetrics", "int", 76, "int") ; SM_XVIRTUALSCREEN
    y := DllCall("user32\GetSystemMetrics", "int", 77, "int") ; SM_YVIRTUALSCREEN
    w := DllCall("user32\GetSystemMetrics", "int", 78, "int") ; SM_CXVIRTUALSCREEN
    h := DllCall("user32\GetSystemMetrics", "int", 79, "int") ; SM_CYVIRTUALSCREEN

    if (w <= 0 || h <= 0)
        throw Error("Bad virtual screen size")

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

    ; Save PNG using fixed CLSID (safe)
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


; ====== PYTHON_BEGIN ======
; Python inserts generated code here
; ====== PYTHON_END ======

return
