#Import Shares cost from a CSV based file
#Suitable for DCA across different Brokers

from modules import general_utils
from modules.general_utils import glob, os, np, pd, dt, go, sp, yf
from modules import collect_data_utils
from modules.collect_data_utils import path,collect_data_from_csv,collect_data_from_list_csv,collect_numb_sample,collect_file

path = "C:\\Users\\Davidde\\Downloads\\Telegram Desktop\\bitpanda-trades-2025-01-30-13-57.csv"

data_to_retrieve = [
    ("trans_id_collect", "Transaction ID"),
    ("date_collect", "Timestamp"),
    ("price_collect", "Price"),
    ("amount_collect", "Amount"),

    

]
