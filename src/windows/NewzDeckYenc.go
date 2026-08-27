// NewzDeckYenc is NewzDeck's small persistent native yEnc decoder helper.
// It uses a length-prefixed stdin/stdout protocol documented in server.py.
// Copyright (C) 2026 NewzDeck contributors.
// SPDX-License-Identifier: GPL-3.0-only
package main

import (
	"bufio"
	"encoding/binary"
	"hash/crc32"
	"io"
	"os"
)

const maxEncoded = 160 * 1024 * 1024

func decodeLine(line []byte, dst []byte) ([]byte, bool) {
	for i := 0; i < len(line); i++ {
		b := line[i]
		if b == '=' {
			i++
			if i >= len(line) {
				return dst, false
			}
			b = line[i] - 64
		}
		dst = append(dst, byte(int(b)-42))
	}
	return dst, true
}

func decodeBlob(encoded []byte) ([]byte, uint32, uint32) {
	out := make([]byte, 0, len(encoded))
	start := 0
	for start <= len(encoded) {
		end := start
		for end < len(encoded) && encoded[end] != '\n' && encoded[end] != '\r' {
			end++
		}
		if end > start {
			var ok bool
			out, ok = decodeLine(encoded[start:end], out)
			if !ok {
				return nil, 0, 1
			}
		}
		if end >= len(encoded) {
			break
		}
		// Treat CRLF as one line separator and ignore empty lines exactly as
		// Python's bytes.splitlines() fallback does.
		if encoded[end] == '\r' && end+1 < len(encoded) && encoded[end+1] == '\n' {
			start = end + 2
		} else {
			start = end + 1
		}
	}
	return out, crc32.ChecksumIEEE(out), 0
}

func main() {
	in := bufio.NewReaderSize(os.Stdin, 1024*1024)
	out := bufio.NewWriterSize(os.Stdout, 1024*1024)
	defer out.Flush()
	var lenBuf [8]byte
	var header [16]byte
	for {
		if _, err := io.ReadFull(in, lenBuf[:]); err != nil {
			return
		}
		n := binary.LittleEndian.Uint64(lenBuf[:])
		if n > maxEncoded {
			binary.LittleEndian.PutUint64(header[0:8], 0)
			binary.LittleEndian.PutUint32(header[8:12], 0)
			binary.LittleEndian.PutUint32(header[12:16], 2)
			_, _ = out.Write(header[:])
			_ = out.Flush()
			return
		}
		encoded := make([]byte, int(n))
		if _, err := io.ReadFull(in, encoded); err != nil {
			return
		}
		decoded, crc, status := decodeBlob(encoded)
		binary.LittleEndian.PutUint64(header[0:8], uint64(len(decoded)))
		binary.LittleEndian.PutUint32(header[8:12], crc)
		binary.LittleEndian.PutUint32(header[12:16], status)
		if _, err := out.Write(header[:]); err != nil {
			return
		}
		if status == 0 {
			if _, err := out.Write(decoded); err != nil {
				return
			}
		}
		if err := out.Flush(); err != nil {
			return
		}
	}
}
