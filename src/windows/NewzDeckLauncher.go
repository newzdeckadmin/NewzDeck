// NewzDeck desktop launcher v3.5.32 — Desktop Startup Performance & Fast Handoff
//
// v3.5.31 proved the version-aware compatibility bootstrap and recovery model,
// but cold service-off desktop launches could spend 10-30 seconds traversing
// Bootstrap -> Core -> runtime/backend -> browser handoff. v3.5.32 keeps the
// proven compatibility executables unchanged and adds a fast path for established
// installations whose private CPython runtime already exists.
package main

import (
	"encoding/binary"
	"encoding/json"
	"fmt"
	"math/bits"
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
var iphlpapi = syscall.NewLazyDLL("iphlpapi.dll")
var procGetExtendedTcpTable = iphlpapi.NewProc("GetExtendedTcpTable")

const errorAlreadyExists = 183

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
	_, _ = fmt.Fprintf(f, "%s [startup-v3.5.32 +%s] %s\r\n", time.Now().Format("2006-01-02 15:04:05.000"), elapsed, msg)
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

func openDesktopApp(port int) error {
	url := fmt.Sprintf("http://127.0.0.1:%d", port)
	if browser := findBrowser(); browser != "" {
		return launchDetached(browser, nil, "--app="+url, "--start-maximized")
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

func compatibilityFallback(start time.Time, version string, args []string) {
	bootstrap := filepath.Join(appDir(), "NewzDeckBootstrap.exe")
	core := filepath.Join(appDir(), "NewzDeckCore.exe")
	if _, err := os.Stat(bootstrap); err != nil {
		logLine(start, "compatibility bootstrap missing: %v", err)
		return
	}
	if err := launchDetached(bootstrap, nil, args...); err != nil {
		logLine(start, "compatibility bootstrap failed: %v", err)
		return
	}
	logLine(start, "compatibility fallback launched")

	deadline := time.Now().Add(60 * time.Second)
	healthyAt := time.Time{}
	for time.Now().Before(deadline) {
		p, h, ok := currentHealth(version)
		if ok {
			if h.ServiceMode {
				logLine(start, "service-mode backend healthy on port %d; compatibility path owns UI handoff", p)
				return
			}
			if heartbeatActive(h) {
				logLine(start, "compatibility path established desktop heartbeat on port %d", p)
				return
			}
			if h.DesktopMode {
				if healthyAt.IsZero() {
					healthyAt = time.Now()
					logLine(start, "compatibility backend healthy on port %d; waiting for its normal UI handoff", p)
				}
				// First-run/runtime-provisioning fallback retains a generous UI
				// handoff window. If Core does not attach, open the already-ready
				// backend directly rather than starting another backend process.
				if time.Since(healthyAt) >= 5*time.Second {
					if err := openDesktopApp(p); err == nil {
						logLine(start, "opened healthy compatibility backend directly after UI handoff timeout")
						if hp, ok := waitHeartbeat(version, time.Now().Add(12*time.Second)); ok {
							logLine(start, "desktop heartbeat established after direct compatibility UI attach on port %d", hp)
						}
						return
					}
					if _, err := os.Stat(core); err == nil {
						_ = launchDetached(core, nil)
						logLine(start, "direct browser attach failed; invoked Core as final UI fallback")
					}
					return
				}
			}
		}
		time.Sleep(150 * time.Millisecond)
	}
	logLine(start, "compatibility fallback reached 60s without a current-version backend")
}

func main() {
	started := time.Now()
	version := localVersion()
	if version == "" {
		logLine(started, "version.txt could not be read")
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
			if h.DesktopMode && !h.ServiceMode && python != "" && terminateStaleDesktopBackend(started, p, h.Version) {
				// Fall through to the established-runtime fast path below.
			} else {
				logLine(started, "stale backend v%s detected on port %d (service=%v); delegating version handoff", h.Version, p, h.ServiceMode)
				compatibilityFallback(started, version, os.Args[1:])
				return
			}
		} else {
			if h.DesktopMode && heartbeatActive(h) {
				logLine(started, "desktop heartbeat already active on port %d; suppressing duplicate launch", p)
				return
			}
			if h.ServiceMode {
				logLine(started, "current-version service backend detected on port %d; delegating handoff to compatibility bootstrap", p)
				compatibilityFallback(started, version, os.Args[1:])
				return
			}
			if h.DesktopMode {
				logLine(started, "healthy desktop backend already exists on port %d without an active heartbeat; attaching UI directly", p)
				if err := openDesktopApp(p); err != nil {
					logLine(started, "direct UI attach failed: %v; using compatibility fallback", err)
					compatibilityFallback(started, version, os.Args[1:])
					return
				}
				if hp, ok := waitHeartbeat(version, time.Now().Add(15*time.Second)); ok {
					logLine(started, "desktop heartbeat established after direct attach on port %d", hp)
				} else {
					logLine(started, "browser was launched but no desktop heartbeat arrived within 15s")
				}
				return
			}
		}
	}

	if python == "" {
		logLine(started, "private runtime not present; using compatibility bootstrap for first-run provisioning")
		compatibilityFallback(started, version, os.Args[1:])
		return
	}

	logLine(started, "established private runtime found; starting fast desktop backend directly")
	if err := startFastDesktopBackend(python, version); err != nil {
		logLine(started, "fast backend launch failed: %v; using compatibility fallback", err)
		compatibilityFallback(started, version, os.Args[1:])
		return
	}

	p, h, ok := waitCurrentBackend(version, time.Now().Add(25*time.Second))
	if !ok {
		logLine(started, "fast backend did not become healthy within 25s; using compatibility fallback")
		compatibilityFallback(started, version, os.Args[1:])
		return
	}
	if h.ServiceMode {
		logLine(started, "service backend won startup race on port %d; delegating UI handoff", p)
		compatibilityFallback(started, version, os.Args[1:])
		return
	}
	logLine(started, "fast desktop backend healthy on port %d; opening UI immediately", p)
	if err := openDesktopApp(p); err != nil {
		logLine(started, "browser launch failed: %v; invoking Core UI fallback", err)
		core := filepath.Join(appDir(), "NewzDeckCore.exe")
		if err2 := launchDetached(core, nil); err2 != nil {
			logLine(started, "Core UI fallback also failed: %v", err2)
		}
		return
	}
	if hp, ok := waitHeartbeat(version, time.Now().Add(15*time.Second)); ok {
		logLine(started, "desktop heartbeat established on port %d; startup complete", hp)
	} else {
		logLine(started, "UI process launched but no desktop heartbeat arrived within 15s")
	}
}
