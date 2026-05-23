# Run a pipeline locally

## Simulated run (no model required)

```bash
python scripts/run_pipeline.py pipeline/research-entity --simulate
```

The runner walks the pipeline DAG step-by-step, prints a trace, and
emits a sample-run JSON to stdout. With `--simulate`, harness and tool
steps return stub outputs so you can see the flow without any external
calls.

## Run with inputs from a file

```bash
echo '{"entity_name": "Acme Corp", "entity_kind": "company"}' > /tmp/in.json
python scripts/run_pipeline.py pipeline/research-entity --inputs /tmp/in.json --simulate
```

## Live run (with Ollama)

```bash
ollama pull llama3.1:8b
OH_MODEL=ollama/llama3.1:8b python scripts/run_pipeline.py pipeline/research-entity --inputs /tmp/in.json
```

The runner reads the pipeline's default `model_adapter` and invokes
the corresponding adapter manifest. Override per-run by setting
`OH_MODEL`.

## Interactive playground

For an interactive UI, run the Gradio app:

```bash
pip install -r hf-space/requirements.txt
python hf-space/app.py
# open http://127.0.0.1:7860
```

The same app deploys unchanged to Hugging Face Spaces - see
[Deploy the hub](deploy.md).
