# components/api/routes/strategy_routes.py
from fastapi import APIRouter

router = APIRouter()

@router.post("/strategies")
async def create_strategy(strategy_data: dict):
    try:
        strategy_manager = StrategyManager()
        success = strategy_manager.add_strategy(
            strategy_data['name'],
            {
                'rules': strategy_data['rules'],
                'stop_loss': strategy_data['stopLoss'],
                'take_profit': strategy_data['takeProfit']
            }
        )
        return {"success": success}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/strategies")
async def get_strategies():
    try:
        with open('config/strategies.json', 'r') as f:
            strategies = json.load(f)
        return strategies
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))