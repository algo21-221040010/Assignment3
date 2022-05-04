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


# 计算因子 北向资金的增量
def get_factor(data, north_buy_sell, future_data):
    """ 求北向因子： factor = 对所有成分股 Σ[( OIt - OI(t-1) ) *Pt]
        其中OI为沪港通、深港通的单个股票交易量数据, P为股票收盘价

    Args:
        data (dataframe): 股指成分股中 开通了沪港通、深港通的所有成分股的 行情数据
        north_buy_sell (dataframe): 北向的买入、卖出金额数据
        future_data (dataframe): 复权后的日度期货数据

    Returns:
        dataframe: 因子数据['date','factor']
    """
    ### 计算因子值：factor = 对所有成分股 Σ[(OIt - OI(t-1))*Pt] / Σ[amount(t)]
    data = data.set_index(['date','code','close','amount'])
    data = data.groupby(['code'])['oi'].diff()
    data.name = 'delta_oi'
    data = data.reset_index()
    # 第一天的dalta，以及新纳入股票的第一天的delta会是空值，此处以 0 填充
    data.fillna(0, inplace=True)
    
    # 按 date groupby
    grouped = data.groupby(['date'])
    factor_data = grouped.apply(lambda x: np.divide(np.multiply(x['delta_oi'],x['close']).sum(), x['amount'].sum()) )
    factor_data.name = 'factor'
    factor_data = factor_data.reset_index()

    future_data = future_data.drop('factor', axis=1)
    data_factor = pd.merge(factor_data, future_data, on='date', how='left')
    data_factor['date_time'] = data_factor.apply(lambda x:datetime.datetime.strptime(str(x['date'])\
                    ,'%Y%m%d'), axis=1) 
    # 加上北向的买入、卖出金额数据
    data_factor = pd.merge(data_factor, north_buy_sell[['date_time','buy','sell']], on='date_time', how='left')
    data_factor['inflow_tense'] = data_factor['factor']/(data_factor['buy']+data_factor['sell'])
    print('存在数据缺失的日期：', list(data_factor[(data_factor['inflow_tense'].isnull())]['date']))
    return data_factor


def get_trading_sig(data_factor,s1=60,s_1=-40): 
    """计算买卖信号

    Args:
        data_factor (dateframe): 因子数据（字段['factor']）
        s1 (int, optional): 因子阈值. Defaults to 60.
        s_1 (int, optional): 因子阈值. Defaults to -40.

    Returns:
        _type_: _description_
    """
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