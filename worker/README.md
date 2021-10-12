# OpenStreetMap to simple svg for laser cutting

## Introduction

At [RLab (Reading Hackspace)](https://rlab.org.uk/) we wanted a way of turning 
openstreetmap data into files suitable for laser cutting.

There is already a lot of good software available for manipulating 
[openstreetmap](http://www.openstreetmap.org) data, including tools like 
[Maperitive](https://wiki.openstreetmap.org/wiki/Maperitive) that can render 
into beautiful svg files.

The problems I had with using these tools for my purpose are as follows:

* The tools are giant "swiss army knives" that contain so much functionality it 
  is sometimes difficult to understand how to configure them to achieve your 
  aim
* Frequently, even when configured, they don't quite do what you need
* Some tools require large and heavyweight frameworks to run e.g. Mono

The aim of this project is to provide a simple set of tools, with minimal 
software requirements, and a simple process that can allow the majority of 
hackspace members to get a map they can lasercut.

## Installation

### Python 3

This software is written in python 3, so you will need a computer that has a 
python 3 interpreter installed.  Most moder linux distributions will already 
have this installed, but if not it can usually be installed with your package 
manager.

If you are running Microsoft Windows, then you can download python 
[here](https://www.python.org/downloads/windows/)

Once you have python 3 installed - check by doing the following from a command 
prompt:

~~~ shell
python3 --version
~~~

If you don't get any errors then you should have it installed OK.  If it can't 
find `python3` then you may need to modify your PATH to include the directory 
where the executable is installed

#### Additional packages for building python modules in venv

~~shell
sudo apt install python3-venv python3-dev
~~~

### Clone the code

Use git to clone this repository:

~~~ sh
git clone https://gitlab.com/vanceb/osm2lbsvg.git
~~~

### Create a virtual environment to hold the packages you need

Move into the cloned directory:

~~~ sh
cd osm2lbsvg
~~~

Rather than mess up your general python environment it is a good idea to create 
a specific environment for your particular application.  This can be achieved 
as follows:

~~~ sh
python3 -m venv ./venv
~~~

To operate inside this environment (which you should do each time you want to 
run the software) you need to activate it.  So from inside the project 
directory you can activate it by:

~~~ sh
. ./venv/bin/activate
~~~

### Getting the python packages needed

Once you have activated the virtual python environment you can install python 
packages in this environment.  To install all required packages type the 
following:

~~~ sh
pip install -r requirements.txt
~~~

### Contour lines (Optional)
If you want to include contour lines in your map you will need additional 
packages.  These are a little more heavyweight hence including them in a 
separate optional instruction

~~~ sh
pip install -r requirements_contours.txt
~~~

## The Tools...

The python tools with their general purposes.  To work out how to use them run the python file with the `--help` option
* `overpass.py` Uses the Openstreetmap overpass API to get the data
* `contours.py` Gets height data from NASA/USGS and creates contour lines
* `svgmap.py` Converts openstreetmap data, and contours to an svg file using a specific config
* `srtm.py` Used mainly as a library, but can be used to create a standalone OSM file if you just want a topo map
* `osm.py` A library to encapsulate openstreetmap data
* `svg.py` A library that performs the conversion from OSM data to svg

## Creating a first map

Once you have the software installed you can make your first map!

### Get the openstreetmap data

1. Go to [openstreetmap.org](http://www.openstreetmap.org) and go to a location 
   of your choosing.
2. Click the "Export" button at the top of the screen.  In the left panel it 
   will show you an export box with the top, bottom, left, and right lat/lons.  
   This is the area you can see on the screen.  Just below that grey box is 
   some blue text saying "Manually slelect a different area", click on this 
   text.  It will pop up a box with 4 moveable corners.
3. Move the corners to select the area of the map you want.  Make this area 
   small, the map contains lots of data!  Click on the blue "Export" button to 
   download your data
4. Once the data is downloaded I recommend moving it to a data folder, I use 
   `<project folder>/data`

~~~ sh
mkdir data
cp ~/Downloads/Map.osm ./data/<name of map>.osm
~~~

### Add contour lines (Optional)

If you installed the software needed to generate contour lines earlier on then 
now is the time to add them to the map data.

#### Register with USGS to be able to download the height data

Go to the USGS [User Registration](https://ers.cr.usgs.gov/register/) page and 
fill in the details to get a username and password.

Recently this hasn't seemed to work.  If it fails for you try to register 
[here](https://urs.earthdata.nasa.gov/)

Put your registration details into the file `<project folder>/conf/credentials.yaml`

~~~ ./conf/credentials.yaml
username: <your username>
password: <your password>
~~~

#### Add contour lines to your data file

The following command looks at your data file to work out the region it is 
covering.  It will then download the appropriate height data from USGS and 
process it to create the contour lines that will be added to your data file.

There is no height data for regions of only sea, so you may see errors about 
not being able to download some tiles if your region contains a lot of sea.

~~~ sh
python contours.py ./data/<name of map>.osm
~~~

### Turn the OSM data into an svg

The openstreetmap data file contains loads of data.  Most of it is irrelevant 
for our purposes, so we need to choose which data we render into the svg file.  
There are a number of config files with different settings, but for the 
purposes of this demonstration we are going to use the default one which 
includes a lot of data (The svg is going to look cluttered!), but it is 
interesting to see the types of data that are available.  

The data included in the default config is by no means everything we could 
plot, but is a good starting point.  Later on you can create a copy of this 
file and edit it to suit your project, but for now lets just go with it.

There are a number of command line options that can modify the output of the 
svg.  You can find out what options there are by running `python svgmap.py -h`
For the moment we are going to go with the defaults:

~~~ sh
python svgmap.py data/<name of map>.osm
~~~

You should now have an svg file in the same location as the openstreetmap data 
file.  You can view it by dragging the file into a browser window or opening it 
with inkscape.

