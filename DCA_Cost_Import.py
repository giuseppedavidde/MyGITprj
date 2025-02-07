#Import Shares cost from a CSV based file
#Suitable for DCA across different Brokers

from modules import general_utils
from modules.general_utils import glob, os, np, pd, dt, go, sp, yf
from modules import collect_data_utils
from modules.collect_data_utils import get_current_user,collect_data_from_csv,collect_data_from_list_csv,collect_numb_sample,collect_file

path = f"C:\\Users\\{get_current_user()}\\Downloads\\Telegram Desktop\\bitpanda-trades-2025-01-30-13-57.csv"

data_to_retrieve = [
    ("trans_id_collect", "Transaction ID"),
    ("date_collect", "Timestamp"),
    ("asset_collect", "Asset"),
    ("amount_fiat_collect", "Amount Fiat"),
    ("amount_asset_collect", "Amount Asset"),
    ("asset_market_price_collect", "Asset market price"),
    ("fee_asset_collect","Fee"),
]

data_collected = {
    config[0]: collect_data_from_csv(path, config[1], config[2], scaling_factor=1)
    for config in data_to_retrieve
}

print(f"{data_collected}")
