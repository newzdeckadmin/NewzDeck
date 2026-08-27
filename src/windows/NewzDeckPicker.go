// NewzDeckPicker provides NewzDeck's native Windows folder chooser and a
// best-effort taskbar icon fixer for Chromium app-mode windows.
// Copyright (C) 2026 NewzDeck contributors.
// SPDX-License-Identifier: GPL-3.0-only
package main

import (
	"fmt"
	"os"
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
	procCoTaskMemFree                           = ole32.NewProc("CoTaskMemFree")
	procCoInitializeEx                          = ole32.NewProc("CoInitializeEx")
	procCoUninitialize                          = ole32.NewProc("CoUninitialize")
	procSendMessageW                            = user32.NewProc("SendMessageW")
	procEnumWindows                             = user32.NewProc("EnumWindows")
	procGetWindowTextLengthW                    = user32.NewProc("GetWindowTextLengthW")
	procGetWindowTextW                          = user32.NewProc("GetWindowTextW")
	procIsWindowVisible                         = user32.NewProc("IsWindowVisible")
	procIsWindow                                = user32.NewProc("IsWindow")
	procLoadImageW                              = user32.NewProc("LoadImageW")
	procDestroyIcon                             = user32.NewProc("DestroyIcon")
	procSetCurrentProcessExplicitAppUserModelID = shell32.NewProc("SetCurrentProcessExplicitAppUserModelID")
	procMoveFileExW                             = kernel32.NewProc("MoveFileExW")
)

const (
	coinitApartmentThreaded = 0x2
	bifReturnOnlyFSDirs     = 0x0001
	bifEditBox              = 0x0010
	bifNewDialogStyle       = 0x0040
	wmUser                  = 0x0400
	bffmInitialized         = 1
	bffmSetSelectionW       = wmUser + 103
	wmSetIcon               = 0x0080
	iconSmall               = 0
	iconBig                 = 1
	imageIcon               = 1
	lrLoadFromFile          = 0x0010
	lrDefaultSize           = 0x0040
	movefileReplaceExisting = 0x1
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
	// os.Rename cannot replace an existing destination on Windows. The protocol
	// uses unique filenames, but MoveFileEx makes the write robust anyway.
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
	bi := browseInfo{
		pszDisplayName: &display[0], lpszTitle: p16(title),
		ulFlags: bifReturnOnlyFSDirs | bifEditBox | bifNewDialogStyle,
		lpfn:    syscall.NewCallback(browseCallback),
	}
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

func applyWindowIcon(hwnd, icon uintptr) {
	procSendMessageW.Call(hwnd, wmSetIcon, iconSmall, icon)
	procSendMessageW.Call(hwnd, wmSetIcon, iconBig, icon)
}

func findAndFix(icon uintptr) []uintptr {
	found := []uintptr{}
	cb := syscall.NewCallback(func(hwnd uintptr, lparam uintptr) uintptr {
		vis, _, _ := procIsWindowVisible.Call(hwnd)
		if vis == 0 {
			return 1
		}
		title := strings.TrimSpace(windowTitle(hwnd))
		if strings.EqualFold(title, "NewzDeck") || strings.HasPrefix(strings.ToLower(title), "newzdeck -") {
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
	// Keep a stable explicit identity for this native companion and apply the
	// NewzDeck icon to the actual Chromium app window. Windows taskbar grouping
	// also benefits from the launcher's dedicated --app URL/profile behavior.
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

func main() {
	for _, a := range os.Args[1:] {
		if a == "--taskbar-fix" {
			taskbarFix()
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
