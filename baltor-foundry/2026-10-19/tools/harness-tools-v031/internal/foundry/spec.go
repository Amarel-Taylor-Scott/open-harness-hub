package foundry

import (
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"errors"
	"fmt"
	"os"
	"path/filepath"
	"sort"
	"strings"
)

const Version = "0.3.1"
const Schema = "baltor.harness/1"

// Deliberately a closed set. Model-authored recipes are data, not executable code.
var SupportedOps = map[string]string{
	"scene.frames":     "Render a layered, deterministic procedural animation from an authored shot timeline",
	"audio.synth":      "Produce a deterministic original PCM soundtrack",
	"frames.metrics":   "Measure per-frame average brightness and consecutive-frame pixel change",
	"frames.contact":   "Generate an image contact sheet from rendered or sampled frames",
	"video.encode":     "Encode images and PCM to MP4 using a fixed ffmpeg argument template",
	"video.probe":      "Inspect encoded or ingested video streams with ffprobe",
	"video.sample":     "Sample frames from an ingested authorized MP4 using ffmpeg",
	"layout.lint":      "Validate placement/padding fields in an imported v0.2 layout JSON",
	"frames.transform": "Apply normalized Ken Burns transforms and deterministic color grading to a frame stage",
	"frames.overlay":   "Composite JSON-defined text, panels, progress, lines and reticles onto frames",
	"frames.spatial":   "Score nine caption-placement regions using pixel activity and motion heuristics",
	"timeline.compile": "Compile deterministic shot/frame timing to CSV",
	"artifact.hash":    "Write an SHA-256 report for a workspace-relative output or input",
}

type Node struct {
	ID     string                     `json:"id"`
	Op     string                     `json:"op"`
	Deps   []string                   `json:"deps"`
	Params map[string]json.RawMessage `json:"params,omitempty"`
}
type Camera struct {
	Pan   float64 `json:"pan"`
	Zoom  float64 `json:"zoom"`
	Shake float64 `json:"shake"`
}
type Layout struct {
	TitleAnchor   string `json:"title_anchor"`
	CaptionAnchor string `json:"caption_anchor"`
	Padding       []int  `json:"padding"`
	Border        int    `json:"border"`
	Panels        int    `json:"panels"`
	HUD           string `json:"hud"`
}
type Shot struct {
	ID      string   `json:"id"`
	Frames  int      `json:"frames"`
	Mode    string   `json:"mode"`
	Title   string   `json:"title"`
	Caption string   `json:"caption"`
	Label   string   `json:"label"`
	Camera  Camera   `json:"camera"`
	Layout  Layout   `json:"layout"`
	Palette []string `json:"palette,omitempty"`
}
type Canvas struct {
	Width  int `json:"width"`
	Height int `json:"height"`
	FPS    int `json:"fps"`
}
type Recipe struct {
	Schema string `json:"schema"`
	Name   string `json:"name"`
	Seed   uint64 `json:"seed"`
	Canvas Canvas `json:"canvas"`
	Shots  []Shot `json:"shots,omitempty"`
	Nodes  []Node `json:"nodes"`
}

func ReadRecipe(filename string) (Recipe, []byte, error) {
	data, err := os.ReadFile(filename)
	if err != nil {
		return Recipe{}, nil, err
	}
	var r Recipe
	if err = json.Unmarshal(data, &r); err != nil {
		return r, nil, fmt.Errorf("invalid JSON: %w", err)
	}
	if err = Validate(r); err != nil {
		return r, nil, err
	}
	norm, err := json.Marshal(r)
	return r, norm, err
}
func Validate(r Recipe) error {
	if r.Schema != Schema {
		return fmt.Errorf("schema must be %s", Schema)
	}
	if !safeName(r.Name) {
		return fmt.Errorf("unsafe or empty recipe name: %q", r.Name)
	}
	if len(r.Nodes) == 0 || len(r.Nodes) > 48 {
		return errors.New("node count must be 1..48")
	}
	if r.Canvas.Width < 0 || r.Canvas.Height < 0 || r.Canvas.FPS < 0 {
		return errors.New("negative canvas setting")
	}
	needsCanvas := false
	ids := map[string]bool{}
	singleton := map[string]bool{}
	for _, n := range r.Nodes {
		if !safeName(n.ID) {
			return fmt.Errorf("invalid node id %q", n.ID)
		}
		if ids[n.ID] {
			return fmt.Errorf("duplicate node %s", n.ID)
		}
		ids[n.ID] = true
		if _, ok := SupportedOps[n.Op]; !ok {
			return fmt.Errorf("operator %q is not allowlisted", n.Op)
		}
		if n.Op == "scene.frames" || n.Op == "audio.synth" || n.Op == "timeline.compile" {
			needsCanvas = true
		}
		// Operations writing to a fixed output may appear only once per DAG.
		switch n.Op {
		case "scene.frames", "audio.synth", "frames.metrics", "frames.contact", "frames.spatial", "video.encode", "video.probe", "video.sample", "layout.lint", "artifact.hash", "timeline.compile":
			if singleton[n.Op] {
				return fmt.Errorf("duplicate singleton operator %s", n.Op)
			}
			singleton[n.Op] = true
		}
		if len(n.Params) > 20 {
			return fmt.Errorf("too many params in node %s", n.ID)
		}
		allowed := map[string][]string{
			"scene.frames": {"presentation"}, "audio.synth": {},
			"frames.transform": {"from", "zoom_start", "zoom_end", "pan_x", "pan_y", "contrast", "saturation"},
			"frames.overlay":   {"from", "elements"}, "frames.metrics": {"from"}, "frames.contact": {"from"}, "frames.spatial": {"from"},
			"video.encode": {"from"}, "video.probe": {"input"}, "video.sample": {"input", "every", "max_frames"},
			"layout.lint": {"input"}, "artifact.hash": {"source"}, "timeline.compile": {},
		}
		for k := range n.Params {
			found := false
			for _, valid := range allowed[n.Op] {
				if k == valid {
					found = true
					break
				}
			}
			if !found {
				return fmt.Errorf("operator %s disallows parameter %q", n.Op, k)
			}
		}
		for k, v := range n.Params {
			if !safeName(k) {
				return fmt.Errorf("invalid param %s", k)
			}
			var unused any
			if err := json.Unmarshal(v, &unused); err != nil {
				return err
			}
		}
	}
	if needsCanvas {
		c := r.Canvas
		if c.Width < 160 || c.Width > 1080 || c.Height < 160 || c.Height > 1920 || c.FPS < 1 || c.FPS > 60 || int64(c.Width)*int64(c.Height)*int64(c.FPS) > 50_000_000 {
			return errors.New("canvas exceeds safety limits")
		}
		if len(r.Shots) == 0 || len(r.Shots) > 80 {
			return errors.New("scene.frames needs 1..80 shots")
		}
		frames := 0
		for _, s := range r.Shots {
			if !safeName(s.ID) {
				return fmt.Errorf("invalid shot id %s", s.ID)
			}
			if s.Frames < 1 {
				return fmt.Errorf("shot %s has no frames", s.ID)
			}
			frames += s.Frames
			switch s.Mode {
			case "survival", "blueprint", "nodes", "comic", "infographic":
			default:
				return fmt.Errorf("invalid scene mode %q", s.Mode)
			}
			if len(s.Title) > 110 || len(s.Caption) > 160 || len(s.Label) > 70 {
				return fmt.Errorf("oversized text in shot %s", s.ID)
			}
			if s.Camera.Zoom < 0.7 || s.Camera.Zoom > 2.5 || s.Camera.Pan < -3 || s.Camera.Pan > 3 || s.Camera.Shake < 0 || s.Camera.Shake > 2 {
				return fmt.Errorf("camera bounds in shot %s", s.ID)
			}
			for _, a := range []string{s.Layout.TitleAnchor, s.Layout.CaptionAnchor} {
				if a != "" && a != "top" && a != "middle" && a != "bottom" {
					return fmt.Errorf("invalid text anchor %q", a)
				}
			}
			if s.Layout.Border < 0 || s.Layout.Border > 25 || s.Layout.Panels < 0 || s.Layout.Panels > 4 {
				return fmt.Errorf("invalid frame/panel settings in %s", s.ID)
			}
			if len(s.Layout.Padding) != 0 && len(s.Layout.Padding) != 4 {
				return errors.New("layout.padding must be [top,right,bottom,left]")
			}
			for _, p := range s.Layout.Padding {
				if p < 0 || p > 150 {
					return errors.New("padding must be 0..150 pixels")
				}
			}
			if len(s.Palette) > 4 {
				return errors.New("palette too long")
			}
		}
		if frames > 1800 {
			return errors.New("recipe may produce at most 1800 frames")
		}
		if int64(c.Width)*int64(c.Height)*int64(frames) > 300_000_000 {
			return errors.New("recipe exceeds 300-million pixel processing budget")
		}
	}
	for _, n := range r.Nodes {
		raw, ok := n.Params["from"]
		if !ok {
			continue
		}
		var source string
		if err := json.Unmarshal(raw, &source); err != nil {
			return fmt.Errorf("from must be string for %s", n.ID)
		}
		if strings.HasPrefix(source, "stages/") {
			id := strings.TrimPrefix(source, "stages/")
			found := false
			for _, dep := range n.Deps {
				if dep == id {
					found = true
				}
			}
			if !found {
				return fmt.Errorf("%s reads stage %s without declaring dependency", n.ID, id)
			}
		}
	}
	_, err := Topological(r)
	return err
}
func safeName(s string) bool {
	if len(s) == 0 || len(s) > 64 {
		return false
	}
	for _, c := range s {
		if !(c >= 'a' && c <= 'z' || c >= 'A' && c <= 'Z' || c >= '0' && c <= '9' || c == '_' || c == '-') {
			return false
		}
	}
	return true
}
func Topological(r Recipe) ([]Node, error) {
	by := map[string]Node{}
	for _, n := range r.Nodes {
		by[n.ID] = n
	}
	visit := map[string]int{}
	out := []Node{}
	var dfs func(string) error
	dfs = func(id string) error {
		switch visit[id] {
		case 1:
			return fmt.Errorf("DAG cycle at %s", id)
		case 2:
			return nil
		}
		n, ok := by[id]
		if !ok {
			return fmt.Errorf("unknown dependency %s", id)
		}
		visit[id] = 1
		deps := append([]string{}, n.Deps...)
		sort.Strings(deps)
		for _, dep := range deps {
			if err := dfs(dep); err != nil {
				return err
			}
		}
		visit[id] = 2
		out = append(out, n)
		return nil
	}
	for _, n := range r.Nodes {
		if err := dfs(n.ID); err != nil {
			return nil, err
		}
	}
	return out, nil
}
func RecipeHash(normalized []byte) string {
	digest := sha256.Sum256(append([]byte("baltor-harness-v"+Version+"\n"), normalized...))
	return hex.EncodeToString(digest[:])
}

func SafePath(root, rel string) (string, error) {
	if rel == "" || filepath.IsAbs(rel) || strings.Contains(rel, "\\") || strings.ContainsRune(rel, '\x00') {
		return "", errors.New("absolute, empty, or invalid workspace path")
	}
	for _, seg := range strings.Split(filepath.ToSlash(rel), "/") {
		if seg == ".." || seg == "." {
			return "", fmt.Errorf("dot/path-traversal component blocked: %q", rel)
		}
	}
	cleaned := filepath.Clean(rel)
	if cleaned == "." || cleaned == ".." || strings.HasPrefix(cleaned, ".."+string(filepath.Separator)) {
		return "", fmt.Errorf("workspace traversal blocked: %q", rel)
	}
	// Reject symbolic links at each pre-existing component, including the target.
	rootAbs, err := filepath.Abs(root)
	if err != nil {
		return "", err
	}
	parts := strings.Split(cleaned, string(filepath.Separator))
	cur := rootAbs
	for _, part := range parts {
		cur = filepath.Join(cur, part)
		if info, err := os.Lstat(cur); err == nil && info.Mode()&os.ModeSymlink != 0 {
			return "", fmt.Errorf("symlink in workspace path %s", rel)
		}
	}
	return filepath.Join(rootAbs, cleaned), nil
}
func ParamBool(n Node, key string, def bool) (bool, error) {
	raw, ok := n.Params[key]
	if !ok {
		return def, nil
	}
	var v bool
	if err := json.Unmarshal(raw, &v); err != nil {
		return false, fmt.Errorf("%s must be bool", key)
	}
	return v, nil
}
func ParamString(n Node, key, def string) (string, error) {
	raw, ok := n.Params[key]
	if !ok {
		return def, nil
	}
	var s string
	if err := json.Unmarshal(raw, &s); err != nil {
		return "", fmt.Errorf("%s must be string", key)
	}
	return s, nil
}
func ParamInt(n Node, key string, def int) (int, error) {
	raw, ok := n.Params[key]
	if !ok {
		return def, nil
	}
	var s int
	if err := json.Unmarshal(raw, &s); err != nil {
		return 0, fmt.Errorf("%s must be int", key)
	}
	return s, nil
}

func GraphDOT(r Recipe) string {
	var b strings.Builder
	b.WriteString("digraph baltor {\n  rankdir=LR;\n  graph [bgcolor=\"#071526\"];\n  node [shape=box, style=rounded, fontcolor=white, color=\"#72E7D8\"];\n  edge [color=\"#B0C8CE\"];\n")
	order, _ := Topological(r)
	for _, n := range order {
		fmt.Fprintf(&b, "  %s [label=\"%s\\n%s\"];\n", n.ID, n.ID, n.Op)
	}
	for _, n := range order {
		for _, dep := range n.Deps {
			fmt.Fprintf(&b, "  %s -> %s;\n", dep, n.ID)
		}
	}
	b.WriteString("}\n")
	return b.String()
}
