"""
处理交易信号：
    不持有空仓     adjust_trading_sig
    不在节假日交易 take_off_crossHoliday
"""
import datetime
import numpy as np
import matplotlib.pyplot as plt


def adjust_trading_sig(data):
    """调整 sig 数据，假设不持有 空头 

    Args:
        data (dateframe): 因子数据（字段['sig']）

    Raises:
        NameError: there is no signal!

    Returns:
        dateframe: 信号数据（字段['sig','pos']）
    """
    ### 调整多空头: 不考虑空头，保证【多头、空头交错】
    buy_idx = data[ data.sig==1 ].index.tolist()
    sell_idx = data[ data.sig==-1 ].index.tolist()
    if not (buy_idx and sell_idx): # 只要 buy、sell一个为空
        raise NameError('there is no signal!')
    buy_sell_idx = [buy_idx, sell_idx] # 列表嵌套列表

    sig_list = []      
    sig_list.append(buy_sell_idx[0][0])
    i,j = 0,1
    while i<len(buy_sell_idx[0]) and j< len(buy_sell_idx[1])+1:
        # sell_index和 buy相比，大于则纳入sig
        if len(sig_list)%2==1:
            if buy_sell_idx[1][i] > sig_list[-1]:
                sig_list.append(buy_sell_idx[1][i])
                i += 1
            elif buy_sell_idx[1][i] <= sig_list[-1]:
                del buy_sell_idx[1][i]
        # buy_index和 sell相比，大于则纳入sig
        elif len(sig_list)%2==0:
            if buy_sell_idx[0][j]>sig_list[-1]:
                sig_list.append(buy_sell_idx[0][j])
                j += 1
            elif buy_sell_idx[0][j]<=sig_list[-1]:
                del buy_sell_idx[0][j]
        else:
            print('\n','!'*80,'\nsth wrong!!!!!!')

    #print('before #'*8,len(buy_idx), len(sell_idx))
    # 若结果sell/buy有多，截取
    if len(buy_sell_idx[0])<len(buy_sell_idx[1]):
        buy_sell_idx[1] = buy_sell_idx[1][:len(buy_sell_idx[0])]
        print('减去了sell')
    elif len(buy_sell_idx[0])>len(buy_sell_idx[1]):        
        buy_sell_idx[0] = buy_sell_idx[0][:len(buy_sell_idx[1])]
        print('减去了buy')
    print('\n','#--'*8, len(buy_sell_idx[0]), len(buy_sell_idx[1]))
    #print(buy_sell_idx[0], buy_sell_idx[1])

    # 修正 sig 数据
    data['sig'] = 0
    data.loc[buy_sell_idx[0],'sig'] = 1
    data.loc[buy_sell_idx[1],'sig'] = -1
    ### 删除 跨假期交易
    drop_list = take_off_crossHoliday(data)
    print('删除第{}个位置的信号数据，因为这是跨期交易'.format(drop_list))
    k = 0
    for i in drop_list:
        del buy_sell_idx[0][i-k]
        del buy_sell_idx[1][i-k]
        k += 1
    
    # 修正 sig 数据
    data['sig'] = 0
    data.loc[buy_sell_idx[0],'sig'] = 1
    data.loc[buy_sell_idx[1],'sig'] = -1

    # 信号的第二天再真正交易(可能把最后一天的卖shift掉，导致买卖不对称)
    if data['sig'].iloc[-1]==-1 and data['sig'].iloc[-2]!=1:
        data['sig'].iloc[-2]=-1
        print('删了一个')
    elif data['sig'].iloc[-1]==-1 and data['sig'].iloc[-2]==1:
        data['sig'].iloc[-2]=0 # 因为不能同一天买卖，所以这次交易取消
        print('删了一对')
    data['sig'] = data['sig'].shift(1).fillna(0)

    # 求持仓数据
    data['pos'] = np.cumsum(data['sig'])
    return data


def take_off_crossHoliday(data):
    """删除在节假日前一天产生的信号，因为实际交易会延迟到下一交易日（假期后）

    Args:
        data (dateframe): 因子数据（字段['sig','date_time']）

    Returns:
        list: 删除的信号的 位置
    """
    buy_date = list(data[ data.sig==1 ].date_time)

    data = data.copy()
    data['sig'] = data['sig'].shift(1).fillna(0)
    shifted_buydt = list(data[ data.sig==1 ].date_time)
    if len(shifted_buydt)<len(buy_date):
        buy_date.pop()
    
    drop_list = []
    # 如果买入信号生成时刻，和 买入信号执行时刻（即下一期）之间隔有法定假期，则为跨假期交易
    for i in range(len(buy_date)):
        # buy_date 和 shifted_buydt 不在同一日，且二者之间至少间隔 1 天
        if (datetime.datetime.date(shifted_buydt[i])-datetime.datetime.date(buy_date[i])) > datetime.timedelta(days=1):
            drop_list.append(i)
            #print('删除第{}个于{}产生信号{}实际买入的交易，因为是跨假期交易'.format(i, datetime.datetime.date(buy_date[i]), datetime.datetime.date(shifted_buydt[i])) )
    return drop_list

# 绘制买卖信号图
def draw_trade_sig(sig_data, time_freq, startdt=20120000, enddt=20220000):
    """绘制买卖信号图

    Args:
        sig_data (dataframe): 原始数据（字段['date_time','date','open','sig'])
        time_freq (int): 原始数据的时间频率
        startdt (int, optional): 时间区间的开始日期. Defaults to 20120000.
        enddt (int, optional): 时间区间的结束日期. Defaults to 20220000.
    """    
    data = sig_data[ (sig_data.date>=int(startdt)) & (sig_data.date<=int(enddt)) ]
    data.set_index(['date_time'], inplace=True)
    buy_idx = list(data[ data.sig==1 ].index)
    sell_idx = list(data[ data.sig==-1 ].index)
    plt.figure(figsize=(16, 8))
    plt.plot(data['open'],label="open price",color='k',linewidth=1)
    plt.plot(data['open'][buy_idx],'^',color='red',label="buy", markersize=8)
    plt.plot(data['open'][sell_idx],'gv',label="sell", markersize=8)
    plt.legend()
    plt.grid(True)
    plt.show()
    # plt.savefig(r"data\result_data\{}_min_trading_sig.png".format(time_freq))
    plt.close()