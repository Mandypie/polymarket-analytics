"""
Phase 5 Test Script - Demonstrates ML Engine and Strategy Evolution functionality

Run this to verify Phase 5 components are working correctly.
"""

import asyncio
import sys
from datetime import datetime

# Add backend to path
sys.path.insert(0, 'backend')

from analytics.ml_engine import (
    MLEngine,
    MarketOutcomeClassifier,
    PriceMovementPredictor,
    LiquidityForecaster,
    MarketSimilarityEmbedding,
    get_ml_engine
)
from analytics.strategy_evolution import (
    StrategyEvolutionSystem,
    StrategyParameters,
    StrategyPerformance,
    StrategyType,
    StrategyStatus,
    get_strategy_evolution_system
)


async def test_ml_engine():
    """Test ML Engine components"""
    print("=" * 60)
    print("Testing ML Engine Components")
    print("=" * 60)

    # Create ML engine
    ml_engine = await get_ml_engine()

    # Test market data
    market_data = {
        "market_id": "test_market_001",
        "question": "Will BTC hit $100K in 2024?",
        "yes_price": 0.65,
        "liquidity": 75000,
        "volume_24h": 125000,
        "category": "Crypto"
    }

    print("\n1. Testing Market Outcome Classifier")
    print("-" * 40)
    outcome_prediction = await ml_engine.outcome_classifier.predict_outcome(market_data)
    print(f"YES Probability: {outcome_prediction.yes_probability:.2%}")
    print(f"NO Probability: {outcome_prediction.no_probability:.2%}")
    print(f"Direction: {outcome_prediction.direction.value}")
    print(f"Confidence Level: {outcome_prediction.confidence_level.value}")
    print(f"Top Factors: {outcome_prediction.factors[:2]}")

    print("\n2. Testing Price Movement Predictor")
    print("-" * 40)
    price_prediction = await ml_engine.price_predictor.predict_price_movement(
        market_data, horizon_hours=24
    )
    print(f"Current Price: ${price_prediction.current_price:.2f}")
    print(f"Predicted Price: ${price_prediction.predicted_price:.2f}")
    print(f"Target Price: ${price_prediction.target_price:.2f}")
    print(f"Stop Loss: ${price_prediction.stop_loss:.2f}")
    print(f"Expected Move: {price_prediction.expected_move_pct:.2f}%")

    print("\n3. Testing Liquidity Forecaster")
    print("-" * 40)
    liquidity_forecast = await ml_engine.liquidity_forecaster.forecast_liquidity(
        market_data, timeframe_hours=24
    )
    print(f"Current Volume: ${liquidity_forecast.current_volume:,.0f}")
    print(f"Predicted Volume: ${liquidity_forecast.predicted_volume:,.0f}")
    print(f"Volume Trend: {liquidity_forecast.volume_trend}")
    print(f"Current Spread: {liquidity_forecast.current_spread:.2%}")
    print(f"Predicted Spread: {liquidity_forecast.predicted_spread:.2%}")
    print(f"Spread Trend: {liquidity_forecast.spread_trend}")

    print("\n4. Testing Market Similarity Embedding")
    print("-" * 40)

    # Create historical markets
    historical_markets = [
        {
            "market_id": "hist_001",
            "question": "Will ETH hit $10K in 2024?",
            "yes_price": 0.72,
            "liquidity": 85000,
            "volume_24h": 150000,
            "category": "Crypto",
            "outcome": "YES"
        },
        {
            "market_id": "hist_002",
            "question": "Will BTC hit $50K in 2023?",
            "yes_price": 0.45,
            "liquidity": 60000,
            "volume_24h": 90000,
            "category": "Crypto",
            "outcome": "NO"
        }
    ]

    similar_markets = await ml_engine.similarity_finder.find_similar_markets(
        market_data, historical_markets, top_k=2
    )

    print(f"Found {len(similar_markets)} similar markets:")
    for sim in similar_markets:
        print(f"  - {sim.similar_market_question}")
        print(f"    Similarity: {sim.similarity_score:.2%}")
        print(f"    Outcome: {sim.outcome}")

    print("\n✅ ML Engine Test Complete!")


async def test_strategy_evolution():
    """Test Strategy Evolution System"""
    print("\n" + "=" * 60)
    print("Testing Strategy Evolution System")
    print("=" * 60)

    # Get evolution system
    evolution_system = await get_strategy_evolution_system()

    # Initialize with base strategies
    print("\n1. Initializing Evolution System")
    print("-" * 40)

    base_strategies = [
        StrategyParameters(
            name="Edge_Based_Base",
            strategy_type=StrategyType.EDGE_BASED,
            min_confidence=0.6,
            max_position_size=1000.0,
            min_edge=0.02,
            edge_weight=0.35,
            momentum_weight=0.20,
            liquidity_weight=0.15,
            pattern_weight=0.20,
            cross_market_weight=0.10
        ),
        StrategyParameters(
            name="Momentum_Base",
            strategy_type=StrategyType.MOMENTUM,
            min_confidence=0.65,
            max_position_size=800.0,
            min_edge=0.015,
            edge_weight=0.20,
            momentum_weight=0.40,
            liquidity_weight=0.15,
            pattern_weight=0.15,
            cross_market_weight=0.10
        ),
        StrategyParameters(
            name="Liquidity_Base",
            strategy_type=StrategyType.LIQUIDITY,
            min_confidence=0.55,
            max_position_size=1200.0,
            min_edge=0.025,
            edge_weight=0.25,
            momentum_weight=0.15,
            liquidity_weight=0.35,
            pattern_weight=0.15,
            cross_market_weight=0.10
        )
    ]

    population = await evolution_system.initialize(base_strategies)
    print(f"Initialized {len(population)} base strategies")

    print("\n2. Creating Mock Performance Data")
    print("-" * 40)

    # Create mock performance data
    performance_data = {}
    for strategy in population:
        perf = StrategyPerformance(strategy_id=strategy.strategy_id)
        perf.total_trades = 50
        perf.winning_trades = 30 + hash(strategy.strategy_id) % 10
        perf.losing_trades = perf.total_trades - perf.winning_trades
        perf.total_pnl = (hash(strategy.strategy_id) % 500) - 100
        perf.max_drawdown = abs(perf.total_pnl) * 0.3
        perf.sharpe_ratio = 0.5 + (hash(strategy.strategy_id) % 20) / 10
        perf.calculate_metrics()
        performance_data[strategy.strategy_id] = perf

        print(f"{strategy.name}:")
        print(f"  Win Rate: {perf.win_rate:.2%}")
        print(f"  Total PnL: ${perf.total_pnl:.2f}")
        print(f"  Sharpe Ratio: {perf.sharpe_ratio:.2f}")

    print("\n3. Running Evolution Cycle")
    print("-" * 40)

    new_population = await evolution_system.run_evolution_cycle(performance_data)
    print(f"Evolved to Generation {evolution_system.genetic_optimizer.generation}")
    print(f"New population size: {len(new_population)}")

    print("\n4. Testing Parameter Mutation")
    print("-" * 40)

    original = base_strategies[0]
    mutated = original.mutate(mutation_rate=0.5, mutation_strength=0.3)

    print(f"Original min_confidence: {original.min_confidence}")
    print(f"Mutated min_confidence: {mutated.min_confidence}")
    print(f"Original edge_weight: {original.edge_weight}")
    print(f"Mutated edge_weight: {mutated.edge_weight}")

    print("\n5. Testing Parameter Crossover")
    print("-" * 40)

    child = base_strategies[0].crossover(base_strategies[1])
    print(f"Parent 1: {base_strategies[0].name}")
    print(f"Parent 2: {base_strategies[1].name}")
    print(f"Child edge_weight: {child.edge_weight} (avg of parents)")
    print(f"Child momentum_weight: {child.momentum_weight} (avg of parents)")

    print("\n6. Testing A/B Test Creation")
    print("-" * 40)

    active_tests = await evolution_system.get_active_ab_tests()
    print(f"Active A/B tests: {len(active_tests)}")

    if active_tests:
        for test in active_tests:
            print(f"  Test {test['test_id']}: {test['strategies']} strategies")

    print("\n7. Getting Evolution Statistics")
    print("-" * 40)

    stats = evolution_system.get_evolution_stats()
    print(f"Generation: {stats['generation']}")
    print(f"Total Strategies: {stats['total_strategies']}")
    print(f"Active Strategies: {stats['active_strategies']}")
    print(f"Testing Strategies: {stats['testing_strategies']}")
    print(f"Retired Strategies: {stats['retired_strategies']}")

    print("\n✅ Strategy Evolution Test Complete!")


async def test_integration():
    """Test integration of Phase 5 components"""
    print("\n" + "=" * 60)
    print("Testing Integration: Full Prediction with Strategy Selection")
    print("=" * 60)

    ml_engine = await get_ml_engine()
    evolution_system = await get_strategy_evolution_system()

    # Generate full prediction
    market_data = {
        "market_id": "integration_test_001",
        "question": "Will the S&P 500 reach 5000 by end of 2024?",
        "yes_price": 0.58,
        "liquidity": 45000,
        "volume_24h": 85000,
        "category": "Economics"
    }

    print("\n1. Generating Full ML Prediction")
    print("-" * 40)

    full_prediction = await ml_engine.generate_full_prediction(
        market_data=market_data,
        historical_markets=[
            {
                "market_id": "hist_sim_001",
                "question": "Will S&P 500 reach 4500 in 2023?",
                "yes_price": 0.55,
                "liquidity": 40000,
                "volume_24h": 75000,
                "category": "Economics",
                "outcome": "YES",
                "end_date": "2023-12-31T23:59:59Z"
            }
        ]
    )

    print(f"Outcome Prediction: {full_prediction['outcome']['yes_probability']:.2%} YES")
    print(f"Price Direction: {full_prediction['price']['direction']}")
    print(f"Expected Move: {full_prediction['price']['expected_move_pct']:.2f}%")
    print(f"Liquidity Forecast: {full_prediction['liquidity']['volume_trend']}")

    if full_prediction['similar_markets']:
        print(f"\nSimilar Market:")
        print(f"  Question: {full_prediction['similar_markets'][0]['similar_market_question']}")
        print(f"  Outcome: {full_prediction['similar_markets'][0]['outcome']}")

    print("\n2. Selecting Strategy for Market Conditions")
    print("-" * 40)

    # Select strategy based on conditions
    market_conditions = {
        "volatility": 0.4,
        "liquidity_score": 0.6,
        "trend_strength": 0.7
    }

    # Initialize evolution system if not already done
    if not evolution_system.strategies:
        base_strategies = [
            StrategyParameters(
                name="Test_Strategy",
                strategy_type=StrategyType.MOMENTUM,
                min_confidence=0.6,
                max_position_size=1000.0
            )
        ]
        await evolution_system.initialize(base_strategies)

    selected_strategy = await evolution_system.select_strategy_for_conditions(
        market_conditions
    )

    if selected_strategy:
        print(f"Selected Strategy: {selected_strategy.name}")
        print(f"Strategy Type: {selected_strategy.parameters.strategy_type.value}")
        print(f"Min Confidence: {selected_strategy.parameters.min_confidence}")
        print(f"Max Position Size: ${selected_strategy.parameters.max_position_size:.0f}")
    else:
        print("No strategy selected (system not fully initialized)")

    print("\n✅ Integration Test Complete!")


async def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("Phase 5 - Predictive Intelligence Test Suite")
    print("=" * 60)
    print(f"Test Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    try:
        await test_ml_engine()
        await test_strategy_evolution()
        await test_integration()

        print("\n" + "=" * 60)
        print("✅ ALL PHASE 5 TESTS PASSED!")
        print("=" * 60)
        print(f"Test Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    except Exception as e:
        print(f"\n❌ Test Failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
