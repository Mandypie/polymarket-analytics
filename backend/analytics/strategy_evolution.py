"""
Strategy Evolution System for Polymarket Analytics Platform

Provides genetic algorithm optimization, live A/B testing,
auto-retirement of underperforming strategies, and meta-strategy selection.
"""

import logging
import random
import uuid
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
import numpy as np

logger = logging.getLogger(__name__)


class StrategyStatus(Enum):
    """Strategy lifecycle status"""
    DEVELOPMENT = "DEVELOPMENT"
    TESTING = "TESTING"
    ACTIVE = "ACTIVE"
    DEGRADED = "DEGRADED"
    RETIRED = "RETIRED"


class StrategyType(Enum):
    """Strategy type enum"""
    EDGE_BASED = "edge_based"
    MOMENTUM = "momentum"
    MEAN_REVERSION = "mean_reversion"
    LIQUIDITY = "liquidity"
    PATTERN_BASED = "pattern_based"
    ML_ENHANCED = "ml_enhanced"
    META = "meta"


@dataclass
class StrategyParameters:
    """Strategy parameters chromosome"""
    name: str
    strategy_type: StrategyType

    # Core parameters
    min_confidence: float = 0.6
    max_position_size: float = 1000.0
    min_edge: float = 0.02

    # Signal weights
    edge_weight: float = 0.3
    momentum_weight: float = 0.2
    liquidity_weight: float = 0.15
    pattern_weight: float = 0.2
    cross_market_weight: float = 0.15

    # Risk management
    stop_loss_pct: Optional[float] = None
    take_profit_pct: Optional[float] = None
    max_open_positions: int = 10

    # Timing parameters
    signal_freshness_threshold: float = 0.7
    hold_time_hours: int = 24

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "name": self.name,
            "strategy_type": self.strategy_type.value,
            "min_confidence": self.min_confidence,
            "max_position_size": self.max_position_size,
            "min_edge": self.min_edge,
            "edge_weight": self.edge_weight,
            "momentum_weight": self.momentum_weight,
            "liquidity_weight": self.liquidity_weight,
            "pattern_weight": self.pattern_weight,
            "cross_market_weight": self.cross_market_weight,
            "stop_loss_pct": self.stop_loss_pct,
            "take_profit_pct": self.take_profit_pct,
            "max_open_positions": self.max_open_positions,
            "signal_freshness_threshold": self.signal_freshness_threshold,
            "hold_time_hours": self.hold_time_hours
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StrategyParameters":
        """Create from dictionary"""
        return cls(
            name=data["name"],
            strategy_type=StrategyType(data["strategy_type"]),
            min_confidence=data.get("min_confidence", 0.6),
            max_position_size=data.get("max_position_size", 1000.0),
            min_edge=data.get("min_edge", 0.02),
            edge_weight=data.get("edge_weight", 0.3),
            momentum_weight=data.get("momentum_weight", 0.2),
            liquidity_weight=data.get("liquidity_weight", 0.15),
            pattern_weight=data.get("pattern_weight", 0.2),
            cross_market_weight=data.get("cross_market_weight", 0.15),
            stop_loss_pct=data.get("stop_loss_pct"),
            take_profit_pct=data.get("take_profit_pct"),
            max_open_positions=data.get("max_open_positions", 10),
            signal_freshness_threshold=data.get("signal_freshness_threshold", 0.7),
            hold_time_hours=data.get("hold_time_hours", 24)
        )

    def mutate(self, mutation_rate: float = 0.1, mutation_strength: float = 0.2) -> "StrategyParameters":
        """Create mutated copy of parameters"""
        new_params = StrategyParameters(
            name=f"{self.name}_mutated_{uuid.uuid4().hex[:6]}",
            strategy_type=self.strategy_type,
            min_confidence=self._mutate_value(self.min_confidence, mutation_rate, mutation_strength, 0.5, 0.95),
            max_position_size=self._mutate_value(self.max_position_size, mutation_rate, mutation_strength, 100, 10000),
            min_edge=self._mutate_value(self.min_edge, mutation_rate, mutation_strength, 0.005, 0.1),
            edge_weight=self._mutate_weights([self.edge_weight, self.momentum_weight, self.liquidity_weight,
                                               self.pattern_weight, self.cross_market_weight], mutation_rate)[0],
            momentum_weight=self._mutate_weights([self.edge_weight, self.momentum_weight, self.liquidity_weight,
                                                  self.pattern_weight, self.cross_market_weight], mutation_rate)[1],
            liquidity_weight=self._mutate_weights([self.edge_weight, self.momentum_weight, self.liquidity_weight,
                                                    self.pattern_weight, self.cross_market_weight], mutation_rate)[2],
            pattern_weight=self._mutate_weights([self.edge_weight, self.momentum_weight, self.liquidity_weight,
                                                  self.pattern_weight, self.cross_market_weight], mutation_rate)[3],
            cross_market_weight=self._mutate_weights([self.edge_weight, self.momentum_weight, self.liquidity_weight,
                                                      self.pattern_weight, self.cross_market_weight], mutation_rate)[4],
            stop_loss_pct=self._mutate_value(self.stop_loss_pct, mutation_rate, mutation_strength, 0.01, 0.2) if self.stop_loss_pct else None,
            take_profit_pct=self._mutate_value(self.take_profit_pct, mutation_rate, mutation_strength, 0.02, 0.5) if self.take_profit_pct else None,
            max_open_positions=int(self._mutate_value(float(self.max_open_positions), mutation_rate, mutation_strength, 1, 20)),
            signal_freshness_threshold=self._mutate_value(self.signal_freshness_threshold, mutation_rate, mutation_strength, 0.5, 1.0),
            hold_time_hours=int(self._mutate_value(float(self.hold_time_hours), mutation_rate, mutation_strength, 1, 168))
        )
        return new_params

    def _mutate_value(self, value: Optional[float], rate: float, strength: float, min_val: float, max_val: float) -> float:
        """Mutate a single value"""
        if value is None:
            return random.uniform(min_val, max_val)

        if random.random() < rate:
            change = random.uniform(-strength, strength)
            new_value = value * (1 + change)
            return max(min_val, min(max_val, new_value))
        return value

    def _mutate_weights(self, weights: List[float], rate: float) -> List[float]:
        """Mutate weights while maintaining sum = 1"""
        if random.random() < rate:
            # Add noise to weights
            noise = [random.uniform(-0.1, 0.1) for _ in weights]
            new_weights = [w + n for w, n in zip(weights, noise)]

            # Normalize to sum = 1
            total = sum(new_weights)
            if total > 0:
                new_weights = [w / total for w in new_weights]
            return new_weights
        return weights

    def crossover(self, other: "StrategyParameters") -> "StrategyParameters":
        """Create child by crossover with another strategy"""
        child = StrategyParameters(
            name=f"{self.name}_cross_{uuid.uuid4().hex[:6]}",
            strategy_type=self.strategy_type if random.random() < 0.5 else other.strategy_type,
            min_confidence=self.min_confidence if random.random() < 0.5 else other.min_confidence,
            max_position_size=self.max_position_size if random.random() < 0.5 else other.max_position_size,
            min_edge=self.min_edge if random.random() < 0.5 else other.min_edge,
            # Blend weights
            edge_weight=(self.edge_weight + other.edge_weight) / 2,
            momentum_weight=(self.momentum_weight + other.momentum_weight) / 2,
            liquidity_weight=(self.liquidity_weight + other.liquidity_weight) / 2,
            pattern_weight=(self.pattern_weight + other.pattern_weight) / 2,
            cross_market_weight=(self.cross_market_weight + other.cross_market_weight) / 2,
            stop_loss_pct=self.stop_loss_pct if random.random() < 0.5 else other.stop_loss_pct,
            take_profit_pct=self.take_profit_pct if random.random() < 0.5 else other.take_profit_pct,
            max_open_positions=int((self.max_open_positions + other.max_open_positions) / 2),
            signal_freshness_threshold=(self.signal_freshness_threshold + other.signal_freshness_threshold) / 2,
            hold_time_hours=int((self.hold_time_hours + other.hold_time_hours) / 2)
        )
        return child


@dataclass
class StrategyPerformance:
    """Strategy performance metrics"""
    strategy_id: str
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    total_pnl: float = 0.0
    max_drawdown: float = 0.0
    sharpe_ratio: float = 0.0
    win_rate: float = 0.0
    avg_trade_pnl: float = 0.0
    profit_factor: float = 0.0

    # A/B test metrics
    variant_id: Optional[str] = None
    is_control: bool = False

    def calculate_metrics(self) -> None:
        """Calculate derived metrics"""
        if self.total_trades > 0:
            self.win_rate = self.winning_trades / self.total_trades
            self.avg_trade_pnl = self.total_pnl / self.total_trades

        if self.losing_trades > 0:
            avg_win = self.total_pnl / max(1, self.winning_trades)
            avg_loss = abs(self.total_pnl) / max(1, self.losing_trades)
            self.profit_factor = avg_win / avg_loss if avg_loss > 0 else 0

    def fitness_score(self) -> float:
        """Calculate fitness score for genetic algorithm"""
        # Weighted combination of metrics
        weights = {
            "sharpe": 0.3,
            "win_rate": 0.25,
            "total_pnl": 0.25,
            "profit_factor": 0.2
        }

        normalized_metrics = {
            "sharpe": max(0, min(1, self.sharpe_ratio / 3)),
            "win_rate": self.win_rate,
            "total_pnl": max(0, min(1, self.total_pnl / 1000)),
            "profit_factor": max(0, min(1, self.profit_factor / 3))
        }

        fitness = sum(
            normalized_metrics[k] * weights[k]
            for k in weights
        )

        return fitness

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "strategy_id": self.strategy_id,
            "total_trades": self.total_trades,
            "winning_trades": self.winning_trades,
            "losing_trades": self.losing_trades,
            "total_pnl": self.total_pnl,
            "max_drawdown": self.max_drawdown,
            "sharpe_ratio": self.sharpe_ratio,
            "win_rate": self.win_rate,
            "avg_trade_pnl": self.avg_trade_pnl,
            "profit_factor": self.profit_factor,
            "variant_id": self.variant_id,
            "is_control": self.is_control,
            "fitness_score": self.fitness_score()
        }


@dataclass
class EvolvedStrategy:
    """An evolved strategy with parameters and performance"""
    strategy_id: str
    name: str
    parameters: StrategyParameters
    status: StrategyStatus
    generation: int
    created_at: datetime
    performance: StrategyPerformance = field(default_factory=StrategyPerformance)

    # A/B testing
    variant_of: Optional[str] = None
    ab_test_start: Optional[datetime] = None
    ab_test_end: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "strategy_id": self.strategy_id,
            "name": self.name,
            "parameters": self.parameters.to_dict(),
            "status": self.status.value,
            "generation": self.generation,
            "created_at": self.created_at.isoformat(),
            "performance": self.performance.to_dict(),
            "variant_of": self.variant_of,
            "ab_test_start": self.ab_test_start.isoformat() if self.ab_test_start else None,
            "ab_test_end": self.ab_test_end.isoformat() if self.ab_test_end else None
        }


class GeneticAlgorithmOptimizer:
    """
    Genetic algorithm for strategy parameter optimization.

    Evolves strategy parameters over generations to maximize performance.
    """

    def __init__(
        self,
        population_size: int = 20,
        mutation_rate: float = 0.15,
        crossover_rate: float = 0.7,
        elite_ratio: float = 0.2
    ):
        self.population_size = population_size
        self.mutation_rate = mutation_rate
        self.crossover_rate = crossover_rate
        self.elite_ratio = elite_ratio
        self.generation = 0
        self.population: List[EvolvedStrategy] = []
        self.history: List[Dict[str, Any]] = []

    def initialize_population(
        self,
        base_parameters: List[StrategyParameters]
    ) -> List[EvolvedStrategy]:
        """Initialize population from base parameters"""
        self.population = []
        self.generation = 0

        for i, params in enumerate(base_parameters):
            strategy = EvolvedStrategy(
                strategy_id=f"gen0_{uuid.uuid4().hex[:8]}",
                name=f"Strategy_{i}",
                parameters=params,
                status=StrategyStatus.DEVELOPMENT,
                generation=0,
                created_at=datetime.now(),
                performance=StrategyPerformance(strategy_id=f"gen0_{i}")
            )
            self.population.append(strategy)

        self._record_generation()
        return self.population

    def evolve(
        self,
        performance_data: Dict[str, StrategyPerformance]
    ) -> List[EvolvedStrategy]:
        """
        Evolve population based on performance data.

        Args:
            performance_data: Performance metrics for each strategy

        Returns:
            New population for next generation
        """
        # Update performance
        for strategy in self.population:
            if strategy.strategy_id in performance_data:
                strategy.performance = performance_data[strategy.strategy_id]

        # Sort by fitness
        ranked = sorted(
            self.population,
            key=lambda s: s.performance.fitness_score(),
            reverse=True
        )

        # Select elite (top performers)
        elite_count = int(len(ranked) * self.elite_ratio)
        elites = ranked[:elite_count]

        # Create new generation
        new_population = []

        # Keep elites unchanged
        for elite in elites:
            new_strategy = EvolvedStrategy(
                strategy_id=f"gen{self.generation + 1}_{uuid.uuid4().hex[:8]}",
                name=f"{elite.name}_G{self.generation + 1}",
                parameters=elite.parameters,
                status=StrategyStatus.ACTIVE,
                generation=self.generation + 1,
                created_at=datetime.now(),
                performance=StrategyPerformance(strategy_id=elite.strategy_id)
            )
            new_population.append(new_strategy)

        # Generate offspring through crossover and mutation
        while len(new_population) < self.population_size:
            # Tournament selection
            parent1 = self._tournament_select(ranked)
            parent2 = self._tournament_select(ranked)

            # Crossover
            if random.random() < self.crossover_rate:
                child_params = parent1.parameters.crossover(parent2.parameters)
            else:
                child_params = parent1.parameters

            # Mutation
            if random.random() < self.mutation_rate:
                child_params = child_params.mutate(self.mutation_rate)

            # Create child
            child = EvolvedStrategy(
                strategy_id=f"gen{self.generation + 1}_{uuid.uuid4().hex[:8]}",
                name=f"Evolved_{len(new_population)}",
                parameters=child_params,
                status=StrategyStatus.TESTING,
                generation=self.generation + 1,
                created_at=datetime.now(),
                performance=StrategyPerformance(strategy_id=f"gen{self.generation + 1}_{len(new_population)}")
            )
            new_population.append(child)

        self.population = new_population
        self.generation += 1

        self._record_generation()
        return self.population

    def _tournament_select(self, ranked: List[EvolvedStrategy], tournament_size: int = 3) -> EvolvedStrategy:
        """Select strategy using tournament selection"""
        tournament = random.sample(ranked, min(tournament_size, len(ranked)))
        return max(tournament, key=lambda s: s.performance.fitness_score())

    def _record_generation(self) -> None:
        """Record generation statistics"""
        if not self.population:
            return

        fitnesses = [s.performance.fitness_score() for s in self.population]

        self.history.append({
            "generation": self.generation,
            "avg_fitness": np.mean(fitnesses),
            "max_fitness": np.max(fitnesses),
            "min_fitness": np.min(fitnesses),
            "population_size": len(self.population)
        })

    def get_best_strategy(self) -> Optional[EvolvedStrategy]:
        """Get best performing strategy"""
        if not self.population:
            return None
        return max(self.population, key=lambda s: s.performance.fitness_score())


class ABTestManager:
    """
    A/B testing manager for strategies.

    Runs parallel tests of strategy variants to determine
    statistically significant improvements.
    """

    def __init__(self, min_sample_size: int = 50, confidence_level: float = 0.95):
        self.min_sample_size = min_sample_size
        self.confidence_level = confidence_level
        self.active_tests: Dict[str, List[EvolvedStrategy]] = {}
        self.completed_tests: List[Dict[str, Any]] = []

    def create_test(
        self,
        control_strategy: EvolvedStrategy,
        variant_strategies: List[EvolvedStrategy]
    ) -> str:
        """Create new A/B test"""
        test_id = uuid.uuid4().hex[:8]

        # Set control flag
        control_strategy.performance.is_control = True
        for variant in variant_strategies:
            variant.performance.is_control = False
            variant.variant_of = control_strategy.strategy_id

        # Set test dates
        now = datetime.now()
        control_strategy.ab_test_start = now
        for variant in variant_strategies:
            variant.ab_test_start = now

        self.active_tests[test_id] = [control_strategy] + variant_strategies

        logger.info(f"Created A/B test {test_id} with {len(variant_strategies)} variants")
        return test_id

    def evaluate_test(self, test_id: str) -> Optional[Dict[str, Any]]:
        """
        Evaluate A/B test results.

        Returns winner if statistically significant, None otherwise.
        """
        if test_id not in self.active_tests:
            return None

        strategies = self.active_tests[test_id]

        # Check minimum sample size
        for strategy in strategies:
            if strategy.performance.total_trades < self.min_sample_size:
                return None  # Not enough data

        # Perform statistical test
        control = next(s for s in strategies if s.performance.is_control)
        variants = [s for s in strategies if not s.performance.is_control]

        results = []
        for variant in variants:
            # Simple t-test approximation
            significance = self._calculate_significance(control.performance, variant.performance)

            results.append({
                "variant_id": variant.strategy_id,
                "variant_name": variant.name,
                "control_pnl": control.performance.total_pnl,
                "variant_pnl": variant.performance.total_pnl,
                "control_win_rate": control.performance.win_rate,
                "variant_win_rate": variant.performance.win_rate,
                "improvement_pct": ((variant.performance.total_pnl - control.performance.total_pnl) /
                                  max(0.01, abs(control.performance.total_pnl))) * 100,
                "significant": significance > (1 - self.confidence_level),
                "p_value": 1 - significance
            })

        # Determine winner
        significant_results = [r for r in results if r["significant"]]
        if significant_results:
            winner = max(significant_results, key=lambda x: x["improvement_pct"])
        else:
            winner = None

        test_result = {
            "test_id": test_id,
            "completed_at": datetime.now().isoformat(),
            "strategies": len(strategies),
            "results": results,
            "winner": winner,
            "conclusion": "STATISTICALLY_SIGNIFICANT" if winner else "INSUFFICIENT_DATA"
        }

        self.completed_tests.append(test_result)
        del self.active_tests[test_id]

        return test_result

    def _calculate_significance(
        self,
        control: StrategyPerformance,
        variant: StrategyPerformance
    ) -> float:
        """Calculate statistical significance (simplified)"""
        # Simplified z-test for proportions
        if control.total_trades < 10 or variant.total_trades < 10:
            return 0.0

        pooled_win_rate = (control.winning_trades + variant.winning_trades) / \
                         (control.total_trades + variant.total_trades)

        se = (pooled_win_rate * (1 - pooled_win_rate) * (1/control.total_trades + 1/variant.total_trades)) ** 0.5

        if se == 0:
            return 0.0

        z_score = abs(variant.win_rate - control.win_rate) / se

        # Approximate p-value from z-score
        if z_score > 1.96:
            return 0.95
        elif z_score > 1.64:
            return 0.90
        elif z_score > 1.28:
            return 0.80
        else:
            return z_score / 2.0

    def get_active_tests(self) -> List[Dict[str, Any]]:
        """Get all active tests"""
        return [
            {
                "test_id": test_id,
                "strategies": len(strategies),
                "control": next(s.name for s in strategies if s.performance.is_control),
                "started": strategies[0].ab_test_start.isoformat() if strategies else None
            }
            for test_id, strategies in self.active_tests.items()
        ]


class MetaStrategySelector:
    """
    Meta-strategy selector based on market conditions.

    Chooses the best strategy for current market conditions
    using historical performance and condition matching.
    """

    def __init__(self):
        self.condition_weights = {
            "volatility": 0.25,
            "liquidity": 0.25,
            "trend": 0.25,
            "time_of_day": 0.15,
            "day_of_week": 0.10
        }

    async def select_strategy(
        self,
        available_strategies: List[EvolvedStrategy],
        market_conditions: Dict[str, Any]
    ) -> Optional[EvolvedStrategy]:
        """
        Select best strategy for current conditions.

        Args:
            available_strategies: List of active strategies
            market_conditions: Current market condition metrics

        Returns:
            Best strategy for conditions, or None
        """
        if not available_strategies:
            return None

        # Score each strategy based on condition match
        strategy_scores = []

        for strategy in available_strategies:
            score = await self._score_strategy_for_conditions(strategy, market_conditions)
            strategy_scores.append((strategy, score))

        # Select highest scoring strategy
        strategy_scores.sort(key=lambda x: x[1], reverse=True)

        best_strategy, best_score = strategy_scores[0] if strategy_scores else (None, 0)

        logger.info(f"Meta-strategy selected: {best_strategy.name if best_strategy else 'None'} (score: {best_score:.2f})")

        return best_strategy

    async def _score_strategy_for_conditions(
        self,
        strategy: EvolvedStrategy,
        market_conditions: Dict[str, Any]
    ) -> float:
        """Score strategy match to market conditions"""
        scores = {}

        # Volatility match
        volatility = market_conditions.get("volatility", 0.5)
        if strategy.parameters.strategy_type == StrategyType.MOMENTUM:
            scores["volatility"] = 1.0 - volatility  # Momentum prefers stable
        elif strategy.parameters.strategy_type == StrategyType.MEAN_REVERSION:
            scores["volatility"] = volatility  # Mean reversion likes volatility
        else:
            scores["volatility"] = 0.5

        # Liquidity match
        liquidity = market_conditions.get("liquidity_score", 0.5)
        if strategy.parameters.strategy_type == StrategyType.LIQUIDITY:
            scores["liquidity"] = liquidity
        else:
            scores["liquidity"] = 0.5

        # Trend match
        trend = market_conditions.get("trend_strength", 0.5)
        if strategy.parameters.strategy_type == StrategyType.MOMENTUM:
            scores["trend"] = trend
        else:
            scores["trend"] = 0.5

        # Time-based factors
        now = datetime.now()
        hour = now.hour
        day = now.weekday()

        # Trading hours preference
        scores["time_of_day"] = 0.8 if 9 <= hour <= 17 else 0.4

        # Weekday preference
        scores["day_of_week"] = 0.8 if day < 5 else 0.5

        # Weighted score
        total_score = sum(
            scores[k] * self.condition_weights.get(k, 0.1)
            for k in scores
        )

        # Adjust by strategy performance
        performance_boost = strategy.performance.fitness_score() * 0.3
        total_score += performance_boost

        return max(0, min(1, total_score))


class StrategyEvolutionSystem:
    """
    Main strategy evolution system orchestrator.

    Combines genetic optimization, A/B testing, and meta-strategy selection.
    """

    def __init__(self):
        self.genetic_optimizer = GeneticAlgorithmOptimizer()
        self.ab_test_manager = ABTestManager()
        self.meta_selector = MetaStrategySelector()

        self.strategies: Dict[str, EvolvedStrategy] = {}
        self.retired_strategies: List[EvolvedStrategy] = []
        self.evolution_history: List[Dict[str, Any]] = []

    async def initialize(
        self,
        base_strategies: List[StrategyParameters]
    ) -> List[EvolvedStrategy]:
        """Initialize evolution system with base strategies"""
        population = self.genetic_optimizer.initialize_population(base_strategies)

        for strategy in population:
            self.strategies[strategy.strategy_id] = strategy

        logger.info(f"Initialized strategy evolution with {len(population)} base strategies")
        return population

    async def run_evolution_cycle(
        self,
        performance_data: Dict[str, StrategyPerformance]
    ) -> List[EvolvedStrategy]:
        """
        Run one evolution cycle.

        Args:
            performance_data: Performance metrics for current strategies

        Returns:
            New evolved strategies
        """
        # Evolve strategies
        new_population = self.genetic_optimizer.evolve(performance_data)

        # Update strategies
        for strategy in new_population:
            self.strategies[strategy.strategy_id] = strategy

        # Create A/B tests for new strategies
        await self._setup_ab_tests(new_population)

        # Auto-retire underperforming strategies
        await self._retire_underperformers()

        # Record evolution
        self._record_evolution_cycle()

        return new_population

    async def _setup_ab_tests(self, new_population: List[EvolvedStrategy]) -> None:
        """Set up A/B tests for new strategies"""
        # Group by strategy type
        by_type: Dict[StrategyType, List[EvolvedStrategy]] = {}
        for strategy in new_population:
            if strategy.parameters.strategy_type not in by_type:
                by_type[strategy.parameters.strategy_type] = []
            by_type[strategy.parameters.strategy_type].append(strategy)

        # Create tests for each type
        for strategy_type, strategies in by_type.items():
            if len(strategies) >= 2:
                # First is control, rest are variants
                control = strategies[0]
                variants = strategies[1:]

                test_id = self.ab_test_manager.create_test(control, variants)
                logger.info(f"Created A/B test {test_id} for {strategy_type.value}")

    async def _retire_underperformers(self) -> None:
        """Retire strategies that consistently underperform"""
        retirement_threshold = 0.3  # Fitness threshold
        min_trades = 20  # Minimum trades before retirement

        to_retire = []

        for strategy_id, strategy in self.strategies.items():
            if (strategy.performance.total_trades >= min_trades and
                strategy.performance.fitness_score() < retirement_threshold and
                strategy.status != StrategyStatus.RETIRED):

                strategy.status = StrategyStatus.RETIRED
                to_retire.append(strategy)

        for strategy in to_retire:
            self.retired_strategies.append(strategy)
            del self.strategies[strategy.strategy_id]

        if to_retire:
            logger.info(f"Retired {len(to_retire)} underperforming strategies")

    async def select_strategy_for_conditions(
        self,
        market_conditions: Dict[str, Any]
    ) -> Optional[EvolvedStrategy]:
        """Select best strategy using meta-strategy"""
        active_strategies = [
            s for s in self.strategies.values()
            if s.status in [StrategyStatus.ACTIVE, StrategyStatus.TESTING]
        ]

        return await self.meta_selector.select_strategy(active_strategies, market_conditions)

    async def get_ab_test_results(self) -> List[Dict[str, Any]]:
        """Get all A/B test results"""
        return self.ab_test_manager.completed_tests

    async def get_active_ab_tests(self) -> List[Dict[str, Any]]:
        """Get active A/B tests"""
        return self.ab_test_manager.get_active_tests()

    def _record_evolution_cycle(self) -> None:
        """Record evolution cycle statistics"""
        active = [s for s in self.strategies.values() if s.status == StrategyStatus.ACTIVE]
        testing = [s for s in self.strategies.values() if s.status == StrategyStatus.TESTING]

        self.evolution_history.append({
            "timestamp": datetime.now().isoformat(),
            "generation": self.genetic_optimizer.generation,
            "total_strategies": len(self.strategies),
            "active_strategies": len(active),
            "testing_strategies": len(testing),
            "retired_strategies": len(self.retired_strategies),
            "avg_fitness": np.mean([s.performance.fitness_score() for s in self.strategies.values()]),
            "best_fitness": max([s.performance.fitness_score() for s in self.strategies.values()], default=0)
        })

    def get_evolution_stats(self) -> Dict[str, Any]:
        """Get overall evolution statistics"""
        if not self.strategies:
            return {
                "total_strategies": 0,
                "active_strategies": 0,
                "generation": 0,
                "evolution_history": []
            }

        return {
            "total_strategies": len(self.strategies),
            "active_strategies": len([s for s in self.strategies.values() if s.status == StrategyStatus.ACTIVE]),
            "testing_strategies": len([s for s in self.strategies.values() if s.status == StrategyStatus.TESTING]),
            "retired_strategies": len(self.retired_strategies),
            "generation": self.genetic_optimizer.generation,
            "best_strategy": self.genetic_optimizer.get_best_strategy().to_dict() if self.genetic_optimizer.get_best_strategy() else None,
            "evolution_history": self.evolution_history[-10:],  # Last 10 cycles
            "genetic_history": self.genetic_optimizer.history[-10:]  # Last 10 generations
        }

    def get_all_strategies(self) -> List[Dict[str, Any]]:
        """Get all evolved strategies"""
        return [s.to_dict() for s in self.strategies.values()]

    def get_strategy(self, strategy_id: str) -> Optional[Dict[str, Any]]:
        """Get specific strategy"""
        strategy = self.strategies.get(strategy_id)
        return strategy.to_dict() if strategy else None


# Global strategy evolution system instance
_strategy_evolution_system: Optional[StrategyEvolutionSystem] = None


async def get_strategy_evolution_system() -> StrategyEvolutionSystem:
    """Get or create the strategy evolution system"""
    global _strategy_evolution_system
    if _strategy_evolution_system is None:
        _strategy_evolution_system = StrategyEvolutionSystem()
    return _strategy_evolution_system
