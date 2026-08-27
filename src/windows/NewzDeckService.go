// NewzDeckService is NewzDeck's Windows Service wrapper and elevated service
// maintenance helper. It contains no downloader implementation; it starts the
// same published Python backend in NEWZDECK_SERVICE mode.
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
	"sync"
	"syscall"
	"time"
	"unsafe"
)

const serviceName = "NewzDeckService"
const (
	serviceWin32OwnProcess              = 0x10
	serviceStartPending                 = 2
	serviceStopPending                  = 3
	serviceRunning                      = 4
	serviceStopped                      = 1
	serviceAcceptStop                   = 1
	serviceControlStop                  = 1
	errorFailedServiceControllerConnect = 1063
)

type serviceStatus struct {
	ServiceType             uint32
	CurrentState            uint32
	ControlsAccepted        uint32
	Win32ExitCode           uint32
	ServiceSpecificExitCode uint32
	CheckPoint              uint32
	WaitHint                uint32
}
type serviceTableEntry struct {
	Name *uint16
	Proc uintptr
}

var (
	advapi32                        = syscall.NewLazyDLL("advapi32.dll")
	procStartServiceCtrlDispatcherW = advapi32.NewProc("StartServiceCtrlDispatcherW")
	procRegisterServiceCtrlHandlerW = advapi32.NewProc("RegisterServiceCtrlHandlerW")
	procSetServiceStatus            = advapi32.NewProc("SetServiceStatus")
	statusHandle                    uintptr
	stopOnce                        sync.Once
	stopCh                          = make(chan struct{})
	workerMu                        sync.Mutex
	worker                          *exec.Cmd
)

func p16(s string) *uint16 { p, _ := syscall.UTF16PtrFromString(s); return p }
func appDir() string       { p, _ := os.Executable(); return filepath.Dir(p) }
func defaultUserRoot() string {
	b := strings.TrimSpace(os.Getenv("LOCALAPPDATA"))
	if b == "" {
		b = os.TempDir()
	}
	return filepath.Join(b, "NewzDeck")
}
func argValue(name, fallback string) string {
	for i := 1; i < len(os.Args)-1; i++ {
		if os.Args[i] == name {
			return os.Args[i+1]
		}
	}
	return fallback
}
func hasArg(name string) bool {
	for _, a := range os.Args[1:] {
		if a == name {
			return true
		}
	}
	return false
}

func writeJSONAtomic(path string, v any) {
	if path == "" {
		return
	}
	_ = os.MkdirAll(filepath.Dir(path), 0755)
	b, _ := json.MarshalIndent(v, "", "  ")
	tmp := path + ".tmp"
	if os.WriteFile(tmp, b, 0644) == nil {
		_ = os.Remove(path)
		_ = os.Rename(tmp, path)
	}
}
func writeState(root, status, detail string, restarts int) {
	writeJSONAtomic(filepath.Join(root, "data", "service-state.json"), map[string]any{"status": status, "detail": detail, "pid": os.Getpid(), "restarts": restarts, "updated_at": time.Now().Format(time.RFC3339)})
}
func setStatus(state, accepted, checkpoint, waitHint uint32) {
	if statusHandle == 0 {
		return
	}
	s := serviceStatus{ServiceType: serviceWin32OwnProcess, CurrentState: state, ControlsAccepted: accepted, CheckPoint: checkpoint, WaitHint: waitHint}
	procSetServiceStatus.Call(statusHandle, uintptr(unsafe.Pointer(&s)))
}
func serviceHandler(ctrl uint32) uintptr {
	if ctrl == serviceControlStop {
		setStatus(serviceStopPending, 0, 1, 15000)
		stopOnce.Do(func() { close(stopCh) })
	}
	return 0
}

func runtimePython() string {
	for _, n := range []string{"python.exe", "pythonw.exe"} {
		p := filepath.Join(appDir(), "runtime", n)
		if st, e := os.Stat(p); e == nil && !st.IsDir() {
			return p
		}
	}
	return ""
}
func localVersion() string {
	b, e := os.ReadFile(filepath.Join(appDir(), "version.txt"))
	if e != nil {
		return ""
	}
	return strings.TrimSpace(string(b))
}
func withEnv(base []string, vals map[string]string) []string {
	blocked := map[string]bool{}
	for k := range vals {
		blocked[strings.ToUpper(k)] = true
	}
	out := make([]string, 0, len(base)+len(vals))
	for _, item := range base {
		k := item
		if i := strings.IndexByte(item, '='); i >= 0 {
			k = item[:i]
		}
		if !blocked[strings.ToUpper(k)] {
			out = append(out, item)
		}
	}
	for k, v := range vals {
		out = append(out, k+"="+v)
	}
	return out
}
func startBackend(root, defaultDownload string) (*exec.Cmd, error) {
	py := runtimePython()
	if py == "" {
		return nil, fmt.Errorf("private CPython runtime is missing; launch NewzDeck once in desktop mode before starting the service")
	}
	server := filepath.Join(appDir(), "server.py")
	if _, e := os.Stat(server); e != nil {
		return nil, e
	}
	cmd := exec.Command(py, server)
	cmd.Dir = appDir()
	cmd.SysProcAttr = &syscall.SysProcAttr{HideWindow: true, CreationFlags: 0x08000000}
	cmd.Stdout = nil
	cmd.Stderr = nil
	cmd.Stdin = nil
	cmd.Env = withEnv(os.Environ(), map[string]string{
		"NEWZDECK_SERVICE": "1", "NEWZDECK_DESKTOP": "0", "NEWZDECK_NO_OPEN": "1",
		"NEWZDECK_USER_ROOT": root, "NEWZDECK_PORT_FILE": filepath.Join(root, "newzdeck.port"),
		"NEWZDECK_EXPECTED_VERSION": localVersion(), "NEWZDECK_DEFAULT_DOWNLOAD_DIR": defaultDownload,
	})
	if e := cmd.Start(); e != nil {
		return nil, e
	}
	return cmd, nil
}
func readPort(root string) int {
	b, e := os.ReadFile(filepath.Join(root, "newzdeck.port"))
	if e != nil {
		return 0
	}
	p, _ := strconv.Atoi(strings.TrimSpace(string(b)))
	return p
}
func requestBackendShutdown(root string) {
	if p := readPort(root); p > 0 {
		c := &http.Client{Timeout: 2 * time.Second}
		req, _ := http.NewRequest("POST", fmt.Sprintf("http://127.0.0.1:%d/api/service/shutdown", p), bytes.NewReader([]byte("{}")))
		req.Header.Set("Content-Type", "application/json")
		if r, e := c.Do(req); e == nil {
			r.Body.Close()
		}
	}
}
func runWorker(root, defaultDownload string) {
	restarts := 0
	_ = os.MkdirAll(filepath.Join(root, "data"), 0755)
	for {
		select {
		case <-stopCh:
			writeState(root, "stopping", "Background service is stopping.", restarts)
			return
		default:
		}
		writeState(root, "starting", "Starting NewzDeck background backend.", restarts)
		cmd, e := startBackend(root, defaultDownload)
		if e != nil {
			writeState(root, "stopped", e.Error(), restarts)
			return
		}
		workerMu.Lock()
		worker = cmd
		workerMu.Unlock()
		writeState(root, "running", "NewzDeck background backend is running.", restarts)
		done := make(chan error, 1)
		go func() { done <- cmd.Wait() }()
		select {
		case <-stopCh:
			requestBackendShutdown(root)
			select {
			case <-done:
			case <-time.After(8 * time.Second):
				if cmd.Process != nil {
					_ = cmd.Process.Kill()
				}
				<-done
			}
			workerMu.Lock()
			worker = nil
			workerMu.Unlock()
			writeState(root, "stopped", "Background service stopped normally.", restarts)
			return
		case e := <-done:
			workerMu.Lock()
			worker = nil
			workerMu.Unlock()
			select {
			case <-stopCh:
				writeState(root, "stopped", "Background service stopped normally.", restarts)
				return
			default:
			}
			restarts++
			detail := "Backend exited unexpectedly; restarting."
			if e != nil {
				detail = fmt.Sprintf("Backend exited unexpectedly (%v); restarting.", e)
			}
			writeState(root, "restarting", detail, restarts)
			time.Sleep(2 * time.Second)
		}
	}
}
func serviceMain(argc, argv uintptr) uintptr {
	h, _, _ := procRegisterServiceCtrlHandlerW.Call(uintptr(unsafe.Pointer(p16(serviceName))), syscall.NewCallback(serviceHandler))
	if h == 0 {
		return 0
	}
	statusHandle = h
	setStatus(serviceStartPending, 0, 1, 12000)
	root := argValue("--user-root", defaultUserRoot())
	dd := argValue("--default-download-dir", filepath.Join(os.Getenv("USERPROFILE"), "Downloads", "NewzDeck"))
	setStatus(serviceRunning, serviceAcceptStop, 0, 0)
	runWorker(root, dd)
	setStatus(serviceStopped, 0, 0, 0)
	return 0
}
func runAsService() error {
	entries := []serviceTableEntry{{Name: p16(serviceName), Proc: syscall.NewCallback(serviceMain)}, {}}
	r, _, e := procStartServiceCtrlDispatcherW.Call(uintptr(unsafe.Pointer(&entries[0])))
	if r == 0 {
		if errno, ok := e.(syscall.Errno); ok && errno == errorFailedServiceControllerConnect {
			return fmt.Errorf("not started by Windows Service Control Manager")
		}
		return e
	}
	return nil
}

func sc(args ...string) (string, error) {
	cmd := exec.Command(filepath.Join(os.Getenv("SystemRoot"), "System32", "sc.exe"), args...)
	cmd.SysProcAttr = &syscall.SysProcAttr{HideWindow: true}
	b, e := cmd.CombinedOutput()
	return string(b), e
}
func serviceStatusText() string {
	out, e := sc("query", serviceName)
	if e != nil {
		return "not_installed"
	}
	u := strings.ToUpper(out)
	for _, x := range []struct{ k, v string }{{"RUNNING", "running"}, {"START_PENDING", "starting"}, {"STOP_PENDING", "stopping"}, {"STOPPED", "stopped"}} {
		if strings.Contains(u, x.k) {
			return x.v
		}
	}
	return "installed"
}
func quoteBinArg(s string) string { return `"` + strings.ReplaceAll(s, `"`, `\"`) + `"` }
func configuredBinPath(root, dd string) string {
	exe, _ := os.Executable()
	return quoteBinArg(exe) + " --service --user-root " + quoteBinArg(root) + " --default-download-dir " + quoteBinArg(dd)
}
func ensureRegistration(root, dd string) error {
	bin := configuredBinPath(root, dd)
	if serviceStatusText() == "not_installed" {
		if out, e := sc("create", serviceName, "binPath=", bin, "start=", "auto", "DisplayName=", "NewzDeck Background Service"); e != nil {
			return fmt.Errorf("sc create failed: %v (%s)", e, strings.TrimSpace(out))
		}
	} else {
		if out, e := sc("config", serviceName, "binPath=", bin, "start=", "auto", "DisplayName=", "NewzDeck Background Service"); e != nil {
			return fmt.Errorf("sc config failed: %v (%s)", e, strings.TrimSpace(out))
		}
	}
	_, _ = sc("description", serviceName, "Runs NewzDeck downloads and automation continuously in the background.")
	return nil
}
func waitStatus(want string, timeout time.Duration) bool {
	d := time.Now().Add(timeout)
	for time.Now().Before(d) {
		if serviceStatusText() == want {
			return true
		}
		time.Sleep(250 * time.Millisecond)
	}
	return serviceStatusText() == want
}
func startService() error {
	st := serviceStatusText()
	if st == "running" {
		return nil
	}
	out, e := sc("start", serviceName)
	if e != nil && !strings.Contains(strings.ToUpper(out), "ALREADY RUNNING") {
		return fmt.Errorf("sc start failed: %v (%s)", e, strings.TrimSpace(out))
	}
	if !waitStatus("running", 25*time.Second) {
		return fmt.Errorf("service did not reach running state")
	}
	return nil
}
func stopService() error {
	st := serviceStatusText()
	if st == "not_installed" || st == "stopped" {
		return nil
	}
	out, e := sc("stop", serviceName)
	if e != nil && !strings.Contains(strings.ToUpper(out), "NOT STARTED") {
		return fmt.Errorf("sc stop failed: %v (%s)", e, strings.TrimSpace(out))
	}
	if !waitStatus("stopped", 25*time.Second) {
		return fmt.Errorf("service did not stop")
	}
	return nil
}
func uninstallService() error {
	if serviceStatusText() == "not_installed" {
		return nil
	}
	_ = stopService()
	out, e := sc("delete", serviceName)
	if e != nil {
		return fmt.Errorf("sc delete failed: %v (%s)", e, strings.TrimSpace(out))
	}
	return nil
}

type helperResult struct {
	OK     bool   `json:"ok"`
	Action string `json:"action"`
	Status string `json:"status,omitempty"`
	Error  string `json:"error,omitempty"`
}

func writeResult(path, action string, err error) {
	r := helperResult{OK: err == nil, Action: action, Status: serviceStatusText()}
	if err != nil {
		r.Error = err.Error()
	}
	writeJSONAtomic(path, r)
}
func runHelper(action string) error {
	delay, _ := strconv.Atoi(argValue("--delay-ms", "0"))
	if delay > 0 {
		time.Sleep(time.Duration(delay) * time.Millisecond)
	}
	root := argValue("--user-root", defaultUserRoot())
	dd := argValue("--default-download-dir", filepath.Join(os.Getenv("USERPROFILE"), "Downloads", "NewzDeck"))
	switch action {
	case "install":
		if e := ensureRegistration(root, dd); e != nil {
			return e
		}
		return startService()
	case "repair":
		return ensureRegistration(root, dd)
	case "start":
		return startService()
	case "stop":
		return stopService()
	case "restart":
		if e := stopService(); e != nil {
			return e
		}
		return startService()
	case "uninstall", "remove":
		return uninstallService()
	case "status":
		return nil
	default:
		return fmt.Errorf("unknown service action %q", action)
	}
}
func main() {
	if hasArg("--service") {
		_ = runAsService()
		return
	}
	action := ""
	for _, a := range os.Args[1:] {
		if !strings.HasPrefix(a, "--") {
			action = a
			break
		}
	}
	if action == "" {
		_ = runAsService()
		return
	}
	err := runHelper(strings.ToLower(action))
	result := argValue("--result-file", "")
	writeResult(result, action, err)
	if err != nil {
		os.Exit(1)
	}
}
