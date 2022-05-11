'''
价量共振模型
    V1、V2  成交量的奥秘：另类价量共振指标的择时_2019-02-22_华创证券
    V3      2019-05-13_华创证券_牛市让利_熊市得益_价量共振择时之二_如何规避放量下跌_
'''
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from signal_handle import adjust_trading_sig

def calc_AMA(data, n, calc='r_close',fastlen=2, slowlen=30):
    '''
    Function
        计算AMA（卡夫曼自适应移动平均）
            1. 价格方向direction = price –price[n]; 其中price[n]是n个周期前的收盘价。
            2. 波动性 volatility = @sum(@abs(price –price[1]), n);@sum(value, n)是n个周期中的数值之和函数。
            即，此处波动定义为：所有“日到日”的价格绝对变化的总和，在同样的n个周期上。
            3. 效率系数（ER）Efficiency_Ratio = direction/volativity;
                方向移动对噪音之比，称之为效率系数，该系数的值就从0到1 变化。
            4. 每天的均线速度可以用改变平滑系数来改变，成为自适应性的。该公式如下：
                EXPMA = EXPMA[1] + c*(price –EXPMA[1]);
            这个平滑系数是：
                fastest = 2/(N+1) = 2/(2+1) =0.6667;
                slowest = 2/(N+1) = 2/(30+1) =0.0645;
                smooth = ER*(fastest - slowest)+ slowest;
                c = smooth*smooth;
            平方平滑系数迫使c的数值趋向于零。即，较慢的移动平均线的权重大于快的移动平均值。就像出现不确定状况时就更加保守一样。
                AMA = AMA[1] + c*(price –AMA[1]);
    Parameters
    Return
    '''
    data['direction'] = data[calc] - data[calc].shift(n)
    data['volatility'] = abs(data[calc].diff()).rolling(n).sum()
    data['ER'] = np.divide(data['direction'], data['volatility'])
    fast = 2/(fastlen + 1)
    slow = 2/(slowlen + 1)
    data['c'] = np.square((fast - slow)*data['ER']+slow)
    data.dropna(axis=0,inplace=True)

    # 计算 AMA： AMA = AMA[1] + c*(price –AMA[1])
    ama_list = []
    ama_list.append(data[calc].iloc[0])
    for i in range(data.shape[0]):
        ama = ama_list[-1] + data['c'].iloc[i] *(data[calc].iloc[i]- ama_list[-1])
        ama_list.append(ama)
    del ama_list[0]
    data['AMA'+str(n)] = ama_list
    return data


def calc_BMA(data, L, calc='r_close'):
    data['BMA']= data[calc].rolling(L).mean()
    return data


def calc_pvResonance_V1(data,calc_p='r_close',calc_v='volume', shortLen=5, longLen=100, L=50, N=3):
    # 对 量
    data = calc_AMA(data, shortLen, calc=calc_v)
    data = calc_AMA(data, longLen , calc=calc_v)
    data['v'] = data['AMA'+str(shortLen)] / data['AMA'+str(longLen)]
    # 对 价
    data = calc_BMA(data, L, calc=calc_p)
    data['p'] = data['BMA'] / data['BMA']

    data['factor_pv'] = data['p'] * data['v']
    return data


def get_trading_sig_V1(data_factor,factor='factor_pv',s=1.10):
    '''
    Function
    Parameter
        data    
    Return
        data    [dateframe]        信号数据（字段 +['sig']）
    '''
    # 价量共振指标大于 s ，买进。否则，卖出。
    data_factor['pre_'+factor] = data_factor[factor].shift(1).fillna(0)
    
    # macd > 0, 买入; macd < 0; 卖出
    data_factor['sig'] = data_factor.apply(lambda x:1 if (x[factor]>s) #and x['pre_factor']<s
        #and x['AMA'+str(shortLen)]>0 and x['AMA'+str(longLen)]>0)
        else(-1 if (x[factor]<=s)  #and x['pre_factor']>s
        #or (x['AMA'+str(shortLen)]<0 or x['AMA'+str(longLen)]<0)) 
        else 0), axis=1)
    data_factor.drop(['pre_'+factor], axis=1, inplace=True)
    data_factor = adjust_trading_sig(data_factor)
    return data_factor


def classify_market(data,factor='r_close'):
    '''
    划分多空头市场
    当 5 日均线高于 90 日均线，市场划分为多头市场；当 5 日均线小于 90 日均线，市场划分为空头市场。
    '''
    data['MA5'] = data[factor].rolling(5).mean()
    data['MA90'] = data[factor].rolling(90).mean()
    data.dropna(inplace=True)
    print('1111',data)
    data['market'] = data.apply(lambda x:1 if x['MA5']>=x['MA90'] else -1, axis=1)
    return data

def get_trading_sig_V2(data_factor, factor='factor',s1=1.125,s2=1.275):
    '''
    当前为多头市场下，若价量共振指标大于 Threshold1 则做多，否则以 Threshold1 平仓。
    当前为空头市场下，若价量共振指标大于 Threshold2 则做多，否则以 Threshold2 平仓
    '''
    # 辨别多空市场
    data_factor = classify_market(data_factor,factor='r_close')
    # 价量共振指标大于 s ，买进。否则，卖出。
    #data_factor['pre_'+factor] = data_factor[factor].shift(1).fillna(0)
    data_factor['sig'] = data_factor.apply(lambda x:1 if ((x[factor]>s1 and x['market']==1) or (x[factor]>s2 and x['market']==-1))
        else(-1 if ((x[factor]<=s1 and x['market']==1) or (x[factor]<=s2 and x['market']==-1))  
        else 0), axis=1)
    #data_factor.drop(['pre_'+factor], axis=1, inplace=True)
    data_factor = adjust_trading_sig(data_factor)
    return data_factor


if __name__ == '__main__':    
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