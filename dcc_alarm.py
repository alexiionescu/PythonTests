# %% [markdown]
# Basic Call Log csv histograms
# %%
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime,timedelta
# %%
data = pd.read_csv("csv_files/alarms.csv")
data['ClearTime'] = round(data['ExcelClearTime'] * 1440) # minutes
data['StartTime'] = datetime(1899,12,30) + pd.to_timedelta(data['ExcelStartTime'], unit='d')
data['Subject'].hist()
# %%
data.query("Subject == 'Help'")['ClearTime'].hist()
# %%
data.query("Subject == 'Assist'")['ClearTime'].hist()
# %%
data.query("Subject == 'Dry1'")['ClearTime'].hist()
# %%
data.query("Subject == 'Dry2'")['ClearTime'].hist()
# %%
data.query("ClearTime < 1 or ClearTime > 2")