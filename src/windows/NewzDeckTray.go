// NewzDeckTray is NewzDeck's signed-in-user notification-area companion.
// It supplies heartbeat/desktop actions to a background-service backend and
// provides quick Open, Pause/Resume and folder controls.
// Copyright (C) 2026 NewzDeck contributors.
// SPDX-License-Identifier: GPL-3.0-only
package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"net/http"
	"os"
	"os/exec"
	"path/filepath"
	"strconv"
	"strings"
	"syscall"
	"time"
	"unsafe"
)

const (
	wmDestroy       = 0x0002
	wmCommand       = 0x0111
	wmTimer         = 0x0113
	wmApp           = 0x8000
	wmLButtonDblClk = 0x0203
	wmRButtonUp     = 0x0205
	wmContextMenu   = 0x007B
	trayMessage     = wmApp + 17
	nimAdd          = 0
	nimModify       = 1
	nimDelete       = 2
	nimSetVersion   = 4
	nifMessage      = 0x1
	nifIcon         = 0x2
	nifTip          = 0x4
	nifInfo         = 0x10
	niifInfo        = 0x1
	imageIcon       = 1
	lrLoadFromFile  = 0x10
	lrDefaultSize   = 0x40
	mfString        = 0x0
	mfSeparator     = 0x800
	mfChecked       = 0x8
	tpmRightButton  = 0x2
	tpmBottomAlign  = 0x20
	swShownormal    = 1
	idOpen          = 1001
	idPause         = 1002
	idFolder        = 1003
	idAutostart     = 1004
	idExit          = 1099
)

type notifyIconData struct {
	CbSize           uint32
	HWnd             uintptr
	UID              uint32
	UFlags           uint32
	UCallbackMessage uint32
	HIcon            uintptr
	SzTip            [128]uint16
	DwState          uint32
	DwStateMask      uint32
	SzInfo           [256]uint16
	UVersion         uint32
	SzInfoTitle      [64]uint16
	DwInfoFlags      uint32
	GuidItem         [16]byte
	HBalloonIcon     uintptr
}
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

type request struct {
	ID      string `json:"id"`
	Action  string `json:"action"`
	Path    string `json:"path"`
	Initial string `json:"initial"`
	Title   string `json:"title"`
	Text    string `json:"text"`
	Enabled *bool  `json:"enabled"`
}

type app struct {
	hwnd                      uintptr
	icon                      uintptr
	appDir, userRoot, version string
	paused                    bool
}

var a app

var (
	user32                  = syscall.NewLazyDLL("user32.dll")
	shell32                 = syscall.NewLazyDLL("shell32.dll")
	kernel32                = syscall.NewLazyDLL("kernel32.dll")
	procRegisterClassExW    = user32.NewProc("RegisterClassExW")
	procCreateWindowExW     = user32.NewProc("CreateWindowExW")
	procDefWindowProcW      = user32.NewProc("DefWindowProcW")
	procDestroyWindow       = user32.NewProc("DestroyWindow")
	procPostQuitMessage     = user32.NewProc("PostQuitMessage")
	procGetMessageW         = user32.NewProc("GetMessageW")
	procTranslateMessage    = user32.NewProc("TranslateMessage")
	procDispatchMessageW    = user32.NewProc("DispatchMessageW")
	procSetTimer            = user32.NewProc("SetTimer")
	procKillTimer           = user32.NewProc("KillTimer")
	procLoadImageW          = user32.NewProc("LoadImageW")
	procDestroyIcon         = user32.NewProc("DestroyIcon")
	procCreatePopupMenu     = user32.NewProc("CreatePopupMenu")
	procAppendMenuW         = user32.NewProc("AppendMenuW")
	procTrackPopupMenu      = user32.NewProc("TrackPopupMenu")
	procDestroyMenu         = user32.NewProc("DestroyMenu")
	procSetForegroundWindow = user32.NewProc("SetForegroundWindow")
	procGetCursorPos        = user32.NewProc("GetCursorPos")
	procShellNotifyIconW    = shell32.NewProc("Shell_NotifyIconW")
	procShellExecuteW       = shell32.NewProc("ShellExecuteW")
	procGetModuleHandleW    = kernel32.NewProc("GetModuleHandleW")
	procCreateMutexW        = kernel32.NewProc("CreateMutexW")
	procCloseHandle         = kernel32.NewProc("CloseHandle")
)

func p16(s string) *uint16 { p, _ := syscall.UTF16PtrFromString(s); return p }
func putUTF16(dst []uint16, s string) {
	u := syscall.StringToUTF16(s)
	if len(u) > len(dst) {
		u = u[:len(dst)]
	}
	copy(dst, u)
}
func argValue(name, fallback string) string {
	for i := 1; i < len(os.Args)-1; i++ {
		if os.Args[i] == name {
			return os.Args[i+1]
		}
	}
	return fallback
}
func heartbeatFile() string { return filepath.Join(a.userRoot, "tray-heartbeat.txt") }
func requestFile() string   { return filepath.Join(a.userRoot, "tray-request.json") }
func replyDir() string      { return filepath.Join(a.userRoot, "tray-replies") }
func autoMarker() string    { return filepath.Join(a.userRoot, "tray-autostart.enabled") }
func portFile() string      { return filepath.Join(a.userRoot, "newzdeck.port") }

func writeAtomic(path string, b []byte) error {
	_ = os.MkdirAll(filepath.Dir(path), 0755)
	tmp := path + ".tmp"
	if e := os.WriteFile(tmp, b, 0644); e != nil {
		return e
	}
	_ = os.Remove(path)
	return os.Rename(tmp, path)
}
func writeHeartbeat() {
	_ = writeAtomic(heartbeatFile(), []byte(time.Now().Format(time.RFC3339Nano)+"\n"))
}
func readPort() int {
	b, e := os.ReadFile(portFile())
	if e != nil {
		return 0
	}
	p, _ := strconv.Atoi(strings.TrimSpace(string(b)))
	return p
}
func client() *http.Client { return &http.Client{Timeout: 2 * time.Second} }
func api(method, path string, payload any) (map[string]any, error) {
	p := readPort()
	if p <= 0 {
		return nil, fmt.Errorf("NewzDeck backend is not ready")
	}
	var body *bytes.Reader
	if payload != nil {
		b, _ := json.Marshal(payload)
		body = bytes.NewReader(b)
	} else {
		body = bytes.NewReader(nil)
	}
	req, e := http.NewRequest(method, fmt.Sprintf("http://127.0.0.1:%d%s", p, path), body)
	if e != nil {
		return nil, e
	}
	if payload != nil {
		req.Header.Set("Content-Type", "application/json")
	}
	r, e := client().Do(req)
	if e != nil {
		return nil, e
	}
	defer r.Body.Close()
	var v map[string]any
	e = json.NewDecoder(r.Body).Decode(&v)
	if e != nil {
		return nil, e
	}
	if r.StatusCode >= 400 {
		return v, fmt.Errorf("backend returned HTTP %d", r.StatusCode)
	}
	return v, nil
}

func openPath(path string) error {
	if strings.TrimSpace(path) == "" {
		return fmt.Errorf("path is empty")
	}
	r, _, _ := procShellExecuteW.Call(0, uintptr(unsafe.Pointer(p16("open"))), uintptr(unsafe.Pointer(p16(path))), 0, 0, swShownormal)
	if r <= 32 {
		return fmt.Errorf("Windows could not open the requested path")
	}
	return nil
}
func openApp() error {
	exe := filepath.Join(a.appDir, "NewzDeck.exe")
	cmd := exec.Command(exe)
	cmd.Dir = a.appDir
	cmd.SysProcAttr = &syscall.SysProcAttr{HideWindow: true, CreationFlags: 0x00000008}
	return cmd.Start()
}
func downloadFolder() string {
	v, e := api("GET", "/api/settings", nil)
	if e == nil {
		for _, k := range []string{"download_folder", "download_dir"} {
			if s, ok := v[k].(string); ok && s != "" {
				return s
			}
		}
	}
	return filepath.Join(os.Getenv("USERPROFILE"), "Downloads", "NewzDeck")
}
func refreshPaused() {
	v, e := api("GET", "/api/downloads", nil)
	if e != nil {
		return
	}
	if p, ok := v["paused"].(bool); ok {
		a.paused = p
	}
}
func togglePause() {
	refreshPaused()
	act := "pause_all"
	if a.paused {
		act = "resume_all"
	}
	if _, e := api("POST", "/api/downloads/control", map[string]any{"action": act}); e == nil {
		a.paused = !a.paused
	} else {
		notify("NewzDeck", e.Error())
	}
}

func registryCommand() string {
	exe := filepath.Join(a.appDir, "NewzDeckTray.exe")
	return fmt.Sprintf(`"%s" --app-dir "%s" --user-root "%s" --version %s`, exe, a.appDir, a.userRoot, a.version)
}
func setAutostart(enabled bool) error {
	reg := filepath.Join(os.Getenv("SystemRoot"), "System32", "reg.exe")
	key := `HKCU\Software\Microsoft\Windows\CurrentVersion\Run`
	var cmd *exec.Cmd
	if enabled {
		cmd = exec.Command(reg, "ADD", key, "/v", "NewzDeckTray", "/t", "REG_SZ", "/d", registryCommand(), "/f")
	} else {
		cmd = exec.Command(reg, "DELETE", key, "/v", "NewzDeckTray", "/f")
	}
	cmd.SysProcAttr = &syscall.SysProcAttr{HideWindow: true}
	b, e := cmd.CombinedOutput()
	if e != nil && !(!enabled && strings.Contains(strings.ToLower(string(b)), "unable to find")) {
		return fmt.Errorf("autostart registry update failed: %v", e)
	}
	if enabled {
		_ = writeAtomic(autoMarker(), []byte("1\n"))
	} else {
		_ = os.Remove(autoMarker())
	}
	return nil
}
func autostartEnabled() bool { _, e := os.Stat(autoMarker()); return e == nil }

func addIcon() bool {
	nid := notifyIconData{CbSize: uint32(unsafe.Sizeof(notifyIconData{})), HWnd: a.hwnd, UID: 1, UFlags: nifMessage | nifIcon | nifTip, UCallbackMessage: trayMessage, HIcon: a.icon}
	putUTF16(nid.SzTip[:], "NewzDeck "+a.version)
	r, _, _ := procShellNotifyIconW.Call(nimAdd, uintptr(unsafe.Pointer(&nid)))
	if r == 0 {
		return false
	}
	nid.UVersion = 4
	procShellNotifyIconW.Call(nimSetVersion, uintptr(unsafe.Pointer(&nid)))
	return true
}
func removeIcon() {
	nid := notifyIconData{CbSize: uint32(unsafe.Sizeof(notifyIconData{})), HWnd: a.hwnd, UID: 1}
	procShellNotifyIconW.Call(nimDelete, uintptr(unsafe.Pointer(&nid)))
}
func notify(title, text string) {
	nid := notifyIconData{CbSize: uint32(unsafe.Sizeof(notifyIconData{})), HWnd: a.hwnd, UID: 1, UFlags: nifInfo, DwInfoFlags: niifInfo}
	putUTF16(nid.SzInfoTitle[:], title)
	putUTF16(nid.SzInfo[:], text)
	procShellNotifyIconW.Call(nimModify, uintptr(unsafe.Pointer(&nid)))
}

func reply(id string, v map[string]any) {
	if id == "" {
		return
	}
	v["id"] = id
	b, _ := json.Marshal(v)
	_ = writeAtomic(filepath.Join(replyDir(), id+".json"), b)
}
func processRequest() {
	path := requestFile()
	b, e := os.ReadFile(path)
	if e != nil {
		return
	}
	var r request
	if json.Unmarshal(b, &r) != nil {
		return
	}
	_ = os.Remove(path)
	result := map[string]any{"ok": true}
	switch strings.ToLower(strings.TrimSpace(r.Action)) {
	case "notify":
		notify(r.Title, r.Text)
	case "open_path":
		if e := openPath(r.Path); e != nil {
			result["ok"] = false
			result["error"] = e.Error()
		}
	case "set_autostart":
		if r.Enabled == nil {
			result["ok"] = false
			result["error"] = "enabled value is required"
		} else if e := setAutostart(*r.Enabled); e != nil {
			result["ok"] = false
			result["error"] = e.Error()
		}
	default:
		result["ok"] = false
		result["error"] = "Unknown tray helper action: " + r.Action
	}
	reply(r.ID, result)
}

func showMenu() {
	refreshPaused()
	menu, _, _ := procCreatePopupMenu.Call()
	if menu == 0 {
		return
	}
	defer procDestroyMenu.Call(menu)
	pauseText := "Pause Downloads"
	if a.paused {
		pauseText = "Resume Downloads"
	}
	procAppendMenuW.Call(menu, mfString, idOpen, uintptr(unsafe.Pointer(p16("Open NewzDeck"))))
	procAppendMenuW.Call(menu, mfString, idPause, uintptr(unsafe.Pointer(p16(pauseText))))
	procAppendMenuW.Call(menu, mfString, idFolder, uintptr(unsafe.Pointer(p16("Open Downloads Folder"))))
	procAppendMenuW.Call(menu, mfSeparator, 0, 0)
	flags := uintptr(mfString)
	if autostartEnabled() {
		flags |= mfChecked
	}
	procAppendMenuW.Call(menu, flags, idAutostart, uintptr(unsafe.Pointer(p16("Run Tray at Sign-In"))))
	procAppendMenuW.Call(menu, mfSeparator, 0, 0)
	procAppendMenuW.Call(menu, mfString, idExit, uintptr(unsafe.Pointer(p16("Exit Tray"))))
	var pt point
	procGetCursorPos.Call(uintptr(unsafe.Pointer(&pt)))
	procSetForegroundWindow.Call(a.hwnd)
	procTrackPopupMenu.Call(menu, tpmRightButton|tpmBottomAlign, uintptr(pt.X), uintptr(pt.Y), 0, a.hwnd, 0)
}

func wndProc(hwnd uintptr, m uint32, w, l uintptr) uintptr {
	switch m {
	case wmTimer:
		writeHeartbeat()
		processRequest()
		return 0
	case trayMessage:
		ev := uint32(l & 0xffff)
		if ev == wmLButtonDblClk {
			_ = openApp()
			return 0
		}
		if ev == wmRButtonUp || ev == wmContextMenu {
			showMenu()
			return 0
		}
	case wmCommand:
		id := int(w & 0xffff)
		switch id {
		case idOpen:
			_ = openApp()
		case idPause:
			togglePause()
		case idFolder:
			_ = openPath(downloadFolder())
		case idAutostart:
			_ = setAutostart(!autostartEnabled())
		case idExit:
			procDestroyWindow.Call(hwnd)
		}
		return 0
	case wmDestroy:
		procKillTimer.Call(hwnd, 1)
		removeIcon()
		_ = os.Remove(heartbeatFile())
		procPostQuitMessage.Call(0)
		return 0
	}
	r, _, _ := procDefWindowProcW.Call(hwnd, uintptr(m), w, l)
	return r
}

func acquireMutex() (uintptr, bool) {
	h, _, e := procCreateMutexW.Call(0, 0, uintptr(unsafe.Pointer(p16(`Local\NewzDeck-Tray`))))
	if h == 0 {
		return 0, true
	}
	if errno, ok := e.(syscall.Errno); ok && errno == 183 {
		procCloseHandle.Call(h)
		return 0, false
	}
	return h, true
}
func main() {
	a.appDir = argValue("--app-dir", "")
	if a.appDir == "" {
		p, _ := os.Executable()
		a.appDir = filepath.Dir(p)
	}
	a.userRoot = argValue("--user-root", filepath.Join(os.Getenv("LOCALAPPDATA"), "NewzDeck"))
	a.version = argValue("--version", "3.5.33")
	_ = os.MkdirAll(replyDir(), 0755)
	mutex, ok := acquireMutex()
	if !ok {
		return
	}
	defer procCloseHandle.Call(mutex)
	inst, _, _ := procGetModuleHandleW.Call(0)
	iconPath := filepath.Join(a.appDir, "NewzDeck.ico")
	a.icon, _, _ = procLoadImageW.Call(0, uintptr(unsafe.Pointer(p16(iconPath))), imageIcon, 0, 0, lrLoadFromFile|lrDefaultSize)
	if a.icon != 0 {
		defer procDestroyIcon.Call(a.icon)
	}
	className := p16("NewzDeckTrayWindow")
	wc := wndClassEx{CbSize: uint32(unsafe.Sizeof(wndClassEx{})), WndProc: syscall.NewCallback(wndProc), Instance: inst, Icon: a.icon, IconSm: a.icon, ClassName: className}
	atom, _, _ := procRegisterClassExW.Call(uintptr(unsafe.Pointer(&wc)))
	if atom == 0 {
		return
	}
	a.hwnd, _, _ = procCreateWindowExW.Call(0, uintptr(unsafe.Pointer(className)), uintptr(unsafe.Pointer(p16("NewzDeck Tray"))), 0, 0, 0, 0, 0, 0, 0, inst, 0)
	if a.hwnd == 0 {
		return
	}
	if !addIcon() {
		return
	}
	writeHeartbeat()
	processRequest()
	procSetTimer.Call(a.hwnd, 1, 1000, 0)
	var m msg
	for {
		r, _, _ := procGetMessageW.Call(uintptr(unsafe.Pointer(&m)), 0, 0, 0)
		if int32(r) <= 0 {
			break
		}
		procTranslateMessage.Call(uintptr(unsafe.Pointer(&m)))
		procDispatchMessageW.Call(uintptr(unsafe.Pointer(&m)))
	}
}
