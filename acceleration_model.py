import yfinance as yf
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from scipy.signal import butter, lfilter, freqz
from scipy.fft import rfft, rfftfreq, irfft, fft, ifft, fftfreq
import math
#import plotly.express as px

stock_name = "SPY"
data_period = "5d"
resolution = "15m"

stock = yf.Ticker(stock_name)
hist = stock.history(period = data_period, interval = resolution) # historical price data
hist.reset_index(inplace=True) # converts datetime to a column

# set the latest traded price to index 0
# each +1 change in index is equal to +resolution change in time except for day opens
hist['time_index'] = range(-len(hist.index), 0)
hist['time_index'] += 1
#plt.plot(hist["Datetime"], hist["Close"])
plt.plot(hist["time_index"], hist["Close"])
plt.title(stock_name)
plt.xlabel('Time')
plt.ylabel('Price')
#plt.xticks(rotation = 90)
plt.show()

price = hist['Close']
shifted_price = price.shift()
velocity = price - shifted_price  # since del t = 1 index change
acceleration = velocity - velocity.shift()
jerk = acceleration - acceleration.shift()

hist["velocity"] = velocity
hist["acceleration"] = acceleration
hist["jerk"] = jerk

jyf = rfft(jerk.dropna().values)
jxf = rfftfreq(len(hist.index)-3, 1)
#plt.plot(jxf, np.abs(jyf))
#plt.show()
jyf[np.abs(jyf)<1e+1] = 0
new_jyf = irfft(jyf)
plt.subplot(2,1,1)
plt.plot(hist['time_index'][4:], new_jyf)
plt.title('transformed jerk')
plt.subplot(2,1,2)
plt.plot(hist['time_index'], hist["jerk"])
plt.title("original")
plt.show()

ayf = rfft(acceleration.dropna().values)
axf = rfftfreq(len(hist.index)-2, 1)
#plt.plot(axf, np.abs(ayf))
#plt.show()
ayf[np.abs(ayf)<1e+1] = 0
new_ayf = irfft(ayf)
plt.subplot(2,1,1)
plt.plot(hist['time_index'][2:], new_ayf)
plt.title('transformed acceleration')
plt.subplot(2,1,2)
plt.plot(hist['time_index'], hist["acceleration"])
plt.title("original")
plt.show()

vyf = rfft(velocity.dropna().values)
vxf = rfftfreq(len(hist.index)-1, 1)
#plt.plot(vxf, np.abs(vyf))
#plt.show()
vyf[np.abs(vyf)<0.8e+1] = 0
new_vyf = irfft(vyf)
plt.subplot(2,1,1)
plt.plot(hist['time_index'][2:], new_vyf)
plt.title('transformed velocity')
plt.subplot(2,1,2)
plt.plot(hist['time_index'], hist["velocity"])
plt.title("original")
plt.show()

pyf = rfft(hist["Close"].values)
pxf = rfftfreq(len(hist.index), 1)
#plt.plot(pxf, np.abs(pyf))
#plt.show()
pyf[np.abs(pyf)<0.8e+1] = 0  # changes the cut off amplitude. the smaller the cut off the more detail we capture
new_pyf = irfft(pyf)
plt.subplot(2,1,1)
plt.plot(hist['time_index'], new_pyf)
plt.title('transformed price')
plt.subplot(2,1,2)
plt.plot(hist['time_index'], hist['Close'])
plt.title("original")
plt.show()


# find Cn this is wrongly implemented
def C(n, x, fx):
    It = 0
    T = 2*math.pi
    for i in range(len(fx)):
        dI = fx[i]*(math.e)**((2j*math.pi*n*x[i])/T)
        It += dI
    #print(It)
    return It/T
fourier_coeff = np.empty(len(new_jyf))
fourier_coeff[fourier_coeff<1e-15] = 0
for i in range(20):
    fourier_coeff[i] = C(i, hist['time_index'], new_jyf)
fourier_coeff[np.abs(fourier_coeff)<1e-15] = 0
fourier_trans = np.fft.fft(new_jyf)
fourier_trans[np.abs(fourier_trans)<1e-14] = 0
# approximating up to nth term, find future values of y. x0 is historical data, x is where we want to predict until
def f(x0, fx, x, n): #bad code
    func = 0
    T = 2*math.pi
    for a in range(len(x)):
        for i in range(n):
            dI = C(i, x0, fx)*(math.e)**((2j*math.pi*i*x[a])/T)
            func += dI
    return func

fitted = np.empty(len(new_jyf))
for t in range(len(new_jyf)):
    fitted[t] = (f(hist["time_index"], new_jyf, np.array(list(range(-129,1))), 3))
plt.plot(hist['time_index'][4:], np.abs(fitted))



# plt.plot(hist["time_index"], hist["velocity"])
# plt.title(stock_name)
# plt.xlabel('Time')
# plt.ylabel('velocity')
# #plt.xticks(rotation = 90)
# plt.show()

# plt.plot(hist["time_index"], hist["acceleration"])
# plt.title(stock_name)
# plt.xlabel('Time')
# plt.ylabel('acceleration')
# #plt.xticks(rotation = 90)
# plt.show()

# plt.plot(hist["time_index"], hist["jerk"])
# plt.title(stock_name)
# plt.xlabel('Time')
# plt.ylabel('jerk')
# #plt.xticks(rotation = 90)
# plt.show()

# plt.scatter(hist["time_index"], hist["Close"])
# plt.title(stock_name)
# plt.xlabel('Time')
# plt.ylabel('price')
# #plt.xticks(rotation = 90)
# plt.show()


