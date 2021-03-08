# LUP4LDN Backend

## Overview

The Land Use Planning for Land Degradation Neutrality (LUP4LDN) tool allows users to formulate and evaluate Land Use (LU) and Land Management (LM) transition scenarios, providing visual representations of impacts (LD gains and losses) and trade-offs towards achieving land degradation neutrality (LDN).

The LUP4LDN backend comprises the computational modules for the following operations critical for the functions of the tool:

- Mechansims for clipping geo-json files for different administration levels
- Computation of Spectral Indices prospects (NDVI and SMI) at the country level
- Computation of LDN indicators for a defined focus area
- Computation of Land Degradation Impact under different transition scenarios and using custom Transiition Impact Matrices

Furthermore, the backend establishes the integration mechanisms with the different data sources and Geoprocessing platforms used by LUP4LDN, as detailed in the tool's [relevant section](https://lup4ldn.scio.services/#/datasources).

## Technologies

LUP4LDN Backend is developed on: 

[Python 3.7](https://www.python.org/downloads/release/python-370/)

[GDAL](https://gdal.org/)

and deployed through [Flask](https://flask.palletsprojects.com/en/1.1.x/)



