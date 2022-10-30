//Before running the Macro, update sites required are:
// https://sites.imagej.net/BIG-EPFL/
// https://sites.imagej.net/NanoJ/
// https://sites.imagej.net/NanoJ-SQUIRREL/
// https://sites.imagej.net/NanoJ-SRRF/

#@File(label = "Choose an output folder", style = "directory") output_folder
#@File(label = "Image to process") image_file
#@Integer(label = "Number of frames for SRRF Analysis") nFrames

run("Fresh Start"); //to kill all the runnning versions of the macro

open(image_file);
originalImageTitle=getTitle();

//filtering of data to remove stripes arising especially from sCMOS camera
run("Bandpass Filter...", "filter_large=1000 filter_small=1 suppress=Horizontal tolerance=5 process");
run("Bandpass Filter...", "filter_large=1000 filter_small=1 suppress=Vertical tolerance=5 process");
selectImage(originalImageTitle);

//dividing the original set of frames into two sequences for FRC test later on
run("Split image sequence into odd and even frames");

evenImageTitle = originalImageTitle+" - Even Frames";
oddImageTitle = originalImageTitle+" - Odd Frames";

srrf_process(evenImageTitle);
srrf_process(oddImageTitle);

//FRC test
run("FRC Calculation...");
//you need to select the two SRRF files as images to get the FRC plot


//SRRF analysis as a function
function srrf_process(imagePath) {
		
	//performing SRRF analysis: on a set of parameters
	selectImage(imagePath);
	njiFilePath = output_folder+File.separator+imagePath+".nji";
	print("The image will be saved as "+njiFilePath);
	run("Save Image as NJI...", "choose=["+njiFilePath+"]");
	
	//to estimate the drift and correct it while SRRF analysis
	run("Estimate Drift", "time=1 max=0 reference=[first frame (default, better for fixed)] choose=["+njiFilePath+"]");
	
	filePathWithDriftCorrection = njiFilePath+"DriftTable.njt";
	print("Drift file path = "+filePathWithDriftCorrection);
	
	//Here it is possible to modify the command below to include all the settings, like TRAC or modify the values of ring radius, etc.
	//This modification is very much dependent on the type of cells to be analysed and has to be manually controlled to sweep across all the parameters
	
	run("SRRF Analysis", "rbg1=[Temporal Radiality Pairwise Product Mean (TRPPM)] "
	                     +"integrate_temporal_correlations "
	                     +"trac_order=2 do_intensity_weighting "
	                     +"do_gradient_weighting psf_fwhm=2.78 minimize_srrf_patterning save=.tif "
	                     +"ring=1.25 radiality_magnification=10 axes=8 do_drift-correction "
	                     +"frames_per_time-point="+nFrames+" "
	                     +"start=0 end=0 "
	                     +"max="+nFrames+" "
	                     +"preferred=0 "
	                     +"choose=["+filePathWithDriftCorrection+"]");
	                     
	savePathProcessed =  output_folder+File.separator+imagePath+"-processed.tif";
	save(savePathProcessed);
}
