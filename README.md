# osm2svg
Convert [openstreetmap.org[(https://openstreetmap.org)] data into an svg file suitable for lasercutting or other potential uses.

## How to build

### Build the worker container

~~~sh
cd worker
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

for a simple system without persistent storage...

~~~sh
docker-compose up -d
~~~

## Test/use

Go to [http://localhost:5000](http://localhost:5000) to use the simple UI

## Operational use

Edit the `api/.flaskenv` file to turn off debugging

Place this server behind an nginx or other proxy.

Write a better UI...