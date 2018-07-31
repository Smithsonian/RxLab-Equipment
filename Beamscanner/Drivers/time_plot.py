def time_plot(time_data, vvm_data):
    
    import matplotlib.pyplot as plt
    
    amp_data = []
    phase_data = []
    
    if type(vvm_data[0]) == tuple:
        for i in vvm_data:
            amp_data.append(i[0])
            phase_data.append(i[1])
        
    elif type(vvm_data[0]) == str:
        for i in vvm_data:
            amp_data.append(float(i.split(",")[0]))
            phase_data.append(float(i.split(",")[1]))
    
    fig, ax1 = plt.subplots()

    ax1.plot(time_data, amp_data, 'bD--', label = "Amplitude (dB)")
    ax1.set_xlabel('Time (s)')
    ax1.set_ylabel('Amplitude (dB)', color='b')
    ax1.tick_params('y', colors='b')
    plt.legend(loc = "upper left")

    ax2 = ax1.twinx()
    ax2.plot(time_data, phase_data, 'r^-', label = "Phase (deg)")
    ax2.set_ylabel('Phase (deg)', color='r')
    ax2.tick_params('y', colors='r')
    plt.legend(loc = "upper right")
    
    fig.tight_layout()
    plt.grid("on")
    plt.show()
