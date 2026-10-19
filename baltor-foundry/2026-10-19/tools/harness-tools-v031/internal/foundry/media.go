package foundry

import (
	"bytes"
	"context"
	"encoding/binary"
	"encoding/json"
	"errors"
	"fmt"
	"image"
	"image/png"
	"io"
	"math"
	"os"
	"os/exec"
	"path/filepath"
	"sort"
	"strconv"
	"strings"
	"time"
)

// Exec with a deliberately small environment. This is NOT a kernel/container sandbox.
func runProcess(limit time.Duration, name string, args ...string) ([]byte, error) {
	ctx, cancel := context.WithTimeout(context.Background(), limit)
	defer cancel()
	cmd := exec.CommandContext(ctx, name, args...)
	cmd.Env = []string{"PATH=/usr/bin:/bin", "LANG=C", "LC_ALL=C", "TZ=UTC", "HOME=/nonexistent"}
	var stdout, stderr bytes.Buffer
	cmd.Stdout = &stdout
	cmd.Stderr = &stderr
	if err := cmd.Run(); err != nil {
		return nil, fmt.Errorf("%s: %w: %.500s", name, err, stderr.String())
	}
	return stdout.Bytes(), nil
}
func CheckFFmpeg() error {
	_, err := exec.LookPath("ffmpeg")
	if err != nil {
		return errors.New("ffmpeg not installed in PATH")
	}
	_, err = exec.LookPath("ffprobe")
	if err != nil {
		return errors.New("ffprobe not installed in PATH")
	}
	return nil
}
func FFmpegVersion() string {
	data, err := runProcess(5*time.Second, "ffmpeg", "-version")
	if err != nil {
		return "missing"
	}
	return strings.SplitN(string(data), "\n", 2)[0]
}
func WriteAudio(r Recipe, root string) error {
	total := 0
	for _, s := range r.Shots {
		total += s.Frames
	}
	if total == 0 {
		return errors.New("no timeline for audio")
	}
	sr := 48000
	n := int(math.Round(float64(total) / float64(r.Canvas.FPS) * float64(sr)))
	if n <= 0 || n > 48000*125 {
		return errors.New("unsafe audio duration")
	}
	p, err := SafePath(root, "audio/score.wav")
	if err != nil {
		return err
	}
	if err := os.MkdirAll(filepath.Dir(p), 0755); err != nil {
		return err
	}
	f, err := os.Create(p)
	if err != nil {
		return err
	}
	defer f.Close()
	write := func(v any) error { return binary.Write(f, binary.LittleEndian, v) }
	f.Write([]byte("RIFF"))
	write(uint32(36 + n*2))
	f.Write([]byte("WAVEfmt "))
	write(uint32(16))
	write(uint16(1))
	write(uint16(1))
	write(uint32(sr))
	write(uint32(sr * 2))
	write(uint16(2))
	write(uint16(16))
	f.Write([]byte("data"))
	write(uint32(n * 2))
	shotStarts := []float64{}
	elapsed := 0
	for _, s := range r.Shots {
		shotStarts = append(shotStarts, float64(elapsed)/float64(r.Canvas.FPS))
		elapsed += s.Frames
	}
	// Fixed synthesis, no external copyrighted audio and no mutable global PRNG.
	buf := make([]byte, 8192)
	pos := 0
	flush := func() error {
		if pos == 0 {
			return nil
		}
		_, err := f.Write(buf[:pos])
		pos = 0
		return err
	}
	for i := 0; i < n; i++ {
		t := float64(i) / float64(sr)
		drone := .12*math.Sin(2*math.Pi*58*t) + .043*math.Sin(2*math.Pi*116.11*t) + .024*math.Sin(2*math.Pi*174.05*t)
		melody := .03 * math.Sin(2*math.Pi*(220+55*math.Sin(t*.7))*t)
		pulse := math.Exp(-math.Mod(t, 1.2)*12) * .035 * math.Sin(2*math.Pi*420*t)
		// Short rising signal at shot boundaries.
		for _, st := range shotStarts {
			dt := t - st
			if dt >= 0 && dt < .19 {
				pulse += .14 * math.Exp(-dt*17) * math.Sin(2*math.Pi*(580+200*dt)*dt)
			}
		}
		hiss := (unit(r.Seed+uint64(i)*91)*2 - 1) * .016
		val := (drone + melody + pulse + hiss) * (.6 + .12*math.Sin(t*.29))
		if val > 1 {
			val = 1
		}
		if val < -1 {
			val = -1
		}
		v := int16(val * 32767)
		binary.LittleEndian.PutUint16(buf[pos:pos+2], uint16(v))
		pos += 2
		if pos == len(buf) {
			if err := flush(); err != nil {
				return err
			}
		}
	}
	return flush()
}
func EncodeVideo(r Recipe, root, source string) error {
	if err := CheckFFmpeg(); err != nil {
		return err
	}
	out, err := SafePath(root, "media/video.mp4")
	if err != nil {
		return err
	}
	if err = os.MkdirAll(filepath.Dir(out), 0755); err != nil {
		return err
	}
	if _, err := FrameSourceFiles(root, source); err != nil {
		return err
	}
	frames, err := SafePath(root, source+"/frame_%05d.png")
	if err != nil {
		return err
	}
	audio, err := SafePath(root, "audio/score.wav")
	if err != nil {
		return err
	}
	hasAudio := false
	if _, err := os.Stat(audio); err == nil {
		hasAudio = true
	}
	args := []string{"-hide_banner", "-loglevel", "error", "-nostdin", "-y", "-framerate", strconv.Itoa(r.Canvas.FPS), "-start_number", "0", "-i", frames}
	if hasAudio {
		args = append(args, "-i", audio)
	}
	args = append(args, "-map", "0:v:0")
	if hasAudio {
		args = append(args, "-map", "1:a:0")
	}
	args = append(args, "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "medium", "-crf", "21", "-threads", "1", "-flags:v", "+bitexact", "-fflags", "+bitexact", "-x264-params", "threads=1:lookahead-threads=1:scenecut=0", "-r", strconv.Itoa(r.Canvas.FPS))
	if hasAudio {
		args = append(args, "-c:a", "aac", "-b:a", "128k", "-ar", "48000", "-ac", "1", "-shortest")
	}
	args = append(args, "-map_metadata", "-1", "-metadata", "creation_time=1970-01-01T00:00:00Z", "-movflags", "+faststart", out)
	_, err = runProcess(5*time.Minute, "ffmpeg", args...)
	return err
}
func ProbeVideo(path string) (map[string]any, error) {
	if err := CheckFFmpeg(); err != nil {
		return nil, err
	}
	raw, err := runProcess(15*time.Second, "ffprobe", "-v", "error", "-protocol_whitelist", "file,pipe", "-show_entries", "format=duration:stream=index,codec_type,codec_name,width,height,r_frame_rate,nb_frames,sample_rate,channels", "-of", "json", path)
	if err != nil {
		return nil, err
	}
	var obj map[string]any
	if err := json.Unmarshal(raw, &obj); err != nil {
		return nil, err
	}
	return obj, nil
}
func SampleVideo(workspace, root string, n Node) error {
	if err := CheckFFmpeg(); err != nil {
		return err
	}
	rel, err := ParamString(n, "input", "")
	if err != nil {
		return err
	}
	if !strings.HasPrefix(rel, "inputs/") {
		return errors.New("video.sample input must be staged below inputs/")
	}
	path, err := SafePath(workspace, rel)
	if err != nil {
		return err
	}
	if fi, err := os.Stat(path); err != nil || fi.Size() > 500_000_000 {
		return errors.New("input not present or exceeds 500MB")
	}
	every, err := ParamInt(n, "every", 12)
	if err != nil {
		return err
	}
	if every < 1 || every > 600 {
		return errors.New("every must be 1..600")
	}
	maxFrames, err := ParamInt(n, "max_frames", 24)
	if err != nil {
		return err
	}
	if maxFrames < 1 || maxFrames > 90 {
		return errors.New("max_frames must be 1..90")
	}
	sampled, err := SafePath(root, "sampled/frame_%05d.png")
	if err != nil {
		return err
	}
	os.MkdirAll(filepath.Dir(sampled), 0755)
	// fixed filter construction from validated integers only; no shell execution.
	vf := fmt.Sprintf("select=not(mod(n\\,%d)),scale='min(360,iw)':-2", every)
	_, err = runProcess(2*time.Minute, "ffmpeg", "-hide_banner", "-loglevel", "error", "-nostdin", "-y", "-protocol_whitelist", "file,pipe", "-i", path, "-vf", vf, "-fps_mode", "vfr", "-frames:v", strconv.Itoa(maxFrames), "-start_number", "0", sampled)
	return err
}
func FrameFiles(root, sub string) ([]string, error) {
	if sub != "frames" && sub != "sampled" {
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
		return nil, errors.New("too many input frames")
	}
	return files, nil
}
func ContactSheet(root, sub string) error {
	files, err := FrameSourceFiles(root, sub)
	if err != nil {
		return err
	}
	sampleN := min(12, len(files))
	cols := 3
	rows := (sampleN + cols - 1) / cols
	thumbW, thumbH := 190, 338
	im := image.NewRGBA(image.Rect(0, 0, cols*thumbW, rows*(thumbH+30)))
	fillRect(im, 0, 0, im.Bounds().Dx(), im.Bounds().Dy(), dark, 1)
	for j := 0; j < sampleN; j++ {
		ix := 0
		if sampleN > 1 {
			ix = int(math.Round(float64(j) * float64(len(files)-1) / float64(sampleN-1)))
		}
		f, err := os.Open(files[ix])
		if err != nil {
			return err
		}
		src, err := png.Decode(f)
		f.Close()
		if err != nil {
			return err
		}
		w, h := src.Bounds().Dx(), src.Bounds().Dy()
		cx := j % cols * thumbW
		cy := j / cols * (thumbH + 30)
		for y := 0; y < thumbH; y++ {
			for x := 0; x < thumbW; x++ {
				sx := min(w-1, x*w/thumbW)
				sy := min(h-1, y*h/thumbH)
				im.Set(cx+x, cy+y, src.At(sx, sy))
			}
		}
		drawText(im, cx+7, cy+thumbH+10, 2, fmt.Sprintf("FRAME %05d", ix), teal, 1)
	}
	p, _ := SafePath(root, "analysis/contact_sheet.png")
	os.MkdirAll(filepath.Dir(p), 0755)
	return WritePNG(p, im)
}
func ReadImage(path string) (image.Image, error) {
	f, err := os.Open(path)
	if err != nil {
		return nil, err
	}
	defer f.Close()
	return png.Decode(f)
}
func FrameMetric(img image.Image) ([3]float64, [256]float64) {
	b := img.Bounds()
	w, h := b.Dx(), b.Dy()
	var grid16 [256]float64
	brightness := 0.0
	edge := 0.0
	for y := 0; y < 16; y++ {
		for x := 0; x < 16; x++ {
			px := b.Min.X + min(w-1, int((float64(x)+.5)*float64(w)/16))
			py := b.Min.Y + min(h-1, int((float64(y)+.5)*float64(h)/16))
			r, g, bb, _ := img.At(px, py).RGBA()
			v := (.2126*float64(r) + .7152*float64(g) + .0722*float64(bb)) / 65535
			grid16[y*16+x] = v
			brightness += v
			if x > 0 {
				edge += math.Abs(v - grid16[y*16+x-1])
			}
			if y > 0 {
				edge += math.Abs(v - grid16[(y-1)*16+x])
			}
		}
	}
	return [3]float64{brightness / 256, edge / (16 * 16 * 2), 0}, grid16
}
func AnalyzeFrames(root, sub string) error {
	files, err := FrameSourceFiles(root, sub)
	if err != nil {
		return err
	}
	out, _ := SafePath(root, "analysis/frame_metrics.csv")
	os.MkdirAll(filepath.Dir(out), 0755)
	f, err := os.Create(out)
	if err != nil {
		return err
	}
	defer f.Close()
	fmt.Fprintln(f, "frame,mean_luma,mean_edge,frame_delta,possible_cut,near_black")
	var prev [256]float64
	sumMotion := 0.0
	cuts, black := 0, 0
	for i, p := range files {
		im, err := ReadImage(p)
		if err != nil {
			return err
		}
		m, g := FrameMetric(im)
		delta := 0.0
		if i > 0 {
			for j := 0; j < 256; j++ {
				delta += math.Abs(g[j] - prev[j])
			}
			delta /= 256
		}
		cut := i > 0 && delta > .055
		nearBlack := m[0] < .025
		if cut {
			cuts++
		}
		if nearBlack {
			black++
		}
		sumMotion += delta
		fmt.Fprintf(f, "%d,%.6f,%.6f,%.6f,%t,%t\n", i, m[0], m[1], delta, cut, nearBlack)
		prev = g
	}
	report := map[string]any{"schema": "baltor.frame_metrics/1", "source": sub, "frame_count": len(files), "mean_frame_delta": math.Round(sumMotion/float64(len(files))*1e8) / 1e8, "candidate_cut_count": cuts, "near_black_frames": black, "limitations": "16x16 luma sampling; cut detection is a heuristic, not shot or camera reconstruction"}
	b, _ := json.MarshalIndent(report, "", "  ")
	path, _ := SafePath(root, "analysis/frame_report.json")
	return os.WriteFile(path, append(b, '\n'), 0644)
}
func LintLayout(workspace, root string, n Node) error {
	rel, err := ParamString(n, "input", "")
	if err != nil {
		return err
	}
	if !strings.HasPrefix(rel, "inputs/") {
		return errors.New("layout input must be staged below inputs/")
	}
	path, err := SafePath(workspace, rel)
	if err != nil {
		return err
	}
	b, err := os.ReadFile(path)
	if err != nil {
		return err
	}
	var data map[string]any
	if err := json.Unmarshal(b, &data); err != nil {
		return err
	}
	layouts, ok := data["layouts"].(map[string]any)
	if !ok {
		return errors.New("layouts object missing")
	}
	issues := []string{}
	elems := 0
	for name, value := range layouts {
		layout, ok := value.(map[string]any)
		if !ok {
			issues = append(issues, fmt.Sprintf("%s must be an object", name))
			continue
		}
		arr, ok := layout["elements"].([]any)
		if !ok {
			issues = append(issues, fmt.Sprintf("%s elements missing", name))
			continue
		}
		for _, v := range arr {
			e, ok := v.(map[string]any)
			if !ok {
				issues = append(issues, "nonobject element")
				continue
			}
			elems++
			id, _ := e["id"].(string)
			box, ok := e["box"].(map[string]any)
			if !ok {
				issues = append(issues, name+":"+id+": missing box")
				continue
			}
			for _, k := range []string{"dx", "dy", "w", "h"} {
				if num, ok := box[k].(float64); ok && (math.IsNaN(num) || num < -1 || num > 3) {
					issues = append(issues, name+":"+id+":"+k+" outside -1..3")
				}
			}
			if padding, ok := e["padding"].([]any); ok {
				if len(padding) != 4 {
					issues = append(issues, name+":"+id+": padding is not 4-edge")
				}
			}
		}
	}
	report := map[string]any{"schema": "baltor.layout_lint/1", "layouts": len(layouts), "elements": elems, "issues": issues, "note": "Syntactic spatial lint, not subject-aware clearance or visual inspection"}
	p, _ := SafePath(root, "analysis/layout_lint.json")
	os.MkdirAll(filepath.Dir(p), 0755)
	obj, _ := json.MarshalIndent(report, "", "  ")
	return os.WriteFile(p, append(obj, '\n'), 0644)
}
func EnsureFile(path string) error {
	f, err := os.Open(path)
	if err != nil {
		return err
	}
	defer f.Close()
	_, err = io.Copy(io.Discard, io.LimitReader(f, 1))
	return err
}
