
from datetime import date

import os
import pymongo
from dotenv import load_dotenv
load_dotenv()
from Utility.TimeSupervisor import Run_at


import logging
import os
logging.basicConfig(filename=f"{os.getcwd()}/Records/StrategyManager.log", level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def ajj_ka_status(tb_obj):
    try:
        db_client = os.getenv("MONGODB_STRING")
        verion = 2
        mongo_connection = pymongo.MongoClient(db_client)[f'TradBuddy_V{verion}_Worker_1']
        DailyCollection = mongo_connection.get_collection("DailyCollection")

        today_str = str(date.today())
        accounts  = tb_obj.account_list(query = {"is_activate": "Activate"})
        for account in accounts:
            data = tb_obj.generate_report(account['account_id'],False)['body']
            capital = tb_obj.account_get(account['account_id']).get('body').get('account_balance')
            DailyCollection.update_one({"Date": today_str,"account_id":account['account_id']},{"$set": {"Info": data,"Capital":float(capital),"account_id":account['account_id']}}, upsert=True)
            logging.info(f"Todays Status Update :{today_str} {capital}")
            print(f"Todays Status Update :{today_str} - [{capital}] for Account : {account['account_id']}")
    except Exception as e:
        logging.info(f"Something Wrong in [ajj_ka_status] : {e}")
        print(f"Something Wrong in [ajj_ka_status] : {e}")
def trade_margin_manager(tb_obj):
    try:
        accounts  = tb_obj.account_list(query = {"is_activate": "Activate"})
        for account in accounts:
            balance = tb_obj.account_get(account['account_id']).get('body').get('account_balance')
            todays_margin = round(balance*0.7,2)
            total_index = 2
            todays_trad_margin = round(todays_margin/(2*total_index),2)
            max_loss = round(todays_trad_margin*(account['base_stoploss']/100),2)
            min_profit = round(todays_trad_margin*(account['base_stoploss']/100),2)
            update_status =tb_obj.account_update(account['account_id'],{"todays_margin":todays_margin,
                                                                        "todays_trad_margin":todays_trad_margin,
                                                                        "account_max_loss":max_loss,
                                                                        "account_min_profit":min_profit
                                                                        })
        logging.info("Account Setting Updated for the better Performance")
        print("Account Setting Updated for the better Performance")
    except Exception as e:
        logging.info(f"Something Wrong in [trade_margin_manager] : {e}")
        print(f"Something Wrong in [trade_margin_manager] : {e}")

@Run_at("15:29")
def Account_status_update(tb_obj):
    trade_margin_manager(tb_obj)
    ajj_ka_status(tb_obj)




