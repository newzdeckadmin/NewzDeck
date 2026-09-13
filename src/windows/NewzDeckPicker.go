// NewzDeckPicker provides NewzDeck's native Windows folder chooser.
//
// v3.6.92 intentionally keeps this helper single-purpose. Update handoff,
// browser-window control, process launching, and taskbar compatibility behavior
// belong to NewzDeck Setup / NewzDeck.exe, not the folder picker.
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
	"unsafe"
)

var (
	shell32                  = syscall.NewLazyDLL("shell32.dll")
	ole32                    = syscall.NewLazyDLL("ole32.dll")
	user32                   = syscall.NewLazyDLL("user32.dll")
	kernel32                 = syscall.NewLazyDLL("kernel32.dll")
	procSHBrowseForFolderW   = shell32.NewProc("SHBrowseForFolderW")
	procSHGetPathFromIDListW = shell32.NewProc("SHGetPathFromIDListW")
	procCoTaskMemFree        = ole32.NewProc("CoTaskMemFree")
	procCoInitializeEx       = ole32.NewProc("CoInitializeEx")
	procCoUninitialize       = ole32.NewProc("CoUninitialize")
	procSendMessageW         = user32.NewProc("SendMessageW")
	procMoveFileExW          = kernel32.NewProc("MoveFileExW")
)

const (
	coinitApartmentThreaded = 0x2
	bifReturnOnlyFSDirs     = 0x0001
	bifEditBox              = 0x0010
	bifNewDialogStyle       = 0x0040
	wmUser                  = 0x0400
	bffmInitialized         = 1
	bffmSetSelectionW       = wmUser + 103
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

func argValue(name string) string {
	for i := 1; i < len(os.Args)-1; i++ {
		if os.Args[i] == name {
			return os.Args[i+1]
		}
	}
	return ""
}

func main() {
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
