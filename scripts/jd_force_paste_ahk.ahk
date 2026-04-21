#Requires AutoHotkey v2.0

text := A_Args.Length >= 1 ? A_Args[1] : "测试填充123"
windowKeywords := ["evw10158991", "咚咚", "融合工作台"]
points := [
    {rx: 0.26, ry: 0.88},
    {rx: 0.30, ry: 0.88}
]
left := 253
top := 446
right := 1613
bottom := 1066
width := right - left
height := bottom - top
sendModes := ["SendInput", "SendText"]
logPath := A_ScriptDir . "\jd_force_paste_ahk.log"
startedAt := FormatTime(, "yyyy-MM-dd HH:mm:ss")
runStamp := FormatTime(, "yyyyMMdd_HHmmss") . "_" . A_TickCount
diagnosticsPath := A_Temp . "\jd_ahk_fill\run_" . runStamp
beforeFullPath := diagnosticsPath . "\before_full.png"
afterFullPath := diagnosticsPath . "\after_full.png"
afterInputPath := diagnosticsPath . "\after_input.png"
runJsonPath := diagnosticsPath . "\run.json"
attemptsJson := "[]"

if FileExist(logPath) {
    try FileDelete logPath
}

try {
    DirCreate A_Temp . "\jd_ahk_fill"
    DirCreate diagnosticsPath
    exitCode := main()
    ExitApp exitCode
} catch as exc {
    log("diagnostics_path=" . diagnosticsPath)
    log("status=exception message=" . exc.Message)
    writeRunJson("exception", 0, "", "", attemptsJson)
    ExitApp 1
}

main() {
    global text, windowKeywords, sendModes, points, left, top, width, height, startedAt
    global diagnosticsPath, beforeFullPath, afterFullPath, afterInputPath, attemptsJson

    hwnd := activateTargetWindow()
    if !hwnd {
        log("started_at=" . startedAt . " status=window_not_found text_length=" . StrLen(text))
        log("diagnostics_path=" . diagnosticsPath)
        writeRunJson("window_not_found", StrLen(text), "", "", attemptsJson)
        return 2
    }

    title := WinGetTitle("ahk_id " . hwnd)
    log("started_at=" . startedAt . " target_hwnd=" . hwnd . " title=" . title . " text_length=" . StrLen(text))
    log("diagnostics_path=" . diagnosticsPath)

    captureScreen(beforeFullPath)
    log("before_full=" . beforeFullPath)

    attempts := []
    lastPoint := "none"
    lastMode := "none"

    for point in points {
        x := Floor(left + width * point.rx)
        y := Floor(top + height * point.ry)
        lastPoint := pointLabel(point)

        MouseMove x, y, 12
        Sleep 150
        Click x, y
        Sleep 100
        Click x, y, 2
        Sleep 100

        A_Clipboard := text
        if !ClipWait(1) {
            log("clipboard_wait_failed point=" . lastPoint . " text_length=" . StrLen(text))
        }

        for mode in sendModes {
            lastMode := mode
            sendPaste(mode, text)
            attempts.Push({point: lastPoint, send_mode: mode})
            log(
                "target_hwnd=" . hwnd
                . " title=" . title
                . " text_length=" . StrLen(text)
                . " point=" . lastPoint
                . " send_mode=" . mode
            )
            Sleep 500
        }
    }

    attemptsJson := toJsonValue(attempts)
    captureScreen(afterFullPath)
    captureInputRegion(afterInputPath)
    log("after_full=" . afterFullPath)
    log("after_input=" . afterInputPath)

    finishedAt := FormatTime(, "yyyy-MM-dd HH:mm:ss")
    log(
        "finished_at=" . finishedAt
        . " target_hwnd=" . hwnd
        . " title=" . title
        . " text_length=" . StrLen(text)
        . " point=" . lastPoint
        . " send_mode=" . lastMode
        . " status=done"
    )
    writeRunJson("done", StrLen(text), hwnd, title, attemptsJson)
    return 0
}

activateTargetWindow() {
    global windowKeywords

    windows := WinGetList()
    for hwnd in windows {
        title := WinGetTitle("ahk_id " . hwnd)
        if (title = "")
            continue

        for keyword in windowKeywords {
            if InStr(title, keyword) {
                WinActivate "ahk_id " . hwnd
                WinWaitActive "ahk_id " . hwnd, , 2
                Sleep 300
                return hwnd
            }
        }
    }

    return 0
}

sendPaste(mode, text) {
    if (mode = "SendInput") {
        SendInput "^v"
        return
    }
    if (mode = "SendText") {
        SendText text
        return
    }
}

captureScreen(outputPath) {
    width := A_ScreenWidth
    height := A_ScreenHeight
    captureRegion(outputPath, 0, 0, width, height)
}

captureInputRegion(outputPath) {
    global left, top, right, bottom
    captureRegion(outputPath, left, top, right - left, bottom - top)
}

captureRegion(outputPath, x, y, width, height) {
    psScript := "$ErrorActionPreference='Stop'; Add-Type -AssemblyName System.Drawing; "
        . "$bmp = New-Object System.Drawing.Bitmap(" . width . "," . height . "); "
        . "$graphics = [System.Drawing.Graphics]::FromImage($bmp); "
        . "$graphics.CopyFromScreen(" . x . "," . y . ",0,0,$bmp.Size); "
        . "$bmp.Save('" . escapeForSingleQuotedPowerShell(outputPath) . "',[System.Drawing.Imaging.ImageFormat]::Png); "
        . "$graphics.Dispose(); $bmp.Dispose()"
    command := A_ComSpec . ' /c powershell -NoProfile -ExecutionPolicy Bypass -Command "' . psScript . '"'
    RunWait command, , "Hide"
}

escapeForSingleQuotedPowerShell(value) {
    return StrReplace(value, "'", "''")
}

writeRunJson(status, textLength, targetHwnd, title, attemptsJson) {
    global runJsonPath, beforeFullPath, afterFullPath, afterInputPath
    payload := "{"
        . '"status":' . jsonString(status)
        . ',"text_length":' . textLength
        . ',"target_hwnd":' . jsonString(String(targetHwnd))
        . ',"title":' . jsonString(title)
        . ',"attempts":' . attemptsJson
        . ',"screenshots":{'
        . '"before_full":' . jsonString(beforeFullPath)
        . ',"after_full":' . jsonString(afterFullPath)
        . ',"after_input":' . jsonString(afterInputPath)
        . '}'
        . ',"requires_manual_confirmation":true'
        . "}"
    if FileExist(runJsonPath) {
        FileDelete runJsonPath
    }
    FileAppend payload, runJsonPath, "UTF-8"
}

jsonString(value) {
    escaped := StrReplace(value, "\", "\\")
    escaped := StrReplace(escaped, '"', '\"')
    escaped := StrReplace(escaped, "`r", "\r")
    escaped := StrReplace(escaped, "`n", "\n")
    return '"' . escaped . '"'
}

toJsonValue(value) {
    if IsObject(value) {
        if hasOwnProp(value, "Length") {
            items := []
            for item in value {
                items.Push(toJsonValue(item))
            }
            return "[" . joinJson(items) . "]"
        }
        parts := []
        for key, item in value.OwnProps() {
            parts.Push(jsonString(String(key)) . ":" . toJsonValue(item))
        }
        return "{" . joinJson(parts) . "}"
    }
    if (value == true)
        return "true"
    if (value == false)
        return "false"
    if value is Number
        return String(value)
    return jsonString(String(value))
}

joinJson(items) {
    result := ""
    for index, item in items {
        result .= (index = 1 ? "" : ",") . item
    }
    return result
}

hasOwnProp(value, name) {
    try {
        return value.HasProp(name)
    } catch {
        return false
    }
}

pointLabel(point) {
    return "(" . point.rx . "," . point.ry . ")"
}

log(message) {
    global logPath
    FileAppend FormatTime(, "yyyy-MM-dd HH:mm:ss") . " | " . message . "`n", logPath, "UTF-8"
}
