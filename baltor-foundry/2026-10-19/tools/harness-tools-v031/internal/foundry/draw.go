package foundry

import (
	"bytes"
	"encoding/json"
	"fmt"
	"image"
	"image/color"
	"image/draw"
	"image/png"
	"math"
	"os"
	"path/filepath"
	"strings"
)

var ink = color.RGBA{239, 248, 253, 255}
var teal = color.RGBA{91, 242, 212, 255}
var amber = color.RGBA{255, 189, 91, 255}
var coral = color.RGBA{255, 111, 118, 255}
var dark = color.RGBA{8, 17, 33, 255}

func cHex(s string, fallback color.RGBA) color.RGBA {
	if len(s) != 7 || s[0] != '#' {
		return fallback
	}
	var a, b, c uint8
	if _, err := fmt.Sscanf(s, "#%02x%02x%02x", &a, &b, &c); err != nil {
		return fallback
	}
	return color.RGBA{a, b, c, 255}
}
func blend(dst *image.RGBA, x, y int, c color.RGBA, alpha float64) {
	b := dst.Bounds()
	if x < b.Min.X || x >= b.Max.X || y < b.Min.Y || y >= b.Max.Y {
		return
	}
	if alpha <= 0 {
		return
	}
	if alpha > 1 {
		alpha = 1
	}
	i := dst.PixOffset(x, y)
	p := dst.Pix[i:]
	a := alpha * float64(c.A) / 255
	ia := 1 - a
	p[0] = uint8(float64(p[0])*ia + float64(c.R)*a + 0.5)
	p[1] = uint8(float64(p[1])*ia + float64(c.G)*a + 0.5)
	p[2] = uint8(float64(p[2])*ia + float64(c.B)*a + 0.5)
	p[3] = 255
}
func fillRect(dst *image.RGBA, x0, y0, x1, y1 int, c color.RGBA, a float64) {
	if x0 > x1 {
		x0, x1 = x1, x0
	}
	if y0 > y1 {
		y0, y1 = y1, y0
	}
	b := dst.Bounds()
	x0 = max(x0, b.Min.X)
	x1 = min(x1, b.Max.X)
	y0 = max(y0, b.Min.Y)
	y1 = min(y1, b.Max.Y)
	if a >= 0.999 {
		draw.Draw(dst, image.Rect(x0, y0, x1, y1), &image.Uniform{C: c}, image.Point{}, draw.Src)
		return
	}
	for y := y0; y < y1; y++ {
		for x := x0; x < x1; x++ {
			blend(dst, x, y, c, a)
		}
	}
}
func line(dst *image.RGBA, x0, y0, x1, y1, r int, c color.RGBA, a float64) {
	dx := math.Abs(float64(x1 - x0))
	dy := math.Abs(float64(y1 - y0))
	steps := int(math.Max(dx, dy))*2 + 1
	if steps < 1 {
		steps = 1
	}
	for i := 0; i <= steps; i++ {
		t := float64(i) / float64(steps)
		x := int(math.Round(float64(x0)*(1-t) + float64(x1)*t))
		y := int(math.Round(float64(y0)*(1-t) + float64(y1)*t))
		disc(dst, x, y, r, c, a)
	}
}
func disc(dst *image.RGBA, cx, cy, r int, c color.RGBA, a float64) {
	if r < 1 {
		r = 1
	}
	for y := -r; y <= r; y++ {
		for x := -r; x <= r; x++ {
			if x*x+y*y <= r*r {
				blend(dst, cx+x, cy+y, c, a)
			}
		}
	}
}
func ring(dst *image.RGBA, cx, cy, r, thickness int, c color.RGBA, a float64) {
	steps := int(math.Max(36, float64(r)*3))
	for i := 0; i < steps; i++ {
		t := 2 * math.Pi * float64(i) / float64(steps)
		x := cx + int(math.Cos(t)*float64(r))
		y := cy + int(math.Sin(t)*float64(r))
		disc(dst, x, y, max(1, thickness/2), c, a)
	}
}
func rng(seed uint64) uint64 {
	z := seed + 0x9e3779b97f4a7c15
	z = (z ^ (z >> 30)) * 0xbf58476d1ce4e5b9
	z = (z ^ (z >> 27)) * 0x94d049bb133111eb
	return z ^ (z >> 31)
}
func unit(seed uint64) float64 { return float64(rng(seed)>>11) / (1 << 53) }
func gradient(im *image.RGBA, a, b color.RGBA) {
	w, h := im.Bounds().Dx(), im.Bounds().Dy()
	for y := 0; y < h; y++ {
		t := float64(y) / float64(h)
		t = t*t*0.7 + t*0.3
		c := color.RGBA{uint8(float64(a.R)*(1-t) + float64(b.R)*t), uint8(float64(a.G)*(1-t) + float64(b.G)*t), uint8(float64(a.B)*(1-t) + float64(b.B)*t), 255}
		fillRect(im, 0, y, w, y+1, c, 1)
	}
}
func polygon(im *image.RGBA, pts []image.Point, c color.RGBA, alpha float64) {
	if len(pts) < 3 {
		return
	}
	miny, maxy := pts[0].Y, pts[0].Y
	for _, p := range pts {
		if p.Y < miny {
			miny = p.Y
		}
		if p.Y > maxy {
			maxy = p.Y
		}
	}
	for y := max(0, miny); y < min(im.Bounds().Dy(), maxy+1); y++ {
		xs := []int{}
		for i := 0; i < len(pts); i++ {
			p, q := pts[i], pts[(i+1)%len(pts)]
			if (p.Y <= y && q.Y > y) || (q.Y <= y && p.Y > y) {
				x := float64(p.X) + float64(y-p.Y)*float64(q.X-p.X)/float64(q.Y-p.Y)
				xs = append(xs, int(x))
			}
		}
		if len(xs) >= 2 {
			for a := 0; a < len(xs); a++ {
				for b := a + 1; b < len(xs); b++ {
					if xs[b] < xs[a] {
						xs[b], xs[a] = xs[a], xs[b]
					}
				}
			}
			for i := 0; i+1 < len(xs); i += 2 {
				fillRect(im, xs[i], y, xs[i+1]+1, y+1, c, alpha)
			}
		}
	}
}

// Five by seven pixel alphabet embedded as source. No external font asset is bundled.
var glyph = map[rune][]string{
	'A': {"01110", "10001", "10001", "11111", "10001", "10001", "10001"},
	'B': {"11110", "10001", "10001", "11110", "10001", "10001", "11110"},
	'C': {"01111", "10000", "10000", "10000", "10000", "10000", "01111"},
	'D': {"11110", "10001", "10001", "10001", "10001", "10001", "11110"},
	'E': {"11111", "10000", "10000", "11110", "10000", "10000", "11111"},
	'F': {"11111", "10000", "10000", "11110", "10000", "10000", "10000"},
	'G': {"01111", "10000", "10000", "10111", "10001", "10001", "01111"},
	'H': {"10001", "10001", "10001", "11111", "10001", "10001", "10001"},
	'I': {"11111", "00100", "00100", "00100", "00100", "00100", "11111"},
	'J': {"00111", "00010", "00010", "00010", "10010", "10010", "01100"},
	'K': {"10001", "10010", "10100", "11000", "10100", "10010", "10001"},
	'L': {"10000", "10000", "10000", "10000", "10000", "10000", "11111"},
	'M': {"10001", "11011", "10101", "10101", "10001", "10001", "10001"},
	'N': {"10001", "11001", "10101", "10011", "10001", "10001", "10001"},
	'O': {"01110", "10001", "10001", "10001", "10001", "10001", "01110"},
	'P': {"11110", "10001", "10001", "11110", "10000", "10000", "10000"},
	'Q': {"01110", "10001", "10001", "10001", "10101", "10010", "01101"},
	'R': {"11110", "10001", "10001", "11110", "10100", "10010", "10001"},
	'S': {"01111", "10000", "10000", "01110", "00001", "00001", "11110"},
	'T': {"11111", "00100", "00100", "00100", "00100", "00100", "00100"},
	'U': {"10001", "10001", "10001", "10001", "10001", "10001", "01110"},
	'V': {"10001", "10001", "10001", "10001", "10001", "01010", "00100"},
	'W': {"10001", "10001", "10001", "10101", "10101", "10101", "01010"},
	'X': {"10001", "10001", "01010", "00100", "01010", "10001", "10001"},
	'Y': {"10001", "10001", "01010", "00100", "00100", "00100", "00100"},
	'Z': {"11111", "00001", "00010", "00100", "01000", "10000", "11111"},
	'0': {"01110", "10001", "10011", "10101", "11001", "10001", "01110"},
	'1': {"00100", "01100", "00100", "00100", "00100", "00100", "01110"},
	'2': {"01110", "10001", "00001", "00110", "01000", "10000", "11111"},
	'3': {"11110", "00001", "00001", "01110", "00001", "00001", "11110"},
	'4': {"00010", "00110", "01010", "10010", "11111", "00010", "00010"},
	'5': {"11111", "10000", "10000", "11110", "00001", "00001", "11110"},
	'6': {"01111", "10000", "10000", "11110", "10001", "10001", "01110"},
	'7': {"11111", "00001", "00010", "00100", "01000", "01000", "01000"},
	'8': {"01110", "10001", "10001", "01110", "10001", "10001", "01110"},
	'9': {"01110", "10001", "10001", "01111", "00001", "00001", "11110"},
	' ': {"00000", "00000", "00000", "00000", "00000", "00000", "00000"},
	'-': {"00000", "00000", "00000", "11111", "00000", "00000", "00000"},
	'.': {"00000", "00000", "00000", "00000", "00000", "01100", "01100"},
	':': {"00000", "01100", "01100", "00000", "01100", "01100", "00000"},
	'/': {"00001", "00001", "00010", "00100", "01000", "10000", "10000"},
	'?': {"01110", "10001", "00001", "00010", "00100", "00000", "00100"},
	'+': {"00000", "00100", "00100", "11111", "00100", "00100", "00000"},
	'!': {"00100", "00100", "00100", "00100", "00100", "00000", "00100"},
	'%': {"11001", "11010", "00100", "00100", "01011", "10011", "00000"},
	'=': {"00000", "11111", "00000", "11111", "00000", "00000", "00000"},
	'#': {"01010", "11111", "01010", "11111", "01010", "00000", "00000"},
}

func textWidth(s string, scale int) int { return len([]rune(s)) * 6 * scale }
func drawText(im *image.RGBA, x, y, scale int, s string, c color.RGBA, alpha float64) {
	if scale < 1 {
		scale = 1
	}
	for _, ch := range strings.ToUpper(s) {
		rows, ok := glyph[ch]
		if !ok {
			rows = glyph['?']
		}
		for j, row := range rows {
			for i, r := range row {
				if r == '1' {
					fillRect(im, x+i*scale, y+j*scale, x+(i+1)*scale, y+(j+1)*scale, c, alpha)
				}
			}
		}
		x += 6 * scale
	}
}
func wrap(s string, maxChars int) []string {
	s = strings.TrimSpace(strings.ToUpper(s))
	if maxChars < 4 {
		maxChars = 4
	}
	out := []string{}
	for _, explicit := range strings.Split(s, "\n") {
		current := ""
		for _, w := range strings.Fields(explicit) {
			if len(current) > 0 && len(current)+len(w)+1 > maxChars {
				out = append(out, current)
				current = w
			} else if current == "" {
				current = w
			} else {
				current += " " + w
			}
		}
		if current != "" {
			out = append(out, current)
		}
	}
	return out
}
func drawCaption(im *image.RGBA, body string, anchor string, big bool, pad []int, accent color.RGBA) {
	if strings.TrimSpace(body) == "" {
		return
	}
	w, h := im.Bounds().Dx(), im.Bounds().Dy()
	m := max(18, w/18)
	if len(pad) != 4 {
		pad = []int{10, 12, 10, 12}
	}
	scale := max(2, w/115)
	if big {
		scale = max(3, w/93)
	}
	maxChars := max(8, (w-2*m-pad[1]-pad[3])/(6*scale))
	lines := wrap(body, maxChars)
	if len(lines) > 3 {
		lines = lines[:3]
	}
	hh := len(lines)*9*scale + pad[0] + pad[2]
	top := int(float64(h) * 0.17)
	if anchor == "middle" {
		top = (h - hh) / 2
	}
	if anchor == "bottom" {
		top = h - hh - int(float64(h)*0.115)
	}
	fillRect(im, m, top, w-m, top+hh, dark, 0.77)
	fillRect(im, m, top, m+max(3, w/130), top+hh, accent, 1)
	for j, s := range lines {
		drawText(im, m+pad[3], top+pad[0]+j*9*scale, scale, s, ink, 1)
	}
}
func drawHeader(im *image.RGBA, label string, accent color.RGBA) {
	w, h := im.Bounds().Dx(), im.Bounds().Dy()
	m := max(18, w/18)
	drawText(im, m, int(float64(h)*.06), max(1, w/180), label, accent, 1)
	line(im, m, int(float64(h)*.093), w-m, int(float64(h)*.093), 1, accent, .6)
}
func drawBorder(im *image.RGBA, border int, accent color.RGBA) {
	w, h := im.Bounds().Dx(), im.Bounds().Dy()
	if border == 0 {
		return
	}
	if border > 8 {
		border = 8
	}
	for k := 0; k < border; k++ {
		line(im, k, k, w-1-k, k, 1, accent, .32)
		line(im, k, h-1-k, w-1-k, h-1-k, 1, accent, .32)
		line(im, k, k, k, h-1-k, 1, accent, .32)
		line(im, w-1-k, k, w-1-k, h-1-k, 1, accent, .32)
	}
	q := max(10, w/14)
	for _, x := range []int{border + 5, w - border - 6} {
		sx := 1
		if x > w/2 {
			sx = -1
		}
		for _, y := range []int{border + 5, h - border - 6} {
			sy := 1
			if y > h/2 {
				sy = -1
			}
			line(im, x, y, x+sx*q, y, 2, accent, 1)
			line(im, x, y, x, y+sy*q, 2, accent, 1)
		}
	}
}
func grid(im *image.RGBA, c color.RGBA, step, scroll int) {
	w, h := im.Bounds().Dx(), im.Bounds().Dy()
	if step <= 0 {
		step = 24
	}
	for x := ((-scroll)%step + step) % step; x < w; x += step {
		line(im, x, 0, x, h, 1, c, .12)
	}
	for y := 0; y < h; y += step {
		line(im, 0, y, w, y, 1, c, .12)
	}
}
func drawLandscape(im *image.RGBA, frame int, progress float64, s Shot, seed uint64, accent color.RGBA) {
	w, h := im.Bounds().Dx(), im.Bounds().Dy()
	z := s.Camera.Zoom
	if z <= 0 {
		z = 1
	}
	shift := int(s.Camera.Pan * float64(w) * progress)
	for i := 0; i < 42; i++ {
		r := rng(seed + uint64(i)*13)
		x := int(r % uint64(w))
		y := int((r >> 16) % uint64(h*2/3))
		disc(im, x, y, int(r%2)+1, ink, .15+.4*float64((r>>7)%10)/10)
	}
	// Layer 1 mountains (slower parallax than foreground).
	pts := []image.Point{{-w / 2, h}, {-w / 2, h * 57 / 100}, {w/7 - shift/5, h * 37 / 100}, {w/3 - shift/5, h * 61 / 100}, {w*65/100 - shift/5, h * 41 / 100}, {w + w/2, h * 64 / 100}, {w + w/2, h}}
	polygon(im, pts, color.RGBA{19, 39, 58, 255}, 1)
	pts2 := []image.Point{{0, h}, {0, h * 68 / 100}, {w/4 - shift/2, h * 57 / 100}, {w/2 - shift/2, h * 66 / 100}, {w*82/100 - shift/2, h * 53 / 100}, {w, h * 64 / 100}, {w, h}}
	polygon(im, pts2, color.RGBA{13, 30, 43, 255}, 1)
	// Layer 2 ruined buildings.
	for i := 0; i < 12; i++ {
		x := (i*w/9-shift*2/3+w*4)%(w*3) - w
		bh := h/13 + int(rng(seed+uint64(i))%uint64(h/5))
		bw := w/13 + int(rng(seed+uint64(i*11))%uint64(w/20+1))
		fillRect(im, x, h*74/100-bh, x+bw, h*74/100, color.RGBA{7, 21, 34, 255}, 1)
		for wy := h*74/100 - bh + 8; wy < h*72/100; wy += max(9, h/39) {
			for wx := x + 6; wx < x+bw-5; wx += 11 {
				if rng(uint64(wx*5+wy+int(seed)))%5 == 0 {
					fillRect(im, wx, wy, wx+3, wy+5, accent, .38)
				}
			}
		}
	}
	// Ground
	fillRect(im, 0, h*74/100, w, h, color.RGBA{6, 18, 29, 255}, 1)
	for i := 0; i < 65; i++ {
		r := rng(seed + uint64(i*25))
		x := int(r % uint64(w))
		y := h*78/100 + int((r>>10)%uint64(h/4))
		line(im, x, y, x+int((r>>20)%uint64(9))-4, y-2, 1, teal, .08)
	}
	// Walking hero with linked joints and a luminous beacon.
	x := w/2 + int(.1*float64(w)*math.Sin(progress*math.Pi*1.2))
	ground := h * 75 / 100
	bob := int(float64(h) * .006 * math.Sin(float64(frame)*.25))
	headY := ground - int(float64(h)*.19*z) + bob
	hipsY := ground - int(float64(h)*.08*z) + bob
	neckY := ground - int(float64(h)*.15*z) + bob
	swing := int(float64(w) * .035 * math.Sin(float64(frame)*.22))
	ring(im, x, headY, max(8, int(float64(w)*.035*z)), max(2, w/130), ink, 1)
	line(im, x, neckY, x, hipsY, max(2, w/130), ink, 1)
	line(im, x, neckY, x-int(float64(w)*.052), neckY+int(float64(h)*.042), max(2, w/130), ink, 1)
	line(im, x, neckY, x+int(float64(w)*.07), neckY+int(float64(h)*.048), max(2, w/130), ink, 1)
	line(im, x, hipsY, x-int(float64(w)*.045)+swing, ground, max(2, w/130), ink, 1)
	line(im, x, hipsY, x+int(float64(w)*.045)-swing, ground, max(2, w/130), ink, 1)
	// Backpack
	fillRect(im, x+int(float64(w)*.018), neckY+5, x+int(float64(w)*.058), hipsY-4, color.RGBA{92, 117, 121, 255}, 1)
	// Radio beacon/ring trail
	bx := x + int(float64(w)*.07)
	by := neckY + int(float64(h)*.048)
	disc(im, bx, by, max(3, w/115), accent, 1)
	for i := 0; i < 3; i++ {
		radius := int(float64(w) * (.035 + math.Mod(progress*3+float64(i)/3, 1)*.22))
		ring(im, bx, by, radius, 1, accent, .40*(1-float64(radius)/float64(w)))
	}
	// Rain particles (deterministically indexed)
	for i := 0; i < 85; i++ {
		r := rng(seed + uint64(i*97))
		x := int((r + uint64(frame*3)) % uint64(w))
		y := int(((r >> 22) + uint64(frame*11)) % uint64(h))
		line(im, x, y, x-3, y+max(9, h/40), 1, ink, .13)
	}
}
func drawBlueprint(im *image.RGBA, frame int, progress float64, s Shot, seed uint64, accent color.RGBA) {
	w, h := im.Bounds().Dx(), im.Bounds().Dy()
	grid(im, accent, max(20, w/12), int(progress*float64(w)/8))
	cx, cy := w/2, h*60/100
	ring(im, cx, cy, max(45, w/4), 1, accent, .5)
	ring(im, cx, cy, max(38, w/5), 1, accent, .19)
	l1, l2, l3 := float64(w)*.26, float64(w)*.22, float64(w)*.16
	a := 2.3 + math.Sin(progress*math.Pi*2)*.5
	b := -1.4 + math.Cos(progress*math.Pi*2)*.7
	c := -.6 + math.Sin(progress*math.Pi*4)*.4
	j0 := image.Pt(cx, cy+int(l1))
	j1 := image.Pt(j0.X+int(l1*math.Cos(a)), j0.Y-int(l1*math.Sin(a)))
	j2 := image.Pt(j1.X+int(l2*math.Cos(a+b)), j1.Y-int(l2*math.Sin(a+b)))
	j3 := image.Pt(j2.X+int(l3*math.Cos(a+b+c)), j2.Y-int(l3*math.Sin(a+b+c)))
	for _, pair := range [][2]image.Point{{j0, j1}, {j1, j2}, {j2, j3}} {
		line(im, pair[0].X, pair[0].Y, pair[1].X, pair[1].Y, max(4, w/55), color.RGBA{36, 111, 140, 255}, 1)
		line(im, pair[0].X, pair[0].Y, pair[1].X, pair[1].Y, max(2, w/90), ink, 1)
	}
	for i, p := range []image.Point{j0, j1, j2, j3} {
		disc(im, p.X, p.Y, max(4, w/40), dark, 1)
		ring(im, p.X, p.Y, max(4, w/40), 2, accent, 1)
		if i < 3 {
			drawText(im, p.X+8, p.Y-20, max(1, w/260), fmt.Sprintf("J%d", i), ink, 1)
		}
	}
	drawText(im, max(18, w/18), h*79/100, max(1, w/165), fmt.Sprintf("JOINT A  %3.0f DEG", a*180/math.Pi), accent, 1)
	drawText(im, max(18, w/18), h*82/100, max(1, w/165), fmt.Sprintf("JOINT B  %3.0f DEG", b*180/math.Pi), accent, 1)
}
func drawNodes(im *image.RGBA, frame int, progress float64, s Shot, seed uint64, accent color.RGBA) {
	w, h := im.Bounds().Dx(), im.Bounds().Dy()
	grid(im, accent, max(28, w/9), int(progress*float64(w)/10))
	pts := []image.Point{{w / 5, h * 43 / 100}, {w / 2, h * 31 / 100}, {w * 4 / 5, h * 45 / 100}, {w * 33 / 100, h * 61 / 100}, {w * 69 / 100, h * 67 / 100}}
	connections := [][2]int{{0, 1}, {1, 2}, {0, 3}, {1, 3}, {1, 4}, {2, 4}, {3, 4}}
	for _, e := range connections {
		p, q := pts[e[0]], pts[e[1]]
		line(im, p.X, p.Y, q.X, q.Y, 2, accent, .4)
		t := math.Mod(progress*2+float64(e[0]+e[1])*.23, 1)
		x := int(float64(p.X)*(1-t) + float64(q.X)*t)
		y := int(float64(p.Y)*(1-t) + float64(q.Y)*t)
		disc(im, x, y, max(3, w/80), amber, 1)
	}
	for i, p := range pts {
		ring(im, p.X, p.Y, max(12, w/23), 2, accent, 1)
		disc(im, p.X, p.Y, max(6, w/50), dark, 1)
		drawText(im, p.X-6, p.Y-4, max(1, w/300), fmt.Sprintf("%d", i+1), ink, 1)
	}
	drawText(im, w/12, h*77/100, max(1, w/150), "COMPOSABLE EXECUTION", accent, 1)
	drawText(im, w/12, h*80/100, max(1, w/180), "DETERMINISTIC NODES", ink, 1)
}
func drawComic(im *image.RGBA, frame int, progress float64, s Shot, seed uint64, accent color.RGBA, presentation bool) {
	w, h := im.Bounds().Dx(), im.Bounds().Dy()
	pad := max(18, w/20)
	upper := h * 24 / 100
	lower := h * 78 / 100
	fillRect(im, pad, upper, w-pad, lower, dark, .9)
	mid := w / 2
	line(im, mid, upper, mid, lower, 5, ink, 1)
	for k := 0; k < 24; k++ {
		a := 2 * math.Pi * float64(k) / 24
		cx := w / 4
		cy := (upper + lower) / 2
		r := float64(w) * (.13 + .06*math.Sin(progress*math.Pi))
		line(im, cx, cy, cx+int(r*math.Cos(a)), cy+int(r*math.Sin(a)), 1, accent, .35)
	}
	ring(im, w/4, (upper+lower)/2, w/7, 3, coral, 1)
	// Close-up silhouette vs schematic on second panel.
	x := w * 3 / 4
	head := (upper+lower)/2 - int(float64(h)*.07)
	ring(im, x, head, w/13, 4, ink, 1)
	line(im, x, head+w/13, x, (upper+lower)/2+int(float64(h)*.14), 6, ink, 1)
	for i := 0; i < 4; i++ {
		r := w/18 + i*10
		ring(im, w/4, (upper+lower)/2, r, 1, accent, .45)
	}
	if presentation {
		drawText(im, pad+8, upper+14, max(1, w/160), "SIGNAL", amber, 1)
		drawText(im, mid+8, upper+14, max(1, w/180), "REACTION", amber, 1)
	}
}
func drawInfographic(im *image.RGBA, frame int, progress float64, s Shot, seed uint64, accent color.RGBA) {
	w, h := im.Bounds().Dx(), im.Bounds().Dy()
	x := w / 12
	y := h * 34 / 100
	bw := w * 5 / 6
	for i := 0; i < 4; i++ {
		v := int(float64(bw) * (0.16 + 0.16*float64(i+1)) * progress)
		fillRect(im, x, y+i*h/12, x+bw, y+i*h/12+h/28, color.RGBA{23, 46, 62, 255}, 1)
		fillRect(im, x, y+i*h/12, x+v, y+i*h/12+h/28, []color.RGBA{teal, amber, coral, teal}[i], 1)
		drawText(im, x, y-13+i*h/12, max(1, w/230), []string{"FRAME ANALYSIS", "MOTION CURVES", "SPATIAL LAYOUT", "QA TESTS"}[i], ink, 1)
	}
	line(im, x, h*78/100, w-x, h*78/100, 2, accent, .7)
}
func DrawFrame(r Recipe, frameIndex int, presentation bool) *image.RGBA {
	w, h := r.Canvas.Width, r.Canvas.Height
	im := image.NewRGBA(image.Rect(0, 0, w, h))
	idx := frameIndex
	var shot Shot
	for _, s := range r.Shots {
		if idx < s.Frames {
			shot = s
			break
		}
		idx -= s.Frames
	}
	if shot.ID == "" {
		shot = r.Shots[len(r.Shots)-1]
		idx = shot.Frames - 1
	}
	progress := float64(idx) / float64(max(1, shot.Frames-1))
	accent := teal
	if shot.Mode == "comic" {
		accent = coral
	}
	if shot.Mode == "infographic" {
		accent = amber
	}
	if len(shot.Palette) > 0 {
		accent = cHex(shot.Palette[0], accent)
	}
	top := dark
	bottom := color.RGBA{13, 48, 65, 255}
	if shot.Mode == "blueprint" {
		bottom = color.RGBA{6, 47, 60, 255}
	}
	if shot.Mode == "comic" {
		bottom = color.RGBA{51, 26, 52, 255}
	}
	if shot.Mode == "infographic" {
		bottom = color.RGBA{40, 44, 61, 255}
	}
	gradient(im, top, bottom)
	switch shot.Mode {
	case "survival":
		drawLandscape(im, frameIndex, progress, shot, r.Seed, accent)
	case "blueprint":
		drawBlueprint(im, frameIndex, progress, shot, r.Seed, accent)
	case "nodes":
		drawNodes(im, frameIndex, progress, shot, r.Seed, accent)
	case "comic":
		drawComic(im, frameIndex, progress, shot, r.Seed, accent, presentation)
	case "infographic":
		drawInfographic(im, frameIndex, progress, shot, r.Seed, accent)
	}
	label := shot.Label
	if label == "" {
		label = fmt.Sprintf("BALTOR / %s", strings.ToUpper(shot.Mode))
	}
	if presentation {
		drawHeader(im, label, accent)
	}
	titleAnchor := shot.Layout.TitleAnchor
	if titleAnchor == "" {
		titleAnchor = "top"
	}
	captionAnchor := shot.Layout.CaptionAnchor
	if captionAnchor == "" {
		captionAnchor = "bottom"
	}
	if presentation {
		drawCaption(im, shot.Title, titleAnchor, true, shot.Layout.Padding, accent)
		drawCaption(im, shot.Caption, captionAnchor, false, shot.Layout.Padding, accent)
		drawBorder(im, shot.Layout.Border, accent)
	}
	return im
}
func WritePNG(path string, im image.Image) error {
	var b bytes.Buffer
	if err := (&png.Encoder{CompressionLevel: png.BestSpeed}).Encode(&b, im); err != nil {
		return err
	}
	return os.WriteFile(path, b.Bytes(), 0644)
}
func RenderFrames(r Recipe, root string, presentation bool) (int, error) {
	dir, err := SafePath(root, "frames")
	if err != nil {
		return 0, err
	}
	if err := os.MkdirAll(dir, 0755); err != nil {
		return 0, err
	}
	count := 0
	for _, s := range r.Shots {
		count += s.Frames
	}
	for k := 0; k < count; k++ {
		p := filepath.Join(dir, fmt.Sprintf("frame_%05d.png", k))
		if err := WritePNG(p, DrawFrame(r, k, presentation)); err != nil {
			return k, err
		}
	}
	timeline := struct {
		Schema string `json:"schema"`
		FPS    int    `json:"fps"`
		Frames int    `json:"frames"`
		Shots  []Shot `json:"shots"`
	}{"baltor.timeline/1", r.Canvas.FPS, count, r.Shots}
	b, _ := json.MarshalIndent(timeline, "", "  ")
	err = os.WriteFile(filepath.Join(root, "timeline.json"), append(b, '\n'), 0644)
	return count, err
}
