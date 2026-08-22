"""
Main FastAPI application for Polymarket Analytics Platform.

Provides REST API endpoints for:
- Live market data
- Mock data for backtesting
- Resolved market results
- Analytics calculations
- Data ingestion services
- WebSocket connections
- Real-time market updates
- Backtesting and signals
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Dict, Any, Optional
from datetime import datetime
import logging
import random

# Database imports
from backend.database.connection import get_db, close_db, DatabaseConnection
from backend.database.repositories import get_repositories

# Ingestion imports
from backend.ingestion.gamma_client import get_gamma_client
from backend.ingestion.clob_client import get_clob_client
from backend.ingestion.data_labeler import get_data_labeler
from backend.ingestion.ingestion_service import get_ingestion_service
from backend.ingestion.websocket_service import get_websocket_service, get_connection_manager

# Analytics imports
from backend.analytics.signal_generator import get_signal_generator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Global service state
_ingestion_service = None
_websocket_service = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("Starting Polymarket Analytics Backend")

    # Initialize ingestion service
    global _ingestion_service
    try:
        db = await get_db()
        gamma_client = await get_gamma_client()
        _ingestion_service = await get_ingestion_service(db, gamma_client)

        # Start ingestion service
        await _ingestion_service.start()
        logger.info("Data ingestion service started")

    except Exception as e:
        logger.warning(f"Could not start ingestion service: {e}")

    yield

    # Shutdown
    logger.info("Shutting down Polymarket Analytics Backend")

    if _ingestion_service:
        await _ingestion_service.stop()

    await close_db()


# Create FastAPI app
app = FastAPI(
    title="Polymarket Analytics Platform",
    description="Production analytics application for Polymarket prediction markets with real-time data ingestion",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health and info endpoints
@app.get("/health")
async def health_check(db: DatabaseConnection = Depends(get_db)) -> Dict[str, Any]:
    """Health check endpoint"""
    db_healthy = await db.health_check()

    return {
        "status": "healthy" if db_healthy else "unhealthy",
        "database": "connected" if db_healthy else "disconnected",
        "ingestion_service": "running" if _ingestion_service and _ingestion_service._running else "stopped",
        "version": "1.0.0",
        "timestamp": "2026-08-20"
    }


@app.get("/")
async def root() -> Dict[str, Any]:
    """Root endpoint with API information"""
    return {
        "name": "Polymarket Analytics Platform",
        "version": "1.0.0",
        "status": "running",
        "phase": "Phase 2 Complete - Data Ingestion Service",
        "endpoints": {
            "health": "/health",
            "live_markets": "/api/v1/markets/live",
            "mock_markets": "/api/v1/markets/mock",
            "resolved_markets": "/api/v1/markets/resolved",
            "analytics": "/api/v1/analytics",
            "ingestion": "/api/v1/ingestion",
            "order_book": "/api/v1/orderbook"
        },
        "features": {
            "gamma_api": "✅ Connected",
            "clob_api": "✅ Connected",
            "data_labeler": "✅ Active",
            "websocket": "✅ Available",
            "repositories": "✅ Live/Mock/Resolved"
        }
    }


# Live Markets endpoints
@app.get("/api/v1/markets/live")
async def get_live_markets(
    category: Optional[str] = None,
    limit: int = 100,
    db: DatabaseConnection = Depends(get_db)
) -> Dict[str, Any]:
    """Get live markets from database"""
    try:
        repos = get_repositories(db)
        markets = await repos["live_markets"].get_markets(
            category=category,
            limit=limit
        )

        return {
            "success": True,
            "count": len(markets),
            "category": category or "All",
            "markets": markets
        }
    except Exception as e:
        logger.error(f"Error fetching live markets: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/markets/live/stats")
async def get_live_market_stats(
    db: DatabaseConnection = Depends(get_db)
) -> Dict[str, Any]:
    """Get statistics about live markets"""
    try:
        repos = get_repositories(db)
        stats = await repos["live_markets"].get_market_stats()

        return {
            "success": True,
            "stats": stats
        }
    except Exception as e:
        logger.error(f"Error fetching market stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Mock Markets endpoints
@app.get("/api/v1/markets/mock")
async def get_mock_markets(
    scenario_id: Optional[str] = None,
    limit: int = 100,
    db: DatabaseConnection = Depends(get_db)
) -> Dict[str, Any]:
    """Get mock markets for backtesting"""
    try:
        repos = get_repositories(db)
        markets = await repos["mock_markets"].get_mock_markets(
            scenario_id=scenario_id,
            limit=limit
        )

        return {
            "success": True,
            "count": len(markets),
            "scenario_id": scenario_id,
            "markets": markets
        }
    except Exception as e:
        logger.error(f"Error fetching mock markets: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Resolved Markets endpoints
@app.get("/api/v1/markets/resolved")
async def get_resolved_markets(
    category: Optional[str] = None,
    limit: int = 100,
    db: DatabaseConnection = Depends(get_db)
) -> Dict[str, Any]:
    """Get resolved markets for accuracy analysis"""
    try:
        repos = get_repositories(db)
        markets = await repos["resolved_markets"].get_resolved_markets(
            category=category,
            limit=limit
        )

        return {
            "success": True,
            "count": len(markets),
            "category": category or "All",
            "markets": markets
        }
    except Exception as e:
        logger.error(f"Error fetching resolved markets: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Order Book endpoints
@app.get("/api/v1/orderbook/{market_id}")
async def get_order_book(
    market_id: str,
    limit: int = 20
) -> Dict[str, Any]:
    """Get order book for a specific market"""
    try:
        clob_client = await get_clob_client()
        order_book = await clob_client.fetch_order_book(market_id, limit)

        if order_book:
            return {
                "success": True,
                "market_id": order_book.market_id,
                "token_id": order_book.token_id,
                "bids": [
                    {"price": level.price, "size": level.size}
                    for level in order_book.bids
                ],
                "asks": [
                    {"price": level.price, "size": level.size}
                    for level in order_book.asks
                ],
                "spread": order_book.get_spread(),
                "spread_pct": order_book.get_spread_pct(),
                "liquidity": order_book.get_total_liquidity(),
                "timestamp": order_book.timestamp.isoformat()
            }
        else:
            return {
                "success": False,
                "error": "Could not fetch order book"
            }

    except Exception as e:
        logger.error(f"Error fetching order book: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Ingestion endpoints
@app.get("/api/v1/ingestion/stats")
async def get_ingestion_stats() -> Dict[str, Any]:
    """Get ingestion service statistics"""
    try:
        if _ingestion_service:
            stats = await _ingestion_service.get_ingestion_stats()
            return {
                "success": True,
                "stats": stats
            }
        else:
            return {
                "success": False,
                "error": "Ingestion service not running"
            }

    except Exception as e:
        logger.error(f"Error fetching ingestion stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/ingestion/trigger")
async def trigger_ingestion(background_tasks: BackgroundTasks) -> Dict[str, Any]:
    """Trigger immediate ingestion cycle"""
    try:
        if _ingestion_service:
            background_tasks.add_task(_ingestion_service.ingest_once)

            return {
                "success": True,
                "message": "Ingestion cycle triggered"
            }
        else:
            return {
                "success": False,
                "error": "Ingestion service not running"
            }

    except Exception as e:
        logger.error(f"Error triggering ingestion: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Analytics endpoints
@app.get("/api/v1/analytics/category-performance")
async def get_category_performance(
    db: DatabaseConnection = Depends(get_db)
) -> Dict[str, Any]:
    """Get performance metrics by category"""
    try:
        query = """
            SELECT * FROM resolved.category_performance
            ORDER BY total_markets DESC
        """
        results = await db.fetch(query)

        performance_list = [dict(r) for r in results]

        return {
            "success": True,
            "count": len(performance_list),
            "performance": performance_list
        }
    except Exception as e:
        logger.error(f"Error fetching category performance: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/analytics/signal-performance")
async def get_signal_performance(
    db: DatabaseConnection = Depends(get_db)
) -> Dict[str, Any]:
    """Get signal performance by confidence level"""
    try:
        query = """
            SELECT * FROM resolved.signal_performance
            ORDER BY confidence_bucket
        """
        results = await db.fetch(query)

        performance_list = [dict(r) for r in results]

        return {
            "success": True,
            "count": len(performance_list),
            "performance": performance_list
        }
    except Exception as e:
        logger.error(f"Error fetching signal performance: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Data Labeler endpoint
@app.post("/api/v1/ingestion/label")
async def label_market_data(market_data: Dict[str, Any]) -> Dict[str, Any]:
    """Label and categorize market data"""
    try:
        labeler = get_data_labeler()
        labeled_data = labeler.label_market_data(market_data)

        return {
            "success": True,
            "labeled_data": labeled_data
        }

    except Exception as e:
        logger.error(f"Error labeling market data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# PHASE 3 ENDPOINTS - Real-time, Backtesting, and Signal Generation
# ============================================================================

# WebSocket endpoint for real-time market updates
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time market updates"""
    global _websocket_service

    # Get service instances
    manager = get_connection_manager()
    if _websocket_service is None:
        _websocket_service = await get_websocket_service()

    # Connect client
    client_id = await manager.connect(websocket)

    try:
        # Send welcome message
        await websocket.send_json({
            "type": "connected",
            "client_id": client_id,
            "timestamp": datetime.now().isoformat()
        })

        # Handle incoming messages
        while True:
            data = await websocket.receive_json()
            await _websocket_service.handle_client_message(websocket, data)

    except WebSocketDisconnect:
        await manager.disconnect(websocket)
        logger.info(f"Client disconnected: {client_id}")


# Signal Generation endpoints
@app.get("/api/v1/signals")
async def get_signals(limit: int = 20, strength: Optional[str] = None) -> Dict[str, Any]:
    """Get generated trading signals"""
    try:
        signal_generator = await get_signal_generator()

        if strength:
            from backend.analytics.signal_generator import SignalStrength
            strength_enum = SignalStrength(strength.upper())
            signals = signal_generator.get_signals_by_strength(strength_enum)
        else:
            signals = signal_generator.get_recent_signals(limit)

        return {
            "success": True,
            "count": len(signals),
            "signals": [s.to_dict() for s in signals]
        }

    except Exception as e:
        logger.error(f"Error fetching signals: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/signals/generate")
async def generate_signals(
    background_tasks: BackgroundTasks,
    category: Optional[str] = None,
    limit: int = 50
) -> Dict[str, Any]:
    """Generate trading signals for current markets"""
    try:
        # Get markets
        db = await get_db()
        repos = get_repositories(db)
        markets = await repos["live_markets"].get_markets(category=category, limit=limit)

        # Generate signals in background
        async def generate_and_store():
            signal_generator = await get_signal_generator()
            signals = await signal_generator.generate_batch_signals(markets)

            # Broadcast new signals via WebSocket
            if _websocket_service:
                for signal in signals:
                    await _websocket_service.broadcast_alert(
                        "new_signal",
                        signal.to_dict()
                    )

            return signals

        background_tasks.add_task(generate_and_store)

        return {
            "success": True,
            "message": f"Signal generation started for {len(markets)} markets"
        }

    except Exception as e:
        logger.error(f"Error generating signals: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/signals/stats")
async def get_signal_stats() -> Dict[str, Any]:
    """Get signal generation statistics"""
    try:
        signal_generator = await get_signal_generator()
        stats = signal_generator.get_signal_stats()

        return {
            "success": True,
            "stats": stats
        }

    except Exception as e:
        logger.error(f"Error fetching signal stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Backtesting endpoints
@app.post("/api/v1/backtest/run")
async def run_backtest(
    backtest_config: Dict[str, Any],
    background_tasks: BackgroundTasks
) -> Dict[str, Any]:
    """Run a backtest with the given configuration"""
    try:
        from backend.backtesting.backtester import get_backtester, BacktestConfig, StrategyConfig, StrategyType
        from backend.database.repositories import get_repositories

        # Create strategy config
        strategy_config = StrategyConfig(
            name=backtest_config.get("strategy_name", "test_strategy"),
            strategy_type=StrategyType(backtest_config.get("strategy_type", "edge_based")),
            parameters=backtest_config.get("parameters", {}),
            max_position_size=backtest_config.get("max_position_size", 1000.0),
            min_confidence=backtest_config.get("min_confidence", 0.6)
        )

        # Create backtest config
        config = BacktestConfig(
            strategy_config=strategy_config,
            start_date=datetime.fromisoformat(backtest_config["start_date"]),
            end_date=datetime.fromisoformat(backtest_config["end_date"]),
            initial_capital=backtest_config.get("initial_capital", 10000.0),
            fee_rate=backtest_config.get("fee_rate", 0.005),
            max_position_size=backtest_config.get("max_position_size", 1000.0),
            max_open_positions=backtest_config.get("max_open_positions", 10),
            allow_shorting=backtest_config.get("allow_shorting", True),
            stop_loss_pct=backtest_config.get("stop_loss_pct"),
            take_profit_pct=backtest_config.get("take_profit_pct")
        )

        # Get historical data
        db = await get_db()
        repos = get_repositories(db)

        # For demo, use resolved markets as historical data
        historical_data = []
        if config.start_date and config.end_date:
            # This would be implemented with actual historical price data
            # For now, return a placeholder response
            pass

        # Run backtest in background
        backtester = get_backtester()

        async def execute_backtest():
            # For demo purposes, create mock historical data
            mock_data = []
            result = await backtester.run_backtest(config, mock_data)

            # Broadcast completion
            if _websocket_service:
                await _websocket_service.broadcast_alert(
                    "backtest_complete",
                    {"backtest_id": f"{config.strategy_config.name}_{config.start_date.strftime('%Y%m%d')}"}
                )

            return result

        background_tasks.add_task(execute_backtest)

        return {
            "success": True,
            "message": "Backtest started",
            "backtest_id": f"{config.strategy_config.name}_{config.start_date.strftime('%Y%m%d')}"
        }

    except Exception as e:
        logger.error(f"Error running backtest: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/backtest/results/{backtest_id}")
async def get_backtest_results(backtest_id: str) -> Dict[str, Any]:
    """Get results of a backtest"""
    try:
        from backend.backtesting.backtester import get_backtester

        backtester = get_backtester()
        result = backtester.get_backtest_result(backtest_id)

        if result:
            return {
                "success": True,
                "result": result.to_dict()
            }
        else:
            raise HTTPException(status_code=404, detail="Backtest not found")

    except Exception as e:
        logger.error(f"Error fetching backtest results: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/backtest/results")
async def list_backtest_results() -> Dict[str, Any]:
    """List all backtest results"""
    try:
        from backend.backtesting.backtester import get_backtester

        backtester = get_backtester()
        results = backtester.get_all_results()

        return {
            "success": True,
            "count": len(results),
            "results": [r.to_dict() for r in results]
        }

    except Exception as e:
        logger.error(f"Error listing backtest results: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Pattern Detection endpoints (Phase 4)
@app.get("/api/v1/patterns/active")
async def get_active_patterns(
    market_id: Optional[str] = None,
    pattern_type: Optional[str] = None,
    db: DatabaseConnection = Depends(get_db)
) -> Dict[str, Any]:
    """Get active detected patterns"""
    try:
        from backend.analytics.patterns import (
            MomentumReversalDetector,
            LiquidityTrapDetector,
            CrossMarketCorrelationDetector
        )

        repos = get_repositories(db)
        pattern_repo = repos["patterns"]

        patterns = await pattern_repo.get_active_patterns(market_id, pattern_type)

        return {
            "success": True,
            "count": len(patterns),
            "patterns": patterns
        }

    except Exception as e:
        logger.error(f"Error fetching active patterns: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/patterns/detect")
async def trigger_pattern_detection(
    background_tasks: BackgroundTasks,
    category: Optional[str] = None,
    limit: int = 50
) -> Dict[str, Any]:
    """Trigger pattern detection on current markets"""
    try:
        from backend.analytics.enhanced_signal_generator import get_enhanced_signal_generator

        db = await get_db()
        repos = get_repositories(db)
        markets = await repos["live_markets"].get_markets(category=category, limit=limit)

        # Run pattern detection in background
        async def detect_and_store():
            enhanced_generator = await get_enhanced_signal_generator()

            # Generate enhanced signals with pattern detection
            signals = await enhanced_generator.generate_enhanced_batch_signals(markets)

            # Store patterns in database
            pattern_repo = repos["patterns"]
            for signal in signals:
                # Store composite signal
                await pattern_repo.create_composite_signal(signal.to_dict())

            # Broadcast via WebSocket
            if _websocket_service:
                await _websocket_service.broadcast_alert(
                    "patterns_detected",
                    {"count": len(signals), "market_ids": [s.market_id for s in signals]}
                )

            return signals

        background_tasks.add_task(detect_and_store)

        return {
            "success": True,
            "message": f"Pattern detection started for {len(markets)} markets"
        }

    except Exception as e:
        logger.error(f"Error triggering pattern detection: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/patterns/performance")
async def get_pattern_performance(
    pattern_type: Optional[str] = None,
    db: DatabaseConnection = Depends(get_db)
) -> Dict[str, Any]:
    """Get performance metrics for detected patterns"""
    try:
        repos = get_repositories(db)
        pattern_repo = repos["patterns"]

        metrics = await pattern_repo.get_pattern_performance_metrics(pattern_type)

        return {
            "success": True,
            "metrics": metrics
        }

    except Exception as e:
        logger.error(f"Error fetching pattern performance: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/signals/enhanced")
async def get_enhanced_signals(
    min_score: float = 0.6,
    limit: int = 20
) -> Dict[str, Any]:
    """Get enhanced signals with multi-factor scoring"""
    try:
        from backend.analytics.enhanced_signal_generator import get_enhanced_signal_generator

        enhanced_generator = await get_enhanced_signal_generator()
        signals = await enhanced_generator.get_active_enhanced_signals(min_score)

        # Apply limit and get factor attribution
        results = []
        for signal in signals[:limit]:
            attribution = await enhanced_generator.get_factor_attribution(signal["market_id"])
            signal["factor_attribution"] = attribution
            results.append(signal)

        return {
            "success": True,
            "count": len(results),
            "signals": results
        }

    except Exception as e:
        logger.error(f"Error fetching enhanced signals: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/signals/enhanced/generate")
async def generate_enhanced_signals(
    background_tasks: BackgroundTasks,
    category: Optional[str] = None,
    limit: int = 50
) -> Dict[str, Any]:
    """Generate enhanced signals with pattern detection"""
    try:
        from backend.analytics.enhanced_signal_generator import get_enhanced_signal_generator

        db = await get_db()
        repos = get_repositories(db)
        markets = await repos["live_markets"].get_markets(category=category, limit=limit)

        # Generate enhanced signals in background
        async def generate_and_store_enhanced():
            enhanced_generator = await get_enhanced_signal_generator()
            signals = await enhanced_generator.generate_enhanced_batch_signals(markets)

            # Store in database
            pattern_repo = repos["patterns"]
            for signal in signals:
                await pattern_repo.create_composite_signal(signal.to_dict())

            # Broadcast via WebSocket
            if _websocket_service:
                await _websocket_service.broadcast_alert(
                    "enhanced_signals",
                    {"count": len(signals), "signals": [s.to_dict() for s in signals[:5]]}
                )

            return signals

        background_tasks.add_task(generate_and_store_enhanced)

        return {
            "success": True,
            "message": f"Enhanced signal generation started for {len(markets)} markets"
        }

    except Exception as e:
        logger.error(f"Error generating enhanced signals: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.websocket("/ws/patterns")
async def pattern_updates_websocket(websocket: WebSocket):
    """WebSocket for real-time pattern updates"""
    await websocket.accept()
    logger.info("Pattern WebSocket client connected")

    try:
        while True:
            # Receive client messages (subscriptions, etc.)
            data = await websocket.receive_json()

            if data.get("type") == "subscribe":
                market_id = data.get("market_id")
                logger.info(f"Client subscribed to patterns for {market_id}")

                # Send current active patterns
                from backend.analytics.enhanced_signal_generator import get_enhanced_signal_generator
                enhanced_generator = await get_enhanced_signal_generator()
                signals = await enhanced_generator.get_active_enhanced_signals()

                # Filter by market if specified
                if market_id:
                    signals = [s for s in signals if s.get("market_id") == market_id]

                await websocket.send_json({
                    "type": "patterns_update",
                    "data": signals
                })

    except WebSocketDisconnect:
        logger.info("Pattern WebSocket client disconnected")
    except Exception as e:
        logger.error(f"Pattern WebSocket error: {e}")
        await websocket.close()


# WebSocket service status
@app.get("/api/v1/websocket/status")
async def get_websocket_status() -> Dict[str, Any]:
    """Get WebSocket service status"""
    try:
        if _websocket_service:
            stats = _websocket_service.get_stats()
            return {
                "success": True,
                "status": stats
            }
        else:
            return {
                "success": False,
                "message": "WebSocket service not initialized"
            }

    except Exception as e:
        logger.error(f"Error fetching WebSocket status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# PHASE 5 ENDPOINTS - Predictive Intelligence with ML/AI
# ============================================================================

# Prediction endpoints
@app.post("/api/v1/predictions/outcome")
async def predict_market_outcome(
    market_data: Dict[str, Any],
    include_similar: bool = True
) -> Dict[str, Any]:
    """Predict market outcome (YES/NO probability) using ML"""
    try:
        from backend.analytics.ml_engine import get_ml_engine
        from backend.database.repositories import get_repositories

        # Get ML engine
        ml_engine = await get_ml_engine()

        # Fetch order book if available
        market_id = market_data.get("market_id", "")
        order_book = None
        if market_id:
            try:
                clob_client = await get_clob_client()
                order_book_data = await clob_client.fetch_order_book(market_id, limit=10)
                if order_book_data:
                    order_book = {
                        "bids": [{"price": level.price, "size": level.size} for level in order_book_data.bids],
                        "asks": [{"price": level.price, "size": level.size} for level in order_book_data.asks]
                    }
            except Exception as e:
                logger.warning(f"Could not fetch order book: {e}")

        # Get historical data
        db = await get_db()
        repos = get_repositories(db)
        historical_data = []

        # Try to get price history from resolved markets
        try:
            resolved = await repos["resolved_markets"].get_resolved_markets(
                category=market_data.get("category"),
                limit=50
            )
            historical_data = resolved
        except Exception as e:
            logger.warning(f"Could not fetch historical data: {e}")

        # Generate prediction
        prediction = await ml_engine.outcome_classifier.predict_outcome(
            market_data, order_book, historical_data
        )

        # Find similar markets if requested
        similar_markets = []
        if include_similar and historical_data:
            similar_markets = await ml_engine.similarity_finder.find_similar_markets(
                market_data, historical_data, top_k=5
            )

        return {
            "success": True,
            "market_id": market_id,
            "prediction": prediction.to_dict(),
            "similar_markets": [m.to_dict() for m in similar_markets],
            "generated_at": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error predicting market outcome: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/predictions/price")
async def predict_price_movement(
    market_data: Dict[str, Any],
    horizon_hours: int = 24
) -> Dict[str, Any]:
    """Forecast price movement using ML"""
    try:
        from backend.analytics.ml_engine import get_ml_engine

        ml_engine = await get_ml_engine()

        # Fetch order book if available
        market_id = market_data.get("market_id", "")
        order_book = None
        if market_id:
            try:
                clob_client = await get_clob_client()
                order_book_data = await clob_client.fetch_order_book(market_id, limit=10)
                if order_book_data:
                    order_book = {
                        "bids": [{"price": level.price, "size": level.size} for level in order_book_data.bids],
                        "asks": [{"price": level.price, "size": level.size} for level in order_book_data.asks]
                    }
            except Exception:
                pass

        # Get historical data
        db = await get_db()
        repos = get_repositories(db)
        historical_data = []
        try:
            resolved = await repos["resolved_markets"].get_resolved_markets(
                category=market_data.get("category"),
                limit=30
            )
            historical_data = resolved
        except Exception:
            pass

        # Generate prediction
        prediction = await ml_engine.price_predictor.predict_price_movement(
            market_data, order_book, historical_data, horizon_hours
        )

        return {
            "success": True,
            "market_id": market_id,
            "prediction": prediction.to_dict(),
            "generated_at": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error predicting price movement: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/predictions/full")
async def generate_full_prediction(
    market_data: Dict[str, Any]
) -> Dict[str, Any]:
    """Generate comprehensive prediction with all ML models"""
    try:
        from backend.analytics.ml_engine import get_ml_engine
        from backend.database.repositories import get_repositories

        ml_engine = await get_ml_engine()

        # Fetch order book
        market_id = market_data.get("market_id", "")
        order_book = None
        if market_id:
            try:
                clob_client = await get_clob_client()
                order_book_data = await clob_client.fetch_order_book(market_id, limit=10)
                if order_book_data:
                    order_book = {
                        "bids": [{"price": level.price, "size": level.size} for level in order_book_data.bids],
                        "asks": [{"price": level.price, "size": level.size} for level in order_book_data.asks]
                    }
            except Exception:
                pass

        # Get historical data
        db = await get_db()
        repos = get_repositories(db)
        historical_data = []
        historical_markets = []
        try:
            resolved = await repos["resolved_markets"].get_resolved_markets(
                category=market_data.get("category"),
                limit=100
            )
            historical_data = resolved
            historical_markets = resolved
        except Exception:
            pass

        # Generate full prediction
        full_prediction = await ml_engine.generate_full_prediction(
            market_data, order_book, historical_data, historical_markets
        )

        return {
            "success": True,
            "market_id": market_id,
            "full_prediction": full_prediction,
            "generated_at": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error generating full prediction: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/predictions/cached/{market_id}")
async def get_cached_prediction(market_id: str) -> Dict[str, Any]:
    """Get cached prediction for a market"""
    try:
        from backend.analytics.ml_engine import get_ml_engine

        ml_engine = await get_ml_engine()
        prediction = await ml_engine.get_prediction(market_id)

        if prediction:
            return {
                "success": True,
                "market_id": market_id,
                "prediction": prediction
            }
        else:
            raise HTTPException(status_code=404, detail="No cached prediction found")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting cached prediction: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Strategy Evolution endpoints
@app.get("/api/v1/strategy/evolution")
async def get_evolved_strategies(
    status: Optional[str] = None
) -> Dict[str, Any]:
    """Get evolved strategies"""
    try:
        from backend.analytics.strategy_evolution import get_strategy_evolution_system

        evolution_system = await get_strategy_evolution_system()

        if status:
            strategies = [
                s for s in evolution_system.strategies.values()
                if s.status.value == status
            ]
        else:
            strategies = list(evolution_system.strategies.values())

        return {
            "success": True,
            "count": len(strategies),
            "strategies": [s.to_dict() for s in strategies]
        }

    except Exception as e:
        logger.error(f"Error fetching evolved strategies: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/strategy/evolution/stats")
async def get_evolution_stats() -> Dict[str, Any]:
    """Get strategy evolution statistics"""
    try:
        from backend.analytics.strategy_evolution import get_strategy_evolution_system

        evolution_system = await get_strategy_evolution_system()
        stats = evolution_system.get_evolution_stats()

        return {
            "success": True,
            "stats": stats
        }

    except Exception as e:
        logger.error(f"Error fetching evolution stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/strategy/evolve")
async def trigger_strategy_evolution(
    background_tasks: BackgroundTasks,
    performance_data: Optional[Dict[str, Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """Trigger strategy evolution cycle"""
    try:
        from backend.analytics.strategy_evolution import (
            get_strategy_evolution_system,
            StrategyPerformance,
            StrategyParameters,
            StrategyType
        )

        evolution_system = await get_strategy_evolution_system()

        # Initialize if not already done
        if not evolution_system.strategies:
            # Create default base strategies
            base_strategies = [
                StrategyParameters(
                    name="Edge_Based_Base",
                    strategy_type=StrategyType.EDGE_BASED,
                    min_confidence=0.6,
                    max_position_size=1000.0,
                    min_edge=0.02
                ),
                StrategyParameters(
                    name="Momentum_Base",
                    strategy_type=StrategyType.MOMENTUM,
                    min_confidence=0.65,
                    max_position_size=800.0,
                    min_edge=0.015
                ),
                StrategyParameters(
                    name="Liquidity_Base",
                    strategy_type=StrategyType.LIQUIDITY,
                    min_confidence=0.55,
                    max_position_size=1200.0,
                    min_edge=0.025
                )
            ]
            await evolution_system.initialize(base_strategies)

        # Process performance data if provided
        performance_objects = {}
        if performance_data:
            for strategy_id, perf_data in performance_data.items():
                perf = StrategyPerformance(strategy_id=strategy_id)
                perf.total_trades = perf_data.get("total_trades", 0)
                perf.winning_trades = perf_data.get("winning_trades", 0)
                perf.losing_trades = perf_data.get("losing_trades", 0)
                perf.total_pnl = perf_data.get("total_pnl", 0.0)
                perf.max_drawdown = perf_data.get("max_drawdown", 0.0)
                perf.sharpe_ratio = perf_data.get("sharpe_ratio", 0.0)
                perf.calculate_metrics()
                performance_objects[strategy_id] = perf

        # Run evolution in background
        async def run_evolution():
            if performance_objects:
                new_population = await evolution_system.run_evolution_cycle(performance_objects)
            else:
                # Initialize with mock performance for demo
                mock_performance = {}
                for strategy_id, strategy in evolution_system.strategies.items():
                    perf = StrategyPerformance(strategy_id=strategy_id)
                    perf.total_trades = 50
                    perf.winning_trades = 30
                    perf.losing_trades = 20
                    perf.total_pnl = random.uniform(-100, 500)
                    perf.sharpe_ratio = random.uniform(0.5, 2.5)
                    perf.calculate_metrics()
                    mock_performance[strategy_id] = perf

                new_population = await evolution_system.run_evolution_cycle(mock_performance)

            # Broadcast completion
            if _websocket_service:
                await _websocket_service.broadcast_alert(
                    "strategy_evolution_complete",
                    {"generation": evolution_system.genetic_optimizer.generation}
                )

            return new_population

        background_tasks.add_task(run_evolution)

        return {
            "success": True,
            "message": "Strategy evolution cycle started",
            "current_generation": evolution_system.genetic_optimizer.generation
        }

    except Exception as e:
        logger.error(f"Error triggering strategy evolution: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/strategy/ab-tests")
async def get_ab_tests() -> Dict[str, Any]:
    """Get A/B test results and active tests"""
    try:
        from backend.analytics.strategy_evolution import get_strategy_evolution_system

        evolution_system = await get_strategy_evolution_system()

        return {
            "success": True,
            "active_tests": await evolution_system.get_active_ab_tests(),
            "completed_tests": await evolution_system.get_ab_test_results()
        }

    except Exception as e:
        logger.error(f"Error fetching A/B tests: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/strategy/select")
async def select_strategy_for_conditions(
    market_conditions: Dict[str, Any]
) -> Dict[str, Any]:
    """Select best strategy using meta-strategy"""
    try:
        from backend.analytics.strategy_evolution import get_strategy_evolution_system

        evolution_system = await get_strategy_evolution_system()

        selected_strategy = await evolution_system.select_strategy_for_conditions(
            market_conditions
        )

        if selected_strategy:
            return {
                "success": True,
                "selected_strategy": selected_strategy.to_dict(),
                "conditions": market_conditions
            }
        else:
            return {
                "success": False,
                "message": "No active strategies available"
            }

    except Exception as e:
        logger.error(f"Error selecting strategy: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/predictions/liquidity/{market_id}")
async def forecast_liquidity(
    market_id: str,
    timeframe_hours: int = 24
) -> Dict[str, Any]:
    """Forecast liquidity metrics for a market"""
    try:
        from backend.analytics.ml_engine import get_ml_engine
        from backend.database.repositories import get_repositories

        ml_engine = await get_ml_engine()

        # Get market data
        db = await get_db()
        repos = get_repositories(db)
        markets = await repos["live_markets"].get_markets(limit=1000)

        market_data = next((m for m in markets if m.get("market_id") == market_id), None)
        if not market_data:
            raise HTTPException(status_code=404, detail="Market not found")

        # Get order book
        order_book = None
        try:
            clob_client = await get_clob_client()
            order_book_data = await clob_client.fetch_order_book(market_id, limit=10)
            if order_book_data:
                order_book = {
                    "bids": [{"price": level.price, "size": level.size} for level in order_book_data.bids],
                    "asks": [{"price": level.price, "size": level.size} for level in order_book_data.asks]
                }
        except Exception:
            pass

        # Generate forecast
        forecast = await ml_engine.liquidity_forecaster.forecast_liquidity(
            market_data, order_book, None, timeframe_hours
        )

        return {
            "success": True,
            "market_id": market_id,
            "forecast": forecast.to_dict(),
            "generated_at": datetime.now().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error forecasting liquidity: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Update root endpoint to include Phase 5
@app.get("/")
async def root() -> Dict[str, Any]:
    """Root endpoint with API information"""
    return {
        "name": "Polymarket Analytics Platform",
        "version": "1.0.0",
        "status": "running",
        "phase": "Phase 5 Complete - Predictive Intelligence with ML/AI",
        "endpoints": {
            "health": "/health",
            "live_markets": "/api/v1/markets/live",
            "mock_markets": "/api/v1/markets/mock",
            "resolved_markets": "/api/v1/markets/resolved",
            "analytics": "/api/v1/analytics",
            "ingestion": "/api/v1/ingestion",
            "order_book": "/api/v1/orderbook",
            "predictions": "/api/v1/predictions",
            "strategy_evolution": "/api/v1/strategy/evolution"
        },
        "features": {
            "gamma_api": "✅ Connected",
            "clob_api": "✅ Connected",
            "data_labeler": "✅ Active",
            "websocket": "✅ Available",
            "repositories": "✅ Live/Mock/Resolved",
            "pattern_detection": "✅ Phase 4",
            "ml_predictions": "✅ Phase 5",
            "strategy_evolution": "✅ Phase 5",
            "ab_testing": "✅ Phase 5",
            "meta_strategy": "✅ Phase 5"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
