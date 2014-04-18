'''
Created on Apr 2, 2014

@author: marco
'''
import os

from pymodelica import compile_jmu
from pymodelica import compile_fmux
from pyjmi import JMUModel
from pyjmi import CasadiModel

import matplotlib.pyplot as plt
import numpy as np

def getData(new_time, plot = False):
    """
    This function get data from CSV files
    """
    # get current directory
    curr_dir = os.path.dirname(os.path.abspath(__file__));
    path_csv = os.path.join(curr_dir,"..","..","Data","DataExample.csv")
    data = np.loadtxt(open(path_csv,"rb"), delimiter=",", skiprows=1)
    
    # Get time vector
    time = data[:, 0]
    
    # Get data and normalize them
    pv   = data[:, 1:4]
    pv   = pv/np.max(pv)
    bldg = -data[:, 4:]
    bldg = bldg/np.max(bldg)
    bldg = bldg + 0.5*np.ones(np.shape(bldg))
    bldg = bldg/np.max(bldg)
    
    # interpolate
    pv_new = np.zeros((len(new_time),3))
    bldg_new = np.zeros((len(new_time),3))
    for i in range(3):
        pv_new[:,i]   = np.interp(new_time, time, pv[:,i])
        bldg_new[:,i] = np.interp(new_time, time, bldg[:,i])
    
    # plot if requested 
    if plot:
        figPv = plt.figure()
        ax = figPv.add_subplot(211) 
        ax.plot(new_time, pv_new, 'r', alpha=0.3)
        ax.set_xlabel('Time [hours]')
        ax.set_ylabel('Power [W]')
        ax.set_xlim([0, 86400])
        ax.set_ylim([0, 1])
        
        ax = figPv.add_subplot(212) 
        ax.plot(new_time, bldg_new, 'b', alpha=0.3)
        ax.set_xlabel('Time [hours]')
        ax.set_ylabel('Power [W]')
        ax.set_xlim([0, 86400])
        ax.set_ylim([0, 1])
        
        plt.show()
    
    return (pv_new, bldg_new)

def run_simulation_with_inputs(time, price, pv, bldg, plot = False):
    """
    This function runs a simulation that uses inputs data series
    """
    
    # get current directory
    curr_dir = os.path.dirname(os.path.abspath(__file__));
    
    # compile FMU
    path = os.path.join(curr_dir,"..","..","Models","ElectricalNetwork.mop")
    jmu_model = compile_jmu('ElectricNetwork.ACnetwork', path)

    # Load the model instance into Python
    model = JMUModel(jmu_model)
    
    # create input data series for price and current battery
    Npoints = len(time)
    
    # for the simulation no power flow in the battery
    P  = np.zeros(Npoints)
    Q  = np.zeros(Npoints)
    
    # Build input trajectory matrix for use in simulation
    u = np.transpose(np.vstack((t_data, P, Q, price, -np.squeeze(bldg[:,0]), -np.squeeze(bldg[:,1]), -np.squeeze(bldg[:,2]), \
                                np.squeeze(pv[:,0]), np.squeeze(pv[:,1]), np.squeeze(pv[:,2]))))
    
    # Solve the DAE initialization system
    model.initialize()
    
    # Simulate
    res = model.simulate(input=(['P_batt', 'Q_batt', 'price', 'P_bldg1', 'P_bldg2', 'P_bldg3', 'P_pv1', 'P_pv2', 'P_pv3'], u), start_time=0., final_time=24.0*3600.0)
    
    # Extract variable profiles
    if plot:
        plotFunction(res)
    
def plotFunction(res):
    
    time = res["time"]/3600.0
    price= res["price"]
    V1   = res["bldg1.Vrms"]
    V2   = res["bldg2.Vrms"]
    V3   = res["bldg3.Vrms"]
    P_batt = res["batt.P"]
    Q_batt = res["batt.Q"]
    SOC    = res["batt.SOC"]
    
    figPrice = plt.figure()
    ax = figPrice.add_subplot(111) 
    ax.plot(time, price, 'r', label='$Price$')
    ax.set_xlim([0, 24])
    ax.set_ylim([0.1, 0.25])
    ax.set_xlabel('time [hoyrs]')
    ax.set_ylabel('Energy price [$/kWh]')
    ax.legend()
    
    figV = plt.figure()
    ax = figV.add_subplot(111) 
    ax.plot(time, V1, 'r', label='$V_1$')
    ax.plot(time, V2, 'g', label='$V_2$')
    ax.plot(time, V3, 'b', label='$V_3$')
    ax.set_xlim([0, 24])
    ax.set_xlabel('time [hours]')
    ax.set_ylabel('Voltage [V]')
    ax.legend()
    
    figBatt = plt.figure()
    ax = figBatt.add_subplot(211) 
    ax.plot(time, P_batt, 'r', label='$P_{BATT}$')
    ax.plot(time, Q_batt, 'g', label='$Q_{BATT}$')
    ax.set_xlim([0, 24])
    ax.set_xlabel('time [hours]')
    ax.set_ylabel('Power fed into the battery [W]')
    ax.legend()
    
    ax = figBatt.add_subplot(212) 
    ax.plot(time, SOC, 'r', label='$SOC$')
    ax.set_xlim([0, 24])
    ax.set_xlabel('time [hours]')
    ax.set_ylabel('State of Charge [$\cdot$]')
    ax.legend()
    
    plt.show()

if __name__ == '__main__':
    #run_simulation()
    #res = run_simulation_with_inputs()
    #run_optimization(res)
    
    # Define the points over which the inputs will be provided
    # One point every 10 minutes
    Npoints = 24*6+1
    
    # Time vector
    t_data = np.linspace(0.0, 24*3600, Npoints)
    
    # Define the price for the electricity
    t_data = np.linspace(0.0, 24*3600, Npoints)
    t_price = np.array([0.0, 6.0, 8.0, 12.0, 13.0, 16.0, 18.0, 19.0, 22.0, 24.0])*3600.0
    price =   np.array([0.5, 0.5, 0.6, 0.8,  1.0,  1.1,  0.8,  0.7,  0.5,  0.5])
    price = 0.22*np.interp(t_data, t_price, price)
    
    # Time series for buildings and PVs
    (pv, bldg) = getData(t_data, plot = False)
    
    # Run the simulation
    res = run_simulation_with_inputs(t_data, price, pv, bldg, plot = True)