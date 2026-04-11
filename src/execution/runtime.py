"""Runtime-internal provider and tool execution layer."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Callable, Mapping

from contracts import WorkflowNodeContract
from core import EvidenceRecord, GateVerdict, LineageLink, LineageLinkType, ObjectRef
from governance import GateType, GovernanceRuntime, RuntimeContext
from surfaces import ArtifactRoute, FileBackedSurfaceManager

_VENDOR_TOKENS = ("openai", "anthropic", "claude", "gpt", "gemini", "copilot", "cursor")


class ExecutionRuntimeError(RuntimeError):
    """Raised when execution cannot be prepared or normalized."""


class ExecutionStatus(StrEnum):
    COMPLETED = "completed"
    BLOCKED = "blocked"
    FAILED = "failed"
    INTERRUPTED = "interrupted"


class ExecutionEventType(StrEnum):
    STARTED = "execution-started"
    PARTIAL_OUTPUT = "partial-output-streamed"
    TOOL_CALL_REQUESTED = "tool-call-requested"
    TOOL_RESULT_RETURNED = "tool-result-returned"
    COMPLETED = "execution-completed"
    INTERRUPTED = "execution-interrupted"
    FAILED = "execution-failed"
    BLOCKED = "execution-blocked"


@dataclass(slots=True, frozen=True)
class ToolCapability:
    capability_id: str
    description: str
    allowed_pack_ids: tuple[str, ...] = ()


@dataclass(slots=True, frozen=True)
class ToolCallEnvelope:
    call_id: str
    capability_id: str
    arguments: Mapping[str, Any] = field(default_factory=dict)


@dataclass(slots=True, frozen=True)
class ToolResult:
    call_id: str
    capability_id: str
    success: bool
    output: str
    metadata: Mapping[str, str] = field(default_factory=dict)


@dataclass(slots=True, frozen=True)
class ExecutionRequest:
    request_id: str
    pack_id: str
    node_id: str
    role_id: str
    provider_id: str
    prompt: str
    requested_tool_capabilities: tuple[str, ...] = ()
    gate_type: GateType = GateType.ENTRY
    action_name: str | None = None
    metadata: Mapping[str, str] = field(default_factory=dict)


@dataclass(slots=True, frozen=True)
class ExecutionContext:
    workspace_id: str
    session_id: str
    pack_id: str
    node_id: str
    role_id: str
    allowed_tool_capabilities: tuple[str, ...] = ()
    policy_refs: tuple[str, ...] = ()
    evidence_requirements: tuple[str, ...] = ()
    host_adapter_id: str | None = None


@dataclass(slots=True, frozen=True)
class ProviderResponse:
    output_text: str
    tool_calls: tuple[ToolCallEnvelope, ...] = ()
    partial_outputs: tuple[str, ...] = ()
    metadata: Mapping[str, str] = field(default_factory=dict)


@dataclass(slots=True, frozen=True)
class ExecutionEvent:
    event_id: str
    event_type: ExecutionEventType
    message: str
    metadata: Mapping[str, str] = field(default_factory=dict)


@dataclass(slots=True, frozen=True)
class ExecutionTrace:
    trace_id: str
    request_ref: ObjectRef
    session_ref: ObjectRef
    status: ExecutionStatus
    events: tuple[ExecutionEvent, ...]
    final_output: str | None = None


@dataclass(slots=True, frozen=True)
class ApprovalCheckpoint:
    checkpoint_id: str
    gate_type: GateType
    verdict: GateVerdict
    decision_ref: ObjectRef
    missing: tuple[str, ...] = ()


@dataclass(slots=True, frozen=True)
class ExecutionOutcome:
    request: ExecutionRequest
    context: ExecutionContext
    checkpoint: ApprovalCheckpoint
    trace: ExecutionTrace
    response: ProviderResponse | None
    tool_results: tuple[ToolResult, ...]
    evidence_record: EvidenceRecord
    evidence_lineage: LineageLink
    evidence_route: ArtifactRoute | None = None


class ProviderAdapter:
    """Base adapter that absorbs provider-specific invocation details."""

    adapter_id: str

    def execute(self, request: ExecutionRequest, context: ExecutionContext) -> ProviderResponse:
        raise NotImplementedError


@dataclass(slots=True, frozen=True)
class _RegisteredTool:
    capability: ToolCapability
    executor: Callable[[ToolCallEnvelope, ExecutionContext], ToolResult]


class ToolRegistry:
    """Register runtime tool capabilities and normalize their invocation results."""

    def __init__(self) -> None:
        self._tools: dict[str, _RegisteredTool] = {}

    def register(
        self,
        capability: ToolCapability,
        executor: Callable[[ToolCallEnvelope, ExecutionContext], ToolResult],
    ) -> None:
        if capability.capability_id in self._tools:
            raise ExecutionRuntimeError(f"Duplicate tool capability {capability.capability_id!r}.")
        self._tools[capability.capability_id] = _RegisteredTool(capability=capability, executor=executor)

    def invoke(self, call: ToolCallEnvelope, context: ExecutionContext) -> ToolResult:
        try:
            registered = self._tools[call.capability_id]
        except KeyError as exc:
            raise ExecutionRuntimeError(f"Unknown tool capability {call.capability_id!r}.") from exc
        if context.allowed_tool_capabilities and call.capability_id not in context.allowed_tool_capabilities:
            raise ExecutionRuntimeError(
                f"Tool capability {call.capability_id!r} is not allowed in the current execution context."
            )
        if registered.capability.allowed_pack_ids and context.pack_id not in registered.capability.allowed_pack_ids:
            raise ExecutionRuntimeError(
                f"Tool capability {call.capability_id!r} is not available to pack {context.pack_id!r}."
            )
        return registered.executor(call, context)


def requested_capabilities_for_node(node: WorkflowNodeContract) -> tuple[str, ...]:
    """Read pack capability requests from the existing node contract extension map."""

    raw = node.extensions.get("executionCapabilities", ())
    if raw in (None, ()):
        return ()
    if isinstance(raw, str):
        values = (raw,)
    elif isinstance(raw, list):
        values = tuple(raw)
    else:
        raise ExecutionRuntimeError(
            f"Node {node.node_id!r} declared invalid executionCapabilities metadata."
        )
    normalized: list[str] = []
    for value in values:
        if not isinstance(value, str) or not value.strip():
            raise ExecutionRuntimeError(
                f"Node {node.node_id!r} declared a non-string execution capability."
            )
        capability_id = value.strip()
        if any(token in capability_id.lower() for token in _VENDOR_TOKENS):
            raise ExecutionRuntimeError(
                f"Node {node.node_id!r} bound a vendor-specific capability {capability_id!r}."
            )
        normalized.append(capability_id)
    return tuple(normalized)


class ExecutionRuntime:
    """Execute provider/tool work under governance with a normalized trace."""

    def __init__(
        self,
        *,
        governance: GovernanceRuntime,
        tool_registry: ToolRegistry | None = None,
        provider_adapters: Mapping[str, ProviderAdapter] | None = None,
        surfaces: FileBackedSurfaceManager | None = None,
    ) -> None:
        self._governance = governance
        self._tool_registry = tool_registry or ToolRegistry()
        self._providers = dict(provider_adapters or {})
        self._surfaces = surfaces

    @property
    def tool_registry(self) -> ToolRegistry:
        return self._tool_registry

    def register_provider(self, adapter: ProviderAdapter) -> None:
        if adapter.adapter_id in self._providers:
            raise ExecutionRuntimeError(f"Duplicate provider adapter {adapter.adapter_id!r}.")
        self._providers[adapter.adapter_id] = adapter

    def execute(self, request: ExecutionRequest, context: ExecutionContext) -> ExecutionOutcome:
        self._validate_request(request, context)
        runtime_context = RuntimeContext(
            workspace_id=context.workspace_id,
            session_id=context.session_id,
            pack_id=context.pack_id,
            node_id=context.node_id,
            action=request.action_name or f"execution.{request.request_id}",
        )
        evaluation = self._governance.evaluate(runtime_context, request.gate_type)
        checkpoint = ApprovalCheckpoint(
            checkpoint_id=f"checkpoint.{request.request_id}",
            gate_type=request.gate_type,
            verdict=evaluation.decision.verdict,
            decision_ref=ObjectRef(kind="gate-decision", object_id=evaluation.decision.decision_id),
            missing=evaluation.decision.missing,
        )

        events: list[ExecutionEvent] = []

        def add_event(
            event_type: ExecutionEventType,
            message: str,
            *,
            metadata: Mapping[str, str] | None = None,
        ) -> None:
            events.append(
                ExecutionEvent(
                    event_id=f"{request.request_id}.{len(events) + 1}",
                    event_type=event_type,
                    message=message,
                    metadata=dict(metadata or {}),
                )
            )

        add_event(
            ExecutionEventType.STARTED,
            f"Execution started for provider {request.provider_id}.",
            metadata={"nodeId": request.node_id, "roleId": request.role_id},
        )

        if checkpoint.verdict != GateVerdict.ALLOW:
            add_event(
                ExecutionEventType.BLOCKED,
                "Execution blocked before provider invocation.",
                metadata={"verdict": checkpoint.verdict.value},
            )
            trace = self._build_trace(
                request=request,
                context=context,
                status=ExecutionStatus.BLOCKED,
                events=events,
                final_output=None,
            )
            return self._finalize_outcome(
                request=request,
                context=context,
                checkpoint=checkpoint,
                trace=trace,
                response=None,
                tool_results=(),
            )

        try:
            adapter = self._providers[request.provider_id]
        except KeyError as exc:
            raise ExecutionRuntimeError(f"Unknown provider adapter {request.provider_id!r}.") from exc

        try:
            response = adapter.execute(request, context)
            for partial_output in response.partial_outputs:
                add_event(
                    ExecutionEventType.PARTIAL_OUTPUT,
                    partial_output,
                    metadata={"providerId": request.provider_id},
                )
            tool_results = self._run_tool_calls(
                request=request,
                context=context,
                tool_calls=response.tool_calls,
                add_event=add_event,
            )
            add_event(
                ExecutionEventType.COMPLETED,
                "Execution completed successfully.",
                metadata={"providerId": request.provider_id},
            )
            trace = self._build_trace(
                request=request,
                context=context,
                status=ExecutionStatus.COMPLETED,
                events=events,
                final_output=response.output_text,
            )
            return self._finalize_outcome(
                request=request,
                context=context,
                checkpoint=checkpoint,
                trace=trace,
                response=response,
                tool_results=tool_results,
            )
        except Exception as exc:
            add_event(
                ExecutionEventType.FAILED,
                "Execution failed.",
                metadata={"error": str(exc)},
            )
            trace = self._build_trace(
                request=request,
                context=context,
                status=ExecutionStatus.FAILED,
                events=events,
                final_output=None,
            )
            return self._finalize_outcome(
                request=request,
                context=context,
                checkpoint=checkpoint,
                trace=trace,
                response=None,
                tool_results=(),
            )

    def _validate_request(self, request: ExecutionRequest, context: ExecutionContext) -> None:
        if request.pack_id != context.pack_id or request.node_id != context.node_id or request.role_id != context.role_id:
            raise ExecutionRuntimeError("Execution request and context must agree on pack/node/role identity.")
        if request.requested_tool_capabilities and context.allowed_tool_capabilities:
            unknown = sorted(set(request.requested_tool_capabilities) - set(context.allowed_tool_capabilities))
            if unknown:
                raise ExecutionRuntimeError(
                    f"Requested tool capabilities are outside the current execution context: {unknown}."
                )

    def _run_tool_calls(
        self,
        *,
        request: ExecutionRequest,
        context: ExecutionContext,
        tool_calls: tuple[ToolCallEnvelope, ...],
        add_event: Callable[..., None],
    ) -> tuple[ToolResult, ...]:
        tool_results: list[ToolResult] = []
        for call in tool_calls:
            if request.requested_tool_capabilities and call.capability_id not in request.requested_tool_capabilities:
                raise ExecutionRuntimeError(
                    f"Provider requested undeclared tool capability {call.capability_id!r}."
                )
            add_event(
                ExecutionEventType.TOOL_CALL_REQUESTED,
                f"Tool call requested for {call.capability_id}.",
                metadata={"callId": call.call_id},
            )
            result = self._tool_registry.invoke(call, context)
            tool_results.append(result)
            add_event(
                ExecutionEventType.TOOL_RESULT_RETURNED,
                f"Tool result returned for {result.capability_id}.",
                metadata={"callId": result.call_id, "success": str(result.success).lower()},
            )
        return tuple(tool_results)

    def _build_trace(
        self,
        *,
        request: ExecutionRequest,
        context: ExecutionContext,
        status: ExecutionStatus,
        events: list[ExecutionEvent],
        final_output: str | None,
    ) -> ExecutionTrace:
        return ExecutionTrace(
            trace_id=f"trace.{request.request_id}",
            request_ref=ObjectRef(kind="execution-request", object_id=request.request_id),
            session_ref=ObjectRef(kind="session-state", object_id=context.session_id),
            status=status,
            events=tuple(events),
            final_output=final_output,
        )

    def _finalize_outcome(
        self,
        *,
        request: ExecutionRequest,
        context: ExecutionContext,
        checkpoint: ApprovalCheckpoint,
        trace: ExecutionTrace,
        response: ProviderResponse | None,
        tool_results: tuple[ToolResult, ...],
    ) -> ExecutionOutcome:
        evidence_id = f"evidence.execution.{request.request_id}"
        lineage = LineageLink(
            link_id=f"lineage.execution.{request.request_id}",
            link_type=LineageLinkType.DERIVED_FROM,
            source_ref=ObjectRef(kind="execution-trace", object_id=trace.trace_id),
            target_ref=ObjectRef(kind="evidence", object_id=evidence_id),
            rationale="Execution evidence was materialized from the runtime trace.",
        )
        evidence = EvidenceRecord(
            evidence_id=evidence_id,
            evidence_type="execution-trace",
            session_ref=trace.session_ref,
            node_ref=ObjectRef(kind="node", object_id=context.node_id),
            artifact_refs=(),
            outcome_or_verdict=trace.status.value,
            source_pointer=f"execution-trace:{trace.trace_id}",
            lineage_link_refs=(ObjectRef(kind="lineage-link", object_id=lineage.link_id),),
        )
        evidence_route = None
        if self._surfaces is not None:
            summary = self._summarize_trace(trace, checkpoint, response, tool_results)
            evidence_route = self._surfaces.emit_evidence(
                pack_id=request.pack_id,
                record=evidence,
                summary=summary,
            )
        return ExecutionOutcome(
            request=request,
            context=context,
            checkpoint=checkpoint,
            trace=trace,
            response=response,
            tool_results=tool_results,
            evidence_record=evidence,
            evidence_lineage=lineage,
            evidence_route=evidence_route,
        )

    def _summarize_trace(
        self,
        trace: ExecutionTrace,
        checkpoint: ApprovalCheckpoint,
        response: ProviderResponse | None,
        tool_results: tuple[ToolResult, ...],
    ) -> str:
        lines = [
            f"trace_id: {trace.trace_id}",
            f"status: {trace.status.value}",
            f"gate_verdict: {checkpoint.verdict.value}",
            f"event_count: {len(trace.events)}",
            f"tool_result_count: {len(tool_results)}",
        ]
        if response is not None:
            lines.append(f"output_preview: {response.output_text[:120]}")
        if checkpoint.missing:
            lines.append("missing: " + ", ".join(checkpoint.missing))
        return "\n".join(lines)
