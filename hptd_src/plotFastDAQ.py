import pandas as pd
import os
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
import scipy as sp
from numpy.fft import fft, fftfreq, rfft, rfftfreq
from scipy.signal import find_peaks
from scipy.signal import savgol_filter



params = {'legend.fontsize': 'small',
          'figure.figsize': (6, 4),
         'axes.labelsize': 'medium',
         'axes.titlesize':'medium',
         'xtick.labelsize':'x-small',
         'ytick.labelsize':'x-small'}
plt.rcParams.update(params)



def legendOutside(ax):
    # Shrink current axis by 20%
    box = ax.get_position()
    ax.set_position([box.x0, box.y0, box.width * 0.7, box.height]) #[left, bottom, width, height]
    # Put a legend to the right of the current axis
    
def convertLJUstream(file_prefix, config = 'pwr',filt_window='none', filt_order='none'):  # filt_window=25, filt_order=3):



    ##################################################

    #get sorted list of files
    wipDir=os.path.dirname(file_prefix)
    files=sorted(os.listdir(wipDir))

    # make the target filename
    mergeFile=os.path.join(wipDir, file_prefix+'_merge.dat')

    cnt=0
    foundfiles=[]
    for filename in files:
        if filename.startswith(os.path.basename(file_prefix)) and (os.path.basename(mergeFile)!=filename):
            
            #locPath=os.getcwd()+'\\sensorNode\\sensorData'
            #Path(locPath).mkdir(parents=True, exist_ok=True)
            #locFilename = os.path.join(locPath, filename)
            foundfiles=[foundfiles, filename]
            thisFile=os.path.join(wipDir, filename)
            # read the stream data
            if config=='pwr':

                try:
                    streamCols = ['Time','y0', 'y1', 'y2']
                    headerRows=5
                    thisdf=pd.read_csv(thisFile,
                                header=headerRows,
                                sep='\t',
                                usecols = streamCols)
                except:
                    streamCols = ['Time','y0', 'y1']
                    headerRows=4
                    thisdf=pd.read_csv(thisFile,
                                header=headerRows,
                                sep='\t',
                                usecols = streamCols)
            
            # rename the columns
            #thisdf = thisdf.rename(columns=renameCols)

            thisdf['Capture Time, s']=thisdf['Time']
            # scale the current
            thisdf['Raw Input Current, A']=(thisdf['y1']*0.2)
            # label voltage
            thisdf['Raw Input Voltage, V']=(thisdf['y0'])
            try:
                thisdf['TI Voltage, V']=(thisdf['y2'])
            except:
                pass



            # filter the current
            if filt_window == 'none':
                thisdf['Input Current, A']=thisdf['Raw Input Current, A']
                thisdf['Input Voltage, V']=thisdf['Raw Input Voltage, V']
            else:
                # filter the current. Caution - may adversely affect the frequency response!!
                thisdf['Input Current, A']=savgol_filter(thisdf['Raw Input Current, A'], filt_window, filt_order)
                # filter the voltage
                thisdf['Input Voltage, V']=savgol_filter(thisdf['Raw Input Voltage, V'], filt_window, filt_order)
                
            
            if cnt >0:
                # next files, append the dataframe
                alldf=pd.concat([alldf, thisdf])
            else:
                # first file, create the start of the dataframe
                alldf=thisdf
            cnt+=1

    if cnt>0:
        print (foundfiles)
        alldf.to_csv(mergeFile, sep='\t',index = False ,float_format='%6.6f')

        
        ########################## plot the input data #################################
    
        if filt_window != 'none':
            # plot the filter response for checking
            # setup axes
            inputFig=plt.figure("Check filter output, {:s}".format(mergeFile),figsize=(4,6))#(6.6, 7.7))
            axraw=inputFig.add_subplot(311,position=[0.15, 0.05, 0.9, 0.9]) #[left, bottom, width, height]
            axfilt=inputFig.add_subplot(312,position=[0.15, 0.05, 0.9, 0.9]) 
            axcomb=inputFig.add_subplot(313,position=[0.15, 0.05, 0.9, 0.9])

            # plot the data
            alldf.plot(x="Time", y="Raw Input Current, A", color ='tab:green', ax=axraw)
            alldf.plot(x="Time", y="Input Current, A", color ='tab:blue', ax=axfilt)
            alldf.plot(x="Time", y=["Raw Input Current, A","Input Current, A"], color =['tab:green','tab:blue'], ax=axcomb)

            # remove legends
            axraw.get_legend().remove()
            axfilt.get_legend().remove()
            axcomb.get_legend().remove()

            # set axis labels
            axraw.set_title("Raw Input: Current" ,)
            axraw.set_ylabel("Current, A")
            axraw.set_xlabel(None)
            axraw.grid(which='minor')


            axfilt.set_title("Filter Window: {:d}, Filter Order:  {:d}".format(filt_window, filt_order))

            axfilt.set_ylabel("Current, A")
            axfilt.set_xlabel(None)
            axfilt.grid(which='minor')

            axcomb.set_title("Raw and Filtered Combined: Current")
            axcomb.set_ylabel("Current, A")
            axcomb.grid(which='minor')
            # don't remove the xlabel from the bottom plot
            #set title
            plt.suptitle("file: {:s}".format(os.path.basename(mergeFile)), fontsize=8)
            plt.tight_layout()




def processDaqData(file, startTime=0, endTime=-1, all='yes', startup='no', config='pwr', readHeader='no'):

####################### process raw data #######################################

    if config=='pwr':

        pwrStreamCols = ['Time','y0', 'y1']

        captureCols=["Capture Time, s",
            "Input Voltage, V",
            "Input Current, A"]

        renameCols={'Time':"Capture Time, s",
                    'y0':"Input Voltage, V",
                    'y1':"Input Current, A"}


        allCols=["Input Voltage, V",
            "Input Current, A"]


    if readHeader=='no':
        alldf=pd.read_csv(file, header=None, names=captureCols, sep='\t')
    else:
        alldf=pd.read_csv(file, header=0, sep='\t')


    # calculate normalised time
    alldf["Time, s"]=alldf["Capture Time, s"]-alldf["Capture Time, s"].iloc[0]
    if startup=='yes':
        # re-centre zero on the switch on event (i.e. when current rises above 50 mA)
        trig=alldf["Input Current, A"].ge(0.07)
        alldf["Time, s"]=alldf["Time, s"]-alldf["Time, s"].iloc[trig.idxmax()] 
    t="Time, s"
    ## calculate power
    alldf["Input Power, W"]=alldf["Input Voltage, V"]*alldf["Input Current, A"]

    # plot all data
    if all=='yes':
        rawFig=plt.figure("Raw data, file: {:s}".format(file))
        axAll=rawFig.add_subplot(111,position=[0.15, 0.05, 0.4, 1]) #[left, bottom, width, height]
        alldf.plot(x=t, y=allCols, ax=axAll, grid='minor')
        plt.title('Raw data')
        axAll.legend(loc='upper left', bbox_to_anchor=(1.05, 1))
        plt.suptitle("file: {:s}".format(os.path.basename(file)), fontsize=8)


############## crop data if start/end args have been passed#####################
    if startup=='yes':
        if startTime != 0:
            startIdx=(alldf["Time, s"] <= startTime).idxmin()
        else:
            startIdx=0
        if endTime != -1:
            endIdx=(alldf["Time, s"] >= endTime).idxmax()
        else:
            endIdx=-1
    else:
        startIdx=0
        endIdx=len(alldf)
     

    # copy cropped data into new dataframe
    df=alldf[startIdx:endIdx].copy()
    df.reset_index()
    if startup=='no':
        df["Time, s"]-= df["Time, s"].iloc[0]

    return df


def plot(df, title, mean='no', config='pwr'):
########################## plot the input data #################################
    # setup axes
    inputFig=plt.figure("Battery Input Data, {:s}".format(title),figsize=(4,6))#(6.6, 7.7))
    axV=inputFig.add_subplot(311,position=[0.15, 0.05, 0.9, 0.9]) #[left, bottom, width, height]
    axI=inputFig.add_subplot(312,position=[0.15, 0.05, 0.9, 0.9]) 
    axP=inputFig.add_subplot(313,position=[0.15, 0.05, 0.9, 0.9])

    # plot the data
    df.plot(x="Time, s", y="Input Voltage, V", color ='tab:red', ax=axV, grid='minor')
    df.plot(x="Time, s", y="Input Current, A", color ='tab:blue', ax=axI, grid='minor')
    df.plot(x="Time, s", y="Input Power, W", color ='tab:green', ax=axP, grid='minor')
    if mean == 'yes':
        try:
            # using this option only makes sense for steady-state data

            # get text x offset
            textx=df['Time, s'].loc[25]
            # get mean voltage
            meanV=df["Input Voltage, V"].mean()
            # plot mean line
            axV.axhline( meanV, color='tab:grey')
            # annotate plot with mean value
            axV.text(textx, meanV, 'Mean = {:0.3f} V'.format( meanV), fontsize = 11.5)

            # as before, for current
            meanI=df["Input Current, A"].mean()
            axI.axhline(meanI, color='tab:grey')
            axI.text(textx, meanI, 'Mean = {:0.3f} A'.format( meanI), fontsize = 11.5)

            # as before, for power
            meanP=df["Input Power, W"].mean()
            axP.axhline(meanP, color='tab:grey')
            axP.text(textx, meanP, 'Mean = {:0.3f} W'.format( meanP), fontsize = 11.5)
        except:
            print("Failed to get mean data")

    # remove legends
    axV.get_legend().remove()
    axI.get_legend().remove()
    axP.get_legend().remove()
    
    # set axis labels
    axV.set_title("Battery Input: Voltage" ,)
    axV.set_ylabel("Voltage, V")
    axV.set_xlabel(None)
    axV.grid(which='minor')

    axI.set_title("Battery Input: Current")
    axI.set_ylabel("Current, A")
    axI.set_xlabel(None)
    axI.grid(which='minor')

    axP.set_title("Battery Input: Power")
    axP.set_ylabel("Power, W")
    axP.grid(which='minor')
    # don't remove the xlabel from the bottom plot
    #set title
    plt.suptitle("file: {:s}".format(os.path.basename(title)), fontsize=8)
    plt.tight_layout()

    try:
        # setup axes
        TIFig=plt.figure("TI voltage",figsize=(6,4))#(6.6, 7.7))
        axTI=TIFig.add_subplot(111,position=[0.15, 0.05, 0.9, 0.9]) #[left, bottom, width, height]
        # plot the data
        df.plot(x="Time, s", y=["TI Voltage, V", "Input Power, W"], color =['tab:red', 'tab:green'], ax=axTI, grid='minor')
        plt.suptitle("file: {:s}".format(os.path.basename(title)), fontsize=8)
    except:
        pass

############################## plot system voltages ############################


def plotFFT(df, file, param):

# %%
    SAMPLE_RATE=1/df["Time, s"].diff().median()
    N=len(df)
    # subtract DC component
    DC_subtract =False
    if DC_subtract:
        # remove DC offset and compute the FFT
        yf=rfft(df[param]-df[param].mean())
    else:
        # copmpute the FFT, including DC offset
        yf=rfft(df[param], norm='forward')
        
        # note norm='forward' gives the equivalent of (1/N * yf), i.e.
        # it reverses the scaling factor which is otherwise * N points
# %%
    # add a (fake, negative freq) element so that the DC peak is found
    yf = np.insert(yf,0,min(yf), axis=0)

    # get the frequency bins
    xf=rfftfreq(N, 1/SAMPLE_RATE)
    xf= np.insert(xf,0,(xf[0]-xf[1]), axis=0)
   
    # find the peaks
    peaks_idx, peak_props =find_peaks(abs(yf), height=2.5e-3, threshold =1e-3)
    [print("%4.4f    \t %3.4f" %(xf[peaks_idx[i]], peak_props['peak_heights'][i])) for i in range(len(peaks_idx))]
    # plot the FFT, with peaks marked
    fftFig=plt.figure("{:s} FFT: {:s}".format(param,file))
    axfft=fftFig.add_subplot(111,position=[0.15, 0.05, 0.4, 1]) #[left, bottom, width, height]
    axfft.plot(xf, abs(yf), '-', xf[peaks_idx], peak_props['peak_heights'], 'x')
    #axfft.stem(xf[peaks_idx], abs(yf[peaks_idx]),markerfmt=" ")
    plt.yscale("log")
    axfft.set_xlim(-5,xf[peaks_idx].max()+50)
    axfft.set_xlabel("Frequency, Hz")
    axfft.set_ylabel(param)
    axfft.grid(which='minor')
    tick_spacing=30
    axfft.xaxis.set_major_locator(ticker.MultipleLocator(tick_spacing))

    axfft.text(xf[peaks_idx[0]+5],peak_props['peak_heights'][0], 'DC power = {:0.3f} W'.format( peak_props['peak_heights'][0]), fontsize = 11.5)

    plt.title('FFT of {:s} '.format(param))
    plt.suptitle("file: {:s}".format(os.path.basename(file)), fontsize=8)
    


from tkinter import Tk
from tkinter.filedialog import askopenfilename

Tk().withdraw() # we don't want a full GUI, so keep the root window from appearing
fname = askopenfilename() # show an "Open" dialog box and return the path to the selected file

print(fname)

# get everything prior to the last underscore, e.g. 'data'('_0.dat')
fname_prefix= fname.rsplit('_', 1)[0]
fname_merge = fname_prefix+'_merge.dat'

convertLJUstream(fname_prefix, config='pwr', filt_window='none')

df=processDaqData(fname_merge, 
        startTime=-.25,
        endTime=2,
        all='yes',
        startup='yes',
        config='pwr',
        readHeader='yes')

plot(df, fname_merge, mean='yes',config='pwr')
#plotFFT(df, fname_merge, param="Input Power, W")


plt.show(block = True)

# %%



