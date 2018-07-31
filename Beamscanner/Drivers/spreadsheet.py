def spreadsheet(time_data, pos_data, vvm_data, save_name):

    import os
    import pyoo
    
    # Creates localhost for libre office
    os.system("soffice --accept='socket,host=localhost,port=2002;urp;' --norestore --nologo --nodefault # --headless")
    # Uses pyoo to open spreadsheet
    desktop = pyoo.Desktop('localhost',2002)
    doc = desktop.create_spreadsheet()
    
    try:
        # Writes data to spreadsheet
        sheet = doc.sheets[0]
        sheet[0,0:5].values = ["Time (s)","X Position (mm)", "Y Position (mm)", "Amplitude (dB)", "Phase (deg)"]

        for i in range(len(pos_data)):
            sheet[i+1,0].value = time_data[i]
            sheet[i+1,1].value = pos_data[i][0]
            sheet[i+1,2].value = pos_data[i][1]
            sheet[i+1,3].value = vvm_data[i][0]
            sheet[i+1,4].value = vvm_data[i][1]

        doc.save('BeamScannerData/' + str(save_name) + '.xlsx')
        doc.close()

    except (ValueError, KeyboardInterrupt, RuntimeError):
        doc.close()
        pass

