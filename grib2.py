# Base URL for downloading grib2 files
base_url = 'http://weather.noaa.gov/pub/SL.us008001/ST.opnl/DF.gr2/DC.ndfd/AR.conus'
noaa_params = ['maxt', 'temp', 'mint', 'pop12', 'sky', 'wspd', 'apt', 'qpf', 'snow', 'wx', 'wgust', 'icons', 'rhm']

verbose = False

# Degrib path
degrib_path = '/usr/local/bin/degrib'

def download(data_dir):
    """
    Download grib2 files to data directory
    """
    import urllib, re, os, sys

    print(verbose)
  
    # Loop over directories that have forecast data files
    for dir in ['VP.001-003','VP.004-007']: # loop over remote directories

        # Get directory listing
        ls_url = "%s/%s/ls-l" % (base_url, dir)
        f = urllib.urlopen(ls_url)
        data = f.read()
        lines = data.split("\n")
  
        # TODO - replace this
        p = re.compile("\s+") # regex used below
  
        # Change to data dir to get wget -N to work properly - TODO eliminate this chdir()
        current_data_dir = "%s/%s" % (data_dir, dir)
        #os.chdir(current_data_dir) TODO
  
        # Loop over lines
        for line in lines: # loop over lines

            # Suppose sample line is:
            # text0 text1 text2 text3 text4 month day time filename.[param].bin?? TODO
            print(line)
            info(line)

            # Only process if this is a .bin file
            if line.find(".bin") != -1:

                # Split line to get information
                month, day, time, filename = re.split("\s+", line)[5:9]

                # Split filename to get param
                param = filename.split('.')[1]

                # Only download files if we are interested in this parameter
                if param in noaa_params:

                    info("%s last modified %s/%s @ %s" % (filename, month, day, time))

                    # Use wget -N to only download if last modified date has changed
                    remote_filepath = "%s/%s/%s" % (base_url, dir, filename)
                    cmd = "wget -N %s" % (remote_filepath)
                    #os.popen(cmd)

                return

                # Cube data files if any were downloaded - TODO check to see if files were actually downloaded
                cmd = "{degrib} {data_dir}/VP.001-003/*.bin {data_dir}/VP.004-007/*.bin -Data -Index {data_dir}/all.ind -out {data_dir}/all.dat".format(
                    degrib = degrib_path,
                    data_dir = data_dir
                )
                info(cmd)
                output = ""
                for line in os.popen(cmd).readlines():

                    output += line

                info(output)

def xml(data_dir, latitude, longitude):
    """
    Generate XML file from grib2 data cube

    args:
        data_dir - Directory where grib2 data cube is located
        latitude - Latitude
        longitude - Longitude

    returns - xml string
    """

    import os

    # build and execute command
    cmd = "{degrib_path} {data_dir}/all.ind -DP -pnt {latitude},{longitude} -XML 1 -geoData {data_dir}/geodata".format(
        data_dir = data_dir, latitude = latitude, longitude = longitude, degrib_path = degrib_path)

    info(cmd)
    xml = ""
    for line in os.popen(cmd).readlines():

        xml += line

    # return output
    return xml

def info(str):

    if verbose:

        print(str)