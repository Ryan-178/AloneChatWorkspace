"""
Agent编排系统示例
展示如何使用顺序、并行、DAG三种编排模式
"""
import asyncio
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from agent_framework.observability.logger import get_logger, LogLevel
from agent_framework.observability.metrics import get_metrics_collector, MetricType
from agent_framework.observability.tracer import get_tracer
from agent_framework.orchestration.sequential import SequentialFlow, SequentialOrchestrator
from agent_framework.orchestration.parallel import ParallelFlow, ParallelOrchestrator
from agent_framework.orchestration.dag import DAGOrchestrator


# 初始化可观测性
logger = get_logger("orchestration_example", level=LogLevel.INFO)
metrics = get_metrics_collector()
tracer = get_tracer("orchestration_service")


class SimpleAgent:
    """简单的示例Agent"""
    def __init__(self, name: str, delay: float = 0.1):
        self.name = name
        self.delay = delay
    
    async def run_async(self, input_data: str) -> str:
        """异步执行"""
        await asyncio.sleep(self.delay)
        result = f"[{self.name}] processed: {input_data}"
        logger.info(f"Agent {self.name} completed: {result}")
        return result
    
    def run(self, input_data: str) -> str:
        """同步执行"""
        import time
        time.sleep(self.delay)
        result = f"[{self.name}] processed: {input_data}"
        logger.info(f"Agent {self.name} completed: {result}")
        return result


def example_sequential_flow():
    """顺序编排示例"""
    logger.info("=" * 50)
    logger.info("Example 1: Sequential Flow")
    logger.info("=" * 50)
    
    with tracer.span("sequential_flow_example"):
        # 创建顺序流
        flow = SequentialFlow()
        
        # 添加步骤
        flow.add_step("step1", "Prepare Data", lambda x: f"preprocessed: {x}")
        flow.add_step("step2", "Analyze", lambda x: f"analyzed: {x}")
        flow.add_step("step3", "Format Output", lambda x: f"formatted: {x}")
        
        # 执行
        result = flow.run("initial input")
        
        logger.info(f"Sequential Flow Result: {result.success}")
        logger.info(f"Final Output: {result.final_output}")
        logger.info(f"Total Duration: {result.total_duration_ms:.2f}ms")
        
        # 显示各步骤
        for step in result.trajectory:
            logger.info(f"  Step {step.step_id}: {step.status}, duration={step.duration_ms:.2f}ms")


def example_parallel_flow():
    """并行编排示例"""
    logger.info("\n" + "=" * 50)
    logger.info("Example 2: Parallel Flow")
    logger.info("=" * 50)
    
    with tracer.span("parallel_flow_example"):
        # 创建并行流
        flow = ParallelFlow()
        
        # 添加并行任务
        flow.add_task("task_a", "Task A", lambda x: f"[A] {x}", input_data="input for A")
        flow.add_task("task_b", "Task B", lambda x: f"[B] {x}", input_data="input for B")
        flow.add_task("task_c", "Task C", lambda x: f"[C] {x}", input_data="input for C")
        
        # 执行
        result = flow.run()
        
        logger.info(f"Parallel Flow Result: {result.success}")
        logger.info(f"All Succeeded: {result.all_succeeded}")
        logger.info(f"Total Duration: {result.total_duration_ms:.2f}ms")
        
        # 显示各任务
        for task in result.results:
            logger.info(f"  Task {task.task_id}: {task.status}, duration={task.duration_ms:.2f}ms")


def example_dag_workflow():
    """DAG工作流示例"""
    logger.info("\n" + "=" * 50)
    logger.info("Example 3: DAG Workflow")
    logger.info("=" * 50)
    
    with tracer.span("dag_workflow_example"):
        # 创建DAG编排器
        orchestrator = DAGOrchestrator()
        
        # 添加节点
        orchestrator.add_node("fetch", lambda x: "data from API", "Fetch Data")
        orchestrator.add_node("process_a", lambda x: f"Process A: {x}", "Process A")
        orchestrator.add_node("process_b", lambda x: f"Process B: {x}", "Process B")
        orchestrator.add_node("merge", lambda x: f"Merged: {x['process_a']} + {x['process_b']}", "Merge Results")
        
        # 添加边（依赖关系）
        orchestrator.add_edge("fetch", "process_a")
        orchestrator.add_edge("fetch", "process_b")
        orchestrator.add_edge("process_a", "merge")
        orchestrator.add_edge("process_b", "merge")
        
        # 验证DAG
        is_valid = orchestrator.validate()
        logger.info(f"DAG Valid: {is_valid}")
        
        # 执行
        result = orchestrator.run_workflow()
        
        logger.info(f"DAG Workflow Result: {result.success}")
        logger.info(f"Total Duration: {result.total_duration_ms:.2f}ms")
        logger.info(f"Failed Nodes: {result.failed_nodes}")
        
        # 显示各节点
        for node in result.results:
            logger.info(f"  Node {node.node_id}: {node.status}, duration={node.duration_ms:.2f}ms")


async def example_async_sequential():
    """异步顺序编排示例"""
    logger.info("\n" + "=" * 50)
    logger.info("Example 4: Async Sequential Flow")
    logger.info("=" * 50)
    
    with tracer.span("async_sequential_example"):
        # 创建Agent
        agent1 = SimpleAgent("Agent1", delay=0.2)
        agent2 = SimpleAgent("Agent2", delay=0.1)
        agent3 = SimpleAgent("Agent3", delay=0.15)
        
        # 创建异步顺序流
        flow = SequentialFlow()
        flow.add_step("agent1", "Agent 1", agent1.run_async)
        flow.add_step("agent2", "Agent 2", agent2.run_async)
        flow.add_step("agent3", "Agent 3", agent3.run_async)
        
        # 执行
        result = await flow.run_async("start")
        
        logger.info(f"Async Sequential Result: {result.success}")
        logger.info(f"Final Output: {result.final_output}")


async def example_async_parallel():
    """异步并行编排示例"""
    logger.info("\n" + "=" * 50)
    logger.info("Example 5: Async Parallel Flow")
    logger.info("=" * 50)
    
    with tracer.span("async_parallel_example"):
        # 创建Agent
        agents = [
            SimpleAgent(f"Agent{i}", delay=0.1)
            for i in range(5)
        ]
        
        # 创建异步并行流
        flow = ParallelFlow()
        for i, agent in enumerate(agents):
            flow.add_task(
                f"agent_{i}",
                f"Agent {i}",
                agent.run_async,
                input_data=f"task {i}"
            )
        
        # 执行
        result = await flow.run_async()
        
        logger.info(f"Async Parallel Result: {result.success}")
        logger.info(f"Total Duration: {result.total_duration_ms:.2f}ms")


def example_metrics():
    """指标使用示例"""
    logger.info("\n" + "=" * 50)
    logger.info("Example 6: Metrics Usage")
    logger.info("=" * 50)
    
    # Counter
    metrics.create_counter("requests_total", "Total requests")
    metrics.increment("requests_total")
    metrics.increment("requests_total")
    
    # Gauge
    metrics.create_gauge("active_sessions", "Active sessions")
    metrics.set_gauge("active_sessions", 100)
    
    # Histogram
    metrics.create_histogram("request_duration", "Request duration")
    metrics.observe("request_duration", 0.1)
    metrics.observe("request_duration", 0.2)
    metrics.observe("request_duration", 0.15)
    
    # Timer context manager
    with metrics.time("operation_duration"):
        import time
        time.sleep(0.1)
    
    # Export metrics
    metric_data = metrics.export()
    logger.info(f"Metrics exported: uptime={metric_data['uptime_seconds']:.1f}s")
    logger.info(f"Total requests: {metric_data['metrics']['requests_total']['count']}")


def main():
    """主函数"""
    logger.info("🤖 Agent Orchestration Examples")
    
    try:
        # 运行所有示例
        example_sequential_flow()
        example_parallel_flow()
        example_dag_workflow()
        
        # 运行异步示例
        logger.info("\n" + "=" * 50)
        logger.info("Running async examples...")
        logger.info("=" * 50)
        asyncio.run(example_async_sequential())
        asyncio.run(example_async_parallel())
        
        # 指标示例
        example_metrics()
        
        # 显示追踪信息
        logger.info("\n" + "=" * 50)
        logger.info("Trace Information")
        logger.info("=" * 50)
        spans = tracer.export_spans()
        logger.info(f"Total spans: {len(spans)}")
        
    except Exception as e:
        logger.error(f"Example failed: {e}", exc_info=True)


if __name__ == "__main__":
    main()
