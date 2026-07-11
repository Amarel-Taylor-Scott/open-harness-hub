"""Object-first Python facade for deterministic Teleon primitive pipelines.

The pyprefix runtime in ``pipeline_templates`` remains the execution/compiler
core. This module is the ergonomic authoring layer: Python authors compose real
objects, while the facade deterministically emits the same primitive handles,
step specs, compact views, and candidate-only compiled plans.
"""
from __future__ import annotations

from dataclasses import dataclass
from types import ModuleType
from typing import Any, Callable, Iterable, Mapping

from src.teleon.synthesis import pipeline_templates as _runtime


SERVES_TRUTH = False


@dataclass(frozen=True)
class Primitive:
    """Inspectable callable-backed primitive object."""

    fn: Callable[..., Any]
    handle: dict[str, Any]

    @property
    def primitive_id(self) -> str:
        return str(self.handle["primitive_id"])

    @property
    def record(self) -> dict[str, Any]:
        return dict(self.handle.get("primitive_record") or {})

    @property
    def llm_view(self) -> dict[str, Any]:
        return dict(self.handle.get("llm_view") or {})

    @property
    def label(self) -> str:
        surface = self.record.get("surface") or _runtime.py_function_src_teleon_synthesis_pipeline_templates__callable_surface(self.fn)
        return str(surface.get("name") or self.primitive_id.rsplit(":", 1)[-1])

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        return self.fn(*args, **kwargs)

    def __rshift__(self, other: "Primitive | Pipeline") -> "Pipeline":
        return Pipeline((self,)).then(other)

    def with_options(
        self,
        *,
        state_mode: str | None = None,
        input_path: str | None = None,
        output_path: str | None = None,
        input_bindings: dict[str, str] | None = None,
        output_storage: str | None = None,
        max_attempts: int | None = None,
        required: bool | None = None,
    ) -> "Primitive":
        """Return a new primitive object with deterministic handle overrides."""
        merged = dict(self.handle)
        if state_mode is not None:
            merged["state_mode"] = state_mode
        if input_path is not None:
            merged["input_path"] = input_path
        if output_path is not None:
            merged["output_path"] = output_path
        if input_bindings is not None:
            merged["input_bindings"] = dict(input_bindings)
        if output_storage is not None:
            merged["output_storage"] = output_storage
        if max_attempts is not None:
            merged["max_attempts"] = int(max_attempts)
        if required is not None:
            merged["required"] = bool(required)
        merged["callable"] = self.fn
        merged["primitive_record"] = _runtime.py_function_src_teleon_synthesis_pipeline_templates__primitive_record_from_callable(
            self.fn,
            merged,
        )
        merged["llm_view"] = _runtime.py_function_src_teleon_synthesis_pipeline_templates__compact_llm_view_from_primitive_record(
            merged["primitive_record"],
        )
        return Primitive(self.fn, merged)

    def artifact_output(self) -> "Primitive":
        return self.with_options(
            output_storage=_runtime.py_const_src_teleon_synthesis_pipeline_templates__OUTPUT_STORAGE_ARTIFACT_REF,
        )


@dataclass(frozen=True)
class Pipeline:
    """Composable primitive sequence that compiles to the existing runtime."""

    steps: tuple[Primitive, ...]

    def __rshift__(self, other: Primitive | "Pipeline") -> "Pipeline":
        return self.then(other)

    def then(self, other: Primitive | "Pipeline") -> "Pipeline":
        if isinstance(other, Pipeline):
            return Pipeline(self.steps + other.steps)
        if isinstance(other, Primitive):
            return Pipeline(self.steps + (other,))
        raise TypeError(f"unsupported pipeline object: {other!r}")

    def to_teleon_primitives(self) -> list[dict[str, Any]]:
        return [dict(step.handle) for step in self.steps]

    def compile(self, template_id: str, purpose: str | None = None) -> dict[str, Any]:
        return _runtime.py_function_src_teleon_synthesis_pipeline_templates__compile_pipeline_template_from_primitives(
            template_id,
            self.to_teleon_primitives(),
            purpose or f"Object-authored pipeline {template_id}.",
        )

    def run(self, task: Any, *, template_id: str = "object_pipeline", run_id: str | None = None) -> dict[str, Any]:
        compiled = self.compile(template_id)
        return _runtime.py_function_src_teleon_synthesis_pipeline_templates__execute_compiled_pipeline_template(
            compiled,
            task,
            py_arg_run_id=run_id,
        )

    def compact_view(self) -> str:
        return " >> ".join(step.label for step in self.steps)


def primitive(
    fn: Callable[..., Any] | None = None,
    *,
    primitive_id: str | None = None,
    state_mode: str = _runtime.py_const_src_teleon_synthesis_pipeline_templates__STATE_MODE_TASK_VALUE,
    input_path: str = "$task",
    output_path: str = "$task",
    input_bindings: dict[str, str] | None = None,
    output_storage: str = _runtime.py_const_src_teleon_synthesis_pipeline_templates__OUTPUT_STORAGE_INLINE,
    max_attempts: int = _runtime.py_const_src_teleon_synthesis_pipeline_templates__DEFAULT_MAX_ATTEMPTS,
    required: bool = True,
) -> Primitive | Callable[[Callable[..., Any]], Primitive]:
    """Decorate or wrap a callable as an object-first Teleon primitive."""

    def wrap(real_fn: Callable[..., Any]) -> Primitive:
        decorated = _runtime.py_function_src_teleon_synthesis_pipeline_templates__primitive_metadata(
            py_arg_primitive_id=primitive_id,
            py_arg_state_mode=state_mode,
            py_arg_input_path=input_path,
            py_arg_output_path=output_path,
            py_arg_input_bindings=input_bindings,
            py_arg_output_storage=output_storage,
            py_arg_max_attempts=max_attempts,
            py_arg_required=required,
        )(real_fn)
        return Primitive(
            decorated,
            _runtime.py_function_src_teleon_synthesis_pipeline_templates__coerce_primitive_handle(decorated),
        )

    if fn is None:
        return wrap
    return wrap(fn)


def pipeline(*steps: Primitive | Pipeline) -> Pipeline:
    current = Pipeline(())
    for step in steps:
        current = current.then(step)
    return current


def discover_primitives(namespace: ModuleType | Mapping[str, Any] | object) -> list[Primitive]:
    """Discover explicit primitive objects from a module, mapping, class, or object."""
    if isinstance(namespace, Mapping):
        values = namespace.values()
    else:
        values = vars(namespace).values()
    discovered: list[Primitive] = []
    for value in values:
        if isinstance(value, Primitive):
            discovered.append(value)
            continue
        if callable(value) and getattr(value, _runtime.py_const_src_teleon_synthesis_pipeline_templates__PRIMITIVE_SPEC_ATTR, None):
            discovered.append(
                Primitive(
                    value,
                    _runtime.py_function_src_teleon_synthesis_pipeline_templates__coerce_primitive_handle(value),
                )
            )
    return discovered


def compact_alias_lines(primitives: Iterable[Primitive], *, prefix: str = "P") -> list[str]:
    """Return standardized compact line records for LLM planning context."""
    lines: list[str] = []
    for index, item in enumerate(primitives):
        view = item.llm_view
        inputs = ",".join(view.get("in") or [])
        output = str(view.get("out") or "Any")
        mode = str(view.get("mode") or "-")
        storage = str(view.get("storage") or "-")
        truth = "0" if view.get("truth") is False else "1"
        lines.append(f"{prefix}{index} {item.label} {inputs}>{output} mode:{mode} storage:{storage} truth:{truth}")
    return lines
