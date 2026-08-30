// NewzDeckThumb v3.6.8 - persistent WIC-first bounded thumbnail helper.
// Copyright (C) 2026 NewzDeck contributors.
// SPDX-License-Identifier: GPL-3.0-only
package main

import (
	"bufio"
	"encoding/json"
	"image"
	"image/color"
	"image/gif"
	"image/jpeg"
	"image/png"
	"math"
	"os"
	"runtime"
	"strconv"
	"syscall"
	"unsafe"
)

type guid struct {
	Data1 uint32
	Data2 uint16
	Data3 uint16
	Data4 [8]byte
}

type workerRequest struct {
	ID     string `json:"id"`
	Input  string `json:"input"`
	Output string `json:"output"`
	MaxDim int    `json:"max_dim"`
}

type workerResponse struct {
	ID           string `json:"id,omitempty"`
	Width        int    `json:"width,omitempty"`
	Height       int    `json:"height,omitempty"`
	SourceWidth  int    `json:"source_width,omitempty"`
	SourceHeight int    `json:"source_height,omitempty"`
	Format       string `json:"format,omitempty"`
	Method       string `json:"method,omitempty"`
	VisualBlank  bool   `json:"visual_blank,omitempty"`
	Error        string `json:"error,omitempty"`
}

var (
	ole32                  = syscall.NewLazyDLL("ole32.dll")
	procCoInitializeEx     = ole32.NewProc("CoInitializeEx")
	procCoUninitialize     = ole32.NewProc("CoUninitialize")
	procCoCreateInstance   = ole32.NewProc("CoCreateInstance")
	clsidWICImagingFactory = guid{0xCACAF262, 0x9370, 0x4615, [8]byte{0xA1, 0x3B, 0x9F, 0x55, 0x39, 0xDA, 0x4C, 0x0A}}
	iidWICImagingFactory   = guid{0xEC5EC8A9, 0xC395, 0x4314, [8]byte{0x9C, 0x77, 0x54, 0xD7, 0xA9, 0x35, 0xFF, 0x70}}
	pixel32BGRA            = guid{0x6FDDC324, 0x4E03, 0x4BFE, [8]byte{0xB1, 0x85, 0x3D, 0x77, 0x76, 0x8D, 0xC9, 0x0F}}
)

const (
	coinitApartmentThreaded        = 0x2
	clsctxInprocServer             = 0x1
	genericRead                    = 0x80000000
	wicDecodeMetadataCacheOnDemand = 0
	wicBitmapInterpolationModeFant = 3
)

func failed(hr uintptr) bool { return int32(uint32(hr)) < 0 }
func comMethod(obj uintptr, index int) uintptr {
	if obj == 0 {
		return 0
	}
	vt := *(*uintptr)(unsafe.Pointer(obj))
	return *(*uintptr)(unsafe.Pointer(vt + uintptr(index)*unsafe.Sizeof(uintptr(0))))
}
func comCall(obj uintptr, index int, args ...uintptr) uintptr {
	fn := comMethod(obj, index)
	if fn == 0 {
		return ^uintptr(0)
	}
	all := make([]uintptr, 0, len(args)+1)
	all = append(all, obj)
	all = append(all, args...)
	r, _, _ := syscall.SyscallN(fn, all...)
	return r
}
func release(obj uintptr) {
	if obj != 0 {
		comCall(obj, 2)
	}
}

// wicSession pins the worker to one OS thread and keeps COM plus the WIC factory
// alive across many thumbnail jobs. Standalone mode uses the same session for one
// request, while --worker reuses it until the backend closes stdin.
type wicSession struct {
	initialized bool
	factory     uintptr
}

func newWICSession() *wicSession {
	runtime.LockOSThread()
	s := &wicSession{}
	hr, _, _ := procCoInitializeEx.Call(0, coinitApartmentThreaded)
	// RPC_E_CHANGED_MODE is harmless for WIC usage; only balance CoUninitialize
	// when this process performed the successful initialization itself.
	s.initialized = !failed(hr)
	var factory uintptr
	hr, _, _ = procCoCreateInstance.Call(uintptr(unsafe.Pointer(&clsidWICImagingFactory)), 0, clsctxInprocServer, uintptr(unsafe.Pointer(&iidWICImagingFactory)), uintptr(unsafe.Pointer(&factory)))
	if !failed(hr) && factory != 0 {
		s.factory = factory
	}
	return s
}
func (s *wicSession) close() {
	if s == nil {
		return
	}
	if s.factory != 0 {
		release(s.factory)
		s.factory = 0
	}
	if s.initialized {
		procCoUninitialize.Call()
		s.initialized = false
	}
	runtime.UnlockOSThread()
}

func wicThumbnail(factory uintptr, inPath string, maxDim int) (*image.RGBA, int, int, bool) {
	if factory == 0 {
		return nil, 0, 0, false
	}
	p, err := syscall.UTF16PtrFromString(inPath)
	if err != nil {
		return nil, 0, 0, false
	}
	var decoder uintptr
	hr := comCall(factory, 3, uintptr(unsafe.Pointer(p)), 0, genericRead, wicDecodeMetadataCacheOnDemand, uintptr(unsafe.Pointer(&decoder)))
	if failed(hr) || decoder == 0 {
		return nil, 0, 0, false
	}
	defer release(decoder)
	var frame uintptr
	hr = comCall(decoder, 13, 0, uintptr(unsafe.Pointer(&frame)))
	if failed(hr) || frame == 0 {
		return nil, 0, 0, false
	}
	defer release(frame)
	var sw, sh uint32
	hr = comCall(frame, 3, uintptr(unsafe.Pointer(&sw)), uintptr(unsafe.Pointer(&sh)))
	if failed(hr) || sw == 0 || sh == 0 {
		return nil, 0, 0, false
	}
	w, h := int(sw), int(sh)
	if w > maxDim || h > maxDim {
		if w >= h {
			h = int(math.Round(float64(h) * float64(maxDim) / float64(w)))
			w = maxDim
		} else {
			w = int(math.Round(float64(w) * float64(maxDim) / float64(h)))
			h = maxDim
		}
		if w < 1 {
			w = 1
		}
		if h < 1 {
			h = 1
		}
	}
	var scaler uintptr
	hr = comCall(factory, 11, uintptr(unsafe.Pointer(&scaler)))
	if failed(hr) || scaler == 0 {
		return nil, 0, 0, false
	}
	defer release(scaler)
	hr = comCall(scaler, 8, frame, uintptr(uint32(w)), uintptr(uint32(h)), wicBitmapInterpolationModeFant)
	if failed(hr) {
		return nil, 0, 0, false
	}
	var converter uintptr
	hr = comCall(factory, 10, uintptr(unsafe.Pointer(&converter)))
	if failed(hr) || converter == 0 {
		return nil, 0, 0, false
	}
	defer release(converter)
	hr = comCall(converter, 8, scaler, uintptr(unsafe.Pointer(&pixel32BGRA)), 0, 0, 0, 0)
	if failed(hr) {
		return nil, 0, 0, false
	}
	stride := w * 4
	buf := make([]byte, stride*h)
	if len(buf) == 0 {
		return nil, 0, 0, false
	}
	hr = comCall(converter, 7, 0, uintptr(uint32(stride)), uintptr(uint32(len(buf))), uintptr(unsafe.Pointer(&buf[0])))
	if failed(hr) {
		return nil, 0, 0, false
	}
	dst := image.NewRGBA(image.Rect(0, 0, w, h))
	for y := 0; y < h; y++ {
		for x := 0; x < w; x++ {
			i := y*stride + x*4
			j := y*dst.Stride + x*4
			dst.Pix[j] = buf[i+2]
			dst.Pix[j+1] = buf[i+1]
			dst.Pix[j+2] = buf[i]
			dst.Pix[j+3] = 255
		}
	}
	return dst, int(sw), int(sh), true
}

func visuallyBlank(img *image.RGBA) bool {
	if img == nil {
		return false
	}
	b := img.Bounds()
	w, h := b.Dx(), b.Dy()
	if w <= 0 || h <= 0 {
		return true
	}
	sx, sy := 1, 1
	if w > 32 {
		sx = w / 32
	}
	if h > 32 {
		sy = h / 32
	}
	minR, minG, minB, maxR, maxG, maxB := 255, 255, 255, 0, 0, 0
	var sum, sum2 float64
	n := 0
	for y := b.Min.Y; y < b.Max.Y; y += sy {
		for x := b.Min.X; x < b.Max.X; x += sx {
			c := img.RGBAAt(x, y)
			if c.A < 8 {
				continue
			}
			r, g, bb := int(c.R), int(c.G), int(c.B)
			if r < minR {
				minR = r
			}
			if g < minG {
				minG = g
			}
			if bb < minB {
				minB = bb
			}
			if r > maxR {
				maxR = r
			}
			if g > maxG {
				maxG = g
			}
			if bb > maxB {
				maxB = bb
			}
			lum := .2126*float64(r) + .7152*float64(g) + .0722*float64(bb)
			sum += lum
			sum2 += lum * lum
			n++
		}
	}
	if n == 0 {
		return true
	}
	mean := sum / float64(n)
	variance := math.Max(0, sum2/float64(n)-mean*mean)
	spread := maxR - minR
	if maxG-minG > spread {
		spread = maxG - minG
	}
	if maxB-minB > spread {
		spread = maxB - minB
	}
	return spread <= 5 && variance <= 3.0
}

func clamp(v, lo, hi int) int {
	if v < lo {
		return lo
	}
	if v > hi {
		return hi
	}
	return v
}
func resizeBilinear(src image.Image, w, h int) *image.RGBA {
	b := src.Bounds()
	sw, sh := b.Dx(), b.Dy()
	dst := image.NewRGBA(image.Rect(0, 0, w, h))
	if sw <= 0 || sh <= 0 || w <= 0 || h <= 0 {
		return dst
	}
	sxScale := float64(sw) / float64(w)
	syScale := float64(sh) / float64(h)
	for y := 0; y < h; y++ {
		fy := (float64(y)+.5)*syScale - .5
		y0 := int(math.Floor(fy))
		wy := fy - float64(y0)
		y1 := y0 + 1
		y0 = clamp(y0, 0, sh-1)
		y1 = clamp(y1, 0, sh-1)
		for x := 0; x < w; x++ {
			fx := (float64(x)+.5)*sxScale - .5
			x0 := int(math.Floor(fx))
			wx := fx - float64(x0)
			x1 := x0 + 1
			x0 = clamp(x0, 0, sw-1)
			x1 = clamp(x1, 0, sw-1)
			c00 := color.RGBAModel.Convert(src.At(b.Min.X+x0, b.Min.Y+y0)).(color.RGBA)
			c10 := color.RGBAModel.Convert(src.At(b.Min.X+x1, b.Min.Y+y0)).(color.RGBA)
			c01 := color.RGBAModel.Convert(src.At(b.Min.X+x0, b.Min.Y+y1)).(color.RGBA)
			c11 := color.RGBAModel.Convert(src.At(b.Min.X+x1, b.Min.Y+y1)).(color.RGBA)
			mix := func(a, b, c, d uint8) uint8 {
				t0 := float64(a)*(1-wx) + float64(b)*wx
				t1 := float64(c)*(1-wx) + float64(d)*wx
				v := t0*(1-wy) + t1*wy
				if v < 0 {
					v = 0
				}
				if v > 255 {
					v = 255
				}
				return uint8(v + .5)
			}
			dst.SetRGBA(x, y, color.RGBA{R: mix(c00.R, c10.R, c01.R, c11.R), G: mix(c00.G, c10.G, c01.G, c11.G), B: mix(c00.B, c10.B, c01.B, c11.B), A: 255})
		}
	}
	return dst
}
func fallbackThumbnail(path string, maxDim int) (*image.RGBA, int, int, bool) {
	f, err := os.Open(path)
	if err != nil {
		return nil, 0, 0, false
	}
	defer f.Close()
	_, _ = gif.GIF{}, png.Encoder{}
	src, _, err := image.Decode(f)
	if err != nil {
		return nil, 0, 0, false
	}
	b := src.Bounds()
	sw, sh := b.Dx(), b.Dy()
	if sw <= 0 || sh <= 0 {
		return nil, 0, 0, false
	}
	w, h := sw, sh
	if w > maxDim || h > maxDim {
		if w >= h {
			h = int(math.Round(float64(h) * float64(maxDim) / float64(w)))
			w = maxDim
		} else {
			w = int(math.Round(float64(w) * float64(maxDim) / float64(h)))
			h = maxDim
		}
		if w < 1 {
			w = 1
		}
		if h < 1 {
			h = 1
		}
	}
	return resizeBilinear(src, w, h), sw, sh, true
}

func createThumbnail(session *wicSession, inPath, outPath string, maxDim int) (workerResponse, bool) {
	if maxDim < 32 || maxDim > 4096 {
		return workerResponse{Error: "invalid max_dim"}, false
	}
	dst, sw, sh, ok := wicThumbnail(session.factory, inPath, maxDim)
	method := "wic"
	if !ok {
		dst, sw, sh, ok = fallbackThumbnail(inPath, maxDim)
		method = "go-fallback"
	}
	if !ok || dst == nil {
		return workerResponse{Error: "decode failed"}, false
	}
	if visuallyBlank(dst) {
		return workerResponse{Width: dst.Bounds().Dx(), Height: dst.Bounds().Dy(), SourceWidth: sw, SourceHeight: sh, Format: "jpeg", Method: method, VisualBlank: true}, true
	}
	out, err := os.Create(outPath)
	if err != nil {
		return workerResponse{Error: "output create failed"}, false
	}
	if err := jpeg.Encode(out, dst, &jpeg.Options{Quality: 84}); err != nil {
		out.Close()
		return workerResponse{Error: "jpeg encode failed"}, false
	}
	if err := out.Close(); err != nil {
		return workerResponse{Error: "output close failed"}, false
	}
	return workerResponse{Width: dst.Bounds().Dx(), Height: dst.Bounds().Dy(), SourceWidth: sw, SourceHeight: sh, Format: "jpeg", Method: method}, true
}

func workerMain() {
	session := newWICSession()
	defer session.close()
	scanner := bufio.NewScanner(os.Stdin)
	scanner.Buffer(make([]byte, 4096), 1024*1024)
	enc := json.NewEncoder(os.Stdout)
	for scanner.Scan() {
		var req workerRequest
		if err := json.Unmarshal(scanner.Bytes(), &req); err != nil {
			_ = enc.Encode(workerResponse{Error: "invalid request"})
			continue
		}
		resp, ok := createThumbnail(session, req.Input, req.Output, req.MaxDim)
		resp.ID = req.ID
		if !ok && resp.Error == "" {
			resp.Error = "thumbnail failed"
		}
		_ = enc.Encode(resp)
	}
}

func fail() { os.Exit(1) }
func main() {
	if len(os.Args) == 2 && os.Args[1] == "--worker" {
		workerMain()
		return
	}
	if len(os.Args) < 4 {
		fail()
	}
	maxDim, err := strconv.Atoi(os.Args[3])
	if err != nil {
		fail()
	}
	session := newWICSession()
	defer session.close()
	resp, ok := createThumbnail(session, os.Args[1], os.Args[2], maxDim)
	if !ok {
		fail()
	}
	_ = json.NewEncoder(os.Stdout).Encode(resp)
}
