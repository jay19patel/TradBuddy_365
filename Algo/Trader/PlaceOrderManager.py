import asyncio
import pandas as pd
import requests
from datetime import datetime
import os
import io
import os
import glob



import logging
logging.basicConfig(filename=f"{os.getcwd()}/Records/StrategyManager.log", level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')



def fetch_option_details():
    logging.info("Fetching new Option details from Online")
    spotnames = ['BANKNIFTY', 'FINNIFTY', 'NIFTY', 'SENSEX', 'BANKEX'] 
    nse_fetch = requests.get('https://public.fyers.in/sym_details/NSE_FO.csv')
    bse_fetch = requests.get('https://public.fyers.in/sym_details/BSE_FO.csv')

    nse_df = pd.read_csv(io.StringIO(nse_fetch.text), header=None)
    bse_df = pd.read_csv(io.StringIO(bse_fetch.text), header=None)

    row_df = pd.concat([nse_df, bse_df])
    row_df = row_df[[0,1,3,8,9,13,15,16]]
    column_names = ["ID", "INDEX INFO", "LOT", "TIMESTAMP", "SYMBOL", "INDEX", "STRIKE PRICE", "SIDE"]
    row_df.columns = column_names
    row_df["EXDATETIME"] = pd.to_datetime(row_df["TIMESTAMP"], unit='s')

    current_date = datetime.now().strftime('%Y-%m-%d')
    filtered_df = row_df[row_df['INDEX'].isin(spotnames) & (pd.to_datetime(row_df["TIMESTAMP"], unit='s').dt.date >= datetime.now().date())]
    

    [os.remove(file) for file in glob.glob(f"{os.getcwd()}/Records/sym_details_*")]

    file_path = f"{os.getcwd()}/Records/sym_details_{current_date}.csv"
    filtered_df.to_csv(file_path, index=False)
    logging.info(f"Option details Successfully saved to {file_path}") 

    
    

def get_option_for(trad_index, trad_side, price):
    tred_sp = round(price,-2)
    current_date = datetime.now().strftime('%Y-%m-%d')
    file_path = f"{os.getcwd()}/Records/sym_details_{current_date}.csv"
    if not os.path.exists(file_path):
        fetch_option_details()

    option_df = pd.read_csv(file_path)
    option_df["EXDATETIME"]=pd.to_datetime(option_df["TIMESTAMP"],unit='s')
    final_data = option_df[
    (option_df["STRIKE PRICE"] == tred_sp)&
    (option_df["EXDATETIME"] >= pd.to_datetime(f"{datetime.now().strftime('%Y-%m-%d')} 10:00:00")) &
    (option_df["SIDE"] == trad_side) &
    (option_df['INDEX'] == trad_index)
    ]
    if final_data.shape[0] == 0:
        logging.info("Filter Datatable is Not available Some this wrong ")
        return None
    else:
        return final_data.iloc[0].to_dict()

def get_index_sortname(option_symbol):
    index_mapping = {
        "NSE:NIFTY50-INDEX": "NIFTY",
        "NSE:NIFTYBANK-INDEX":"BANKNIFTY",
        "NSE:FINNIFTY-INDEX": "FINNIFTY",
        "BSE:BANKEX-INDEX": "BANKEX",
        "BSE:SENSEX-INDEX": "SENSEX"
    }
    return index_mapping.get(option_symbol)


async def PlaceOrder(account_id, strategy_name, trad_index, trad_side,trad_price,Fyers,TradBuddy):
    # print(account_id, strategy_name, trad_index, trad_side,trad_price,Fyers,TradBuddy)

    # FIND OPTION DETAILS-------------------
    print(get_index_sortname(trad_index),trad_side,trad_price)
    get_option_details = get_option_for(get_index_sortname(trad_index),trad_side,trad_price)
    # {'ID': 101124043049532, 'INDEX INFO': 'BANKNIFTY 24 Apr 30 48200 PE', 'LOT': 15, 
    #  'TIMESTAMP': 1714471200, 'SYMBOL': 'NSE:BANKNIFTY2443048200PE', 'INDEX': 'BANKNIFTY', 
    #  'STRIKE PRICE': 48200.0, 'SIDE': 'PE', 'EXDATETIME': ('2024-04-30 10:00:00')}

    if get_option_details == None:
        logging.info("Option Details Not found")
        return

    option_symbol = get_option_details["SYMBOL"]
    genral_mux = 1
    option_lot = get_option_details["LOT"]
    option_expiry = get_option_details["EXDATETIME"]
    option_id = get_option_details["ID"]

    
    # GET LIVE MARKET DATA -------------------
    get_live_data = Fyers.get_current_ltp(f"{trad_index},{option_symbol}")
    if  "Unknown" in get_live_data:
        logging.info(f"Live Data Not found for index :{trad_index},{option_symbol}")
        return 
    # {'NIFTYBANK-INDEX': 48201.05, 'BANKNIFTY2443048200PE': 220}
    ((current_index_name, current_index_price), (current_option_name, current_option_price)) = tuple(zip(get_live_data.keys(),get_live_data.values()))



    # FIND SL - TARGET -------------------
    index_sl,index_tg = 20,40
    current_option_sl, current_option_tg = [current_option_price * (100 - index_sl) / 100, current_option_price * (100 + index_tg) / 100]


    order_place_status = TradBuddy.order_place(
        account_id = account_id,
        strategy = strategy_name,
        trad_index = trad_index,
        trad_side = trad_side,
        trigger_price = current_index_price,
        option_symbol = option_symbol,
        qnty = option_lot*genral_mux,
        buyprice = current_option_price,
        sl_price = current_option_sl,
        target_price = current_option_tg,
        notes = "Test"        
    )
    logging.info(f" Order Placed : {order_place_status}")
    
    
