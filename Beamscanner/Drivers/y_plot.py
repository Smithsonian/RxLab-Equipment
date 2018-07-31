def y_plot(pos_data, vvm_data):
    
    import matplotlib.pyplot as plt
    import numpy as np
    import numpy.polynomial.polynomial as poly
    
    y_data = []
    amp_data = []
    phase_data = []    

    for i in range(len(pos_data)):
        if pos_data[i][0] == 0:
            y_data.append(pos_data[i][1])
    
            if type(vvm_data[0]) == tuple:
                amp_data.append(vvm_data[i][0])
                phase_data.append(vvm_data[i][1])
        
            elif type(vvm_data[0]) == str:
                amp_data.append(float(vvm_data[i].split(",")[0]))
                phase_data.append(float(vvm_data[i].split(",")[1]))
            
    fig, ax1 = plt.subplots()
    
    x_new = np.linspace(y_data[0], y_data[-1], num=len(y_data)*10)
    
    coefs_amp = poly.polyfit(y_data, amp_data, 2)    
    fit_amp = poly.polyval(x_new, coefs_amp)
    ax1.plot(y_data, amp_data, 'bD', label = "Amp (meas)")
    ax1.plot(x_new, fit_amp, 'b--', label = "Amp (fitted)")
    ax1.set_xlabel("Y position (mm)")
    ax1.set_ylabel("Amplitude (dB)", color='b')
    ax1.tick_params('y', colors='b')
    ax1.legend(loc = "upper left")
    
    coefs_phase = poly.polyfit(y_data, phase_data, 2)
    fit_phase = poly.polyval(x_new, coefs_phase)
    ax2 = ax1.twinx()
    ax2.plot(y_data, phase_data, 'r^', label = "Phase (meas)")
    ax2.plot(x_new, fit_phase, 'r-', label = "Phase (fitted)")
    ax2.set_ylabel('Phase (deg)', color='r')
    ax2.tick_params('y', colors='r')
    ax2.legend(loc = "upper right")
    
    fig.tight_layout()
    plt.grid("on")
    plt.show()
