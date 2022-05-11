from factor import *
from data_handle import *
from signal_handle import *

# 定义策略中需要用到的参数
start_dt = 20170101
end_dt = 20210617
future_code = 'IC'
# 定义策略中需要用到的参数--> 只用AMA平均线时的最优参数-IC:3,5,1.1; IF:3,11,1--7.11; 5,11,1--7.01
shortLen, longLen, L, N = 5, 100, 50, 3  # 研报默认: 5, 100, 50, 3
s = 1.15   # 阈值                    # 研报默认: 1.15


allocation = 10000000 # 策略初始资金一千万

# 获取数据
# 获取 复权数据
d = GetData(future_code, time_frequency=240)
future_data = d.get_refactor_option_data()
print(future_data)

# 获取 因子数据
# 生成 指标
data = calc_pvResonance_V1(future_data,calc_p='r_close',calc_v='volume',
                shortLen=shortLen,longLen=longLen,L=L,N=N)

### 获取买卖信号
data_factor = data.reset_index()
data_sig = get_trading_sig_V1(data_factor,'factor_pv')
data_sig.rename(columns={'factor_pv':'factor'},inplace=True)

print(data_sig)
draw_trade_sig(data_sig, time_freq=240, startdt=start_dt, enddt=end_dt)