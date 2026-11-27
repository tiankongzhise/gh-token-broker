//go:build windows

package winmutex

import (
	"crypto/sha256"
	"encoding/hex"
	"fmt"
	"runtime"
	"sync"

	"golang.org/x/sys/windows"
)

func Lock(name string) (func(), error) {
	runtime.LockOSThread()
	digest := sha256.Sum256([]byte(name))
	mutexName := `Local\gh-token-broker-` + hex.EncodeToString(digest[:16])
	namePtr, err := windows.UTF16PtrFromString(mutexName)
	if err != nil {
		runtime.UnlockOSThread()
		return nil, fmt.Errorf("build mutex name: %w", err)
	}
	handle, createErr := windows.CreateMutex(nil, false, namePtr)
	if handle == 0 {
		runtime.UnlockOSThread()
		return nil, fmt.Errorf("create mutex: %w", createErr)
	}
	closeHandle := func() {
		_ = windows.CloseHandle(handle)
	}
	event, err := windows.WaitForSingleObject(handle, windows.INFINITE)
	if err != nil {
		closeHandle()
		runtime.UnlockOSThread()
		return nil, fmt.Errorf("wait for mutex: %w", err)
	}
	if event != windows.WAIT_OBJECT_0 && event != windows.WAIT_ABANDONED {
		closeHandle()
		runtime.UnlockOSThread()
		return nil, fmt.Errorf("wait for mutex returned event 0x%x", event)
	}
	var once sync.Once
	return func() {
		once.Do(func() {
			_ = windows.ReleaseMutex(handle)
			closeHandle()
			runtime.UnlockOSThread()
		})
	}, nil
}
