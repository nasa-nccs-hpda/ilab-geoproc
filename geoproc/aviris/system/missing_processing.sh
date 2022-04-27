# Provide list of files that are missing processing
# bash not_aux.sh '/adapt/nobackup/projects/ilab/data/Aviris/AvirisAnalysisReady/*/*' | more
find $1 -type d | while read dir ; do
    ls ${dir}/*.xml > /dev/null 2>&1
    if [ $? -ne 0 ] ; then
        #ls -lth $dir
        echo $dir
    fi
done