import numpy as np
import matplotlib.pyplot as plt

x = np.array([10,20,30,40,50,60,70])
y = np.array([10,15,20,25,30,35,40])

#### 简单线性回归####
def calculate_one(x,y):

    # 计量回归系数
    slope,intercept = np.polyfit(x,y,1)

    # 绘制拟合曲线
    # plt.scatter(x,y)
    # plt.plot(x, slope*x+intercept, color="red")

    # plt.show()
    return slope,intercept


#### 多项式回归####
def calculate_two(x,y):
    # 计量多项式回归系数
    coefs = np.polyfit(x,y,3)

    # 使用np.poly1d函数来生成一个多项式拟合对象
    poly = np.poly1d(coefs)
    
    # 生成新的横坐标,使得拟合曲线更加平滑
    new_x = np.linspace(min(x),max(x),1000)

    # 绘制拟合曲线
    plt.scatter(x,y)
    plt.plot(new_x, poly(new_x), color="red")

    plt.show()

