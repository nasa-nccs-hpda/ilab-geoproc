# REAMDE for working with HLS data and the Prithvi model

## Download the HLS data

We use the following script to downlaod the HLS data. Note that we are including both as the -prod argument so we test how the 
model is performing against L30 product as well. The important arguments from this command are:

- start: the start date to look at the data
- end: the end date to look at the data
- bands: important since these are the ones the model is expecting
- cc: how many clouds will we allow
- dir: the output directory location
- roi: the shapefile to use to locate the command

An example is listed below:

```bash
python HLS_SuPER.py -roi /Users/jacaraba/Desktop/PhD/notebooks/HLS_SuPER/burn_scar_0_2015_8.geojson -start 06/01/2016 -end 08/01/2016 -prod both -bands BLUE,GREEN,RED,NIR1,SWIR1,SWIR2 -cc 25 -dir /Users/jacaraba/Desktop/PhD/notebooks/HLS_SuPER/burn_scar_0_2015_8
```

## Reorganized imagery into their own directory

The next step is to reorganize the image pairs into their own directories. This can be achieved with the following. Note
that we are moving all files from that pair (including all extensions), into their own subdir. This will be important to
make the stack step easier.

```bash
mkdir HLS.L30.T04WFS.2016174T213730
mv HLS.L30.T04WFS.2016174T213730* HLS.L30.T04WFS.2016174T213730
```

## Stack the imagery

This command will download invidual files per band. We can stack the bands in the proper order with the following script.
The only argument needed to run this directory is the main directory where all the subdirs of HLS are located at. For example,
all of the file of id HLS.L30.T04WFS.2016158T213725 are located under HLS_SuPER/burn_scar_1_2022_8/HLS.L30.T04WFS.2016158T213725.
We then use the following command to iterate over each subdir under burn_scar_1_2022_8 and stack the different groups of images
per their unique id.

```bash
python stack.py /Users/jacaraba/Desktop/PhD/notebooks/HLS_SuPER/burn_scar_1_2022_8
```

## Tile the images

Once we have the images stacked, we go ahead and tile the images. For this, we select the images we want to stack and then run the
following command:

```bash
mkdir burn_scar_4_2019_8_tiles
python gdal_retile.py -ps 512 512 -r cubic -targetDir burn_scar_4_2019_8_tiles burn_scar_4_2019_8/HLS.S30.T05WPN.2019248T213531.tif
```

This creates the new tiles into a directory. Now, some of these tiles are not 512x512 like the model asks for, so we need to do one
more step to resize them. Therefore, once we get the small tiles, we run the following script to resize all of them.

```bash
for f in burn_scar_4_2019_8_tiles/*.tif; do gdal_translate -outsize 512 512 $f ${f%.tif}.resized.tif; done
```

Note that this directory was the previous one we used to output the tiles. Now we are ready to run the model on the tiles and get
some figures out of them. You only need to predict the files that have the "resized.tif" extension.
For a comprehensive list of the files we are currently predicting for experiment 2:

```bash
/explore/nobackup/projects/ilab/ilab_testing/geospacial-foundation-model/BurnScars/AlaskaBurnScars/*_tiles
```

## Experiment with California

A filtering dataset of California fire perimeters is under the following path:

```bash
/explore/nobackup/projects/ilab/ilab_testing/geospacial-foundation-model/CaliforniaFire/California_Fire_Perimeters_2013-2022.gpkg
```

## Example of Running Inference with IBM Model

Activate the Anaconda environment from their repo:

```bash
export PATH="/panfs/ccds02/app/modules/anaconda/platform/x86_64/rhel/8.6/3-2022.05/bin:$PATH"
eval "$(conda shell.bash hook)"
source activate /explore/nobackup/people/sstrong/.conda/envs/burn-scars/
```

Run the inference on the selected files:

```bash
cd /explore/nobackup/projects/ilab/ilab_testing/geospacial-foundation-model/BurnScars/hls-foundation-os
python model_inference.py -config configs/burn_scars.py -ckpt /explore/nobackup/projects/ilab/ilab_testing/geospacial-foundation-model/BurnScars/Prithvi-100M-burn-scar/burn_scars_Prithvi_100M.pth -input '/explore/nobackup/projects/ilab/ilab_testing/geospacial-foundation-model/BurnScars/AlaskaBurnScars/burn_scar_0_2015_8_tiles/*.resized.tif' -output /explore/nobackup/projects/ilab/ilab_testing/geospacial-foundation-model/BurnScars/AlaskaBurnScars/burn_scar_0/predictions/ -input_type tif -bands "[0,1,2,3,4,5]"
```

Note that based on their script, its important to have a trailing "/" at the end of the output path.
