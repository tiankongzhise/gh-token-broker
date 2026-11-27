//go:build !windows

package winmutex

import "errors"

func Lock(string) (func(), error) {
	return nil, errors.New("windows named mutexes are unavailable on this platform")
}
