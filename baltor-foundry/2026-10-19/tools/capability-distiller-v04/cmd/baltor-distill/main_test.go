package main

import (
	"encoding/json"
	"os"
	"path/filepath"
	"reflect"
	"strings"
	"testing"
)

func TestFrontmatter(t *testing.T) {
	m, w := frontmatter("---\nname: my-skill\ndescription: >\n  this is a test\nlicense: MIT\n---\n# Title\n")
	if m["name"] != "my-skill" || !strings.Contains(m["description"], "this is a test") || len(w) > 0 {
		t.Fatal(m, w)
	}
}
func TestScanDoesNotExecuteScripts(t *testing.T) {
	dir := t.TempDir()
	sk := filepath.Join(dir, "unsafe")
	os.MkdirAll(filepath.Join(sk, "scripts"), 0755)
	target := filepath.Join(sk, "scripts", "evil.sh")
	os.WriteFile(target, []byte("#!/bin/sh\necho poisoned >"+filepath.Join(dir, "EXECUTED")+"\n"), 0755)
	os.WriteFile(filepath.Join(sk, "SKILL.md"), []byte("---\nname: unsafe\ndescription: test fixture\n---\nRun scripts/evil.sh"), 0644)
	r, e := scan(dir)
	if e != nil || len(r.Skills) != 1 || len(r.Skills[0].Scripts) != 1 {
		t.Fatal(r, e)
	}
	if _, e := os.Stat(filepath.Join(dir, "EXECUTED")); !os.IsNotExist(e) {
		t.Fatal("unexpected execution")
	}
}
func TestScanDeterminism(t *testing.T) {
	dir := t.TempDir()
	os.Mkdir(filepath.Join(dir, "skill"), 0755)
	os.WriteFile(filepath.Join(dir, "skill", "SKILL.md"), []byte("---\nname: example\ndescription: thing\n---\n"), 0644)
	a, _ := scan(dir)
	b, _ := scan(dir)
	if !reflect.DeepEqual(a, b) {
		t.Fatal("scans differ")
	}
}
func TestSkillProposalsNeverExecutable(t *testing.T) {
	r := ScanReport{Skills: []Skill{{ID: "x", Name: "Sample", Risk: []string{"outbound_network_mentioned"}}}}
	a := proposals(r)
	if len(a) != 1 || a[0].ExecutionAllowed || a[0].Status != "PROPOSAL_ONLY_NOT_EXECUTABLE" {
		t.Fatal(a)
	}
}
func TestLayoutCollision(t *testing.T) {
	var s LayoutSpec
	s.Canvas.Width = 1080
	s.Canvas.Height = 1920
	s.Canvas.SafeTop = .1
	s.Canvas.SafeBottom = .14
	s.Elements = []LayoutElement{{ID: "title", Type: "text", X: .1, Y: .2, W: .5, H: .1, StartMS: 0, EndMS: 1000}, {ID: "hero", Type: "subject", X: .3, Y: .2, W: .3, H: .6, StartMS: 0, EndMS: 1000}}
	rep := lintLayout(s)
	found := false
	for _, v := range rep.Issues {
		if v.Code == "text_subject_overlap" {
			found = true
		}
	}
	if !found || !rep.Valid {
		t.Fatal(rep)
	}
}
func TestLayoutRejectsOutOfCanvas(t *testing.T) {
	var s LayoutSpec
	s.Canvas.Width = 540
	s.Canvas.Height = 960
	s.Elements = []LayoutElement{{ID: "x", Type: "text", X: .9, Y: .5, W: .3, H: .2, EndMS: 1000}}
	if lintLayout(s).Valid {
		t.Fatal("accepted bad element")
	}
}
func TestStoryFramesConserved(t *testing.T) {
	s := Story{FPS: 24, Canvas: [2]int{1080, 1920}, Shots: []StoryShot{{ID: "one", DurationMS: 2500, Text: "Hi"}, {ID: "two", DurationMS: 3500, Text: "Bye"}}}
	o, e := compileStory(s, "deadbeef")
	if e != nil || o.TotalFrames != 144 || o.Timeline[0].EndFrameExclusive != o.Timeline[1].StartFrame {
		t.Fatal(o, e)
	}
	if !strings.Contains(formatSRT(o), "00:00:02,500") {
		t.Fatal(formatSRT(o))
	}
}
func TestStoryRejectDuplicate(t *testing.T) {
	s := Story{FPS: 24, Canvas: [2]int{1080, 1920}, Shots: []StoryShot{{ID: "x", DurationMS: 1000}, {ID: "x", DurationMS: 1000}}}
	if _, e := compileStory(s, ""); e == nil {
		t.Fatal("duplicate accepted")
	}
}
func TestVariantsDeterministic(t *testing.T) {
	v := VariantSpec{Base: "ad", Axes: []VariantAxis{{Name: "palette", Values: []string{"warm", "cold"}}, {Name: "camera", Values: []string{"push", "orbit"}}}}
	a, e := variants(v)
	b, _ := variants(v)
	if e != nil || len(a) != 4 || !reflect.DeepEqual(a, b) {
		t.Fatal(e, a, b)
	}
	raw, _ := json.Marshal(a)
	if len(raw) == 0 {
		t.Fatal("invalid JSON")
	}
}
func TestVariantsBounded(t *testing.T) {
	v := VariantSpec{Base: "x"}
	for i := 0; i < 9; i++ {
		v.Axes = append(v.Axes, VariantAxis{Name: string(rune('a' + i)), Values: []string{"x", "y"}})
	}
	if _, e := variants(v); e == nil {
		t.Fatal("should bound variants")
	}
}
