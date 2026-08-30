// NewzDeck desktop launcher v3.5.33 — Source-Complete Runtime & Handoff
//
// v3.6.5 preserves the source-complete runtime/handoff path and adds Windows taskbar
// identity for the browser-hosted application window. The legacy opaque Bootstrap/Core
// executables are no longer required or shipped.
package main

import (
	"archive/zip"
	"bytes"
	"crypto/sha256"
	"encoding/binary"
	"encoding/json"
	"fmt"
	"io"
	"math/bits"
	"net/http"
	"os"
	"os/exec"
	"path/filepath"
	"runtime"
	"strconv"
	"strings"
	"syscall"
	"time"
	"unsafe"
)

type healthReply struct {
	OK                   bool     `json:"ok"`
	Version              string   `json:"version"`
	DesktopMode          bool     `json:"desktop_mode"`
	ServiceMode          bool     `json:"service_mode"`
	DesktopHeartbeatSeen bool     `json:"desktop_heartbeat_seen"`
	DesktopHeartbeatAge  *float64 `json:"desktop_heartbeat_age_seconds"`
}

var httpClient = &http.Client{Timeout: 750 * time.Millisecond}
var kernel32 = syscall.NewLazyDLL("kernel32.dll")
var procCreateMutexW = kernel32.NewProc("CreateMutexW")
var procCloseHandle = kernel32.NewProc("CloseHandle")
var user32 = syscall.NewLazyDLL("user32.dll")
var procMessageBoxW = user32.NewProc("MessageBoxW")
var iphlpapi = syscall.NewLazyDLL("iphlpapi.dll")
var procGetExtendedTcpTable = iphlpapi.NewProc("GetExtendedTcpTable")

// v3.6.5 taskbar identity support. Edge/Chrome still render NewzDeck's localhost
// UI, but the hosted application window is assigned an explicit NewzDeck Windows
// identity so Explorer uses NewzDeck branding instead of the browser's taskbar icon.
type taskbarGUID struct {
	Data1 uint32
	Data2 uint16
	Data3 uint16
	Data4 [8]byte
}

type taskbarPROPERTYKEY struct {
	Fmtid taskbarGUID
	Pid   uint32
}

type taskbarPROPVARIANT struct {
	Vt        uint16
	Reserved1 uint16
	Reserved2 uint16
	Reserved3 uint16
	Data      [2]uintptr
}

type taskbarIPropertyStore struct {
	Vtbl *taskbarIPropertyStoreVtbl
}

type taskbarIPropertyStoreVtbl struct {
	QueryInterface uintptr
	AddRef         uintptr
	Release        uintptr
	GetCount       uintptr
	GetAt          uintptr
	GetValue       uintptr
	SetValue       uintptr
	Commit         uintptr
}

var shell32 = syscall.NewLazyDLL("shell32.dll")
var ole32 = syscall.NewLazyDLL("ole32.dll")
var procEnumWindows = user32.NewProc("EnumWindows")
var procIsWindowVisible = user32.NewProc("IsWindowVisible")
var procGetWindowThreadProcessId = user32.NewProc("GetWindowThreadProcessId")
var procGetClassNameW = user32.NewProc("GetClassNameW")
var procGetWindowTextLengthW = user32.NewProc("GetWindowTextLengthW")
var procGetWindowTextW = user32.NewProc("GetWindowTextW")
var procSendMessageTimeoutW = user32.NewProc("SendMessageTimeoutW")
var procLoadImageW = user32.NewProc("LoadImageW")
var procOpenProcess = kernel32.NewProc("OpenProcess")
var procQueryFullProcessImageNameW = kernel32.NewProc("QueryFullProcessImageNameW")
var procSHGetPropertyStoreForWindow = shell32.NewProc("SHGetPropertyStoreForWindow")
var procSetCurrentProcessExplicitAUMID = shell32.NewProc("SetCurrentProcessExplicitAppUserModelID")
var procCoInitializeEx = ole32.NewProc("CoInitializeEx")
var procCoUninitialize = ole32.NewProc("CoUninitialize")

const (
	taskbarProcessQueryLimitedInformation = 0x1000
	taskbarWMSetIcon                      = 0x0080
	taskbarIconSmall                      = 0
	taskbarIconBig                        = 1
	taskbarImageIcon                      = 1
	taskbarLRLoadFromFile                 = 0x0010
	taskbarLRDefaultSize                  = 0x0040
	taskbarSMTOAbortIfHung                = 0x0002
	taskbarVTLPWSTR                       = 31
	taskbarCOINITApartmentThreaded        = 0x2
)

var taskbarIIDPropertyStore = taskbarGUID{0x886D8EEB, 0x8CF2, 0x4446, [8]byte{0x8D, 0x02, 0xCD, 0xBA, 0x1D, 0xBD, 0xCF, 0x99}}
var taskbarAppUserModelFmtid = taskbarGUID{0x9F4C2855, 0x9F79, 0x4B39, [8]byte{0xA8, 0xD0, 0xE1, 0xD4, 0x2D, 0xE1, 0xD5, 0xF3}}
var taskbarPkeyRelaunchCommand = taskbarPROPERTYKEY{taskbarAppUserModelFmtid, 2}
var taskbarPkeyRelaunchIcon = taskbarPROPERTYKEY{taskbarAppUserModelFmtid, 3}
var taskbarPkeyRelaunchName = taskbarPROPERTYKEY{taskbarAppUserModelFmtid, 4}
var taskbarPkeyAppID = taskbarPROPERTYKEY{taskbarAppUserModelFmtid, 5}

func taskbarHRESULTFailed(hr uintptr) bool { return int32(uint32(hr)) < 0 }

func taskbarSetCurrentAUMID(start time.Time, id string) {
	p, err := syscall.UTF16PtrFromString(id)
	if err != nil {
		return
	}
	hr, _, _ := procSetCurrentProcessExplicitAUMID.Call(uintptr(unsafe.Pointer(p)))
	if taskbarHRESULTFailed(hr) {
		logLine(start, "taskbar SetCurrentProcessExplicitAppUserModelID failed hr=0x%08x", uint32(hr))
	}
}

func taskbarPropVariantString(s string) (taskbarPROPVARIANT, *uint16, error) {
	p, err := syscall.UTF16PtrFromString(s)
	if err != nil {
		return taskbarPROPVARIANT{}, nil, err
	}
	return taskbarPROPVARIANT{Vt: taskbarVTLPWSTR, Data: [2]uintptr{uintptr(unsafe.Pointer(p)), 0}}, p, nil
}

func taskbarSetStoreString(store *taskbarIPropertyStore, key *taskbarPROPERTYKEY, value string) error {
	pv, keep, err := taskbarPropVariantString(value)
	if err != nil {
		return err
	}
	hr, _, _ := syscall.SyscallN(store.Vtbl.SetValue, uintptr(unsafe.Pointer(store)), uintptr(unsafe.Pointer(key)), uintptr(unsafe.Pointer(&pv)))
	runtime.KeepAlive(keep)
	if taskbarHRESULTFailed(hr) {
		return fmt.Errorf("SetValue hr=0x%08x", uint32(hr))
	}
	return nil
}

func taskbarReleaseStore(store *taskbarIPropertyStore) {
	if store == nil || store.Vtbl == nil {
		return
	}
	_, _, _ = syscall.SyscallN(store.Vtbl.Release, uintptr(unsafe.Pointer(store)))
}

func taskbarCommitStore(store *taskbarIPropertyStore) error {
	hr, _, _ := syscall.SyscallN(store.Vtbl.Commit, uintptr(unsafe.Pointer(store)))
	if taskbarHRESULTFailed(hr) {
		return fmt.Errorf("Commit hr=0x%08x", uint32(hr))
	}
	return nil
}

func taskbarProcessImage(pid uint32) string {
	h, _, _ := procOpenProcess.Call(taskbarProcessQueryLimitedInformation, 0, uintptr(pid))
	if h == 0 {
		return ""
	}
	defer procCloseHandle.Call(h)
	buf := make([]uint16, 1024)
	size := uint32(len(buf))
	r, _, _ := procQueryFullProcessImageNameW.Call(h, 0, uintptr(unsafe.Pointer(&buf[0])), uintptr(unsafe.Pointer(&size)))
	if r == 0 || size == 0 {
		return ""
	}
	return syscall.UTF16ToString(buf[:size])
}

func taskbarWindowClass(hwnd uintptr) string {
	buf := make([]uint16, 256)
	n, _, _ := procGetClassNameW.Call(hwnd, uintptr(unsafe.Pointer(&buf[0])), uintptr(len(buf)))
	if n == 0 {
		return ""
	}
	return syscall.UTF16ToString(buf[:n])
}

func taskbarWindowTitle(hwnd uintptr) string {
	n, _, _ := procGetWindowTextLengthW.Call(hwnd)
	if n == 0 {
		return ""
	}
	buf := make([]uint16, n+1)
	got, _, _ := procGetWindowTextW.Call(hwnd, uintptr(unsafe.Pointer(&buf[0])), n+1)
	if got == 0 {
		return ""
	}
	return syscall.UTF16ToString(buf[:got])
}

func taskbarBrowserWindows() map[uintptr]bool {
	found := map[uintptr]bool{}
	cb := syscall.NewCallback(func(hwnd uintptr, lparam uintptr) uintptr {
		visible, _, _ := procIsWindowVisible.Call(hwnd)
		if visible == 0 {
			return 1
		}
		class := taskbarWindowClass(hwnd)
		if !strings.HasPrefix(class, "Chrome_WidgetWin_") {
			return 1
		}
		var pid uint32
		procGetWindowThreadProcessId.Call(hwnd, uintptr(unsafe.Pointer(&pid)))
		if pid == 0 {
			return 1
		}
		image := strings.ToLower(filepath.Base(taskbarProcessImage(pid)))
		if image == "msedge.exe" || image == "chrome.exe" {
			found[hwnd] = true
		}
		return 1
	})
	procEnumWindows.Call(cb, 0)
	return found
}

func taskbarApplyWindowIdentity(hwnd uintptr) error {
	var store *taskbarIPropertyStore
	hr, _, _ := procSHGetPropertyStoreForWindow.Call(hwnd, uintptr(unsafe.Pointer(&taskbarIIDPropertyStore)), uintptr(unsafe.Pointer(&store)))
	if taskbarHRESULTFailed(hr) || store == nil {
		return fmt.Errorf("SHGetPropertyStoreForWindow hr=0x%08x", uint32(hr))
	}
	defer taskbarReleaseStore(store)

	exe := filepath.Join(appDir(), "NewzDeck.exe")
	icon := filepath.Join(appDir(), "NewzDeck.ico") + ",0"
	relaunch := `"` + exe + `"`
	if err := taskbarSetStoreString(store, &taskbarPkeyAppID, "NewzDeck.Desktop"); err != nil {
		return fmt.Errorf("AppID: %w", err)
	}
	if err := taskbarSetStoreString(store, &taskbarPkeyRelaunchCommand, relaunch); err != nil {
		return fmt.Errorf("RelaunchCommand: %w", err)
	}
	if err := taskbarSetStoreString(store, &taskbarPkeyRelaunchName, "NewzDeck"); err != nil {
		return fmt.Errorf("RelaunchName: %w", err)
	}
	if err := taskbarSetStoreString(store, &taskbarPkeyRelaunchIcon, icon); err != nil {
		return fmt.Errorf("RelaunchIcon: %w", err)
	}
	if err := taskbarCommitStore(store); err != nil {
		return err
	}

	iconPath, _ := syscall.UTF16PtrFromString(filepath.Join(appDir(), "NewzDeck.ico"))
	hIcon, _, _ := procLoadImageW.Call(0, uintptr(unsafe.Pointer(iconPath)), taskbarImageIcon, 0, 0, taskbarLRLoadFromFile|taskbarLRDefaultSize)
	if hIcon != 0 {
		var ignored uintptr
		procSendMessageTimeoutW.Call(hwnd, taskbarWMSetIcon, taskbarIconBig, hIcon, taskbarSMTOAbortIfHung, 250, uintptr(unsafe.Pointer(&ignored)))
		procSendMessageTimeoutW.Call(hwnd, taskbarWMSetIcon, taskbarIconSmall, hIcon, taskbarSMTOAbortIfHung, 250, uintptr(unsafe.Pointer(&ignored)))
	}
	return nil
}

func taskbarPatchNewWindow(start time.Time, before map[uintptr]bool) {
	runtime.LockOSThread()
	defer runtime.UnlockOSThread()
	hr, _, _ := procCoInitializeEx.Call(0, taskbarCOINITApartmentThreaded)
	if !taskbarHRESULTFailed(hr) {
		defer procCoUninitialize.Call()
	}

	deadline := time.Now().Add(18 * time.Second)
	patched := map[uintptr]bool{}
	firstPatch := time.Time{}
	for time.Now().Before(deadline) {
		for hwnd := range taskbarBrowserWindows() {
			if before[hwnd] {
				continue
			}
			title := taskbarWindowTitle(hwnd)
			if !strings.Contains(strings.ToLower(title), "newzdeck") {
				continue
			}
			if err := taskbarApplyWindowIdentity(hwnd); err != nil {
				logLine(start, "taskbar identity failed for window 0x%x title=%q: %v", hwnd, title, err)
				continue
			}
			if !patched[hwnd] {
				logLine(start, "assigned NewzDeck.Desktop taskbar identity to browser window 0x%x title=%q", hwnd, title)
			}
			patched[hwnd] = true
			if firstPatch.IsZero() {
				firstPatch = time.Now()
			}
		}
		if !firstPatch.IsZero() && time.Since(firstPatch) > 5*time.Second {
			break
		}
		time.Sleep(200 * time.Millisecond)
	}
	if len(patched) == 0 {
		logLine(start, "taskbar identity: no new Edge/Chrome NewzDeck application window found before timeout")
	} else {
		logLine(start, "taskbar identity applied to %d NewzDeck browser window(s)", len(patched))
	}
}

const errorAlreadyExists = 183
const (
	pythonRuntimeURL    = "https://www.python.org/ftp/python/3.12.10/python-3.12.10-embed-amd64.zip"
	pythonRuntimeSHA256 = "4acbed6dd1c744b0376e3b1cf57ce906f9dc9e95e68824584c8099a63025a3c3"
	mbOK                = 0x00000000
	mbYesNo             = 0x00000004
	mbIconError         = 0x00000010
	mbIconQuestion      = 0x00000020
	idYes               = 6
)

func appDir() string {
	exe, err := os.Executable()
	if err != nil {
		return "."
	}
	return filepath.Dir(exe)
}

func userRoot() string {
	if v := strings.TrimSpace(os.Getenv("NEWZDECK_USER_ROOT")); v != "" {
		return v
	}
	base := strings.TrimSpace(os.Getenv("LOCALAPPDATA"))
	if base == "" {
		base = os.TempDir()
	}
	return filepath.Join(base, "NewzDeck")
}

func localVersion() string {
	b, err := os.ReadFile(filepath.Join(appDir(), "version.txt"))
	if err != nil {
		return ""
	}
	return strings.TrimSpace(string(b))
}

func logLine(start time.Time, format string, args ...any) {
	root := filepath.Join(userRoot(), "data")
	_ = os.MkdirAll(root, 0755)
	f, err := os.OpenFile(filepath.Join(root, "launcher-handoff.log"), os.O_CREATE|os.O_APPEND|os.O_WRONLY, 0644)
	if err != nil {
		return
	}
	defer f.Close()
	msg := fmt.Sprintf(format, args...)
	elapsed := time.Since(start).Round(time.Millisecond)
	_, _ = fmt.Fprintf(f, "%s [startup-v3.6.14 +%s] %s\r\n", time.Now().Format("2006-01-02 15:04:05.000"), elapsed, msg)
}

func acquireStartupMutex() (uintptr, bool) {
	name, _ := syscall.UTF16PtrFromString(`Local\NewzDeck-Desktop-Startup-Handoff`)
	handle, _, callErr := procCreateMutexW.Call(0, 0, uintptr(unsafe.Pointer(name)))
	if handle == 0 {
		return 0, true
	}
	if errno, ok := callErr.(syscall.Errno); ok && errno == errorAlreadyExists {
		procCloseHandle.Call(handle)
		return 0, false
	}
	return handle, true
}

func closeHandle(h uintptr) {
	if h != 0 {
		procCloseHandle.Call(h)
	}
}

func listenerPID(port int) (uint32, bool) {
	// GetExtendedTcpTable lets us terminate only the exact desktop backend that
	// answered NewzDeck health on a stale localhost port. This avoids a slow
	// Bootstrap/Core round trip during an installed-version upgrade while leaving
	// Windows service-mode listeners entirely to the compatibility path.
	const (
		afInet              = 2
		tcpTableOwnerPIDAll = 5
		tcpStateListen      = 2
		rowSize             = 24 // six DWORDs in MIB_TCPROW_OWNER_PID
	)
	var size uint32
	r1, _, _ := procGetExtendedTcpTable.Call(0, uintptr(unsafe.Pointer(&size)), 0, afInet, tcpTableOwnerPIDAll, 0)
	if size < 4 || (r1 != 0 && r1 != 122) { // ERROR_INSUFFICIENT_BUFFER = 122
		return 0, false
	}
	buf := make([]byte, size)
	r1, _, _ = procGetExtendedTcpTable.Call(uintptr(unsafe.Pointer(&buf[0])), uintptr(unsafe.Pointer(&size)), 0, afInet, tcpTableOwnerPIDAll, 0)
	if r1 != 0 || len(buf) < 4 {
		return 0, false
	}
	count := binary.LittleEndian.Uint32(buf[:4])
	for i := uint32(0); i < count; i++ {
		off := 4 + int(i)*rowSize
		if off+rowSize > len(buf) {
			break
		}
		state := binary.LittleEndian.Uint32(buf[off : off+4])
		localPortRaw := binary.LittleEndian.Uint32(buf[off+8 : off+12])
		owningPID := binary.LittleEndian.Uint32(buf[off+20 : off+24])
		localPort := int(bits.ReverseBytes16(uint16(localPortRaw & 0xffff)))
		if state == tcpStateListen && localPort == port && owningPID > 0 {
			return owningPID, true
		}
	}
	return 0, false
}

func terminateStaleDesktopBackend(start time.Time, port int, version string) bool {
	pid, ok := listenerPID(port)
	if !ok {
		logLine(start, "stale desktop backend v%s is on port %d but its listener PID could not be resolved", version, port)
		return false
	}
	proc, err := os.FindProcess(int(pid))
	if err != nil {
		logLine(start, "stale desktop backend pid=%d could not be opened: %v", pid, err)
		return false
	}
	if err := proc.Kill(); err != nil {
		logLine(start, "stale desktop backend pid=%d could not be terminated: %v", pid, err)
		return false
	}
	deadline := time.Now().Add(3 * time.Second)
	for time.Now().Before(deadline) {
		if _, ok := health(port); !ok {
			logLine(start, "terminated stale desktop backend v%s pid=%d on port %d; continuing with fast current-version startup", version, pid, port)
			return true
		}
		time.Sleep(75 * time.Millisecond)
	}
	logLine(start, "stale desktop backend pid=%d was terminated but port %d remained healthy; using compatibility fallback", pid, port)
	return false
}

func readPort() int {
	b, err := os.ReadFile(filepath.Join(userRoot(), "newzdeck.port"))
	if err != nil {
		return 0
	}
	p, _ := strconv.Atoi(strings.TrimSpace(string(b)))
	if p < 1 || p > 65535 {
		return 0
	}
	return p
}

func heartbeatActive(h healthReply) bool {
	// The browser posts a heartbeat every 3 seconds. Treat a recent beat as an
	// active desktop lease, but do not suppress relaunches for the full backend
	// stale-heartbeat lifetime after the Chromium window has been closed.
	if !h.DesktopHeartbeatSeen || h.DesktopHeartbeatAge == nil {
		return false
	}
	return *h.DesktopHeartbeatAge <= 6.5
}

func health(port int) (healthReply, bool) {
	var h healthReply
	if port < 1 {
		return h, false
	}
	r, err := httpClient.Get(fmt.Sprintf("http://127.0.0.1:%d/api/health?startup=1", port))
	if err != nil {
		return h, false
	}
	defer r.Body.Close()
	if r.StatusCode != http.StatusOK {
		return h, false
	}
	if err := json.NewDecoder(r.Body).Decode(&h); err != nil {
		return h, false
	}
	return h, h.OK
}

func candidatePorts() []int {
	seen := map[int]bool{}
	ports := make([]int, 0, 26)
	if p := readPort(); p > 0 {
		ports = append(ports, p)
		seen[p] = true
	}
	for p := 8765; p < 8790; p++ {
		if !seen[p] {
			ports = append(ports, p)
		}
	}
	return ports
}

func primaryPorts() []int {
	seen := map[int]bool{}
	ports := make([]int, 0, 2)
	if p := readPort(); p > 0 {
		ports = append(ports, p)
		seen[p] = true
	}
	if !seen[8765] {
		ports = append(ports, 8765)
	}
	return ports
}

func currentHealth(version string) (int, healthReply, bool) {
	// Once a backend starts it writes its actual port to newzdeck.port. Poll only
	// that port plus the default instead of scanning 25 localhost ports on every
	// 100 ms startup tick.
	for _, p := range primaryPorts() {
		h, ok := health(p)
		if ok && strings.TrimSpace(h.Version) == version {
			return p, h, true
		}
	}
	return 0, healthReply{}, false
}

func anyExistingHealth() (int, healthReply, bool) {
	// A full small-range scan is used only once before starting a new backend so
	// an unusual stale listener whose port file was lost can still be handed to
	// the compatibility cleanup path.
	for _, p := range candidatePorts() {
		h, ok := health(p)
		if ok && strings.TrimSpace(h.Version) != "" {
			return p, h, true
		}
	}
	return 0, healthReply{}, false
}

func launchDetached(path string, env []string, args ...string) error {
	cmd := exec.Command(path, args...)
	cmd.Dir = appDir()
	cmd.SysProcAttr = &syscall.SysProcAttr{HideWindow: true, CreationFlags: 0x00000008}
	cmd.Stdout, cmd.Stderr, cmd.Stdin = nil, nil, nil
	if env != nil {
		cmd.Env = env
	}
	return cmd.Start()
}

func runtimePython() string {
	candidates := []string{
		filepath.Join(appDir(), "runtime", "pythonw.exe"),
		filepath.Join(appDir(), "runtime", "python.exe"),
	}
	for _, p := range candidates {
		if st, err := os.Stat(p); err == nil && !st.IsDir() {
			return p
		}
	}
	return ""
}

func withEnv(base []string, values map[string]string) []string {
	blocked := map[string]bool{}
	for k := range values {
		blocked[strings.ToUpper(k)] = true
	}
	out := make([]string, 0, len(base)+len(values))
	for _, item := range base {
		key := item
		if i := strings.IndexByte(item, '='); i >= 0 {
			key = item[:i]
		}
		if !blocked[strings.ToUpper(key)] {
			out = append(out, item)
		}
	}
	for k, v := range values {
		out = append(out, k+"="+v)
	}
	return out
}

func startFastDesktopBackend(python, version string) error {
	server := filepath.Join(appDir(), "server.py")
	if _, err := os.Stat(server); err != nil {
		return fmt.Errorf("server.py missing: %w", err)
	}
	defaultDownload := filepath.Join(strings.TrimSpace(os.Getenv("USERPROFILE")), "Downloads", "NewzDeck")
	env := withEnv(os.Environ(), map[string]string{
		"NEWZDECK_DESKTOP":              "1",
		"NEWZDECK_SERVICE":              "0",
		"NEWZDECK_NO_OPEN":              "1",
		"NEWZDECK_USER_ROOT":            userRoot(),
		"NEWZDECK_PORT_FILE":            filepath.Join(userRoot(), "newzdeck.port"),
		"NEWZDECK_EXPECTED_VERSION":     version,
		"NEWZDECK_LAUNCHER_PID":         strconv.Itoa(os.Getpid()),
		"NEWZDECK_DEFAULT_DOWNLOAD_DIR": defaultDownload,
	})
	return launchDetached(python, env, server)
}

func findBrowser() string {
	pf := strings.TrimSpace(os.Getenv("ProgramFiles"))
	pfx86 := strings.TrimSpace(os.Getenv("ProgramFiles(x86)"))
	local := strings.TrimSpace(os.Getenv("LOCALAPPDATA"))
	candidates := []string{
		filepath.Join(pf, "Microsoft", "Edge", "Application", "msedge.exe"),
		filepath.Join(pfx86, "Microsoft", "Edge", "Application", "msedge.exe"),
		filepath.Join(pf, "Google", "Chrome", "Application", "chrome.exe"),
		filepath.Join(pfx86, "Google", "Chrome", "Application", "chrome.exe"),
		filepath.Join(local, "Google", "Chrome", "Application", "chrome.exe"),
	}
	for _, p := range candidates {
		if p == "" {
			continue
		}
		if st, err := os.Stat(p); err == nil && !st.IsDir() {
			return p
		}
	}
	for _, name := range []string{"msedge.exe", "chrome.exe"} {
		if p, err := exec.LookPath(name); err == nil {
			return p
		}
	}
	return ""
}

func openDesktopApp(start time.Time, port int) error {
	url := fmt.Sprintf("http://127.0.0.1:%d", port)
	if browser := findBrowser(); browser != "" {
		before := taskbarBrowserWindows()
		if err := launchDetached(browser, nil, "--app="+url, "--start-maximized"); err != nil {
			return err
		}
		taskbarPatchNewWindow(start, before)
		return nil
	}
	rundll := filepath.Join(strings.TrimSpace(os.Getenv("SystemRoot")), "System32", "rundll32.exe")
	if _, err := os.Stat(rundll); err != nil {
		rundll = "rundll32.exe"
	}
	return launchDetached(rundll, nil, "url.dll,FileProtocolHandler", url)
}

func waitCurrentBackend(version string, deadline time.Time) (int, healthReply, bool) {
	for time.Now().Before(deadline) {
		if p, h, ok := currentHealth(version); ok {
			return p, h, true
		}
		time.Sleep(100 * time.Millisecond)
	}
	return 0, healthReply{}, false
}

func waitHeartbeat(version string, deadline time.Time) (int, bool) {
	for time.Now().Before(deadline) {
		if p, h, ok := currentHealth(version); ok && h.DesktopMode && heartbeatActive(h) {
			return p, true
		}
		time.Sleep(125 * time.Millisecond)
	}
	return 0, false
}

func messageBox(text, title string, flags uintptr) int {
	ptext, _ := syscall.UTF16PtrFromString(text)
	ptitle, _ := syscall.UTF16PtrFromString(title)
	r, _, _ := procMessageBoxW.Call(0, uintptr(unsafe.Pointer(ptext)), uintptr(unsafe.Pointer(ptitle)), flags)
	return int(r)
}

func runtimeReadyAt(dir string) bool {
	for _, name := range []string{"python.exe", "pythonw.exe"} {
		if st, err := os.Stat(filepath.Join(dir, name)); err == nil && !st.IsDir() {
			return true
		}
	}
	return false
}

func unzipRuntime(data []byte, dst string) error {
	zr, err := zip.NewReader(bytes.NewReader(data), int64(len(data)))
	if err != nil {
		return err
	}
	cleanDst, err := filepath.Abs(dst)
	if err != nil {
		return err
	}
	for _, f := range zr.File {
		name := filepath.Clean(filepath.FromSlash(f.Name))
		if filepath.IsAbs(name) || name == ".." || strings.HasPrefix(name, ".."+string(os.PathSeparator)) {
			return fmt.Errorf("unsafe path in CPython archive: %q", f.Name)
		}
		target := filepath.Join(cleanDst, name)
		absTarget, err := filepath.Abs(target)
		if err != nil {
			return err
		}
		if absTarget != cleanDst && !strings.HasPrefix(strings.ToLower(absTarget), strings.ToLower(cleanDst+string(os.PathSeparator))) {
			return fmt.Errorf("unsafe extraction target: %q", f.Name)
		}
		if f.FileInfo().IsDir() {
			if err := os.MkdirAll(target, 0755); err != nil {
				return err
			}
			continue
		}
		if err := os.MkdirAll(filepath.Dir(target), 0755); err != nil {
			return err
		}
		r, err := f.Open()
		if err != nil {
			return err
		}
		w, err := os.OpenFile(target, os.O_CREATE|os.O_TRUNC|os.O_WRONLY, 0644)
		if err != nil {
			r.Close()
			return err
		}
		_, copyErr := io.Copy(w, io.LimitReader(r, 64*1024*1024))
		closeErr := w.Close()
		r.Close()
		if copyErr != nil {
			return copyErr
		}
		if closeErr != nil {
			return closeErr
		}
	}
	return nil
}

func provisionRuntime(start time.Time) error {
	if runtimePython() != "" {
		return nil
	}
	if messageBox("NewzDeck needs its private Python 3.12 runtime.\n\nDownload and install the official CPython 3.12.10 embeddable runtime now?", "NewzDeck", mbYesNo|mbIconQuestion) != idYes {
		return fmt.Errorf("runtime installation canceled")
	}
	logLine(start, "downloading official CPython 3.12.10 embeddable runtime")
	client := &http.Client{Timeout: 3 * time.Minute}
	req, _ := http.NewRequest("GET", pythonRuntimeURL, nil)
	req.Header.Set("User-Agent", "NewzDeck/3.6.7")
	resp, err := client.Do(req)
	if err != nil {
		return fmt.Errorf("CPython download failed: %w", err)
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusOK {
		return fmt.Errorf("python.org returned HTTP %d", resp.StatusCode)
	}
	data, err := io.ReadAll(io.LimitReader(resp.Body, 32*1024*1024+1))
	if err != nil {
		return err
	}
	if len(data) == 0 || len(data) > 32*1024*1024 {
		return fmt.Errorf("CPython runtime download has an invalid size")
	}
	actual := fmt.Sprintf("%x", sha256.Sum256(data))
	if !strings.EqualFold(actual, pythonRuntimeSHA256) {
		return fmt.Errorf("CPython SHA-256 verification failed (got %s)", actual)
	}
	target := filepath.Join(appDir(), "runtime")
	tmp := filepath.Join(appDir(), fmt.Sprintf("runtime.new-%d", os.Getpid()))
	_ = os.RemoveAll(tmp)
	if err := os.MkdirAll(tmp, 0755); err != nil {
		return err
	}
	if err := unzipRuntime(data, tmp); err != nil {
		_ = os.RemoveAll(tmp)
		return fmt.Errorf("runtime extraction failed: %w", err)
	}
	if !runtimeReadyAt(tmp) {
		_ = os.RemoveAll(tmp)
		return fmt.Errorf("runtime extraction did not produce python.exe")
	}
	// The embeddable distribution's default ._pth already contains python312.zip
	// and '.', which is sufficient because NewzDeck loads its sibling modules by
	// explicit file path. Keep the upstream isolation policy intact.
	if runtimeReadyAt(target) {
		_ = os.RemoveAll(tmp)
		return nil
	}
	_ = os.RemoveAll(target)
	if err := os.Rename(tmp, target); err != nil {
		_ = os.RemoveAll(tmp)
		return fmt.Errorf("could not activate private runtime: %w", err)
	}
	logLine(start, "verified CPython runtime installed successfully")
	return nil
}

func fatal(start time.Time, format string, args ...any) {
	msg := fmt.Sprintf(format, args...)
	logLine(start, "%s", msg)
	messageBox(msg, "NewzDeck", mbOK|mbIconError)
}

func main() {
	started := time.Now()
	taskbarSetCurrentAUMID(started, "NewzDeck.Desktop")
	version := localVersion()
	if version == "" {
		fatal(started, "NewzDeck could not read version.txt.")
		return
	}
	mutex, acquired := acquireStartupMutex()
	if !acquired {
		logLine(started, "startup already in progress; suppressing duplicate shortcut click")
		return
	}
	defer closeHandle(mutex)

	python := runtimePython()
	if p, h, ok := anyExistingHealth(); ok {
		if strings.TrimSpace(h.Version) != version {
			if h.DesktopMode && !h.ServiceMode && terminateStaleDesktopBackend(started, p, h.Version) {
				// Continue below with the current source-built runtime/backend.
			} else if h.ServiceMode {
				fatal(started, "A different NewzDeck background-service version (v%s) is still running. Stop or repair that service, then launch NewzDeck again.", h.Version)
				return
			} else {
				fatal(started, "An older NewzDeck backend (v%s) is still using local port %d and could not be handed over safely. Close it and try again.", h.Version, p)
				return
			}
		} else {
			if heartbeatActive(h) {
				logLine(started, "active NewzDeck UI heartbeat already exists on port %d; suppressing duplicate launch", p)
				return
			}
			logLine(started, "current-version backend already healthy on port %d (service=%v); attaching UI directly", p, h.ServiceMode)
			if err := openDesktopApp(started, p); err != nil {
				fatal(started, "NewzDeck could not open its application window: %v", err)
				return
			}
			if h.DesktopMode {
				if hp, ok := waitHeartbeat(version, time.Now().Add(15*time.Second)); ok {
					logLine(started, "desktop heartbeat established after direct attach on port %d", hp)
				}
			}
			return
		}
	}

	if python == "" {
		if err := provisionRuntime(started); err != nil {
			fatal(started, "NewzDeck could not install its private runtime.\n\n%v", err)
			return
		}
		python = runtimePython()
		if python == "" {
			fatal(started, "NewzDeck's private runtime was installed but python.exe could not be found.")
			return
		}
	}

	logLine(started, "private runtime ready; starting desktop backend directly")
	if err := startFastDesktopBackend(python, version); err != nil {
		fatal(started, "NewzDeck could not start its local backend.\n\n%v", err)
		return
	}
	p, h, ok := waitCurrentBackend(version, time.Now().Add(25*time.Second))
	if !ok {
		fatal(started, "NewzDeck's local backend did not become ready. Check %%LOCALAPPDATA%%\\NewzDeck\\logs\\server.log and launcher-handoff.log for startup details.")
		return
	}
	if h.ServiceMode {
		logLine(started, "service backend won startup race on port %d; attaching UI", p)
	}
	logLine(started, "backend healthy on port %d; opening UI immediately", p)
	if err := openDesktopApp(started, p); err != nil {
		fatal(started, "NewzDeck could not open its application window.\n\n%v", err)
		return
	}
	if h.DesktopMode {
		if hp, ok := waitHeartbeat(version, time.Now().Add(15*time.Second)); ok {
			logLine(started, "desktop heartbeat established on port %d; startup complete", hp)
		} else {
			logLine(started, "UI process launched but no desktop heartbeat arrived within 15s")
		}
	}
}
