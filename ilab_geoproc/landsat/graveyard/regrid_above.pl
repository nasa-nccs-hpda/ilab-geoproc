#!/usr/bin/perl -w

# include classes/libraries
use warnings;
use strict;

# print hostname from where script is executed
# root directory where data resides
my $host = `/bin/hostname`;
my $rootdir="/adapt/nobackup/people/mcarrol2/AKNED";
print "Hostname: $host";
print "Root dir: $rootdir\n";


open (TILE, "/adapt/nobackup/people/jacaraba/development/geoProc/geoproc/landsat/list");

# iterate over each line from the list file
while (my $tile= <TILE>){
    
    chomp $tile;  # remove trailing newline
    print "$tile\n";

    my $hh = substr($tile, 1, 3);
    my $vv = substr($tile, 5, 3);
    print "HH: $hh VV: $vv\n";

    my $x_max = -3400020 + (($hh + 1) * (180 * 6000));
    my $x_min = -3400020 + ($hh * (180 * 6000));
    my $y_max = 4640000  - ($vv * (180 * 6000));
    my $y_min = 4640000  - (($vv + 1) * (180 * 6000));
    my $TE = "$x_min $y_min $x_max $y_max";
    
    print "x_max: $x_max x_min: $x_min y_max: $y_max y_min: $y_min TE: $TE\n";
    
    #my $out = "ABoVE.GladARD.$dateaquisition.A$tile.011.$productdate.tif";   
    my $out = "ABoVE.GladARD.200118.B$tile.001.20221514.tif";   # example tile
    my $inputs="/adapt/nobackup/projects/ilab/data/LandSatABoVE/62N/164W_62N/815.tif"; # 9xxx something vrts
    `gdalwarp -multi -wo NUM_THREADS=ALL_CPUS -t_srs \'+proj=aea +lat_1=50 +lat_2=70 +lat_0=40 +lon_0=-96 +x_0=0 +y_0=0 +ellps=GRS80 +datum=NAD83\' -te $TE -tr 30 30 -dstnodata -9999 $inputs $out`;
}
close TILE;