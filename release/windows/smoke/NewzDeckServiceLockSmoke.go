package main

import (
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"syscall"
	"time"
	"unsafe"
)

const (
	serviceName                         = "NewzDeckService"
	serviceWin32OwnProcess              = 0x10
	serviceStopped                      = 1
	serviceStartPending                 = 2
	serviceStopPending                  = 3
	serviceRunning                      = 4
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
	stopCh                          = make(chan struct{})
)

func p16(s string) *uint16 { p, _ := syscall.UTF16PtrFromString(s); return p }

func setStatus(state, accepted, checkpoint, waitHint uint32) {
	if statusHandle == 0 {
		return
	}
	s := serviceStatus{ServiceType: serviceWin32OwnProcess, CurrentState: state, ControlsAccepted: accepted, CheckPoint: checkpoint, WaitHint: waitHint}
	procSetServiceStatus.Call(statusHandle, uintptr(unsafe.Pointer(&s)))
}

func handler(ctrl uint32) uintptr {
	if ctrl == serviceControlStop {
		setStatus(serviceStopPending, 0, 1, 5000)
		select {
		case <-stopCh:
		default:
			close(stopCh)
		}
	}
	return 0
}

func serviceMain(argc, argv uintptr) uintptr {
	h, _, _ := procRegisterServiceCtrlHandlerW.Call(uintptr(unsafe.Pointer(p16(serviceName))), syscall.NewCallback(handler))
	if h == 0 {
		return 0
	}
	statusHandle = h
	setStatus(serviceStartPending, 0, 1, 3000)
	setStatus(serviceRunning, serviceAcceptStop, 0, 0)
	<-stopCh
	// Deliberately exceed the old installer 1.2 second fixed wait.
	time.Sleep(2500 * time.Millisecond)
	setStatus(serviceStopped, 0, 0, 0)
	return 0
}

func runService() error {
	entries := []serviceTableEntry{{Name: p16(serviceName), Proc: syscall.NewCallback(serviceMain)}, {}}
	r, _, e := procStartServiceCtrlDispatcherW.Call(uintptr(unsafe.Pointer(&entries[0])))
	if r == 0 {
		if errno, ok := e.(syscall.Errno); ok && errno == errorFailedServiceControllerConnect {
			return e
		}
		return e
	}
	return nil
}

func sc(args ...string) (string, error) {
	exe := filepath.Join(os.Getenv("SystemRoot"), "System32", "sc.exe")
	cmd := exec.Command(exe, args...)
	cmd.SysProcAttr = &syscall.SysProcAttr{HideWindow: true}
	b, err := cmd.CombinedOutput()
	return string(b), err
}

func status() string {
	out, err := sc("query", serviceName)
	if err != nil {
		return "not_installed"
	}
	u := strings.ToUpper(out)
	if strings.Contains(u, "STOPPED") {
		return "stopped"
	}
	if strings.Contains(u, "STOP_PENDING") {
		return "stopping"
	}
	if strings.Contains(u, "RUNNING") {
		return "running"
	}
	if strings.Contains(u, "START_PENDING") {
		return "starting"
	}
	return "installed"
}

func stop() error {
	if st := status(); st == "stopped" || st == "not_installed" {
		return nil
	}
	_, _ = sc("stop", serviceName)
	deadline := time.Now().Add(20 * time.Second)
	for time.Now().Before(deadline) {
		if status() == "stopped" {
			return nil
		}
		time.Sleep(200 * time.Millisecond)
	}
	if status() == "stopped" {
		return nil
	}
	return fmt.Errorf("service did not stop")
}

func main() {
	if len(os.Args) > 1 && strings.EqualFold(os.Args[1], "stop") {
		if err := stop(); err != nil {
			os.Exit(1)
		}
		return
	}
	_ = runService()
}
