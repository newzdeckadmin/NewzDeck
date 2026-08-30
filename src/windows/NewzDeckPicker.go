// NewzDeckPicker provides NewzDeck's native Windows folder chooser plus short-lived
// desktop/update handoff helpers. The retired --taskbar-fix mode remains only for
// compatibility with older callers.
// Copyright (C) 2026 NewzDeck contributors.
// SPDX-License-Identifier: GPL-3.0-only
package main

import (
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"runtime"
	"strings"
	"syscall"
	"time"
	"unsafe"
)

var (
	shell32                                     = syscall.NewLazyDLL("shell32.dll")
	ole32                                       = syscall.NewLazyDLL("ole32.dll")
	user32                                      = syscall.NewLazyDLL("user32.dll")
	kernel32                                    = syscall.NewLazyDLL("kernel32.dll")
	procSHBrowseForFolderW                      = shell32.NewProc("SHBrowseForFolderW")
	procSHGetPathFromIDListW                    = shell32.NewProc("SHGetPathFromIDListW")
	procShellExecuteExW                         = shell32.NewProc("ShellExecuteExW")
	procCoTaskMemFree                           = ole32.NewProc("CoTaskMemFree")
	procCoInitializeEx                          = ole32.NewProc("CoInitializeEx")
	procCoUninitialize                          = ole32.NewProc("CoUninitialize")
	procSendMessageW                            = user32.NewProc("SendMessageW")
	procPostMessageW                            = user32.NewProc("PostMessageW")
	procFindWindowW                             = user32.NewProc("FindWindowW")
	procEnumWindows                             = user32.NewProc("EnumWindows")
	procGetWindowTextLengthW                    = user32.NewProc("GetWindowTextLengthW")
	procGetWindowTextW                          = user32.NewProc("GetWindowTextW")
	procIsWindowVisible                         = user32.NewProc("IsWindowVisible")
	procIsWindow                                = user32.NewProc("IsWindow")
	procLoadImageW                              = user32.NewProc("LoadImageW")
	procDestroyIcon                             = user32.NewProc("DestroyIcon")
	procSetCurrentProcessExplicitAppUserModelID = shell32.NewProc("SetCurrentProcessExplicitAppUserModelID")
	procMoveFileExW                             = kernel32.NewProc("MoveFileExW")
	procWaitForSingleObject                     = kernel32.NewProc("WaitForSingleObject")
	procGetExitCodeProcess                      = kernel32.NewProc("GetExitCodeProcess")
	procCloseHandle                             = kernel32.NewProc("CloseHandle")
)

const (
	coinitApartmentThreaded = 0x2
	bifReturnOnlyFSDirs     = 0x0001
	bifEditBox              = 0x0010
	bifNewDialogStyle       = 0x0040
	wmUser                  = 0x0400
	bffmInitialized         = 1
	bffmSetSelectionW       = wmUser + 103
	wmClose                 = 0x0010
	wmSetIcon               = 0x0080
	iconSmall               = 0
	iconBig                 = 1
	imageIcon               = 1
	lrLoadFromFile          = 0x0010
	lrDefaultSize           = 0x0040
	movefileReplaceExisting = 0x1
	seeMaskNoCloseProcess   = 0x00000040
	swHide                  = 0
	waitObject0             = 0
	infinite                = 0xFFFFFFFF
)

type browseInfo struct {
	hwndOwner      uintptr
	pidlRoot       uintptr
	pszDisplayName *uint16
	lpszTitle      *uint16
	ulFlags        uint32
	lpfn           uintptr
	lParam         uintptr
	iImage         int32
}

type shellExecuteInfo struct {
	cbSize       uint32
	fMask        uint32
	hwnd         uintptr
	lpVerb       *uint16
	lpFile       *uint16
	lpParameters *uint16
	lpDirectory  *uint16
	nShow        int32
	hInstApp     uintptr
	lpIDList     uintptr
	lpClass      *uint16
	hkeyClass    uintptr
	dwHotKey     uint32
	hIcon        uintptr
	hProcess     uintptr
}

var browseInitial string

func p16(s string) *uint16 { p, _ := syscall.UTF16PtrFromString(s); return p }

func browseCallback(hwnd uintptr, msg uint32, lParam, data uintptr) uintptr {
	if msg == bffmInitialized && browseInitial != "" {
		procSendMessageW.Call(hwnd, bffmSetSelectionW, 1, uintptr(unsafe.Pointer(p16(browseInitial))))
	}
	return 0
}

func writeAtomic(path, text string) error {
	if path == "" {
		return nil
	}
	if err := os.MkdirAll(filepath.Dir(path), 0755); err != nil {
		return err
	}
	tmp := path + ".tmp"
	if err := os.WriteFile(tmp, []byte(text), 0644); err != nil {
		return err
	}
	r, _, _ := procMoveFileExW.Call(uintptr(unsafe.Pointer(p16(tmp))), uintptr(unsafe.Pointer(p16(path))), movefileReplaceExisting)
	if r == 0 {
		_ = os.Remove(path)
		return os.Rename(tmp, path)
	}
	return nil
}

func chooseFolder(resultFile, startedFile, initial, title string) {
	runtime.LockOSThread()
	defer runtime.UnlockOSThread()
	_, _, _ = procCoInitializeEx.Call(0, coinitApartmentThreaded)
	defer procCoUninitialize.Call()
	_ = writeAtomic(startedFile, "started\n")
	browseInitial = initial
	display := make([]uint16, 32768)
	bi := browseInfo{pszDisplayName: &display[0], lpszTitle: p16(title), ulFlags: bifReturnOnlyFSDirs | bifEditBox | bifNewDialogStyle, lpfn: syscall.NewCallback(browseCallback)}
	pidl, _, _ := procSHBrowseForFolderW.Call(uintptr(unsafe.Pointer(&bi)))
	if pidl == 0 {
		_ = writeAtomic(resultFile, "CANCEL\n")
		return
	}
	defer procCoTaskMemFree.Call(pidl)
	path := make([]uint16, 32768)
	ok, _, _ := procSHGetPathFromIDListW.Call(pidl, uintptr(unsafe.Pointer(&path[0])))
	if ok == 0 {
		_ = writeAtomic(resultFile, "ERROR\nWindows could not resolve the selected folder.\n")
		return
	}
	folder := syscall.UTF16ToString(path)
	if strings.TrimSpace(folder) == "" {
		_ = writeAtomic(resultFile, "CANCEL\n")
		return
	}
	_ = writeAtomic(resultFile, "OK\n"+folder+"\n")
}

func windowTitle(hwnd uintptr) string {
	n, _, _ := procGetWindowTextLengthW.Call(hwnd)
	if n == 0 {
		return ""
	}
	buf := make([]uint16, int(n)+1)
	procGetWindowTextW.Call(hwnd, uintptr(unsafe.Pointer(&buf[0])), uintptr(len(buf)))
	return syscall.UTF16ToString(buf)
}

func isNewzDeckWindow(hwnd uintptr) bool {
	vis, _, _ := procIsWindowVisible.Call(hwnd)
	if vis == 0 {
		return false
	}
	title := strings.TrimSpace(windowTitle(hwnd))
	low := strings.ToLower(title)
	return strings.EqualFold(title, "NewzDeck") ||
		strings.HasPrefix(low, "newzdeck -") ||
		strings.HasPrefix(low, "newzdeck v") ||
		strings.HasSuffix(low, " - newzdeck") ||
		strings.HasSuffix(low, " | newzdeck")
}

func newzDeckWindows() []uintptr {
	found := []uintptr{}
	cb := syscall.NewCallback(func(hwnd uintptr, lparam uintptr) uintptr {
		if isNewzDeckWindow(hwnd) {
			found = append(found, hwnd)
		}
		return 1
	})
	procEnumWindows.Call(cb, 0)
	return found
}

func closeNewzDeckWindows(timeout time.Duration) {
	for _, hwnd := range newzDeckWindows() {
		procPostMessageW.Call(hwnd, wmClose, 0, 0)
	}
	deadline := time.Now().Add(timeout)
	for time.Now().Before(deadline) {
		if len(newzDeckWindows()) == 0 {
			return
		}
		time.Sleep(100 * time.Millisecond)
	}
}

func closeTray(timeout time.Duration) {
	class := p16("NewzDeckTrayWindow")
	hwnd, _, _ := procFindWindowW.Call(uintptr(unsafe.Pointer(class)), 0)
	if hwnd == 0 {
		return
	}
	procPostMessageW.Call(hwnd, wmClose, 0, 0)
	deadline := time.Now().Add(timeout)
	for time.Now().Before(deadline) {
		h, _, _ := procFindWindowW.Call(uintptr(unsafe.Pointer(class)), 0)
		if h == 0 {
			return
		}
		time.Sleep(100 * time.Millisecond)
	}
}

func applyWindowIcon(hwnd, icon uintptr) {
	procSendMessageW.Call(hwnd, wmSetIcon, iconSmall, icon)
	procSendMessageW.Call(hwnd, wmSetIcon, iconBig, icon)
}

func findAndFix(icon uintptr) []uintptr {
	found := []uintptr{}
	cb := syscall.NewCallback(func(hwnd uintptr, lparam uintptr) uintptr {
		if isNewzDeckWindow(hwnd) {
			applyWindowIcon(hwnd, icon)
			found = append(found, hwnd)
		}
		return 1
	})
	procEnumWindows.Call(cb, 0)
	return found
}

func taskbarFix() {
	runtime.LockOSThread()
	defer runtime.UnlockOSThread()
	_, _, _ = procCoInitializeEx.Call(0, coinitApartmentThreaded)
	defer procCoUninitialize.Call()
	procSetCurrentProcessExplicitAppUserModelID.Call(uintptr(unsafe.Pointer(p16("NewzDeck.Desktop"))))
	exe, _ := os.Executable()
	iconPath := filepath.Join(filepath.Dir(exe), "NewzDeck.ico")
	icon, _, _ := procLoadImageW.Call(0, uintptr(unsafe.Pointer(p16(iconPath))), imageIcon, 0, 0, lrLoadFromFile|lrDefaultSize)
	if icon == 0 {
		return
	}
	defer procDestroyIcon.Call(icon)
	seen := false
	lastSeen := time.Now()
	deadline := time.Now().Add(12 * time.Hour)
	for time.Now().Before(deadline) {
		wins := findAndFix(icon)
		if len(wins) > 0 {
			seen = true
			lastSeen = time.Now()
		}
		if seen && time.Since(lastSeen) > 4*time.Second {
			alive := false
			for _, h := range wins {
				r, _, _ := procIsWindow.Call(h)
				if r != 0 {
					alive = true
					break
				}
			}
			if !alive {
				return
			}
		}
		time.Sleep(650 * time.Millisecond)
	}
}

func argValue(name string) string {
	for i := 1; i < len(os.Args)-1; i++ {
		if os.Args[i] == name {
			return os.Args[i+1]
		}
	}
	return ""
}

func argBool(name string, fallback bool) bool {
	v := strings.TrimSpace(strings.ToLower(argValue(name)))
	if v == "" {
		return fallback
	}
	return v == "1" || v == "true" || v == "yes" || v == "on"
}

func appendHandoffLog(root, line string) {
	if strings.TrimSpace(root) == "" {
		return
	}
	path := filepath.Join(root, "data", "update-handoff.log")
	_ = os.MkdirAll(filepath.Dir(path), 0755)
	f, err := os.OpenFile(path, os.O_CREATE|os.O_APPEND|os.O_WRONLY, 0644)
	if err != nil {
		return
	}
	defer f.Close()
	_, _ = fmt.Fprintf(f, "%s %s\n", time.Now().Format(time.RFC3339), line)
}

func runElevatedAndWait(file, params, dir string) int {
	sei := shellExecuteInfo{cbSize: uint32(unsafe.Sizeof(shellExecuteInfo{})), fMask: seeMaskNoCloseProcess, lpVerb: p16("runas"), lpFile: p16(file), lpParameters: p16(params), lpDirectory: p16(dir), nShow: swHide}
	ok, _, _ := procShellExecuteExW.Call(uintptr(unsafe.Pointer(&sei)))
	if ok == 0 || sei.hProcess == 0 {
		return -1
	}
	defer procCloseHandle.Call(sei.hProcess)
	wait, _, _ := procWaitForSingleObject.Call(sei.hProcess, infinite)
	if wait != waitObject0 {
		return -2
	}
	var code uint32
	r, _, _ := procGetExitCodeProcess.Call(sei.hProcess, uintptr(unsafe.Pointer(&code)))
	if r == 0 {
		return -3
	}
	return int(code)
}

func launchDetached(file string, args ...string) error {
	cmd := exec.Command(file, args...)
	cmd.Dir = filepath.Dir(file)
	cmd.SysProcAttr = &syscall.SysProcAttr{HideWindow: true, CreationFlags: 0x08000000}
	return cmd.Start()
}

func updateHandoff() {
	setup := argValue("--setup")
	appDir := argValue("--app-dir")
	userRoot := argValue("--user-root")
	version := argValue("--version")
	if setup == "" || appDir == "" {
		return
	}
	appendHandoffLog(userRoot, "handoff starting for v"+version)

	// Best-effort pre-Setup close. v3.6.12+ Setup is authoritative: after the
	// new files are overlaid it closes the browser-hosted window again from the
	// signed-in Setup session, starts the service, restores the tray, and relaunches
	// NewzDeck. The coordinator deliberately does no second post-Setup restore/UAC.
	closeNewzDeckWindows(6 * time.Second)
	closeTray(5 * time.Second)
	time.Sleep(250 * time.Millisecond)

	cmd := exec.Command(setup, "/update", "/CLOSEAPPLICATIONS", "/FORCECLOSEAPPLICATIONS")
	cmd.Dir = filepath.Dir(setup)
	if err := cmd.Start(); err != nil {
		appendHandoffLog(userRoot, "could not start Setup: "+err.Error())
		return
	}
	if err := cmd.Wait(); err != nil {
		appendHandoffLog(userRoot, "Setup returned error: "+err.Error())
		return
	}
	appendHandoffLog(userRoot, "Setup completed; installer owned runtime restore")
}

func main() {
	for _, a := range os.Args[1:] {
		switch a {
		case "--taskbar-fix":
			taskbarFix()
			return
		case "--close-app-windows":
			closeNewzDeckWindows(6 * time.Second)
			return
		case "--update-handoff":
			updateHandoff()
			return
		}
	}
	result := argValue("--result-file")
	started := argValue("--started-file")
	if result == "" {
		fmt.Fprintln(os.Stderr, "--result-file is required")
		os.Exit(2)
	}
	title := argValue("--title")
	if title == "" {
		title = "Choose a NewzDeck folder"
	}
	chooseFolder(result, started, argValue("--initial"), title)
}
