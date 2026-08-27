// Test-only helper for GitHub Actions installer upgrade smoke testing.
// It deliberately uses the same hidden window class as NewzDeckTray.exe and
// keeps its executable image loaded until WM_CLOSE is received.
package main

import (
    "os"
    "syscall"
    "unsafe"
)

const (
    wmDestroy = 0x0002
    wmClose   = 0x0010
)

type wndClassEx struct {
    CbSize     uint32
    Style      uint32
    WndProc    uintptr
    ClsExtra   int32
    WndExtra   int32
    Instance   uintptr
    Icon       uintptr
    Cursor     uintptr
    Background uintptr
    MenuName   *uint16
    ClassName  *uint16
    IconSm     uintptr
}

type point struct{ X, Y int32 }
type msg struct {
    HWnd           uintptr
    Message        uint32
    WParam, LParam uintptr
    Time           uint32
    Pt             point
    Private        uint32
}

var (
    user32               = syscall.NewLazyDLL("user32.dll")
    kernel32             = syscall.NewLazyDLL("kernel32.dll")
    procRegisterClassExW = user32.NewProc("RegisterClassExW")
    procCreateWindowExW  = user32.NewProc("CreateWindowExW")
    procDefWindowProcW   = user32.NewProc("DefWindowProcW")
    procDestroyWindow    = user32.NewProc("DestroyWindow")
    procPostQuitMessage  = user32.NewProc("PostQuitMessage")
    procGetMessageW      = user32.NewProc("GetMessageW")
    procTranslateMessage = user32.NewProc("TranslateMessage")
    procDispatchMessageW = user32.NewProc("DispatchMessageW")
    procGetModuleHandleW = kernel32.NewProc("GetModuleHandleW")
)

func p16(s string) *uint16 { p, _ := syscall.UTF16PtrFromString(s); return p }

func wndProc(hwnd uintptr, m uint32, w, l uintptr) uintptr {
    switch m {
    case wmClose:
        procDestroyWindow.Call(hwnd)
        return 0
    case wmDestroy:
        procPostQuitMessage.Call(0)
        return 0
    }
    r, _, _ := procDefWindowProcW.Call(hwnd, uintptr(m), w, l)
    return r
}

func main() {
    inst, _, _ := procGetModuleHandleW.Call(0)
    className := p16("NewzDeckTrayWindow")
    wc := wndClassEx{
        CbSize: uint32(unsafe.Sizeof(wndClassEx{})),
        WndProc: syscall.NewCallback(wndProc),
        Instance: inst,
        ClassName: className,
    }
    atom, _, _ := procRegisterClassExW.Call(uintptr(unsafe.Pointer(&wc)))
    if atom == 0 { return }
    hwnd, _, _ := procCreateWindowExW.Call(
        0,
        uintptr(unsafe.Pointer(className)),
        uintptr(unsafe.Pointer(p16("NewzDeck Tray Smoke"))),
        0, 0, 0, 0, 0, 0, 0, inst, 0,
    )
    if hwnd == 0 { return }
    if len(os.Args) > 1 { _ = os.WriteFile(os.Args[1], []byte("ready\n"), 0644) }
    var m msg
    for {
        r, _, _ := procGetMessageW.Call(uintptr(unsafe.Pointer(&m)), 0, 0, 0)
        if int32(r) <= 0 { break }
        procTranslateMessage.Call(uintptr(unsafe.Pointer(&m)))
        procDispatchMessageW.Call(uintptr(unsafe.Pointer(&m)))
    }
}
