package foundry

import (
	"bytes"
	"encoding/json"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

func fixture() Recipe {
	return Recipe{
		Schema: Schema, Name: "fixture", Seed: 123,
		Canvas: Canvas{180, 320, 8},
		Shots:  []Shot{{ID: "a", Frames: 4, Mode: "nodes", Title: "TEST", Caption: "SHOTS", Camera: Camera{Zoom: 1}, Layout: Layout{Padding: []int{4, 5, 4, 5}}}},
		Nodes:  []Node{{ID: "source", Op: "scene.frames"}, {ID: "metrics", Op: "frames.metrics", Deps: []string{"source"}}, {ID: "contact", Op: "frames.contact", Deps: []string{"source"}}, {ID: "timeline", Op: "timeline.compile"}},
	}
}
func TestValidateGood(t *testing.T) {
	if err := Validate(fixture()); err != nil {
		t.Fatal(err)
	}
}
func TestRejectCycles(t *testing.T) {
	r := fixture()
	r.Nodes[0].Deps = []string{"metrics"}
	if err := Validate(r); err == nil || !strings.Contains(err.Error(), "cycle") {
		t.Fatalf("expected cycle, got %v", err)
	}
}
func TestRejectUnknownDependency(t *testing.T) {
	r := fixture()
	r.Nodes[1].Deps = []string{"foobar"}
	if err := Validate(r); err == nil {
		t.Fatal("accepted missing node")
	}
}
func TestRejectUnknownOperator(t *testing.T) {
	r := fixture()
	r.Nodes[0].Op = "shell.execute"
	if err := Validate(r); err == nil {
		t.Fatal("accepted shell operator")
	}
}
func TestRejectUnknownParameter(t *testing.T) {
	r := fixture()
	r.Nodes[0].Params = map[string]json.RawMessage{"command": json.RawMessage(`"rm -rf /"`)}
	if err := Validate(r); err == nil {
		t.Fatal("accepted command param")
	}
}
func TestRejectBadPadding(t *testing.T) {
	r := fixture()
	r.Shots[0].Layout.Padding = []int{1, 2}
	if err := Validate(r); err == nil {
		t.Fatal("accepted incomplete padding")
	}
}
func TestRejectOversizedCanvas(t *testing.T) {
	r := fixture()
	r.Canvas.Width = 999999
	if err := Validate(r); err == nil {
		t.Fatal("accepted massive canvas")
	}
}
func TestRejectOversizedFrames(t *testing.T) {
	r := fixture()
	r.Shots[0].Frames = 2200
	if err := Validate(r); err == nil {
		t.Fatal("accepted huge timeline")
	}
}
func TestRejectInvalidScene(t *testing.T) {
	r := fixture()
	r.Shots[0].Mode = "neural_unverified"
	if err := Validate(r); err == nil {
		t.Fatal("accepted unknown scene")
	}
}
func TestRejectInvalidName(t *testing.T) {
	r := fixture()
	r.Name = "../escape"
	if err := Validate(r); err == nil {
		t.Fatal("accepted unsafe name")
	}
}
func TestSafePathTraversal(t *testing.T) {
	root := t.TempDir()
	for _, p := range []string{"../evil", "inputs/../evil", "/etc/passwd", ".", ""} {
		if _, err := SafePath(root, p); err == nil {
			t.Errorf("unsafe path accepted: %s", p)
		}
	}
}
func TestSafePathSymlink(t *testing.T) {
	root := t.TempDir()
	if err := os.Symlink("/etc", filepath.Join(root, "linked")); err != nil {
		t.Skip(err)
	}
	if _, err := SafePath(root, "linked/passwd"); err == nil {
		t.Fatal("symlink followed")
	}
}
func TestOverlayRejectInvalid(t *testing.T) {
	n := Node{ID: "overlay", Op: "frames.overlay", Params: map[string]json.RawMessage{"elements": json.RawMessage(`[ {"id":"x","kind":"shell","x":0.1,"y":0.1,"w":0.4,"h":0.3} ]`)}}
	if _, err := ParseElements(n); err == nil {
		t.Fatal("bad overlay kind passed")
	}
}
func TestNativeDeterministicFrames(t *testing.T) {
	r := fixture()
	a := DrawFrame(r, 0, true)
	b := DrawFrame(r, 0, true)
	p := filepath.Join(t.TempDir(), "test.png")
	WritePNG(p, a)
	ba, _ := os.ReadFile(p)
	WritePNG(p, b)
	bb, _ := os.ReadFile(p)
	if !bytes.Equal(ba, bb) {
		t.Fatal("PNG output differs")
	}
}
func TestOverlayBoxes(t *testing.T) {
	e := OverlayElement{X: .9, Y: .8, W: .2, H: .1, Anchor: "bottom_right"}
	x0, y0, x1, y1 := overlayBox(e, 200, 400)
	if x0 != 140 || y0 != 280 || x1 != 180 || y1 != 320 {
		t.Fatalf("incorrect box %d %d %d %d", x0, y0, x1, y1)
	}
}
func TestRuntimeRepeatAndTamper(t *testing.T) {
	r := fixture()
	norm, _ := json.Marshal(r)
	w1, w2 := t.TempDir(), t.TempDir()
	d1, m, hit, e := Run(w1, r, norm, false)
	if e != nil {
		t.Fatal(e)
	}
	if hit {
		t.Fatal("unexpected cache hit")
	}
	d2, _, hit, e := Run(w2, r, norm, false)
	if e != nil || hit {
		t.Fatalf("repeat failed %v", e)
	}
	diff, e := DiffRuns(d1, d2)
	if e != nil || !strings.HasPrefix(diff, "IDENTICAL") {
		t.Fatalf("different native builds: %s %v", diff, e)
	}
	_, _, hit, e = Run(w1, r, norm, false)
	if e != nil || !hit {
		t.Fatal("cache verification failed")
	}
	p := filepath.Join(d1, "analysis", "frame_metrics.csv")
	f, e := os.OpenFile(p, os.O_APPEND|os.O_WRONLY, 0644)
	if e != nil {
		t.Fatal(e)
	}
	f.Write([]byte("evil"))
	f.Close()
	if _, e := Verify(d1); e == nil {
		t.Fatal("tampered artifact should fail")
	}
	if _, _, _, e := Run(w1, r, norm, false); e == nil {
		t.Fatal("tampered cache should fail closed")
	}
	_ = m
}
func TestBundleBitExact(t *testing.T) {
	r := fixture()
	norm, _ := json.Marshal(r)
	w := t.TempDir()
	run, _, _, err := Run(w, r, norm, false)
	if err != nil {
		t.Fatal(err)
	}
	a := filepath.Join(w, "a.tgz")
	b := filepath.Join(w, "b.tgz")
	if e := PackageRun(run, a); e != nil {
		t.Fatal(e)
	}
	if e := PackageRun(run, b); e != nil {
		t.Fatal(e)
	}
	ba, _ := os.ReadFile(a)
	bb, _ := os.ReadFile(b)
	if !bytes.Equal(ba, bb) {
		t.Fatal("non-deterministic archives")
	}
}
func TestIngestRejectOverwriteAndTraversal(t *testing.T) {
	w := t.TempDir()
	p := filepath.Join(t.TempDir(), "data.txt")
	os.WriteFile(p, []byte("HELLO"), 0644)
	if _, err := Ingest(w, p, "../escape"); err == nil {
		t.Fatal("traversal allowed")
	}
	if _, err := Ingest(w, p, ".."); err == nil {
		t.Fatal("dotdot allowed")
	}
	if _, err := Ingest(w, p, "data.txt"); err != nil {
		t.Fatal(err)
	}
	if _, err := Ingest(w, p, "data.txt"); err == nil {
		t.Fatal("overwrite allowed")
	}
}
