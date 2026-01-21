"""
Cost tracker for LLM usage.
Tracks tokens and calculates costs across the application.
"""
import threading
from dataclasses import dataclass, field
from typing import Dict
from app.llm.models import ModelSelector


@dataclass
class NodeCost:
    """Cost tracking for a single node."""
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0
    call_count: int = 0


@dataclass
class CostReport:
    """Complete cost report for a workflow run."""
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_cost_usd: float = 0.0
    by_node: Dict[str, NodeCost] = field(default_factory=dict)
    by_model: Dict[str, NodeCost] = field(default_factory=dict)


class CostTracker:
    """
    Thread-safe cost tracking for LLM operations.
    
    Follows Single Responsibility Principle: only tracks costs,
    doesn't handle pricing logic (delegated to ModelSelector).
    """
    
    def __init__(self, model_selector: ModelSelector):
        """
        Initialize cost tracker.
        
        Args:
            model_selector: Model selector for pricing lookup
        """
        self.model_selector = model_selector
        self._lock = threading.Lock()
        self._node_costs: Dict[str, NodeCost] = {}
        self._model_costs: Dict[str, NodeCost] = {}
    
    def track_usage(
        self,
        node_name: str,
        model: str,
        input_tokens: int,
        output_tokens: int
    ):
        """
        Track token usage and calculate cost.
        
        Args:
            node_name: Name of the node making the call
            model: Model identifier
            input_tokens: Input token count
            output_tokens: Output token count
        """
        # Get pricing
        input_price, output_price = self.model_selector.get_pricing(model)
        
        # Calculate cost
        cost = (
            (input_tokens / 1000.0) * input_price +
            (output_tokens / 1000.0) * output_price
        )
        
        with self._lock:
            # Track by node
            if node_name not in self._node_costs:
                self._node_costs[node_name] = NodeCost()
            
            node_cost = self._node_costs[node_name]
            node_cost.input_tokens += input_tokens
            node_cost.output_tokens += output_tokens
            node_cost.cost_usd += cost
            node_cost.call_count += 1
            
            # Track by model
            if model not in self._model_costs:
                self._model_costs[model] = NodeCost()
            
            model_cost = self._model_costs[model]
            model_cost.input_tokens += input_tokens
            model_cost.output_tokens += output_tokens
            model_cost.cost_usd += cost
            model_cost.call_count += 1
    
    def get_report(self) -> CostReport:
        """
        Get complete cost report.
        
        Returns:
            CostReport with totals and breakdowns
        """
        with self._lock:
            # Calculate totals
            total_input = sum(nc.input_tokens for nc in self._node_costs.values())
            total_output = sum(nc.output_tokens for nc in self._node_costs.values())
            total_cost = sum(nc.cost_usd for nc in self._node_costs.values())
            
            return CostReport(
                total_input_tokens=total_input,
                total_output_tokens=total_output,
                total_cost_usd=total_cost,
                by_node=dict(self._node_costs),
                by_model=dict(self._model_costs)
            )
    
    def reset(self):
        """Reset all cost tracking."""
        with self._lock:
            self._node_costs.clear()
            self._model_costs.clear()
