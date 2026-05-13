import pytest
import asyncio

from agent_framework.orchestration.sequential import SequentialFlow
from agent_framework.orchestration.parallel import ParallelFlow
from agent_framework.orchestration.dag import DAGFlow
from agent_framework.core.orchestrator import WorkflowGraph, WorkflowNode


class TestSequentialFlow:
    def test_success(self):
        flow = SequentialFlow([
            lambda x: x + 1,
            lambda x: x * 2,
        ])
        result = flow.run(5)
        assert result["success"] is True
        assert result["result"] == 12
        assert len(result["trajectory"]) == 2

    def test_failure_stops(self):
        flow = SequentialFlow([
            lambda x: x + 1,
            lambda x: 1 / 0,
            lambda x: x * 2,
        ])
        result = flow.run(5)
        assert result["success"] is False
        assert result["failed_at_step"] == 2
        assert len(result["trajectory"]) == 2

    def test_single_task(self):
        flow = SequentialFlow([
            lambda x: x.upper(),
        ])
        result = flow.run("hello")
        assert result["success"] is True
        assert result["result"] == "HELLO"

    def test_empty_tasks(self):
        flow = SequentialFlow([])
        result = flow.run(1)
        assert result["success"] is True
        assert result["result"] == 1


class TestParallelFlow:
    @pytest.mark.asyncio
    async def test_success(self):
        flow = ParallelFlow([
            lambda: 1,
            lambda: 2,
        ])
        result = await flow.run()
        assert result["success"] is True
        outputs = [r["output"] for r in result["results"]]
        assert sorted(outputs) == [1, 2]

    @pytest.mark.asyncio
    async def test_partial_failure(self):
        flow = ParallelFlow([
            lambda: 1,
            lambda: 1 / 0,
        ])
        result = await flow.run()
        assert result["success"] is False
        assert any(r["status"] == "failed" for r in result["results"])

    @pytest.mark.asyncio
    async def test_async_task(self):
        async def async_task():
            await asyncio.sleep(0.01)
            return "async"

        flow = ParallelFlow([
            async_task,
            lambda: "sync",
        ])
        result = await flow.run()
        assert result["success"] is True
        outputs = [r["output"] for r in result["results"]]
        assert "async" in outputs
        assert "sync" in outputs

    @pytest.mark.asyncio
    async def test_empty_tasks(self):
        flow = ParallelFlow([])
        result = await flow.run()
        assert result["success"] is True
        assert result["results"] == []


class TestDAGFlow:
    def test_linear_dag(self):
        graph = WorkflowGraph(
            nodes=[
                WorkflowNode(id="a", agent=lambda x: x + 1),
                WorkflowNode(id="b", agent=lambda x: x * 2, dependencies=["a"]),
            ],
            edges=[("a", "b")],
        )
        flow = DAGFlow(graph)
        result = flow.run(5)
        assert result["success"] is True
        assert result["results"]["b"] == 12
        assert len(result["trajectory"]) == 2

    def test_conditional_skip(self):
        graph = WorkflowGraph(
            nodes=[
                WorkflowNode(id="a", agent=lambda x: x + 1),
                WorkflowNode(id="b", agent=lambda x: x * 2, dependencies=["a"], condition="False"),
            ],
            edges=[("a", "b")],
        )
        flow = DAGFlow(graph)
        result = flow.run(5)
        assert result["success"] is True
        assert "b" not in result["results"]
        assert any(t["status"] == "skipped" for t in result["trajectory"])

    def test_cycle_detection(self):
        graph = WorkflowGraph(
            nodes=[
                WorkflowNode(id="a"),
                WorkflowNode(id="b"),
            ],
            edges=[("a", "b"), ("b", "a")],
        )
        flow = DAGFlow(graph)
        with pytest.raises(ValueError, match="cycles"):
            flow.run(1)

    def test_single_node(self):
        graph = WorkflowGraph(
            nodes=[WorkflowNode(id="only", agent=lambda x: x * 2)],
            edges=[],
        )
        flow = DAGFlow(graph)
        result = flow.run(5)
        assert result["success"] is True
        assert result["results"]["only"] == 10

    def test_failed_node(self):
        graph = WorkflowGraph(
            nodes=[
                WorkflowNode(id="a", agent=lambda x: x + 1),
                WorkflowNode(id="b", agent=lambda x: 1 / 0),
            ],
            edges=[("a", "b")],
        )
        flow = DAGFlow(graph)
        result = flow.run(5)
        assert result["success"] is False
        assert result["failed_node"] == "b"
        assert any(t["status"] == "failed" for t in result["trajectory"])

    def test_trajectory_fields(self):
        graph = WorkflowGraph(
            nodes=[WorkflowNode(id="a", agent=lambda x: x + 1)],
            edges=[],
        )
        flow = DAGFlow(graph)
        result = flow.run(5)
        traj = result["trajectory"][0]
        assert "node_id" in traj
        assert "status" in traj
        assert "input" in traj
        assert "output" in traj
        assert "time_ms" in traj
