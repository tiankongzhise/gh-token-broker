//go:build windows

package winmutex

import (
	"sync"
	"testing"
	"time"
)

func TestLockUnlockAcrossGoroutines(t *testing.T) {
	const workers = 8
	var wg sync.WaitGroup
	errs := make(chan error, workers)
	for i := 0; i < workers; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			unlock, err := Lock("test:lock-unlock-across-goroutines")
			if err != nil {
				errs <- err
				return
			}
			time.Sleep(time.Millisecond)
			unlock()
		}()
	}
	wg.Wait()
	close(errs)
	for err := range errs {
		if err != nil {
			t.Fatal(err)
		}
	}
}
