package foundry

import (
	"archive/tar"
	"compress/gzip"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"sort"
	"strings"
	"time"
)

type Artifact struct {
	Path   string `json:"path"`
	SHA256 string `json:"sha256"`
	Bytes  int64  `json:"bytes"`
}
type NodeReceipt struct {
	ID              string   `json:"id"`
	Op              string   `json:"op"`
	Outputs         []string `json:"outputs"`
	Execution       string   `json:"execution"`
	Reproducibility string   `json:"reproducibility"`
}
type Manifest struct {
	Schema      string            `json:"schema"`
	ToolVersion string            `json:"tool_version"`
	Job         string            `json:"job"`
	RunID       string            `json:"run_id"`
	RecipeSHA   string            `json:"recipe_sha256"`
	InputsSHA   string            `json:"inputs_sha256"`
	Runtime     map[string]string `json:"runtime"`
	Nodes       []NodeReceipt     `json:"nodes"`
	Files       []Artifact        `json:"files"`
	Caveats     []string          `json:"caveats"`
}

func sha(b []byte) string { h := sha256.Sum256(b); return hex.EncodeToString(h[:]) }
func shaFile(path string) (string, int64, error) {
	f, err := os.Open(path)
	if err != nil {
		return "", 0, err
	}
	defer f.Close()
	h := sha256.New()
	n, err := io.Copy(h, f)
	if err != nil {
		return "", 0, err
	}
	return hex.EncodeToString(h.Sum(nil)), n, nil
}
func Artifacts(root string) ([]Artifact, error) {
	arr := []Artifact{}
	err := filepath.WalkDir(root, func(path string, de os.DirEntry, err error) error {
		if err != nil {
			return err
		}
		rel, err := filepath.Rel(root, path)
		if err != nil {
			return err
		}
		if de.Type()&os.ModeSymlink != 0 {
			return fmt.Errorf("symlink not accepted: %s", rel)
		}
		if de.IsDir() {
			return nil
		}
		if rel == "manifest.json" {
			return nil
		}
		if !de.Type().IsRegular() {
			return fmt.Errorf("nonregular artifact not accepted %s", rel)
		}
		hash, size, err := shaFile(path)
		if err != nil {
			return err
		}
		arr = append(arr, Artifact{filepath.ToSlash(rel), hash, size})
		return nil
	})
	sort.Slice(arr, func(i, j int) bool { return arr[i].Path < arr[j].Path })
	return arr, err
}
func inputFingerprint(workspace string) (string, error) {
	dir, err := SafePath(workspace, "inputs")
	if err != nil {
		return "", err
	}
	if _, err := os.Stat(dir); os.IsNotExist(err) {
		return sha([]byte("empty-inputs")), nil
	}
	arr, err := Artifacts(dir)
	if err != nil {
		return "", err
	}
	for _, a := range arr {
		if a.Bytes > 500_000_000 {
			return "", errors.New("input exceeds 500 MB")
		}
	}
	b, _ := json.Marshal(arr)
	return sha(b), nil
}
func Fingerprint(r Recipe, norm []byte, workspace string) (string, string, map[string]string, error) {
	in, err := inputFingerprint(workspace)
	if err != nil {
		return "", "", nil, err
	}
	runtime := map[string]string{"native": "go-stdlib-" + Version}
	for _, n := range r.Nodes {
		if n.Op == "video.encode" || n.Op == "video.sample" || n.Op == "video.probe" {
			runtime["ffmpeg"] = FFmpegVersion()
			break
		}
	}
	parts, _ := json.Marshal(runtime)
	return sha(append(append(append([]byte(Version), norm...), []byte(in)...), parts...))[:20], in, runtime, nil
}
func ingest(workspace, src, as string) (string, error) {
	if as == "." || as == ".." || strings.HasPrefix(as, ".") || !safeName(strings.ReplaceAll(as, ".", "-")) || strings.Contains(as, "/") {
		return "", errors.New("--as must be a simple filename without directory components")
	}
	fi, err := os.Lstat(src)
	if err != nil {
		return "", err
	}
	if !fi.Mode().IsRegular() || fi.Size() > 500_000_000 {
		return "", errors.New("input must be a regular file <= 500MB")
	}
	dst, err := SafePath(workspace, "inputs/"+as)
	if err != nil {
		return "", err
	}
	if err := os.MkdirAll(filepath.Dir(dst), 0755); err != nil {
		return "", err
	}
	if _, err := os.Lstat(dst); err == nil {
		return "", errors.New("input already exists: cannot overwrite staged input")
	}
	f, err := os.Open(src)
	if err != nil {
		return "", err
	}
	defer f.Close()
	out, err := os.OpenFile(dst, os.O_WRONLY|os.O_CREATE|os.O_EXCL, 0644)
	if err != nil {
		return "", err
	}
	_, err = io.Copy(out, f)
	if err2 := out.Close(); err == nil {
		err = err2
	}
	if err != nil {
		os.Remove(dst)
		return "", err
	}
	h, _, err := shaFile(dst)
	return h, err
}
func Ingest(workspace, src, as string) (string, error) { return ingest(workspace, src, as) }

func Run(workspace string, r Recipe, norm []byte, force bool) (string, Manifest, bool, error) {
	if err := os.MkdirAll(workspace, 0755); err != nil {
		return "", Manifest{}, false, err
	}
	id, in, runtime, err := Fingerprint(r, norm, workspace)
	if err != nil {
		return "", Manifest{}, false, err
	}
	runs, err := SafePath(workspace, "runs")
	if err != nil {
		return "", Manifest{}, false, err
	}
	os.MkdirAll(runs, 0755)
	final, err := SafePath(workspace, "runs/"+id)
	if err != nil {
		return "", Manifest{}, false, err
	}
	if _, err := os.Stat(final); err == nil {
		if !force {
			m, e := Verify(final)
			if e != nil {
				return "", Manifest{}, false, fmt.Errorf("cached run failed verification: %w; use --force to regenerate", e)
			}
			return final, m, true, nil
		}
	}
	tmp, err := os.MkdirTemp(runs, ".tmp-")
	if err != nil {
		return "", Manifest{}, false, err
	}
	defer os.RemoveAll(tmp)
	order, err := Topological(r)
	if err != nil {
		return "", Manifest{}, false, err
	}
	nodes := []NodeReceipt{}
	for _, n := range order {
		outputs, determinism, err := execute(workspace, tmp, r, n)
		if err != nil {
			return "", Manifest{}, false, fmt.Errorf("node %s (%s): %w", n.ID, n.Op, err)
		}
		nodes = append(nodes, NodeReceipt{n.ID, n.Op, outputs, "local", "deterministic-native"})
		if determinism != "" {
			nodes[len(nodes)-1].Reproducibility = determinism
		}
	}
	files, err := Artifacts(tmp)
	if err != nil {
		return "", Manifest{}, false, err
	}
	m := Manifest{Schema: "baltor.run_manifest/1", ToolVersion: Version, Job: r.Name, RunID: id, RecipeSHA: sha(norm), InputsSHA: in, Runtime: runtime, Nodes: nodes, Files: files, Caveats: []string{
		"Process allowlists, relative paths and timeouts are not a container, VM or kernel-level sandbox.",
		"Media byte identity is tested only on the same encoder/runtime build; cross-platform equivalence is not claimed.",
		"Motion, cuts and text-placement metrics are heuristics, not semantic reference-video interpretation.",
	}}
	b, _ := json.MarshalIndent(m, "", "  ")
	if err := os.WriteFile(filepath.Join(tmp, "manifest.json"), append(b, '\n'), 0644); err != nil {
		return "", Manifest{}, false, err
	}
	if force { // Keep the previous run intact until replacement has completely succeeded.
		if _, err := os.Stat(final); err == nil {
			if err := os.RemoveAll(final); err != nil {
				return "", Manifest{}, false, err
			}
		}
	}
	if err := os.Rename(tmp, final); err != nil {
		return "", Manifest{}, false, err
	}
	return final, m, false, nil
}
func execute(workspace, root string, r Recipe, n Node) ([]string, string, error) {
	switch n.Op {
	case "scene.frames":
		presentation, err := ParamBool(n, "presentation", true)
		if err != nil {
			return nil, "", err
		}
		count, err := RenderFrames(r, root, presentation)
		return []string{fmt.Sprintf("frames (%d PNG files)", count), "timeline.json"}, "byte-deterministic on same build", err
	case "audio.synth":
		err := WriteAudio(r, root)
		return []string{"audio/score.wav"}, "byte-deterministic on same build", err
	case "frames.transform":
		err := TransformFrames(root, n)
		return []string{"stages/" + n.ID + "/"}, "byte-deterministic on same build", err
	case "frames.overlay":
		err := OverlayFrames(root, n)
		return []string{"stages/" + n.ID + "/"}, "byte-deterministic on same build", err
	case "frames.spatial":
		sub, err := ParamString(n, "from", "frames")
		if err != nil {
			return nil, "", err
		}
		err = SpatialScore(root, sub)
		return []string{"analysis/spatial_score.json"}, "pixel heuristic", err
	case "timeline.compile":
		err := CompileTimeline(r, root)
		return []string{"analysis/timeline.csv"}, "byte-deterministic on same build", err
	case "frames.metrics":
		sub, err := ParamString(n, "from", "frames")
		if err != nil {
			return nil, "", err
		}
		err = AnalyzeFrames(root, sub)
		return []string{"analysis/frame_metrics.csv", "analysis/frame_report.json"}, "byte-deterministic on same build", err
	case "frames.contact":
		sub, err := ParamString(n, "from", "frames")
		if err != nil {
			return nil, "", err
		}
		err = ContactSheet(root, sub)
		return []string{"analysis/contact_sheet.png"}, "byte-deterministic on same build", err
	case "video.encode":
		sub, err := ParamString(n, "from", "frames")
		if err != nil {
			return nil, "", err
		}
		err = EncodeVideo(r, root, sub)
		return []string{"media/video.mp4"}, "runtime-pinned within same ffmpeg/libx264 build; not cross-platform guaranteed", err
	case "video.sample":
		err := SampleVideo(workspace, root, n)
		return []string{"sampled/"}, "runtime-pinned within same ffmpeg build", err
	case "video.probe":
		rel, err := ParamString(n, "input", "media/video.mp4")
		if err != nil {
			return nil, "", err
		}
		base := root
		if strings.HasPrefix(rel, "inputs/") {
			base = workspace
		}
		path, err := SafePath(base, rel)
		if err != nil {
			return nil, "", err
		}
		obj, err := ProbeVideo(path)
		if err != nil {
			return nil, "", err
		}
		output, _ := SafePath(root, "analysis/video_info.json")
		os.MkdirAll(filepath.Dir(output), 0755)
		b, _ := json.MarshalIndent(obj, "", "  ")
		err = os.WriteFile(output, append(b, '\n'), 0644)
		return []string{"analysis/video_info.json"}, "runtime-pinned within same ffprobe build", err
	case "layout.lint":
		err := LintLayout(workspace, root, n)
		return []string{"analysis/layout_lint.json"}, "byte-deterministic on same build", err
	case "artifact.hash":
		rel, err := ParamString(n, "source", "media/video.mp4")
		if err != nil {
			return nil, "", err
		}
		base := root
		if strings.HasPrefix(rel, "inputs/") {
			base = workspace
		}
		path, err := SafePath(base, rel)
		if err != nil {
			return nil, "", err
		}
		digest, size, err := shaFile(path)
		if err != nil {
			return nil, "", err
		}
		obj := map[string]any{"source": rel, "sha256": digest, "bytes": size}
		b, _ := json.MarshalIndent(obj, "", "  ")
		p, _ := SafePath(root, "analysis/artifact_hash.json")
		os.MkdirAll(filepath.Dir(p), 0755)
		err = os.WriteFile(p, append(b, '\n'), 0644)
		return []string{"analysis/artifact_hash.json"}, "byte-deterministic on same build", err
	}
	return nil, "", errors.New("unknown operation")
}
func Verify(run string) (Manifest, error) {
	b, err := os.ReadFile(filepath.Join(run, "manifest.json"))
	if err != nil {
		return Manifest{}, err
	}
	var m Manifest
	if err := json.Unmarshal(b, &m); err != nil {
		return m, err
	}
	if m.Schema != "baltor.run_manifest/1" || len(m.Files) == 0 {
		return m, errors.New("missing or invalid manifest")
	}
	all, err := Artifacts(run)
	if err != nil {
		return m, err
	}
	if len(all) != len(m.Files) {
		return m, fmt.Errorf("artifact count mismatch: expected %d, found %d", len(m.Files), len(all))
	}
	for k, a := range m.Files {
		if all[k] != a {
			return m, fmt.Errorf("artifact mismatch at %s (missing, changed, or extra file)", a.Path)
		}
	}
	return m, nil
}
func DiffRuns(a, b string) (string, error) {
	m1, err := Verify(a)
	if err != nil {
		return "", err
	}
	m2, err := Verify(b)
	if err != nil {
		return "", err
	}
	if len(m1.Files) != len(m2.Files) {
		return fmt.Sprintf("DIFFERENT: artifact count %d vs %d", len(m1.Files), len(m2.Files)), nil
	}
	for i := range m1.Files {
		if m1.Files[i] != m2.Files[i] {
			return fmt.Sprintf("DIFFERENT: %s versus %s", m1.Files[i].Path, m2.Files[i].Path), nil
		}
	}
	return fmt.Sprintf("IDENTICAL: %d artifacts have identical paths, sizes and SHA-256 hashes", len(m1.Files)), nil
}
func PackageRun(run, out string) error {
	m, err := Verify(run)
	if err != nil {
		return err
	}
	f, err := os.Create(out)
	if err != nil {
		return err
	}
	defer f.Close()
	gz := gzip.NewWriter(f)
	gz.Header.ModTime = time.Unix(0, 0)
	gz.Header.Name = ""
	gz.Header.Comment = ""
	tw := tar.NewWriter(gz)
	paths := []string{"manifest.json"}
	for _, a := range m.Files {
		paths = append(paths, a.Path)
	}
	sort.Strings(paths)
	for _, rel := range paths {
		path, err := SafePath(run, rel)
		if err != nil {
			return err
		}
		info, err := os.Stat(path)
		if err != nil {
			return err
		}
		header := &tar.Header{Name: filepath.ToSlash(rel), Mode: 0644, Size: info.Size(), ModTime: time.Unix(0, 0), Uid: 0, Gid: 0, Uname: "", Gname: "", Typeflag: tar.TypeReg, Format: tar.FormatPAX}
		if err := tw.WriteHeader(header); err != nil {
			return err
		}
		r, err := os.Open(path)
		if err != nil {
			return err
		}
		_, err = io.Copy(tw, r)
		r.Close()
		if err != nil {
			return err
		}
	}
	if err := tw.Close(); err != nil {
		return err
	}
	return gz.Close()
}
