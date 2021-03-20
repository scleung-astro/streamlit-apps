'''
This is a StreamLit GUI apps written by demonstrating autoregression and autocorrelation.
In this apps I provide different options to build a simple periodic function with 
different frequencies. Noises can be added as well. And then the user can see how 
the resultant autocorrelation function and 

Written by Shing Chi Leung at 19 March 2021

'''

import streamlit as st
import matplotlib.pyplot as plt
import math
import numpy as np
from random import random

def main():


    # Build the header
    st.title("Autocorrelation and Autoregression Visualization")
    st.write("This is an education apps which aims at demonstrating the autocorrelation by ",
        "using periodic function as a model. You can choose the number of fundamental modes, "
        "their amplitudes and the noise amplitude. Then you can visualize the autocorrelation ",
        "function and use auto-regression to do time-series prediction. Through this work I "
        "hope to demonstrate the role of noise in autocorrelation and autoregression.")
    st.write("Written by Shing Chi Leung at 19 March 2021.")

    if st.checkbox("See instruction"):
        st.write("Procedure")
        st.write("1. Open the option subpanel on the left (click >)")
        st.write(r"2. Design your own periodic function by choosing their corresponding amplitudes $b_n$.")
        st.write("3. The original function is defined as: ($x = 0, 0.01, 0.02, ..., 10.0$)")
        st.write(r""" 
        $$
        f(x) = \sum_{i=1}^5 b_n \sin (n \pi x) + r_n U(0,1),
        $$
        """)
        st.write(r"where $r_n$ is the random noise.")
        st.write("4. Choose Add Noise to include noise and choose its amplitude. Otherwise $r_n = 0$ by default.")
        st.write("5. Then click and see the auto-correlation and auto-regression results.")

    # side bar for options
    st.sidebar.title("Options")
    st.sidebar.subheader("Design your function")
    n_modes = int(st.sidebar.select_slider("Number of modes", options=[1,2,3,4,5], value=1))

    # select amp for the mode amplitudes
    amp = [1 for i in range(n_modes)]
    for i in range(n_modes):
        if i == 0:
            amp[i] = st.sidebar.select_slider("Amplitude of Mode " + str(i+1), options=[round((i+1)*0.1,1) for i in range(10)], value=0.1)    
        else:
            amp[i] = st.sidebar.select_slider("Amplitude of Mode " + str(i+1), options=[round((i)*0.1,1) for i in range(11)], value=0.1)    

    # select noise_amp for the noise amplitudes
    noise_amp = 0
    if st.sidebar.checkbox("Add noise"):
        noise_amp = st.sidebar.select_slider("Noise amplitude", options=[0, 0.001, 0.01, 0.1, 0.5], value=0)

    st.sidebar.subheader("Setting for Autoregression")
    n_orders = int(st.sidebar.select_slider("Order of autoregression", options=[i for i in range(100)], value=1))

    # main page
    # some predefined values for plotting and analysis
    n_points = 2000
    n_autoreg = 400

    # array to be plotted and analyzed
    x = [0.01 * i for i in range(n_points)]
    y = [noise_amp * random() for i in range(n_points)]

    for i in range(n_points):
        for j in range(n_modes):
            y[i] += amp[j] * math.sin((j+1) * math.pi * x[i])


    st.subheader("Source Data")
    if st.checkbox("Show plot"):
        fig, ax = plt.subplots(nrows=1, ncols=1)
        ax.plot(x,y)
        ax.set_title("Primitive time series")
        ax.set_xlim(0,6)
        st.pyplot(fig)

    # Autocorrelation section
    st.subheader("Autocorrelation")
    st.write("Autocorrelation is defined by:")
    st.write(r"""
    $$
    AR_k = \frac{\sum_i(y_{i+k}-\bar{y}) (y_i-\bar{y})}{[\sum_i(y_i-\bar{y})]^2},
    $$
    """)
    st.write(r"where $\bar{y}$ is the mean of $y$ with $y_i$ being the i-th data point.")

    

    # calculate the auto-correlation function
    acr = [0 for i in range(n_autoreg)]

    # first calculate self-correlation
    ymean = np.mean(y)

    denominator = 0
    for j in range(n_points):
        denominator += (y[j] - ymean)**2

    for i in range(0, n_autoreg):
        nominator = 0
        for j in range(0, n_points-i, 1):
            nominator += (y[j] - ymean) * (y[j+i] - ymean)

        acr[i] = nominator / denominator

    if st.checkbox("Show autocorrelation"):
        fig2, ax2 = plt.subplots(nrows=1,ncols=1)
        ax2.plot([i for i in range(n_autoreg)], acr)
        ax2.set_title("Autocorrelation")
        st.pyplot(fig2)

    # Auto-regression section
    st.subheader("Autoregression")
    st.write("Autoregression of order $n$ is defined by:")
    st.write(r"""
    $$
    y_m = \sum_{i=0}^n a_i y_{m-i}
    $$
    """)
    st.write(r"By using historical data, we can fit the coefficient $a_i$, then we can use the coefficients and "
        "new data to predict the future data. Here we can experience how a very small noise can destroy the predictatbility "
        "of this method.")

    A_mat = []
    B_mat = [y[i] for i in range(n_orders, n_points)]

    for i in range(n_points-n_orders):
        A_mat.append(y[i:i+n_orders])

    results = np.linalg.lstsq(A_mat, B_mat)

    # do the free prediction
    y_preds = []
    x_inp = y[-n_orders:]
    for i in range(600):
        y_pred = 0
        for j in range(n_orders):
            y_pred += results[0][j] * x_inp[j]

        # update the output data
        y_preds.append(y_pred)

        # update the input for the next prediction
        for j in range(n_orders-1):
            x_inp[j] = x_inp[j+1]
        x_inp[n_orders-1] = y_pred

    #print(y_preds)

    if st.checkbox("Show autoregression coefficient"):
        st.write(results[0])

    if st.checkbox("Plot Autoregression"):
        fig3, ax3 = plt.subplots(ncols=1, nrows=1)
        ax3.plot(y_preds)
        ax3.set_title("Prediction by autoregression")
        st.pyplot(fig3)

    # ending footer for the sidebar
    st.sidebar.header("Info")
    st.sidebar.info("A short StreamLit apps for understanding the noise in autocorrelation and prediction "
                "by autoregression. Written by Shing Chi Leung at 19 March 2021. See GitHub for more.")

if __name__=="__main__":
    main()