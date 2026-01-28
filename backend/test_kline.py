import tushare as ts
import config

# 初始化
ts.set_token(config.TUSHARE_TOKEN)
pro = ts.pro_api()

ts_code = '000001.SZ'
start_date = '20250101'
end_date = '20260128'

print("测试日线数据:")
df_daily = pro.daily(ts_code=ts_code, start_date=start_date, end_date=end_date)
print(f"日线数据条数: {len(df_daily)}")
if not df_daily.empty:
    print(df_daily.head(3))

print("\n测试周线数据:")
df_weekly = pro.weekly(ts_code=ts_code, start_date=start_date, end_date=end_date)
print(f"周线数据条数: {len(df_weekly)}")
if not df_weekly.empty:
    print(df_weekly.head(3))

print("\n测试月线数据:")
df_monthly = pro.monthly(ts_code=ts_code, start_date='20210101', end_date=end_date)
print(f"月线数据条数: {len(df_monthly)}")
if not df_monthly.empty:
    print(df_monthly.head(3))
