# osm2svg
Convert [openstreetmap.org[(https://openstreetmap.org)] data into an svg file suitable for lasercutting or other potential uses.

## Configuration

### Contours

If you want to be able to create contour lines from [SRTM](https://www.usgs.gov/centers/eros/science/usgs-eros-archive-digital-elevation-shuttle-radar-topography-mission-srtm-1-arc?qt-science_center_objects=0#qt-science_center_objects) data then you need to get a login from NASA to allow download of the data.

You can register for a login [here](https://urs.earthdata.nasa.gov/users).  You will need these credentials later when building the worker container.

## How to build

### Install docker

Follow the instructions [here](https://docs.docker.com/engine/install/)

### Download from github

git clone https://github.com/vanceb/osm2svg.git

### Build the worker container

If you created an account to allow the download of the SRTM data to create contours then you need to place these credentials in the file 

`osm2svg/worker/data/conf/credentials.yaml`
~~~sh
username: "<your username>"
password: "<your password>"
~~~

Then you can build the container:

~~~sh
cd osm2svg/worker
docker build -t osm2svg .
cd ..
~~~

### Build the API/UI container

~~~sh
cd api
docker build -t osm2svgapi .
cd ..
~~~

## Running

Download `docker-compose` using the instructions [here](https://docs.docker.com/compose/install/).  Then for a simple system without persistent storage...

~~~sh
docker-compose up -d
~~~

## Test/use

Go to [http://localhost:5000](http://localhost:5000) to use the simple UI

## Operational use

Place this server behind an nginx or other proxy.

Write a better UI...