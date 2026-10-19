package foundry

import (
	"encoding/json"
	"errors"
	"fmt"
	"image"
	"image/color"
	"math"
	"os"
	"path/filepath"
	"sort"
	"strings"
)

func allowedFrameSource(s string) bool {
	if s == "frames" || s == "sampled" {
		return true
	}
	return strings.HasPrefix(s, "stages/") && safeName(strings.TrimPrefix(s, "stages/"))
}
func FrameSourceFiles(root, sub string) ([]string, error) {
	if !allowedFrameSource(sub) {
		return nil, fmt.Errorf("frame source %q not allowlisted", sub)
	}
	dir, err := SafePath(root, sub)
	if err != nil {
		return nil, err
	}
	files, err := filepath.Glob(filepath.Join(dir, "frame_*.png"))
	if err != nil {
		return nil, err
	}
	sort.Strings(files)
	if len(files) == 0 {
		return nil, fmt.Errorf("no frame files in %s", sub)
	}
	if len(files) > 1800 {
		return nil, errors.New("too many source frames")
	}
	for _, f := range files {
		rel, _ := filepath.Rel(root, f)
		if _, err := SafePath(root, rel); err != nil {
			return nil, err
		}
	}
	return files, nil
}
func ParamFloat(n Node, key string, def float64) (float64, error) {
	raw, ok := n.Params[key]
	if !ok {
		return def, nil
	}
	var v float64
	if err := json.Unmarshal(raw, &v); err != nil {
		return 0, fmt.Errorf("%s must be numeric", key)
	}
	if math.IsNaN(v) || math.IsInf(v, 0) {
		return 0, errors.New("nonfinite float not supported")
	}
	return v, nil
}
func bilinear(img image.Image, x, y float64) color.RGBA {
	b := img.Bounds()
	w, h := b.Dx(), b.Dy()
	if x < 0 || y < 0 || x >= float64(w-1) || y >= float64(h-1) {
		return dark
	}
	x0, y0 := int(x), int(y)
	u, v := x-float64(x0), y-float64(y0)
	a := color.RGBAModel.Convert(img.At(x0, y0)).(color.RGBA)
	bb := color.RGBAModel.Convert(img.At(x0+1, y0)).(color.RGBA)
	c := color.RGBAModel.Convert(img.At(x0, y0+1)).(color.RGBA)
	d := color.RGBAModel.Convert(img.At(x0+1, y0+1)).(color.RGBA)
	mix := func(a, b, c, d uint8) uint8 {
		return uint8(float64(a)*(1-u)*(1-v) + float64(b)*u*(1-v) + float64(c)*(1-u)*v + float64(d)*u*v + .5)
	}
	return color.RGBA{mix(a.R, bb.R, c.R, d.R), mix(a.G, bb.G, c.G, d.G), mix(a.B, bb.B, c.B, d.B), 255}
}
func TransformFrames(root string, n Node) error {
	sub, err := ParamString(n, "from", "frames")
	if err != nil {
		return err
	}
	files, err := FrameSourceFiles(root, sub)
	if err != nil {
		return err
	}
	zoom0, err := ParamFloat(n, "zoom_start", 1)
	if err != nil {
		return err
	}
	zoom1, err := ParamFloat(n, "zoom_end", 1)
	if err != nil {
		return err
	}
	panx, err := ParamFloat(n, "pan_x", 0)
	if err != nil {
		return err
	}
	pany, err := ParamFloat(n, "pan_y", 0)
	if err != nil {
		return err
	}
	contrast, err := ParamFloat(n, "contrast", 1)
	if err != nil {
		return err
	}
	saturation, err := ParamFloat(n, "saturation", 1)
	if err != nil {
		return err
	}
	if zoom0 < .6 || zoom0 > 2.5 || zoom1 < .6 || zoom1 > 2.5 || math.Abs(panx) > .3 || math.Abs(pany) > .3 || contrast < .5 || contrast > 1.6 || saturation < 0 || saturation > 2.5 {
		return errors.New("frame transform setting outside bounds")
	}
	dest, err := SafePath(root, "stages/"+n.ID)
	if err != nil {
		return err
	}
	os.MkdirAll(dest, 0755)
	for k, path := range files {
		src, err := ReadImage(path)
		if err != nil {
			return err
		}
		w, h := src.Bounds().Dx(), src.Bounds().Dy()
		im := image.NewRGBA(image.Rect(0, 0, w, h))
		f := float64(k) / float64(max(1, len(files)-1))
		// smoothstep deterministic ease for virtual-camera transform
		ease := f * f * (3 - 2*f)
		z := zoom0 + (zoom1-zoom0)*ease
		dx := panx * float64(w) * ease
		dy := pany * float64(h) * ease
		for y := 0; y < h; y++ {
			for x := 0; x < w; x++ {
				sx := (float64(x)-float64(w)/2)/z + float64(w)/2 - dx
				sy := (float64(y)-float64(h)/2)/z + float64(h)/2 - dy
				c := bilinear(src, sx, sy)
				brightness := .2126*float64(c.R) + .7152*float64(c.G) + .0722*float64(c.B)
				apply := func(v float64) uint8 {
					v = ((brightness+(v-brightness)*saturation)-127.5)*contrast + 127.5
					if v < 0 {
						v = 0
					}
					if v > 255 {
						v = 255
					}
					return uint8(v + .5)
				}
				im.SetRGBA(x, y, color.RGBA{apply(float64(c.R)), apply(float64(c.G)), apply(float64(c.B)), 255})
			}
		}
		if err := WritePNG(filepath.Join(dest, fmt.Sprintf("frame_%05d.png", k)), im); err != nil {
			return err
		}
	}
	return nil
}

type OverlayElement struct {
	ID         string  `json:"id"`
	Kind       string  `json:"kind"`
	Text       string  `json:"text,omitempty"`
	X          float64 `json:"x"`
	Y          float64 `json:"y"`
	W          float64 `json:"w"`
	H          float64 `json:"h"`
	Anchor     string  `json:"anchor"`
	Padding    []int   `json:"padding,omitempty"`
	Color      string  `json:"color,omitempty"`
	Fill       string  `json:"fill,omitempty"`
	Opacity    float64 `json:"opacity"`
	Z          int     `json:"z"`
	StartFrame int     `json:"start_frame"`
	EndFrame   int     `json:"end_frame"`
	Value      float64 `json:"value"`
	Scale      int     `json:"scale"`
}

func overlayBox(e OverlayElement, w, h int) (int, int, int, int) {
	bw := int(e.W * float64(w))
	bh := int(e.H * float64(h))
	x := int(e.X * float64(w))
	y := int(e.Y * float64(h))
	switch e.Anchor {
	case "top_right":
		x -= bw
	case "bottom_left":
		y -= bh
	case "bottom_right":
		x -= bw
		y -= bh
	case "middle":
		x -= bw / 2
		y -= bh / 2
	case "top_center":
		x -= bw / 2
	case "bottom_center":
		x -= bw / 2
		y -= bh
	case "middle_left":
		y -= bh / 2
	case "middle_right":
		x -= bw
		y -= bh / 2
	}
	return x, y, x + bw, y + bh
}
func ParseElements(n Node) ([]OverlayElement, error) {
	raw, ok := n.Params["elements"]
	if !ok {
		return nil, errors.New("frames.overlay requires elements array")
	}
	var out []OverlayElement
	if err := json.Unmarshal(raw, &out); err != nil {
		return nil, err
	}
	if len(out) == 0 || len(out) > 40 {
		return nil, errors.New("elements must be 1..40")
	}
	ids := map[string]bool{}
	for _, e := range out {
		if !safeName(e.ID) || ids[e.ID] {
			return nil, fmt.Errorf("duplicate/invalid overlay id %s", e.ID)
		}
		ids[e.ID] = true
		switch e.Kind {
		case "text", "pill", "rect", "line", "progress", "reticle", "border":
		default:
			return nil, fmt.Errorf("invalid overlay kind %q", e.Kind)
		}
		if len(e.Text) > 150 {
			return nil, errors.New("overlay text over 150 characters")
		}
		if e.W <= 0 || e.H <= 0 || e.W > 1 || e.H > 1 || e.X < -.1 || e.X > 1.1 || e.Y < -.1 || e.Y > 1.1 {
			return nil, fmt.Errorf("invalid overlay geometry %s", e.ID)
		}
		if e.Opacity < 0 || e.Opacity > 1 || e.Scale < 0 || e.Scale > 8 {
			return nil, fmt.Errorf("invalid overlay styling %s", e.ID)
		}
		if e.EndFrame < 0 || e.StartFrame < 0 || e.StartFrame > 1800 || e.EndFrame > 1800 {
			return nil, errors.New("overlay timing out of range")
		}
		if len(e.Padding) != 0 && len(e.Padding) != 4 {
			return nil, errors.New("overlay padding must have four edges")
		}
		for _, p := range e.Padding {
			if p < 0 || p > 150 {
				return nil, errors.New("overlay padding out of range")
			}
		}
	}
	sort.SliceStable(out, func(i, j int) bool {
		if out[i].Z == out[j].Z {
			return out[i].ID < out[j].ID
		}
		return out[i].Z < out[j].Z
	})
	return out, nil
}
func OverlayFrames(root string, n Node) error {
	source, err := ParamString(n, "from", "frames")
	if err != nil {
		return err
	}
	files, err := FrameSourceFiles(root, source)
	if err != nil {
		return err
	}
	elements, err := ParseElements(n)
	if err != nil {
		return err
	}
	dest, err := SafePath(root, "stages/"+n.ID)
	if err != nil {
		return err
	}
	os.MkdirAll(dest, 0755)
	for k, p := range files {
		src, err := ReadImage(p)
		if err != nil {
			return err
		}
		w, h := src.Bounds().Dx(), src.Bounds().Dy()
		im := image.NewRGBA(image.Rect(0, 0, w, h))
		for y := 0; y < h; y++ {
			for x := 0; x < w; x++ {
				im.Set(x, y, src.At(x, y))
			}
		}
		for _, e := range elements {
			if k < e.StartFrame || e.EndFrame > 0 && k >= e.EndFrame {
				continue
			}
			x0, y0, x1, y1 := overlayBox(e, w, h)
			accent := cHex(e.Color, teal)
			fill := cHex(e.Fill, dark)
			alpha := e.Opacity
			if alpha == 0 {
				alpha = 1
			}
			pad := e.Padding
			if len(pad) != 4 {
				pad = []int{4, 6, 4, 6}
			}
			switch e.Kind {
			case "border":
				drawBorder(im, max(1, e.Scale), accent)
			case "rect":
				fillRect(im, x0, y0, x1, y1, fill, alpha)
			case "line":
				line(im, x0, y0, x1, y1, max(1, e.Scale), accent, alpha)
			case "reticle":
				ring(im, (x0+x1)/2, (y0+y1)/2, max(2, min(x1-x0, y1-y0)/2), max(1, e.Scale), accent, alpha)
				line(im, (x0+x1)/2-12, (y0+y1)/2, (x0+x1)/2+12, (y0+y1)/2, 1, accent, alpha)
			case "progress":
				fillRect(im, x0, y0, x1, y1, fill, .82)
				pct := e.Value
				if pct <= 0 {
					pct = float64(k) / float64(max(1, len(files)-1))
				}
				pct = math.Max(0, math.Min(1, pct))
				fillRect(im, x0, y0, x0+int(pct*float64(x1-x0)), y1, accent, alpha)
			case "pill", "text":
				if e.Kind == "pill" {
					fillRect(im, x0, y0, x1, y1, fill, .85*alpha)
					fillRect(im, x0, y0, x0+max(2, w/130), y1, accent, alpha)
				}
				scale := e.Scale
				if scale < 1 {
					scale = max(1, w/210)
				}
				avail := max(3, (x1-x0-pad[1]-pad[3])/(6*scale))
				lines := wrap(e.Text, avail)
				maxLines := max(1, (y1-y0-pad[0]-pad[2])/(9*scale))
				if len(lines) > maxLines {
					lines = lines[:maxLines]
				}
				for j, s := range lines {
					drawText(im, x0+pad[3], y0+pad[0]+j*9*scale, scale, s, accent, alpha)
				}
			}
		}
		if err := WritePNG(filepath.Join(dest, fmt.Sprintf("frame_%05d.png", k)), im); err != nil {
			return err
		}
	}
	return nil
}
func SpatialScore(root, sub string) error {
	files, err := FrameSourceFiles(root, sub)
	if err != nil {
		return err
	}
	sumEdge := [9]float64{}
	sumMotion := [9]float64{}
	samples := 0
	var prev [9][36]float64
	stride := max(1, len(files)/120)
	for i := 0; i < len(files); i += stride {
		img, err := ReadImage(files[i])
		if err != nil {
			return err
		}
		b := img.Bounds()
		w, h := b.Dx(), b.Dy()
		for cell := 0; cell < 9; cell++ {
			cx, cy := cell%3, cell/3
			var points [36]float64
			for yy := 0; yy < 6; yy++ {
				for xx := 0; xx < 6; xx++ {
					px := b.Min.X + min(w-1, int((float64(cx)+float64(xx)/6+.08)/3*float64(w)))
					py := b.Min.Y + min(h-1, int((float64(cy)+float64(yy)/6+.08)/3*float64(h)))
					cr, cg, cb, _ := img.At(px, py).RGBA()
					v := (.2126*float64(cr) + .7152*float64(cg) + .0722*float64(cb)) / 65535
					j := yy*6 + xx
					points[j] = v
					if xx > 0 {
						sumEdge[cell] += math.Abs(v - points[j-1])
					}
					if yy > 0 {
						sumEdge[cell] += math.Abs(v - points[j-6])
					}
					if samples > 0 {
						sumMotion[cell] += math.Abs(v - prev[cell][j])
					}
				}
			}
			prev[cell] = points
		}
		samples++
	}
	type ScoredCell struct {
		Cell   string  `json:"cell"`
		Edge   float64 `json:"edge"`
		Motion float64 `json:"motion"`
		Score  float64 `json:"quiet_score"`
		Rank   int     `json:"rank"`
	}
	cells := []ScoredCell{}
	names := []string{"top_left", "top_middle", "top_right", "middle_left", "middle", "middle_right", "bottom_left", "bottom_middle", "bottom_right"}
	for i := 0; i < 9; i++ {
		edge := sumEdge[i] / float64(max(1, samples*60))
		motion := sumMotion[i] / float64(max(1, (samples-1)*36))
		cells = append(cells, ScoredCell{Cell: names[i], Edge: edge, Motion: motion, Score: 1 / (1 + edge*9 + motion*12)})
	}
	sort.SliceStable(cells, func(i, j int) bool { return cells[i].Score > cells[j].Score })
	for i := range cells {
		cells[i].Rank = i + 1
	}
	report := map[string]any{"schema": "baltor.spatial_score/1", "source": sub, "sampled_frames": samples, "cells_by_quietness": cells, "limitations": "Color/edge and temporal activity only. It cannot identify faces, silhouettes, semantic text or platform UI occlusion."}
	out, _ := SafePath(root, "analysis/spatial_score.json")
	os.MkdirAll(filepath.Dir(out), 0755)
	b, _ := json.MarshalIndent(report, "", "  ")
	return os.WriteFile(out, append(b, '\n'), 0644)
}
func CompileTimeline(r Recipe, root string) error {
	p, err := SafePath(root, "analysis/timeline.csv")
	if err != nil {
		return err
	}
	os.MkdirAll(filepath.Dir(p), 0755)
	f, err := os.Create(p)
	if err != nil {
		return err
	}
	defer f.Close()
	fmt.Fprintln(f, "shot,mode,start_frame,end_frame_exclusive,start_seconds,end_seconds,title_anchor,caption_anchor,border_px")
	current := 0
	for _, shot := range r.Shots {
		fmt.Fprintf(f, "%s,%s,%d,%d,%.6f,%.6f,%s,%s,%d\n", shot.ID, shot.Mode, current, current+shot.Frames, float64(current)/float64(r.Canvas.FPS), float64(current+shot.Frames)/float64(r.Canvas.FPS), shot.Layout.TitleAnchor, shot.Layout.CaptionAnchor, shot.Layout.Border)
		current += shot.Frames
	}
	return nil
}
