'''
价量共振模型
    V1、V2  成交量的奥秘：另类价量共振指标的择时_2019-02-22_华创证券
    V3      2019-05-13_华创证券_牛市让利_熊市得益_价量共振择时之二_如何规避放量下跌_
'''
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from data_handle import *
from signal_handle import *


def calc_AMA(data, n, calc='fq_close',fastlen=2, slowlen=30):
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


def calc_BMA(data, L, calc='fq_close'):
    data['BMA']= data[calc].rolling(L).mean()
    return data


def calc_pvResonance_V1(data,calc_p='fq_close',calc_v='all_volume', shortLen=5, longLen=100, L=50, N=3):
    # 对 量
    data = calc_AMA(data, shortLen, calc=calc_v)
    data = calc_AMA(data, longLen, calc =calc_v)
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


def get_trading_sig_M(data_factor,s1=10,s_1=-0,s2=0.03,s_2=-0.02):
    """计算买卖信号

    Args:
        data_factor (dateframe): 因子数据（字段['factor']）
        s1 (int, optional): 因子阈值. Defaults to 10.
        s_1 (int, optional): 因子阈值. Defaults to -0.
        s2 (float, optional): 因子阈值. Defaults to 0.03.
        s_2 (float, optional): 因子阈值. Defaults to -0.02.

    Returns:
        dateframe: 信号数据（字段['factor','sig']）
    """
    # 买入信号=1，卖出信号=-1
    data_factor['sig'] = data_factor.apply(lambda x:1 if (x['factor']>s1 and x['inflow_tense']>s2)
                                        else(-1 if (x['factor']<s_1 and x['inflow_tense']<s_2) else 0), axis=1)
    
    return data_factor


if __name__ == '__main__':    
    # 定义策略中需要用到的参数
    start_dt = 20170101
    end_dt = 20210617
    future_code = 'IC'
    s1 = 60; s_1 = -40 # 策略 阈值

    allocation = 10000000 # 策略初始资金一千万

    # 获取数据
    # 获取 复权数据
    d = GetData(future_code, time_frequency=240)
    future_data = d.get_refactor_option_data()
    
    # 获取 因子数据
    data_factor = get_factor(data, future_data)
    print(data_factor)
    
    # 获取 买卖信号数据
    data_sig = get_trading_sig(data_factor, s1,s_1)
    # data_sig = get_trading_sig_M(data_factor)
    print(data_sig)
    draw_trade_sig(data_sig, time_freq=240, startdt=20120000, enddt=20220000)