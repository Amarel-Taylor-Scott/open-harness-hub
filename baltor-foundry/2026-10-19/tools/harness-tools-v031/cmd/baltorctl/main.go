package main

import (
	"baltor.local/harness-tools/internal/foundry"
	"encoding/json"
	"flag"
	"fmt"
	"os"
	"path/filepath"
	"sort"
	"strings"
)

func fail(err error) { fmt.Fprintln(os.Stderr, "ERROR:", err); os.Exit(1) }
func usage() {
	fmt.Printf(`Baltor Harness Tools %s — deterministic local media and DAG primitives

Usage:
  baltorctl catalog [--json]
  baltorctl doctor
  baltorctl validate --recipe recipes/demo.json
  baltorctl plan --recipe recipes/demo.json --workspace ./job [--json]
  baltorctl graph --recipe recipes/demo.json --out graph.dot
  baltorctl ingest --file input.mp4 --as reference.mp4 --workspace ./job
  baltorctl run --recipe recipes/demo.json --workspace ./job [--force] [--json]
  baltorctl inspect --run ./job/runs/<id>
  baltorctl verify --run ./job/runs/<id>
  baltorctl diff --left ./job/runs/<id> --right ./job2/runs/<id>
  baltorctl pack --run ./job/runs/<id> --out ./bundle.tar.gz

The runner accepts a closed operator catalog, never model-produced shell commands.
Workspace root is not an OS isolation boundary. Use an actual container/VM for
untrusted agents and media. No network is needed during a run.
`, foundry.Version)
}
func recipeFlags(args []string) (string, string, bool, bool) {
	fs := flag.NewFlagSet("run", flag.ExitOnError)
	p := fs.String("recipe", "", "recipe JSON")
	w := fs.String("workspace", "./baltor-job", "workspace root")
	force := fs.Bool("force", false, "replace verified/unverified owned run")
	jsonMode := fs.Bool("json", false, "emit machine-readable JSON")
	fs.Parse(args)
	if *p == "" {
		fail(fmt.Errorf("--recipe is required"))
	}
	return *p, *w, *force, *jsonMode
}
func main() {
	arguments := os.Args[1:]
	aliases := map[string]string{
		"baltor-run": "run", "baltor-verify": "verify", "baltor-plan": "plan", "baltor-graph": "graph",
		"baltor-catalog": "catalog", "baltor-ingest": "ingest", "baltor-pack": "pack", "baltor-inspect": "inspect",
		"baltor-doctor": "doctor", "baltor-validate": "validate", "baltor-diff": "diff",
	}
	if alias, ok := aliases[filepath.Base(os.Args[0])]; ok {
		arguments = append([]string{alias}, arguments...)
	}
	if len(arguments) == 0 {
		usage()
		return
	}
	cmd := arguments[0]
	switch cmd {
	case "-h", "--help", "help":
		usage()
	case "--version", "version":
		fmt.Println(foundry.Version)
	case "catalog":
		if len(arguments) > 1 && arguments[1] == "--json" {
			b, _ := json.MarshalIndent(foundry.SupportedOps, "", "  ")
			fmt.Println(string(b))
			return
		}
		names := []string{}
		for n := range foundry.SupportedOps {
			names = append(names, n)
		}
		sort.Strings(names)
		for _, k := range names {
			fmt.Printf("%-19s %s\n", k, foundry.SupportedOps[k])
		}
	case "doctor":
		report := map[string]any{"version": foundry.Version, "ffmpeg": foundry.FFmpegVersion(), "go_runtime_binary": "standalone", "sandbox": "NOT kernel/container isolated; run in a restricted container/VM for hostile inputs", "network_required": false}
		b, _ := json.MarshalIndent(report, "", "  ")
		fmt.Println(string(b))
	case "validate", "plan", "run":
		path, w, force, jsonMode := recipeFlags(arguments[1:])
		r, norm, err := foundry.ReadRecipe(path)
		if err != nil {
			fail(err)
		}
		if cmd == "validate" {
			if jsonMode {
				b, _ := json.Marshal(map[string]any{"valid": true, "job": r.Name, "nodes": len(r.Nodes), "shots": len(r.Shots)})
				fmt.Println(string(b))
			} else {
				fmt.Printf("VALID %s: %d operators, %d shots, %d bytes normalized recipe\n", r.Name, len(r.Nodes), len(r.Shots), len(norm))
			}
			return
		}
		if cmd == "plan" {
			order, err := foundry.Topological(r)
			if err != nil {
				fail(err)
			}
			id, in, rt, err := foundry.Fingerprint(r, norm, w)
			if err != nil {
				fail(err)
			}
			if jsonMode {
				b, _ := json.MarshalIndent(map[string]any{"name": r.Name, "fingerprint": id, "inputs_sha256": in, "runtime": rt, "nodes": order}, "", "  ")
				fmt.Println(string(b))
				return
			}
			fmt.Printf("JOB %s\nFINGERPRINT %s\nINPUTS %s\nRUNTIME %v\n", r.Name, id, in, rt)
			for i, n := range order {
				fmt.Printf("%02d %-18s %-16s deps=%v\n", i+1, n.ID, n.Op, n.Deps)
			}
			return
		}
		dest, manifest, cached, err := foundry.Run(w, r, norm, force)
		if err != nil {
			fail(err)
		}
		if jsonMode {
			b, _ := json.MarshalIndent(map[string]any{"run_id": manifest.RunID, "workspace_run_path": dest, "cached": cached, "nodes": len(manifest.Nodes), "artifacts": len(manifest.Files), "recipe_sha256": manifest.RecipeSHA}, "", "  ")
			fmt.Println(string(b))
			return
		}
		fmt.Printf("RUN %s\nPATH %s\nCACHED %t\nNODES %d\nARTIFACTS %d\n", manifest.RunID, dest, cached, len(manifest.Nodes), len(manifest.Files))
		for _, x := range manifest.Files {
			if strings.HasSuffix(x.Path, ".mp4") || strings.HasSuffix(x.Path, "contact_sheet.png") || strings.HasSuffix(x.Path, "frame_report.json") {
				fmt.Printf("OUTPUT %s\n", filepath.Join(dest, x.Path))
			}
		}
	case "ingest":
		fs := flag.NewFlagSet("ingest", flag.ExitOnError)
		file := fs.String("file", "", "")
		as := fs.String("as", "", "")
		w := fs.String("workspace", "./baltor-job", "")
		fs.Parse(arguments[1:])
		if *file == "" || *as == "" {
			fail(fmt.Errorf("ingest requires --file and --as"))
		}
		hash, err := foundry.Ingest(*w, *file, *as)
		if err != nil {
			fail(err)
		}
		fmt.Printf("STAGED inputs/%s\nSHA256 %s\n", *as, hash)
	case "inspect":
		fs := flag.NewFlagSet("inspect", flag.ExitOnError)
		run := fs.String("run", "", "")
		fs.Parse(arguments[1:])
		if *run == "" {
			fail(fmt.Errorf("--run required"))
		}
		m, err := foundry.Verify(*run)
		if err != nil {
			fail(err)
		}
		b, _ := json.MarshalIndent(m, "", "  ")
		fmt.Println(string(b))
	case "graph":
		fs := flag.NewFlagSet("graph", flag.ExitOnError)
		path := fs.String("recipe", "", "")
		out := fs.String("out", "", "")
		fs.Parse(arguments[1:])
		if *path == "" {
			fail(fmt.Errorf("--recipe required"))
		}
		r, _, err := foundry.ReadRecipe(*path)
		if err != nil {
			fail(err)
		}
		dot := foundry.GraphDOT(r)
		if *out == "" {
			fmt.Print(dot)
		} else {
			if err := os.WriteFile(*out, []byte(dot), 0644); err != nil {
				fail(err)
			}
			fmt.Println("GRAPH", *out)
		}
	case "verify":
		fs := flag.NewFlagSet("verify", flag.ExitOnError)
		run := fs.String("run", "", "")
		fs.Parse(arguments[1:])
		if *run == "" {
			fail(fmt.Errorf("--run required"))
		}
		m, err := foundry.Verify(*run)
		if err != nil {
			fail(err)
		}
		fmt.Printf("VERIFIED %s: %d artifacts\n", m.RunID, len(m.Files))
	case "diff":
		fs := flag.NewFlagSet("diff", flag.ExitOnError)
		a := fs.String("left", "", "")
		b := fs.String("right", "", "")
		fs.Parse(arguments[1:])
		if *a == "" || *b == "" {
			fail(fmt.Errorf("--left and --right required"))
		}
		result, err := foundry.DiffRuns(*a, *b)
		if err != nil {
			fail(err)
		}
		fmt.Println(result)
	case "pack":
		fs := flag.NewFlagSet("pack", flag.ExitOnError)
		r := fs.String("run", "", "")
		out := fs.String("out", "", "")
		fs.Parse(arguments[1:])
		if *r == "" || *out == "" {
			fail(fmt.Errorf("--run and --out required"))
		}
		if err := foundry.PackageRun(*r, *out); err != nil {
			fail(err)
		}
		fmt.Println("PACKED", *out)
	default:
		fail(fmt.Errorf("unknown command %s", cmd))
	}
}
