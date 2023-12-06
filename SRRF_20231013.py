#Before running the Macro, update sites required are:
# https://sites.imagej.net/NanoJ/
# https://sites.imagej.net/NanoJ-SQUIRREL/
# https://sites.imagej.net/NanoJ-SRRF/
# https://biop.epfl.ch/Fiji-Update/

from ij import IJ, ImagePlus, WindowManager as WM
import os
from ij.io import DirectoryChooser
from fnmatch import fnmatch
from ij.process import ImageStatistics as IS  

def preprocess(input_folder):
	imp = IJ.openImage(os.path.join(input_folder, tif_file))
	global imagetitle
	imagetitle = imp.getTitle()
	print imagetitle
	global metadata
	metadata = imp.getCalibration().copy()
	print metadata
	global pix_size
	pix_size = imp.getCalibration().pixelWidth #get the pixel size of the imagestack
	print '### The pixel size is: %s um ###' % (pix_size)
	global img_root
	img_root = imagetitle.split('.')[0]
	global results_folder
	results_folder = os.path.join(output_folder,img_root)
	if not os.path.exists(results_folder):
		os.mkdir(results_folder)
		os.chdir(results_folder)
	else:
		os.chdir(results_folder)
	IJ.run(imp, "Bandpass Filter...", "filter_large=1000 filter_small=1 suppress=Horizontal tolerance=5 process");
	IJ.run(imp, "Bandpass Filter...", "filter_large=1000 filter_small=1 suppress=Vertical tolerance=5 process");
	IJ.run(imp, "Split image sequence into odd and even frames", "");
	save_nji(' - Odd Frames')
	save_nji(' - Even Frames')
			
def save_nji(search):
	img_4nji = IJ.getImage(IJ.selectWindow(imagetitle + search))
	global slices
	slices = img_4nji.getNSlices()
	print slices
	if 'Even' in search:
		img_4nji_title = img_root + '_even.nji'
	elif 'Odd' in search:
		img_4nji_title = img_root + '_odd.nji'
	img_4nji.setTitle(img_4nji_title)
	nji_file = os.path.join(results_folder,img_4nji_title)
	print nji_file
	img_4nji.getCalibration().setXUnit("um")
	IJ.run(img_4nji, "Properties...", "channels=1 slices=[%d] frames=1 pixel_width=[%f] pixel_height=[%f] voxel_depth=[%f]" % (slices,pix_size, pix_size, pix_size))
	IJ.run("Save Image as NJI...","choose=[%s]" % (nji_file))
	img_4nji.close()

def Estimate_Drift(time,max_dr,folder):
	IJ.run("Estimate Drift", 
	"time=[%d] max=[%d] reference=[first frame (default, better for fixed)] do_batch-analysis show_cross-correlation show_drift_plot show_drift_table folder=[%s]"
	% (int(time),int(max_dr),folder))
	#IJ.run("Estimate Drift")

def SRRF(nji_file,nji_path,drift_file,RR,RM,AR,slices,rbg1,srrf_folder,PSF_width):
	print '### Now I start the actual SRRF ###'
	IJ.run("SRRF - Configure Advanced Settings", 
	"rbg1=[%s] integrate_temporal_correlations trac_order=4 do_gradient_smoothing do_intensity_weighting do_gradient_weighting psf_fwhm=[%f] minimize_srrf_patterning save=.tif"
	% (rbg1,PSF_width))
	IJ.run("SRRF Analysis", 
	"choose=[%s] choose=[%s] ring=[%f] radiality_magnification=[%f] axes=[%f] do_drift-correction frames_per_time-point=[%d] start=0 end=0 max=[%d] preferred=0"
	% (nji_path,drift_file,RR,RM,AR,slices,slices))
	nji_base = nji_file.split('-')[0]
	srrf_file = IJ.getImage(IJ.selectWindow(nji_base + ' - SRRF'))
	srrf_tif = 'SRRF_' + nji_base + '.tif'
	log_file = os.path.join(results_folder,srrf_folder,'SRRF_' + nji_base + '_log.txt')
	IJ.log('SRRF analysis of %s \n\n' %(img_root))
	IJ.log('SRRF settings included:\n')
	IJ.log('Ring radius: %f\n' %(RR))
	IJ.log('Radiality magnification: %f\n' %(RM))
	IJ.log('Axes in Ring: %f\n' %(AR))
	IJ.log('SRRF_type: [%s]\n' %(rbg1))
	IJ.selectWindow('Log')
	IJ.saveAs("Text", log_file)
	new_pixel = float(pix_size) / float(RM)
	print '### The old pixel size is: %s um ###' % (pix_size)
	print '### The new pixel size is: %s um ###' % (new_pixel)
	srrf_file.getCalibration().setXUnit("um")
	IJ.run(srrf_file, "Properties...", "channels=1 slices=1 frames=1 pixel_width=[%f] pixel_height=[%f] voxel_depth=[%f]" % (new_pixel, new_pixel, new_pixel))
	srrf_title = os.path.join(results_folder,srrf_folder,srrf_tif)
	IJ.saveAs(srrf_file, "Tiff", srrf_title)
	srrf_file.close()
	
def FRC(results_folder,srrf_folder):
	all_files = []
	all_files = os.listdir('.')
	all_files.sort()
	for files in all_files:
		if 'even.tif' in files:
			print files
			even = IJ.openImage(os.path.join(results_folder,srrf_folder,files))
			even.show()
		if 'odd.tif' in files:
			print files
			odd = IJ.openImage(os.path.join(results_folder,srrf_folder,files))
			odd.show()
			IJ.run("FRC Calculation...", "image_1=[%s] image_2=[%s] resolution=[Fixed 1/7] display" % (even.getTitle(), odd.getTitle()))
			myPlot = WM.getWindow("FRC of [%s]"% (even.getTitle()))
			myPlot = IJ.getImage()
			frc_tif = os.path.join(results_folder,srrf_folder,'FRC_' + img_root + '.tif')
			IJ.saveAs(myPlot, "Tiff", frc_tif)
			print myPlot.getTitle()
			myPlot.close()
			even.close()
			odd.close()
	
IJ.run("Fresh Start", "")
tif_dc = DirectoryChooser("Choose a folder with tif files:")
input_folder = tif_dc.getDirectory()
if input_folder is None:  	
	print "User canceled the dialog!" 
	exit() 
srrf_dc = DirectoryChooser("Choose a folder for the resulting SRRF files:")
output_folder = srrf_dc.getDirectory()
if output_folder is None:  	
	print "User canceled the dialog!" 
	exit()
else:
	#IJ.run("OpenCL Preferences", "  choose=[NVIDIA Corporation_GPU]")
	for tif_file in os.listdir(input_folder):
		if tif_file.endswith(".tif"):
			print "The folder to save results is:", output_folder
			preprocess(input_folder)
			Estimate_Drift(1,0,results_folder)
			RingR = [0.75,1,1.5] # Ring radius
			RadMag = [8,10] # Radiality magnification
			AxesR = [6,8] # Axes in Ring
				#chose a temporal Analysis option
			rbgs = ['TRPPM','TRAC']#'TRA','TRM'
			PSF_width = 1.1829787492752075
			for RR in RingR:
				for RM in RadMag:
					for AR in AxesR:
						for rbg1 in rbgs: 
							print rbg1
							os.chdir(results_folder) 
							srrf_folder = 'SRRF_rRad' + str(RR) + '_rMag' + str(RM) + '_axes' + str(AR) + '_' + str(rbg1)
							if rbg1 == 'TRA':
								rbg1 = 'Temporal Radiality Average (TRA - default)'
							elif rbg1 == 'TRPPM':
								rbg1 = 'Temporal Radiality Pairwise Product Mean (TRPPM)'
							elif rbg1 == 'TRAC':
								rbg1 = 'Temporal Radiality Auto-Correlations (TRAC)'
							elif rbg1 == 'TRM':
								rbg1 = 'Temporal Radiality Maximum (TRM - activate in high-magnification)'
							print rbg1
							if not os.path.exists(srrf_folder):
								os.mkdir(srrf_folder)
								os.chdir(srrf_folder)
							else:
								os.chdir(srrf_folder)
							for files in os.listdir(results_folder):
								if fnmatch(files,'*.nji'):
									IJ.run("Fresh Start", "");
									print '### Now I start SRRF prep ###'
									nji_file = files
									nji_path = os.path.join(results_folder,files)
									drift_file = os.path.join(results_folder,nji_file.split('-')[0] + '-DriftTable.njt')
									if not os.path.exists(os.path.join(results_folder,drift_file)):
										print '##### Drift Files does not exist ####'
										print '##### automatic run does not work ###'
									SRRF(nji_file,nji_path,drift_file,RR,RM,AR,slices,rbg1,srrf_folder,PSF_width)
							IJ.run("Fresh Start", "");
							FRC(results_folder,srrf_folder)



#IJ.run("eSRRF - Analysis", "magnification=1 radius=1.50 sensitivity=1 #=100 vibration avg wide-field perform #_0=50 axial=400");
