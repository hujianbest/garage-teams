import tempfile
import unittest
from pathlib import Path

from core import GateVerdict
from execution import (
    ExecutionContext,
    ExecutionRequest,
    ExecutionRuntime,
    ExecutionStatus,
    ProviderAdapter,
    ProviderResponse,
    ToolCallEnvelope,
    ToolCapability,
    ToolResult,
    requested_capabilities_for_node,
)
from foundation import WorkspaceBinding
from governance import GateType, GovernanceRule, GovernanceRuntime, GovernanceScope
from registry import build_registry
from surfaces import FileBackedSurfaceManager


class ProviderWithWorkspaceRead(ProviderAdapter):
    adapter_id = "provider.mock"

    def execute(self, request: ExecutionRequest, context: ExecutionContext) -> ProviderResponse:
        return ProviderResponse(
            output_text="Implementation draft completed.",
            partial_outputs=("Thinking through the task board.",),
            tool_calls=(
                ToolCallEnvelope(
                    call_id="tool.read.workspace",
                    capability_id="workspace.read",
                    arguments={"path": "README.md"},
                ),
            ),
        )


class ExecutionRuntimeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repo_root = Path(__file__).resolve().parents[1]

    def test_execution_runtime_runs_provider_tools_and_materializes_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            workspace = WorkspaceBinding.from_root("garage-test", Path(tmp_dir))
            runtime = ExecutionRuntime(
                governance=GovernanceRuntime(),
                surfaces=FileBackedSurfaceManager(workspace),
            )
            runtime.register_provider(ProviderWithWorkspaceRead())
            runtime.tool_registry.register(
                ToolCapability(
                    capability_id="workspace.read",
                    description="Read a workspace file.",
                    allowed_pack_ids=("coding", "product-insights"),
                ),
                lambda call, context: ToolResult(
                    call_id=call.call_id,
                    capability_id=call.capability_id,
                    success=True,
                    output=f"Read {call.arguments['path']} for {context.pack_id}.",
                ),
            )

            outcome = runtime.execute(
                ExecutionRequest(
                    request_id="exec.demo",
                    pack_id="coding",
                    node_id="coding.implement",
                    role_id="coding.implementer",
                    provider_id="provider.mock",
                    prompt="Implement the runtime execution layer.",
                    requested_tool_capabilities=("workspace.read",),
                ),
                ExecutionContext(
                    workspace_id=workspace.workspace_id,
                    session_id="session.demo",
                    pack_id="coding",
                    node_id="coding.implement",
                    role_id="coding.implementer",
                    allowed_tool_capabilities=("workspace.read",),
                ),
            )

            self.assertEqual(outcome.trace.status, ExecutionStatus.COMPLETED)
            self.assertEqual(outcome.checkpoint.verdict, GateVerdict.ALLOW)
            self.assertEqual(len(outcome.tool_results), 1)
            self.assertTrue(outcome.evidence_route is not None and outcome.evidence_route.file_path.exists())
            self.assertEqual(outcome.evidence_record.evidence_type, "execution-trace")

    def test_execution_runtime_blocks_before_provider_invocation_when_gate_requires_approval(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            workspace = WorkspaceBinding.from_root("garage-test", Path(tmp_dir))
            runtime = ExecutionRuntime(
                governance=GovernanceRuntime(
                    rules=(
                        GovernanceRule(
                            rule_id="node.execution-needs-approval",
                            scope=GovernanceScope.NODE,
                            gate_type=GateType.ENTRY,
                            verdict=GateVerdict.NEEDS_APPROVAL,
                            rationale="Implementation execution needs creator approval.",
                            applies_to=("coding.implement", "execution.exec.blocked"),
                            missing=("creator-approval",),
                        ),
                    )
                ),
                surfaces=FileBackedSurfaceManager(workspace),
            )
            runtime.register_provider(ProviderWithWorkspaceRead())

            outcome = runtime.execute(
                ExecutionRequest(
                    request_id="exec.blocked",
                    pack_id="coding",
                    node_id="coding.implement",
                    role_id="coding.implementer",
                    provider_id="provider.mock",
                    prompt="Attempt blocked execution.",
                    action_name="execution.exec.blocked",
                ),
                ExecutionContext(
                    workspace_id=workspace.workspace_id,
                    session_id="session.demo",
                    pack_id="coding",
                    node_id="coding.implement",
                    role_id="coding.implementer",
                ),
            )

            self.assertEqual(outcome.trace.status, ExecutionStatus.BLOCKED)
            self.assertIsNone(outcome.response)
            self.assertEqual(outcome.checkpoint.missing, ("creator-approval",))

    def test_reference_pack_nodes_request_capabilities_not_vendors(self) -> None:
        registry = build_registry(
            [
                self.repo_root / "packs" / "product-insights",
                self.repo_root / "packs" / "coding",
            ]
        )

        representative_nodes = (
            registry.nodes["coding.bridge-intake"],
            registry.nodes["coding.implement"],
            registry.nodes["product-insights.research"],
            registry.nodes["product-insights.bridge-ready"],
        )
        requested_capabilities = tuple(
            capability
            for node in representative_nodes
            for capability in requested_capabilities_for_node(node)
        )

        self.assertIn("llm.structuring", requested_capabilities)
        self.assertIn("llm.codegen", requested_capabilities)
        self.assertIn("llm.analysis", requested_capabilities)
        self.assertIn("llm.synthesis", requested_capabilities)
        self.assertIn("workspace.read", requested_capabilities)
        self.assertIn("workspace.write", requested_capabilities)
        for capability in requested_capabilities:
            lowered = capability.lower()
            self.assertNotIn("openai", lowered)
            self.assertNotIn("anthropic", lowered)
            self.assertNotIn("claude", lowered)
            self.assertNotIn("gpt", lowered)
            self.assertNotIn("gemini", lowered)


if __name__ == "__main__":
    unittest.main()
