// NewzDeckThumb generates bounded JPEG preview thumbnails for NewzDeck.
// Copyright (C) 2026 NewzDeck contributors.
// SPDX-License-Identifier: GPL-3.0-only
package main

import (
	"encoding/json"
	"image"
	"image/color"
	"image/gif"
	"image/jpeg"
	"image/png"
	"math"
	"os"
	"strconv"
)

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
		fy := (float64(y)+0.5)*syScale - 0.5
		y0 := int(math.Floor(fy))
		wy := fy - float64(y0)
		y1 := y0 + 1
		y0 = clamp(y0, 0, sh-1)
		y1 = clamp(y1, 0, sh-1)
		for x := 0; x < w; x++ {
			fx := (float64(x)+0.5)*sxScale - 0.5
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
				return uint8(v + 0.5)
			}
			dst.SetRGBA(x, y, color.RGBA{
				R: mix(c00.R, c10.R, c01.R, c11.R), G: mix(c00.G, c10.G, c01.G, c11.G),
				B: mix(c00.B, c10.B, c01.B, c11.B), A: 255,
			})
		}
	}
	return dst
}

func fail() { os.Exit(1) }

func main() {
	if len(os.Args) < 4 {
		fail()
	}
	inPath, outPath := os.Args[1], os.Args[2]
	maxDim, err := strconv.Atoi(os.Args[3])
	if err != nil || maxDim < 32 || maxDim > 4096 {
		fail()
	}
	f, err := os.Open(inPath)
	if err != nil {
		fail()
	}
	defer f.Close()
	// Explicit registrations keep support obvious and source-auditable.
	_, _ = gif.GIF{}, png.Encoder{}
	src, _, err := image.Decode(f)
	if err != nil {
		fail()
	}
	b := src.Bounds()
	sw, sh := b.Dx(), b.Dy()
	if sw <= 0 || sh <= 0 {
		fail()
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
	dst := resizeBilinear(src, w, h)
	out, err := os.Create(outPath)
	if err != nil {
		fail()
	}
	if err := jpeg.Encode(out, dst, &jpeg.Options{Quality: 84}); err != nil {
		out.Close()
		fail()
	}
	if err := out.Close(); err != nil {
		fail()
	}
	_ = json.NewEncoder(os.Stdout).Encode(map[string]any{"width": w, "height": h, "format": "jpeg"})
}
