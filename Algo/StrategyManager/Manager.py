import json
import logging
import os
from datetime import datetime
import asyncio

from Algo.Strategys.BaseStategys import strategy_1, strategy_2,strategy_3,strategy_4
from Utility.TimeSupervisor import market_time_decorator
from Utility.HistoricalData import GetHistoricalDataframe


logging.basicConfig(filename=f"{os.getcwd()}/Records/StrategyManager.log", level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


async def find_entries(index_data, fyers_obj, TimeFrame):
    try:
        data = GetHistoricalDataframe(fyers_obj,index_data[0],TimeFrame)
        strategy_1_task = strategy_1(data, index_data[1])
        strategy_2_task = strategy_2(data, index_data[1])
        strategy_3_task = strategy_3(data, index_data[1])
        strategy_4_task = strategy_4(data, index_data[1])
        strategy_1_status, strategy_2_status,strategy_3_status,strategy_4_status = await asyncio.gather(strategy_1_task, strategy_2_task,strategy_3_task,strategy_4_task)
        
        logging.info(f"[{index_data[0]}] ---- strategy_1_status - {strategy_1_status} || strategy_2_status- {strategy_2_status} || strategy_3_status - {strategy_3_status} || strategy_4_status -{strategy_4_status}")
        return index_data[0], {
            "strategy_1_status": strategy_1_status,
            "strategy_2_status": strategy_2_status,
            "strategy_3_status": strategy_3_status,
            "strategy_4_status": strategy_4_status,
            "price": index_data[1],
            "updated_datetime": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    except Exception as e:
        error_msg = f"Error occurred while processing {index_data[0]}: {e}"
        logging.error(error_msg)
        return []


async def store_strategy_statuses(fyers_obj):   
    Symbol = ["NSE:NIFTY50-INDEX", "NSE:NIFTYBANK-INDEX"]
    TimeFrame = "15"
    results = {}
    try:
        index_data = zip(Symbol, fyers_obj.get_current_ltp(",".join(Symbol)).values())
        gathered_results = await asyncio.gather(*(find_entries(data, fyers_obj, TimeFrame) for data in index_data))
        for result in gathered_results:
            if result:
                results[result[0]] = result[1]    
        output_file_path = os.path.join(os.getcwd(), "Records", "strategies_results.json")
        with open(output_file_path, "w") as f:
            json.dump(results, f)
        logging.info("Strategy Builder Updated successful")
    except Exception as e:
        error_msg = f"Error occurred in store_strategy_statuses: {e}"
        logging.error(error_msg)

@market_time_decorator(Open_time = "9:15",Close_time = "15:30",Interval = 60)
def StrategyBuilder(fyers_obj):
    print("-----------[StrategyBuilder]------------")
    asyncio.run(store_strategy_statuses(fyers_obj))

