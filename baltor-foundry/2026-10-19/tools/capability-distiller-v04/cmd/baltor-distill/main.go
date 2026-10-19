// Baltor Capability Distiller 0.4: conservative, deterministic skill intake and
// parameterized media-storyboard/layout/variation helpers.
// No downloaded script or SKILL.md command is executed by this binary.
package main

import (
	"crypto/sha256"
	"encoding/csv"
	"encoding/hex"
	"encoding/json"
	"errors"
	"flag"
	"fmt"
	"io"
	"io/fs"
	"math"
	"os"
	"path/filepath"
	"regexp"
	"sort"
	"strconv"
	"strings"
	"time"
)

const Version = "0.4.0"
const maxSkillSize = 1 << 20
const maxScanSkills = 5000
const maxVariants = 256

type Skill struct {
	ID             string   `json:"id"`
	Name           string   `json:"name"`
	Description    string   `json:"description"`
	RelativePath   string   `json:"relative_path"`
	SourceSHA256   string   `json:"source_sha256"`
	License        string   `json:"declared_license"`
	Scripts        []string `json:"scripts"`
	References     []string `json:"references"`
	Signals        []string `json:"signals"`
	Risk           []string `json:"review_flags"`
	PotentialScore int      `json:"distillation_potential_heuristic"`
	Status         string   `json:"status"`
}
type ScanReport struct {
	Schema   string         `json:"schema"`
	Root     string         `json:"root"`
	Skills   []Skill        `json:"skills"`
	Counts   map[string]int `json:"counts"`
	Warnings []string       `json:"warnings"`
}
type Proposal struct {
	ID                  string   `json:"id"`
	Name                string   `json:"name"`
	SourceSHA256        string   `json:"source_sha256"`
	SourceRelativePath  string   `json:"source_relative_path"`
	Operation           string   `json:"operation"`
	Parameters          []Param  `json:"parameters"`
	Inputs              []string `json:"inputs"`
	Outputs             []string `json:"outputs"`
	Status              string   `json:"status"`
	ExecutionAllowed    bool     `json:"execution_allowed"`
	RequiresHumanReview []string `json:"requires_human_review"`
}
type Param struct {
	Name        string `json:"name"`
	Type        string `json:"type"`
	Required    bool   `json:"required"`
	Description string `json:"description"`
}

func hash(b []byte) string { s := sha256.Sum256(b); return hex.EncodeToString(s[:]) }
func canonicalJSON(v any) ([]byte, error) {
	b, e := json.MarshalIndent(v, "", "  ")
	if e != nil {
		return nil, e
	}
	return append(b, '\n'), nil
}
func saveJSON(path string, v any) error {
	b, e := canonicalJSON(v)
	if e != nil {
		return e
	}
	return writeFile(path, b)
}
func writeFile(path string, b []byte) error {
	if path == "" {
		_, e := os.Stdout.Write(b)
		return e
	}
	if e := os.MkdirAll(filepath.Dir(path), 0755); e != nil {
		return e
	}
	return os.WriteFile(path, b, 0644)
}
func readJSON(p string, v any) error {
	f, e := os.Open(p)
	if e != nil {
		return e
	}
	defer f.Close()
	d := json.NewDecoder(io.LimitReader(f, 4<<20))
	d.DisallowUnknownFields()
	return d.Decode(v)
}
func isSafeRelative(p string) bool {
	return p != "" && !filepath.IsAbs(p) && p != ".." && !strings.HasPrefix(filepath.Clean(p), ".."+string(filepath.Separator))
}

var slugRE = regexp.MustCompile(`[^a-z0-9-]+`)

func slug(s string) string {
	s = strings.ToLower(strings.TrimSpace(s))
	s = strings.ReplaceAll(s, "_", "-")
	s = slugRE.ReplaceAllString(s, "-")
	s = strings.Trim(s, "-")
	if s == "" {
		return "unnamed"
	}
	if len(s) > 90 {
		s = s[:90]
	}
	return s
}

// We intentionally parse the small, plain scalar subset of YAML frontmatter.
// Fields using advanced YAML are flagged and require a proper YAML parser/review.
func frontmatter(s string) (map[string]string, []string) {
	m := map[string]string{}
	warn := []string{}
	s = strings.ReplaceAll(s, "\r\n", "\n")
	lines := strings.Split(s, "\n")
	if len(lines) < 3 || strings.TrimSpace(lines[0]) != "---" {
		return m, []string{"missing_yaml_frontmatter"}
	}
	foundEnd := false
	active := ""
	for _, line := range lines[1:] {
		if strings.TrimSpace(line) == "---" {
			foundEnd = true
			break
		}
		if (strings.HasPrefix(line, " ") || strings.HasPrefix(line, "\t")) && active != "" {
			m[active] += " " + strings.TrimSpace(line)
			continue
		}
		i := strings.Index(line, ":")
		if i < 0 {
			if strings.TrimSpace(line) != "" {
				warn = append(warn, "advanced_yaml_needs_review")
			}
			continue
		}
		k := strings.TrimSpace(line[:i])
		v := strings.TrimSpace(line[i+1:])
		if k == "" {
			continue
		}
		active = k
		if v == ">" || v == "|" {
			m[k] = ""
			continue
		}
		m[k] = strings.Trim(v, `"'`)
	}
	if !foundEnd {
		warn = append(warn, "unterminated_frontmatter")
	}
	return m, warn
}

var riskMatchers = []struct {
	pattern string
	label   string
}{
	{`curl\s+[^\n]+\|\s*(?:bash|sh)`, "pipe_to_shell"},
	{`(?:wget|curl|https?://|fetch\()`, "outbound_network_mentioned"},
	{`(?:password|api[_-]?key|secret|token|credential)`, "credentials_mentioned"},
	{`(?:sudo|chmod\s+777|rm\s+-rf|shell\s*\(|os\.system\()`, "privileged_or_shell_activity"},
	{`(?:openai|anthropic|llm|model|inference|gpu|cuda)`, "model_dependent_candidate"},
}

func uniqueSorted(a []string) []string {
	m := map[string]bool{}
	for _, x := range a {
		if x != "" {
			m[x] = true
		}
	}
	o := make([]string, 0, len(m))
	for x := range m {
		o = append(o, x)
	}
	sort.Strings(o)
	return o
}
func scan(root string) (ScanReport, error) {
	root, e := filepath.Abs(root)
	if e != nil {
		return ScanReport{}, e
	}
	st, e := os.Stat(root)
	if e != nil {
		return ScanReport{}, e
	}
	if !st.IsDir() {
		return ScanReport{}, errors.New("scan root must be directory")
	}
	result := ScanReport{Schema: "baltor.skill_scan/1", Root: root, Skills: []Skill{}, Warnings: []string{}, Counts: map[string]int{}}
	e = filepath.WalkDir(root, func(p string, d fs.DirEntry, err error) error {
		if err != nil {
			return err
		}
		if d.Type()&os.ModeSymlink != 0 {
			return nil
		}
		if d.IsDir() {
			rel, _ := filepath.Rel(root, p)
			if strings.Count(rel, string(filepath.Separator)) > 11 {
				return filepath.SkipDir
			}
			return nil
		}
		if d.Name() != "SKILL.md" {
			return nil
		}
		if len(result.Skills) >= maxScanSkills {
			return errors.New("maximum skills exceeded")
		}
		info, er := d.Info()
		if er != nil {
			return er
		}
		if info.Size() > maxSkillSize {
			result.Warnings = append(result.Warnings, "oversize_skill_skipped:"+p)
			return nil
		}
		b, er := os.ReadFile(p)
		if er != nil {
			return er
		}
		fm, warns := frontmatter(string(b))
		rel, _ := filepath.Rel(root, p)
		dir := filepath.Dir(p)
		name := fm["name"]
		if name == "" {
			name = filepath.Base(dir)
			warns = append(warns, "missing_name")
		}
		desc := fm["description"]
		if desc == "" {
			warns = append(warns, "missing_description")
		}
		scripts, refs := []string{}, []string{}
		limit := 0
		_ = filepath.WalkDir(dir, func(child string, de fs.DirEntry, er error) error {
			if er != nil {
				return er
			}
			if de.Type()&os.ModeSymlink != 0 {
				return nil
			}
			if de.IsDir() {
				if child != dir && strings.Count(strings.TrimPrefix(child, dir), string(filepath.Separator)) > 4 {
					return filepath.SkipDir
				}
				return nil
			}
			limit++
			if limit > 300 {
				return filepath.SkipAll
			}
			r, _ := filepath.Rel(dir, child)
			r = filepath.ToSlash(r)
			if strings.HasPrefix(r, "scripts/") {
				scripts = append(scripts, r)
			} else if strings.HasPrefix(r, "references/") {
				refs = append(refs, r)
			}
			return nil
		})
		text := strings.ToLower(string(b))
		flags := append([]string{}, warns...)
		signals := []string{}
		for _, m := range riskMatchers {
			if regexp.MustCompile(m.pattern).MatchString(text) {
				flags = append(flags, m.label)
			}
		}
		if strings.Contains(text, "```bash") || strings.Contains(text, "```shell") {
			signals = append(signals, "cli_examples")
		}
		if strings.Contains(text, "test") || strings.Contains(text, "verify") || strings.Contains(text, "assert") {
			signals = append(signals, "validation_documented")
		}
		if len(scripts) > 0 {
			signals = append(signals, "bundled_scripts")
		}
		if strings.Contains(text, "--") && strings.Contains(text, "usage") {
			signals = append(signals, "parameter_hint")
		}
		license := fm["license"]
		if license == "" {
			if _, er := os.Stat(filepath.Join(dir, "LICENSE")); er == nil {
				license = "see_local_LICENSE"
			} else {
				license = "unknown"
				flags = append(flags, "license_not_declared")
			}
		}
		score := 10
		if len(scripts) > 0 {
			score += 30
		}
		if len(refs) > 0 {
			score += 5
		}
		for _, s := range signals {
			switch s {
			case "cli_examples":
				score += 15
			case "parameter_hint":
				score += 10
			case "validation_documented":
				score += 15
			}
		}
		for _, f := range flags {
			switch f {
			case "outbound_network_mentioned":
				score -= 8
			case "privileged_or_shell_activity":
				score -= 20
			case "model_dependent_candidate":
				score -= 8
			case "pipe_to_shell":
				score -= 20
			}
		}
		if score < 0 {
			score = 0
		}
		if score > 100 {
			score = 100
		}
		result.Skills = append(result.Skills, Skill{ID: slug(name) + "-" + hash([]byte(rel))[:8], Name: name, Description: desc, RelativePath: filepath.ToSlash(rel), SourceSHA256: hash(b), License: license, Scripts: uniqueSorted(scripts), References: uniqueSorted(refs), Signals: uniqueSorted(signals), Risk: uniqueSorted(flags), PotentialScore: score, Status: "candidate_unreviewed"})
		return nil
	})
	if e != nil {
		return ScanReport{}, e
	}
	sort.Slice(result.Skills, func(i, j int) bool { return result.Skills[i].RelativePath < result.Skills[j].RelativePath })
	result.Counts["skills"] = len(result.Skills)
	for _, s := range result.Skills {
		result.Counts["scripts"] += len(s.Scripts)
		result.Counts["references"] += len(s.References)
	}
	return result, nil
}
func proposals(rep ScanReport) []Proposal {
	arr := make([]Proposal, 0, len(rep.Skills))
	for _, s := range rep.Skills {
		reviews := append([]string{"manual_semantics_review", "license_and_source_review", "input_output_contract_review", "security_test_before_activation"}, s.Risk...)
		arr = append(arr, Proposal{ID: "proposal." + s.ID, Name: s.Name, SourceSHA256: s.SourceSHA256, SourceRelativePath: s.RelativePath, Operation: slug(s.Name) + ".run", Inputs: []string{"input.json"}, Outputs: []string{"result.json"}, Parameters: []Param{{Name: "workspace", Type: "workspace_path", Required: true, Description: "Sandbox-scoped path, validated by worker"}, {Name: "config", Type: "json", Required: true, Description: "Operation-specific typed schema to be authored and reviewed"}}, Status: "PROPOSAL_ONLY_NOT_EXECUTABLE", ExecutionAllowed: false, RequiresHumanReview: uniqueSorted(reviews)})
	}
	return arr
}

type LayoutSpec struct {
	Canvas struct {
		Width      int     `json:"width"`
		Height     int     `json:"height"`
		SafeTop    float64 `json:"safe_top"`
		SafeRight  float64 `json:"safe_right"`
		SafeBottom float64 `json:"safe_bottom"`
		SafeLeft   float64 `json:"safe_left"`
	} `json:"canvas"`
	Elements []LayoutElement `json:"elements"`
}
type LayoutElement struct {
	ID      string     `json:"id"`
	Type    string     `json:"type"`
	X       float64    `json:"x"`
	Y       float64    `json:"y"`
	W       float64    `json:"w"`
	H       float64    `json:"h"`
	Padding [4]float64 `json:"padding"`
	Z       int        `json:"z"`
	StartMS int        `json:"start_ms"`
	EndMS   int        `json:"end_ms"`
}
type Issue struct {
	Severity string `json:"severity"`
	Code     string `json:"code"`
	ID       string `json:"id,omitempty"`
	Other    string `json:"other,omitempty"`
	Detail   string `json:"detail,omitempty"`
}
type LayoutReport struct {
	Schema string  `json:"schema"`
	Canvas [2]int  `json:"canvas"`
	Issues []Issue `json:"issues"`
	Valid  bool    `json:"valid"`
}

func lintLayout(l LayoutSpec) LayoutReport {
	out := LayoutReport{Schema: "baltor.layout_lint/1", Canvas: [2]int{l.Canvas.Width, l.Canvas.Height}, Issues: []Issue{}, Valid: true}
	add := func(sev, code, id, other, detail string) {
		out.Issues = append(out.Issues, Issue{Severity: sev, Code: code, ID: id, Other: other, Detail: detail})
		if sev == "error" {
			out.Valid = false
		}
	}
	if l.Canvas.Width < 64 || l.Canvas.Height < 64 || l.Canvas.Width > 16384 || l.Canvas.Height > 16384 {
		add("error", "invalid_canvas", "", "", "canvas dimension outside 64..16384")
	}
	for _, z := range []float64{l.Canvas.SafeTop, l.Canvas.SafeBottom, l.Canvas.SafeLeft, l.Canvas.SafeRight} {
		if z < 0 || z >= .5 {
			add("error", "invalid_safe_area", "", "", "safe margins must be 0..0.5")
		}
	}
	seen := map[string]bool{}
	for _, e := range l.Elements {
		if e.ID == "" || seen[e.ID] {
			add("error", "duplicate_or_empty_id", e.ID, "", "")
		}
		seen[e.ID] = true
		if !finite(e.X) || !finite(e.Y) || !finite(e.W) || !finite(e.H) || e.W <= 0 || e.H <= 0 || e.X < 0 || e.Y < 0 || e.X+e.W > 1 || e.Y+e.H > 1 {
			add("error", "out_of_canvas", e.ID, "", "element rectangle must fit 0..1")
		}
		if e.StartMS < 0 || e.EndMS <= e.StartMS {
			add("error", "invalid_time", e.ID, "", "")
		}
		for _, p := range e.Padding {
			if p < 0 || p > .49 {
				add("error", "invalid_padding", e.ID, "", "")
			}
		}
		if e.X < l.Canvas.SafeLeft || e.Y < l.Canvas.SafeTop || e.X+e.W > 1-l.Canvas.SafeRight || e.Y+e.H > 1-l.Canvas.SafeBottom {
			add("warning", "safe_area_intrusion", e.ID, "", "element touches exclusion zone")
		}
	}
	for i, a := range l.Elements {
		for _, b := range l.Elements[i+1:] {
			if a.EndMS <= b.StartMS || b.EndMS <= a.StartMS {
				continue
			}
			if a.X < b.X+b.W && a.X+a.W > b.X && a.Y < b.Y+b.H && a.Y+a.H > b.Y {
				if a.Type == "text" && b.Type == "text" {
					add("warning", "text_overlap", a.ID, b.ID, "")
				} else if a.Type == "text" && b.Type == "subject" || b.Type == "text" && a.Type == "subject" {
					add("warning", "text_subject_overlap", a.ID, b.ID, "")
				}
			}
		}
	}
	sort.Slice(out.Issues, func(i, j int) bool {
		a, b := out.Issues[i], out.Issues[j]
		if a.Code != b.Code {
			return a.Code < b.Code
		}
		if a.ID != b.ID {
			return a.ID < b.ID
		}
		return a.Other < b.Other
	})
	return out
}
func finite(f float64) bool { return !math.IsNaN(f) && !math.IsInf(f, 0) }

type Story struct {
	Schema string      `json:"schema"`
	Title  string      `json:"title"`
	FPS    int         `json:"fps"`
	Canvas [2]int      `json:"canvas"`
	Shots  []StoryShot `json:"shots"`
}
type StoryShot struct {
	ID         string `json:"id"`
	DurationMS int    `json:"duration_ms"`
	Scene      string `json:"scene"`
	Camera     string `json:"camera"`
	Narration  string `json:"narration"`
	Text       string `json:"text"`
	Audio      string `json:"audio"`
}
type ShotResult struct {
	ShotID            string `json:"shot_id"`
	FromMS            int    `json:"from_ms"`
	ToMS              int    `json:"to_ms"`
	StartFrame        int    `json:"start_frame"`
	EndFrameExclusive int    `json:"end_frame_exclusive"`
	Scene             string `json:"scene"`
	Camera            string `json:"camera"`
	Text              string `json:"text"`
	Narration         string `json:"narration"`
	Audio             string `json:"audio"`
}
type StoryReport struct {
	Schema       string       `json:"schema"`
	Title        string       `json:"title"`
	FPS          int          `json:"fps"`
	DurationMS   int          `json:"duration_ms"`
	TotalFrames  int          `json:"total_frames"`
	Timeline     []ShotResult `json:"timeline"`
	SourceSHA256 string       `json:"source_sha256"`
}

func compileStory(s Story, sourcehash string) (StoryReport, error) {
	if s.FPS < 1 || s.FPS > 120 {
		return StoryReport{}, errors.New("fps must be 1..120")
	}
	if len(s.Shots) < 1 || len(s.Shots) > 1000 {
		return StoryReport{}, errors.New("shot count out of range")
	}
	if s.Canvas[0] < 64 || s.Canvas[1] < 64 {
		return StoryReport{}, errors.New("canvas too small")
	}
	out := StoryReport{Schema: "baltor.storyboard_compile/1", Title: s.Title, FPS: s.FPS, Timeline: []ShotResult{}, SourceSHA256: sourcehash}
	seen := map[string]bool{}
	ms := 0
	for _, shot := range s.Shots {
		if shot.ID == "" || seen[shot.ID] {
			return StoryReport{}, errors.New("duplicate/empty shot ID")
		}
		seen[shot.ID] = true
		if shot.DurationMS < 100 || shot.DurationMS > 120000 {
			return StoryReport{}, fmt.Errorf("invalid duration for %s", shot.ID)
		}
		start := ms
		ms += shot.DurationMS
		if ms > 3600000 {
			return StoryReport{}, errors.New("duration exceeds one hour")
		}
		startFrame := (start*s.FPS + 500) / 1000
		endFrame := (ms*s.FPS + 500) / 1000
		if endFrame <= startFrame {
			return StoryReport{}, errors.New("zero-frame shot")
		}
		out.Timeline = append(out.Timeline, ShotResult{shot.ID, start, ms, startFrame, endFrame, shot.Scene, shot.Camera, shot.Text, shot.Narration, shot.Audio})
	}
	out.DurationMS = ms
	out.TotalFrames = (ms*s.FPS + 500) / 1000
	return out, nil
}
func formatSRTTime(ms int) string {
	h := ms / 3600000
	ms %= 3600000
	m := ms / 60000
	ms %= 60000
	s := ms / 1000
	ms %= 1000
	return fmt.Sprintf("%02d:%02d:%02d,%03d", h, m, s, ms)
}
func formatSRT(rep StoryReport) string {
	var b strings.Builder
	idx := 0
	for _, sh := range rep.Timeline {
		caption := strings.TrimSpace(sh.Text)
		if caption == "" {
			continue
		}
		idx++
		fmt.Fprintf(&b, "%d\n%s --> %s\n%s\n\n", idx, formatSRTTime(sh.FromMS), formatSRTTime(sh.ToMS), caption)
	}
	return b.String()
}
func writeTimelineCSV(rep StoryReport) ([]byte, error) {
	var b strings.Builder
	w := csv.NewWriter(&b)
	w.Write([]string{"shot_id", "start_ms", "end_ms", "start_frame", "end_frame_exclusive", "scene", "camera", "text", "narration", "audio"})
	for _, x := range rep.Timeline {
		w.Write([]string{x.ShotID, strconv.Itoa(x.FromMS), strconv.Itoa(x.ToMS), strconv.Itoa(x.StartFrame), strconv.Itoa(x.EndFrameExclusive), x.Scene, x.Camera, x.Text, x.Narration, x.Audio})
	}
	w.Flush()
	return []byte(b.String()), w.Error()
}

type VariantSpec struct {
	Schema string        `json:"schema"`
	Base   string        `json:"base"`
	Axes   []VariantAxis `json:"axes"`
}
type VariantAxis struct {
	Name   string   `json:"name"`
	Values []string `json:"values"`
}
type Variant struct {
	ID     string            `json:"id"`
	Base   string            `json:"base"`
	Params map[string]string `json:"params"`
}

func variants(s VariantSpec) ([]Variant, error) {
	if len(s.Axes) < 1 || len(s.Axes) > 10 {
		return nil, errors.New("axes out of range")
	}
	out := []Variant{{Base: s.Base, Params: map[string]string{}}}
	seen := map[string]bool{}
	for _, axis := range s.Axes {
		if axis.Name == "" || seen[axis.Name] || len(axis.Values) == 0 {
			return nil, errors.New("invalid axis")
		}
		seen[axis.Name] = true
		if len(out)*len(axis.Values) > maxVariants {
			return nil, errors.New("variants exceed cap of 256")
		}
		next := []Variant{}
		for _, v := range out {
			for _, val := range axis.Values {
				if len(val) > 250 {
					return nil, errors.New("value too long")
				}
				p := map[string]string{}
				for k, z := range v.Params {
					p[k] = z
				}
				p[axis.Name] = val
				next = append(next, Variant{Base: s.Base, Params: p})
			}
		}
		out = next
	}
	for i := range out {
		b, _ := json.Marshal(out[i].Params)
		out[i].ID = fmt.Sprintf("variant-%03d-%s", i+1, hash(b)[:8])
	}
	return out, nil
}
func usage() {
	fmt.Print(`Baltor Capability Distiller v` + Version + `
No skill scripts are executed. Proposals are never automatically activatable.
Commands:
  doctor
  scan     --root DIR --out scan.json
  propose  --catalog scan.json --out proposals.json
  layout   --input layout.json --out report.json
  timeline --input story.json --out DIR
  variants --input variants.json --out variants.json
  hash     --input FILE
Use --help after any command for flags.
`)
}
func cli(args []string) error {
	if len(args) == 0 {
		usage()
		return nil
	}
	cmd := args[0]
	f := flag.NewFlagSet(cmd, flag.ContinueOnError)
	f.SetOutput(io.Discard)
	var root, input, out, catalog string
	switch cmd {
	case "version":
		fmt.Println(Version)
		return nil
	case "doctor":
		x := map[string]any{"name": "baltor-distill", "version": Version, "go_runtime": "stdlib_only", "does_not_execute_skill_scripts": true, "max_skills": maxScanSkills, "max_variants": maxVariants, "notes": "workspace/kernel isolation must be provided by external container/VM"}
		return saveJSON("", x)
	case "scan":
		f.StringVar(&root, "root", ".", "root to scan")
		f.StringVar(&out, "out", "", "JSON output")
	case "propose":
		f.StringVar(&catalog, "catalog", "", "scan JSON")
		f.StringVar(&out, "out", "", "JSON output")
	case "layout":
		f.StringVar(&input, "input", "", "layout JSON")
		f.StringVar(&out, "out", "", "report JSON")
	case "timeline":
		f.StringVar(&input, "input", "", "story JSON")
		f.StringVar(&out, "out", "", "output directory")
	case "variants":
		f.StringVar(&input, "input", "", "variation JSON")
		f.StringVar(&out, "out", "", "result JSON")
	case "hash":
		f.StringVar(&input, "input", "", "file")
	default:
		return fmt.Errorf("unknown command %q", cmd)
	}
	f.SetOutput(os.Stderr)
	if err := f.Parse(args[1:]); err != nil {
		return err
	}
	switch cmd {
	case "scan":
		r, e := scan(root)
		if e != nil {
			return e
		}
		return saveJSON(out, r)
	case "propose":
		if catalog == "" {
			return errors.New("--catalog required")
		}
		var r ScanReport
		if e := readJSON(catalog, &r); e != nil {
			return e
		}
		return saveJSON(out, map[string]any{"schema": "baltor.proposals/1", "proposals": proposals(r)})
	case "layout":
		if input == "" {
			return errors.New("--input required")
		}
		var l LayoutSpec
		if e := readJSON(input, &l); e != nil {
			return e
		}
		rep := lintLayout(l)
		if e := saveJSON(out, rep); e != nil {
			return e
		}
		if !rep.Valid {
			return errors.New("layout has errors")
		}
		return nil
	case "timeline":
		if input == "" || out == "" {
			return errors.New("--input and --out required")
		}
		b, e := os.ReadFile(input)
		if e != nil {
			return e
		}
		var s Story
		if e = json.Unmarshal(b, &s); e != nil {
			return e
		}
		rep, e := compileStory(s, hash(b))
		if e != nil {
			return e
		}
		if e = os.MkdirAll(out, 0755); e != nil {
			return e
		}
		if e = saveJSON(filepath.Join(out, "compiled_storyboard.json"), rep); e != nil {
			return e
		}
		csvb, e := writeTimelineCSV(rep)
		if e != nil {
			return e
		}
		if e = writeFile(filepath.Join(out, "timeline.csv"), csvb); e != nil {
			return e
		}
		return writeFile(filepath.Join(out, "captions.srt"), []byte(formatSRT(rep)))
	case "variants":
		if input == "" {
			return errors.New("--input required")
		}
		var s VariantSpec
		if e := readJSON(input, &s); e != nil {
			return e
		}
		a, e := variants(s)
		if e != nil {
			return e
		}
		return saveJSON(out, map[string]any{"schema": "baltor.variants/1", "count": len(a), "variants": a})
	case "hash":
		if input == "" {
			return errors.New("--input required")
		}
		b, e := os.ReadFile(input)
		if e != nil {
			return e
		}
		return saveJSON("", map[string]string{"sha256": hash(b), "file": input})
	}
	return nil
}
func main() {
	if e := cli(os.Args[1:]); e != nil {
		fmt.Fprintln(os.Stderr, "ERROR:", e)
		os.Exit(1)
	}
}

// Keep time import tied to Go 1.23 stdlib compatibility checks.
var _ = time.Second
