#!/usr/bin/env python
# coding: utf-8


import numpy as np
import numpy.ma as ma
import pandas as pd
import geopandas as gpd
import gdal
import os
import pathlib
import fiona
import json
import sys
import flask
from flask import request, jsonify
import subprocess
import logging
import copy
from flask_cors import CORS



log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)
app = flask.Flask(__name__)
CORS(app)
app.config["DEBUG"] = False


@app.route('/', methods=['GET'])
def home():
    return "<h1>Distant Reading Archive</h1><p>This site is a prototype API for distant reading of science fiction novels.</p>"


@app.route('/clipbyregion', methods=['GET'])
def clipbyregion():
    if 'identifier' in request.args:
        identifier = request.args['identifier']
    else:
        return "Error: No identifier field provided. Please specify a identifier."

    if 'geojson' in request.args:
        geojson = request.args['geojson']
        my_json = json.loads(geojson)
        geojson_path = './data/geojson/' + identifier + '.json'
        with open(geojson_path, 'w') as f:
            json.dump(my_json, f)
    else:
        return "Error: No geojson field provided. Please specify a geojson."

    if 'country' in request.args:
        country = request.args['country']
    else:
        return "Error: No country field provided. Please specify a country."

    if country == "TUN":
        ndvi_file = './data/ndvi/TUN_ndvi_modis_250m_MASKED.tif'
        hist_lc_file = './data/landcover/TUN_land_cover_2001_2018.tif'
        soc_file = './data/soil/TUN_soil_orgranic_carbon_MASKED.tif'
        soil_type_file = './data/soil/TUN_soil_type_USDA_MASKED.tif'
        ld_risk = './data/ldrisk/'
    elif country == "BFA":
        ndvi_file = './data/ndvi/BFA_ndvi_modis_250m_MASKED.tif'
        hist_lc_file = './data/landcover/BFA_land_cover_2001_2018.tif'
        soc_file = './data/soil/BFA_soil_orgranic_carbon_MASKED.tif'
        soil_type_file = './data/soil/BFA_soil_type_USDA_MASKED.tif'
        ld_risk = './data/ldrisk/'

    cropped_ndvi_path = './data/cropped/' + identifier + '_ndvi.tif'

    cropped_land_cover_path = './data/cropped/' + identifier + '_landcover.tif'
    cropped_land_cover_path_final = './data/cropped/' + identifier + '_landcover_final.tif'

    cropped_soc_path = './data/cropped/' + identifier + '_soc.tif'
    cropped_soc_path_final = './data/cropped/' + identifier + '_soc_final.tif'

    cropped_soil_type_path = './data/cropped/' + identifier + '_soil_type.tif'
    cropped_soil_type_path_final = './data/cropped/' + identifier + '_soil_type_final.tif'

    cropped_suitability_path = './data/cropped/' + identifier + '_suitability.tif'
    cropped_suitability_path_final = './data/cropped/' + identifier + '_suitability_final.tif'

    cropped_ld_risk_path = './data/cropped/' + identifier + '_ld_risk.tif'
    cropped_ld_risk_path_final = './data/cropped/' + identifier + '_ld_risk_final.tif'

    #NDVI
    os.system(
        "gdalwarp -of GTiff -cutline " + geojson_path + " -crop_to_cutline  -dstnodata -32768.0 " + ndvi_file + " " + cropped_ndvi_path)

    t = gdal.Open(cropped_ndvi_path)
    x_ref = t.RasterXSize
    y_ref = t.RasterYSize

    #LAND COVER
    os.system(
        "gdalwarp -of GTiff -cutline " + geojson_path + " -crop_to_cutline -dstnodata -32768.0 " + hist_lc_file + " " + cropped_land_cover_path)
    #subprocess.run("gdalwarp -of GTiff -cutline " + geojson_path + " -crop_to_cutline -dstnodata -32768.0 " + hist_lc_file + " " + cropped_land_cover_path)

    lc = gdal.Open(cropped_land_cover_path)
    x, y = str(lc.RasterXSize), str(lc.RasterYSize)
    if x != x_ref or y != y_ref:
        bilinear_resize_tif_dimensions_to_ref_tif(cropped_land_cover_path, cropped_land_cover_path_final, x_ref, y_ref)
        os.remove(cropped_land_cover_path)
    else:
        os.system("cp " + cropped_land_cover_path + " " + cropped_land_cover_path_final)
        os.remove(cropped_land_cover_path)

    #SOC
    os.system(
        "gdalwarp -of GTiff -cutline " + geojson_path + " -crop_to_cutline -dstnodata -32768.0 " + soc_file + " " + cropped_soc_path)

    soc = gdal.Open(cropped_soc_path)
    x, y = str(soc.RasterXSize), str(soc.RasterYSize)
    if x != x_ref or y != y_ref:
        bilinear_resize_tif_dimensions_to_ref_tif(cropped_soc_path, cropped_soc_path_final, x_ref, y_ref)
        os.remove(cropped_soc_path)
    else:
        os.system("cp " + cropped_soc_path + " " + cropped_soc_path_final)
        os.remove(cropped_soc_path)

    #SOIL TYPE
    os.system(
        "gdalwarp -of GTiff -cutline " + geojson_path + " -crop_to_cutline  -dstnodata -32768.0 " + soil_type_file + " " + cropped_soil_type_path)

    soil_t = gdal.Open(cropped_soil_type_path)
    x, y = str(soil_t.RasterXSize), str(soil_t.RasterYSize)
    if x != x_ref or y != y_ref:
        bilinear_resize_tif_dimensions_to_ref_tif(cropped_soil_type_path, cropped_soil_type_path_final, x_ref, y_ref)
        os.remove(cropped_soil_type_path)
    else:
        os.system("cp " + cropped_soil_type_path + " " + cropped_soil_type_path_final)
        os.remove(cropped_soil_type_path)

    #SDG

    path_to_precalc_ndvi = "./data/precalculated_data/ndvi/"
    path_to_precalc_lc = "./data/precalculated_data/land_cover/"
    path_to_precalc_soc = "./data/precalculated_data/soc/"
    path_to_precalc_sdg = "./data/precalculated_data/sdg/"

    cropped_sdg_path = './data/cropped/' + identifier + '_sdg.tif'
    cropped_sdg_path_final = './data/cropped/' + identifier + '_sdg.tif'

    hist_sdg_files = os.listdir(path_to_precalc_sdg)
    hist_sdg_files = sorted([x for x in hist_sdg_files if x.endswith("tif")])
    hist_sdg_files = sorted([x for x in hist_sdg_files if x.startswith(country)])
    path_to_cropped_files = "./data/cropped/"

    for file in hist_sdg_files:
        sdg_file = path_to_precalc_sdg + file
        save_sdg_file = (path_to_cropped_files + file).replace(country + "_sdg_15_3_1", identifier + "_cropped_sdg")
        os.system(
            "gdalwarp -of GTiff -cutline " + geojson_path + " -crop_to_cutline  -dstnodata -32768.0 " + sdg_file + " " + cropped_sdg_path)
        sdg_t = gdal.Open(cropped_sdg_path)
        x, y = str(sdg_t.RasterXSize), str(sdg_t.RasterYSize)
        if x != x_ref or y != y_ref:
            bilinear_resize_tif_dimensions_to_ref_tif(cropped_sdg_path, save_sdg_file, x_ref, y_ref)
            os.remove(cropped_sdg_path)
        else:
            os.system("cp " + cropped_sdg_path + " " + save_sdg_file)
            os.remove(cropped_sdg_path)


    #SUITABILITY

    path_to_precalc_suitability = "./data/precalculated_data/suitability/"

    suitability_files = os.listdir(path_to_precalc_suitability)
    suitability_files = sorted([x for x in suitability_files if x.endswith("suitability.tif")])
    suitability_files = sorted([x for x in suitability_files if x.startswith(country)])

    suitability_file = path_to_precalc_suitability + suitability_files[0]

    os.system(
        "gdalwarp -of GTiff -cutline " + geojson_path + " -crop_to_cutline -dstnodata -32768.0 " + suitability_file + " " + cropped_suitability_path)

    suit = gdal.Open(cropped_suitability_path)
    x, y = str(suit.RasterXSize), str(suit.RasterYSize)
    if x != x_ref or y != y_ref:
        bilinear_resize_tif_dimensions_to_ref_tif(cropped_suitability_path, cropped_suitability_path_final, x_ref, y_ref)
    else:
        os.system("cp " + cropped_suitability_path + " " + cropped_suitability_path_final)
    os.remove(cropped_suitability_path)

    #LD RISK

    risk_files = os.listdir(ld_risk)
    risk_files = sorted([x for x in risk_files if x.endswith("risk.tif")])
    risk_files = sorted([x for x in risk_files if x.startswith(country)])

    temp_file = cropped_ld_risk_path

    risk_file = ld_risk + risk_files[0]

    os.system(
        "gdalwarp -of GTiff -cutline " + geojson_path + " -crop_to_cutline -dstnodata -32768.0 " + risk_file + " " + cropped_ld_risk_path)

    suit = gdal.Open(cropped_ld_risk_path)
    x, y = str(suit.RasterXSize), str(suit.RasterYSize)
    if x != x_ref or y != y_ref:
        bilinear_resize_tif_dimensions_to_ref_tif(cropped_ld_risk_path, cropped_ld_risk_path_final, x_ref, y_ref)
    else:
        os.system("cp " + cropped_ld_risk_path + " " + cropped_ld_risk_path_final)
    os.remove(cropped_ld_risk_path)


    return jsonify(
        result="complete"
    )

@app.route('/gethistoricalstatistics', methods=['GET'])
def gethistoricalstatistics():

    if 'identifier' in request.args:
        identifier = request.args['identifier']
    else:
        return "Error: No identifier field provided. Please specify a identifier."

    if 'country' in request.args:
        country = request.args['country']
        if country == "TUN":
            country_name = "Tunisia"
        elif country == "BFA":
            country_name = "Burkina Faso"
    else:
        return "Error: No country field provided. Please specify a country."


    year = list(range(2001, 2019))

    lc_data = {
        "absolute_value": None,
        "percentage_value": None,
        "year": None,
        "unit": "hectares"
    }

    ndvi_data = {
        "value": None,
        "year": None,
    }

    sdg_data = {
        "period": {
            "start_year": None,
            "end_year": None
        },
        "Degradation": {
            "absolute_value": None,
            "percentage_value": None
        },
        "Stable": {
            "absolute_value": None,
            "percentage_value": None
        },
        "Improvement": {
            "absolute_value": None,
            "percentage_value": None
        }
    }

    cropped_ndvi_path = './data/cropped/' + identifier + '_ndvi.tif'
    cropped_land_cover_path_final = './data/cropped/' + identifier + '_landcover_final.tif'
    cropped_soc_path_final = './data/cropped/' + identifier + '_soc_final.tif'


    # NDVI Calculations

    country_ndvi = gdal.Open(cropped_ndvi_path).ReadAsArray()[:-1, :, :].astype(np.int16)
    country_ndvi = np.where(country_ndvi == 0, -32768, country_ndvi)
    country_ndvi = ma.array(country_ndvi, mask=country_ndvi == -32768, fill_value=-32768)
    annual_mean = np.mean(country_ndvi, axis=(1, 2)).astype(np.int16)

    ndvi_data_list = []
    for idx, value in enumerate(annual_mean):
        ndvi_data["value"] = str(value)
        ndvi_data["year"] = str(year[idx])
        ndvi_data_list.append(copy.copy(ndvi_data))

    # Land Cover Calculations
    lc_2001_2018 = gdal.Open(cropped_land_cover_path_final).ReadAsArray().astype(np.int16)
    lc_2001_2018 = ma.array(lc_2001_2018, mask=lc_2001_2018 == -32768, fill_value=-32768)

    lc_perc = {
        1: [],
        2: [],
        3: [],
        4: [],
        5: [],
        6: [],
        7: []
    }
    lc_hect = {
        1: [],
        2: [],
        3: [],
        4: [],
        5: [],
        6: [],
        7: []
    }

    for i in range(len(lc_2001_2018)):
        uni, counts = np.unique(lc_2001_2018[i], return_counts=True)
        total_area = sum(counts[:-1])
        yearly_percentages = [100 * x / total_area for x in counts[:-1]]
        yearly_hectares = [6.25 * x for x in counts[:-1]]

        for idx, j in enumerate(uni[:-1]):
            lc_perc[j].append(yearly_percentages[idx])
            lc_hect[j].append(yearly_hectares[idx])

    lc_data_list = []
    for key in lc_perc:
        class_list = []
        for idx, perc in enumerate(lc_perc[key]):
            lc_data = {}
            lc_data["absolute_value"] = lc_hect[key][idx]
            lc_data["percentage_value"] = perc
            lc_data["year"] = year[idx]
            lc_data["unit"] = "hectares"
            class_list.append(copy.copy(lc_data))
        lc_data_list.append(class_list)

    # SOC Calculations

    country_soc = gdal.Open(cropped_soc_path_final).ReadAsArray().astype(np.int16)
    country_soc = ma.array(country_soc, mask=country_soc < 0)
    soc_min = ma.amin(country_soc).astype(np.int16)
    soc_mean = ma.mean(country_soc).astype(np.int16)
    soc_max = ma.amax(country_soc).astype(np.int16)
    country_soc = country_soc.astype(np.float16)
    soc_1st_quartile = int(np.nanpercentile(country_soc.filled(np.nan), 25))
    soc_3rd_quartile = int(np.nanpercentile(country_soc.filled(np.nan), 75))

    # SDG Calculations

    path_to_sdg = "./data/cropped/"
    files = os.listdir(path_to_sdg)
    print(files)
    files = [x for x in files if x.endswith(".tif")]

    files = sorted([x for x in files if x.startswith(identifier+"_cropped_sdg")])
    sdg_perc = []
    sdg_hect = []
    year_periods = ["2001-2009", "2009-2018"]
    for file in files:
        sdg = gdal.Open(path_to_sdg + file).ReadAsArray()
        sdg = ma.array(sdg, mask=sdg == -32768, fill_value=-32768)
        unique, counts = np.unique(sdg, return_counts=True)
        total_area = sum(counts[:-1])
        yearly_percentages = [100 * x / total_area for x in counts[:-1]]
        yearly_hectares = [6.25 * x for x in counts[:-1]]
        sdg_perc.append(yearly_percentages)
        sdg_hect.append(yearly_hectares)

    sdg_data_list = []
    print(sdg_perc)
    print(sdg_hect)
    for i, period in enumerate(year_periods):
        sdg_data["period"]["start_year"] = period.split("-")[0]
        sdg_data["period"]["end_year"] = period.split("-")[1]
        sdg_data["Degradation"]["absolute_value"] = sdg_hect[i][0]
        sdg_data["Degradation"]["percentage_value"] = sdg_perc[i][0]
        sdg_data["Stable"]["absolute_value"] = sdg_hect[i][1]
        sdg_data["Stable"]["percentage_value"] = sdg_perc[i][1]
        sdg_data["Improvement"]["absolute_value"] = sdg_hect[i][2]
        sdg_data["Improvement"]["percentage_value"] = sdg_perc[i][2]
        sdg_data_list.append(copy.deepcopy(sdg_data))

    my_json = {
        "country": country_name,
        "subindicators": [
            {
                "subindicator": "land_cover",
                "classes": [
                    {
                        "class": "Tree covered",
                        "data": lc_data_list[0]
                    },
                    {
                        "class": "Grassland",
                        "data": lc_data_list[1]
                    },
                    {
                        "class": "Cropland",
                        "data": lc_data_list[2]
                    },
                    {
                        "class": "Wetland",
                        "data": lc_data_list[3]
                    },
                    {
                        "class": "Artificial",
                        "data": lc_data_list[4]
                    },
                    {
                        "class": "Bare land",
                        "data": lc_data_list[5]
                    },
                    {
                        "class": "Water body",
                        "data": lc_data_list[6]
                    }
                ]
            },
            {
                "subindicator": "ndvi",
                "data": ndvi_data_list
            },
            {
                "subindicator": "soc",
                "max": str(soc_max),
                "min": str(soc_min),
                "mean": str(soc_mean),
                "min_quantile": str(soc_1st_quartile),
                "max_quantile": str(soc_3rd_quartile)

            }
        ],
        "sustainable_development_goals": {
            "goal": "15.3.1",
            "data": sdg_data_list
        }
    }

    return jsonify(
        my_json
    )

@app.route('/getregionlandtypes', methods=['GET'])
def getregionlandtypes():

    if 'identifier' in request.args:
        identifier = request.args['identifier']
    else:
        return "Error: No identifier field provided. Please specify a identifier."

    if 'country' in request.args:
        country = request.args['country']
    else:
        return "Error: No country field provided. Please specify a country."

    input_tif = './data/cropped/' + identifier + '_landcover_final.tif'
    suit_tif = './data/cropped/' + identifier + '_suitability_final.tif'
    ld_tif = './data/cropped/' + identifier + '_ld_risk_final.tif'
    most_recent_year_only = "True"

    my_lc = gdal.Open(input_tif)
    data = my_lc.ReadAsArray()
    years = range(2001, 2019)
    save_name = "_lc_hist_yearly.json"

    if most_recent_year_only == "True":
        data = np.expand_dims(data[-1, :, :], axis=0)
        years = [2020]
        save_name = "_lc_most_recent_year.json"

    data = ma.array(data, mask=data == -32768)

    labels_to_classes = {
        1: "Tree-covered",
        2: "Grassland",
        3: "Cropland",
        4: "Wetland",
        5: "Artificial",
        6: "Bare land",
        7: "Water body"
    }

    lc_data_json = {
        "absolute_value": None,
        "percentage_value": None,
        "unit": "hectares"
    }

    lc_class_json = {
        "class": None,
        "data": None
    }

    lc_year_json = {
        "year": None,
        "classes": None
    }

    suit_labels_to_classes = {
        0: "neutral",
        1: "no suitable",
        2: "partially suitable",
        3: "suitable"
    }

    suitability_data_json = {
        "absolute_value": None,
        "percentage_value": None,
        "unit": "hectares"
    }

    suitability_class_json = {
        "class": None,
        "data": None
    }

    lc_class_json = {
        "land_cover_class": None,
        "classes": None
    }

    lc_year_list = []
    for idx, band in enumerate(data):
        unique, counts = np.unique(band, return_counts=True)
        total_area = sum(counts[:-1])
        lc_hectares = dict(zip(unique[:-1], 6.25 * counts[:-1]))
        lc_percentages = dict(zip(unique[:-1], 100 * counts[:-1] / total_area))

        lc_class_list = []
        for label, lc_data in lc_hectares.items():
            lc_data_json["absolute_value"] = lc_data
            lc_data_json["percentage_value"] = lc_percentages[label]
            lc_class_json["class"] = labels_to_classes[label]
            lc_class_json["data"] = lc_data_json
            lc_class_list.append(copy.deepcopy(lc_class_json))
        #     print(lc_class_list)
        lc_year_json["year"] = years[idx]
        lc_year_json["classes"] = lc_class_list
        lc_year_list.append(copy.deepcopy(lc_year_json))

    lc_array = gdal.Open(input_tif).ReadAsArray()[-1, :, :]
    lc_array = ma.array(lc_array, mask=lc_array == -32768, fill_value=-32768)

    suit_array = gdal.Open(suit_tif).ReadAsArray()
    suit_array = ma.array(suit_array, mask=suit_array == -32768, fill_value=-32768)

    combined_array = 10 * lc_array + suit_array

    lc_classes_list = []
    for i in range(1, 8):
        lc_class_pixel_coordinates = np.where(lc_array == i)
        all_suitability_values_for_specific_lc_class = combined_array[lc_class_pixel_coordinates].filled()
        unique, counts = np.unique(all_suitability_values_for_specific_lc_class, return_counts=True)
        try:
            if unique[0] == -32768:
                unique = np.delete(unique, 0)
                counts = np.delete(counts, 0)
        except:
            pass
        total_area = sum(counts)
        suitability_hectares = dict(zip(unique, 6.25 * counts))
        suitability_percentages = dict(zip(unique, 100 * counts / total_area))

        for j in range(0, 4):
            suit_possible_class = 10 * i + j
            if suit_possible_class not in suitability_hectares:
                suitability_hectares[suit_possible_class] = 0
                suitability_percentages[suit_possible_class] = 0

        suitability_class_list = []
        for label, suitability_data in suitability_hectares.items():
            suitability_data_json["absolute_value"] = suitability_data
            suitability_data_json["percentage_value"] = suitability_percentages[label]
            suitability_class_json["class"] = suit_labels_to_classes[label % 10]
            suitability_class_json["data"] = suitability_data_json
            suitability_class_list.append(copy.deepcopy(suitability_class_json))
        lc_class_json["land_cover_class"] = labels_to_classes[i]
        lc_class_json["classes"] = suitability_class_list
        lc_classes_list.append(copy.deepcopy(lc_class_json))

    ld_risk_array = gdal.Open(ld_tif).ReadAsArray()
    initial_gauge_hectares = 6.25 * len(ma.where(ld_risk_array > 0)[0])

    my_json = {
        "country": country,
        "data": lc_year_list,
        "dataSuitability": lc_classes_list,
        "initialHectares": initial_gauge_hectares
    }

    return my_json

@app.route('/calculateScenario', methods=['GET'])
def calculateScenario():
    if 'identifier' in request.args:
        identifier = request.args['identifier']
    else:
        return "Error: No identifier field provided. Please specify a identifier."

    if 'scenario' in request.args:
        scenario = request.args['scenario']
        my_json = json.loads(scenario)
        scenario = './data/scenario/' + identifier + '.json'
        with open(scenario, 'w') as f:
            json.dump(my_json, f)
    else:
        return "Error: No geojson field provided. Please specify a geojson."

    with open(scenario) as json_file:
        data = json.load(json_file)

    lc_changes_scenario = data["scenario"]
    impact_matrix = data["impactMatrix"]

    land_ids = ['treecovered', 'grassland', 'cropland', 'wetland', 'artificialarea', 'bareland', 'waterbody']
    lc_changes_row_format = {
        "treecovered": 0,
        "grassland": 0,
        "cropland": 0,
        "wetland": 0,
        "artificialarea": 0,
        "bareland": 0,
        "waterbody": 0
    }

    initial_lc_hectares_per_class = []
    final_lc_hectares_per_class = []
    lc_changes_array = []
    for source_lc_class in lc_changes_scenario:
        # save initial total hectares per class to a list
        initial_lc_hectares_per_class.append(source_lc_class["landCoverage"]["value"])
        # save final total hectares per class to a list
        final_lc_hectares_per_class.append(source_lc_class["endLandCoverage"]["value"])

        lc_changes_row = copy.copy(lc_changes_row_format)
        for lc_changes_data in source_lc_class["breakDown"]:
            lc_changes_row[lc_changes_data["landId"]] = lc_changes_data["landCoverage"]["value"]

        lc_changes_array.append(list(lc_changes_row.values()))

    lc_changes_array = np.asarray(lc_changes_array)

    impact_array = []
    for item in impact_matrix:
        impact_array.append(item["values"])

    impact_array = np.asarray(impact_array)

    final_array = lc_changes_array * impact_array

    # In[67]:

    per_class_sum = list(np.sum(final_array, axis=1))
    per_class_sum = [int(x) for x in per_class_sum]
    total_sum = int(np.sum(final_array))
    my_json = {
        "impacts": None,
        "total_impact_sum": total_sum,
        "total_final_lc": sum(final_lc_hectares_per_class),
        "final_lc_per_class": None
    }

    lc_per_class = {
        "landId": None,
        "landCoverage": {
            "value": None,
            "unit": "ha"
        }
    }

    impacts_per_class = {
        "landId": None,
        "impact": {
            "value": None,
            "unit": "ha"
        }
    }

    impacts_list = []
    lc_list = []
    for idx, lc_class in enumerate(land_ids):
        impacts_per_class["landId"] = lc_class
        impacts_per_class["impact"] = per_class_sum[idx]

        impacts_list.append(copy.deepcopy(impacts_per_class))

        lc_per_class["landId"] = lc_class
        lc_per_class["landCoverage"] = final_lc_hectares_per_class[idx]

        lc_list.append(copy.deepcopy(lc_per_class))

    my_json["impacts"] = impacts_list
    my_json["final_lc_per_class"] = lc_list

    return my_json
    '''

    land_ids = ['treecovered', 'grassland', 'cropland', 'wetland', 'artificialarea', 'bareland', 'waterbody']
    lc_changes_row_format = {
        "treecovered": 0,
        "grassland": 0,
        "cropland": 0,
        "wetland": 0,
        "artificialarea": 0,
        "bareland": 0,
        "waterbody": 0
    }

    

    impact_array = []
    for item in impact_matrix:
        impact_array.append(item["values"])

    impact_array = np.asarray(impact_array)

    # In[60]:

    final_array = lc_changes_array * impact_array

    # In[67]:

    per_class_sum = np.sum(final_array, axis=1)
    total_sum = np.sum(final_array)

    my_json = {
        "impacts": None,
        "total_impact_sum": total_sum,
        "total_final_lc": sum(final_lc_hectares_per_class),
        "final_lc_per_class": None
    }

    lc_per_class = {
        "landId": None,
        "landCoverage": {
            "value": None,
            "unit": "ha"
        }
    }

    impacts_per_class = {
        "landId": None,
        "impact": {
            "value": None,
            "unit": "ha"
        }
    }

    impacts_list = []
    lc_list = []
    for idx, lc_class in enumerate(land_ids):
        impacts_per_class["landId"] = lc_class
        impacts_per_class["impact"] = per_class_sum[idx]

        impacts_list.append(copy.deepcopy(impacts_per_class))

        lc_per_class["landId"] = lc_class
        lc_per_class["landCoverage"] = final_lc_hectares_per_class[idx]

        lc_list.append(copy.deepcopy(lc_per_class))

    my_json["impacts"] = impacts_list
    my_json["final_lc_per_class"] = lc_list
'''

@app.route('/calculateSOCScenario', methods=['GET'])
def calculateSOCScenario():
    if 'identifier' in request.args:
        identifier = request.args['identifier']
    else:
        return "Error: No identifier field provided. Please specify a identifier."

    if 'socscenario' in request.args:
        scenario = request.args['socscenario']
        my_json = json.loads(scenario)
        scenario = './data/scenario/' + identifier + '_soc_.json'
        with open(scenario, 'w') as f:
            json.dump(my_json, f)
    else:
        return "Error: No geojson field provided. Please specify a geojson."

    with open(scenario) as json_file:
        data = json.load(json_file)

    lc_changes_scenario = data["scenarios"]
    impact_matrix = data["impactMatrix"]
    soc_matrix = data["comatrix"]

    # In[30]:

    land_ids = ['treecovered', 'grassland', 'cropland', 'wetland', 'artificialarea', 'bareland', 'waterbody']
    lc_changes_row_format = {
        "treecovered": 0,
        "grassland": 0,
        "cropland": 0,
        "wetland": 0,
        "artificialarea": 0,
        "bareland": 0,
        "waterbody": 0
    }

    scenario_json = {
        "impacts": None,
        "total_impact_sum": None,
        "total_final_lc": None,
        "final_lc_per_class": None,
        "scenarioStart": None,
        "scenarioEnd": None
    }

    lc_per_class = {
        "landId": None,
        "landCoverage": {
            "value": None,
            "unit": "ha"
        }
    }

    impacts_per_class = {
        "landId": None,
        "impact": {
            "value": None,
            "unit": "ha"
        }
    }

    my_json = {
        "scenarios": None
    }

    # In[42]:

    impact_array = []
    for item in impact_matrix:
        impact_array.append(item["values"])

    impact_array = np.asarray(impact_array)
    adjusted_impact_array = np.where(impact_array < 0, 0, 1)

    # In[33]:

    soc_array = []
    for item in soc_matrix:
        soc_array.append(item["values"])

    soc_array = np.asarray(soc_array)

    scenarios_impact_list = []
    duration_scernario = data["totalYears"]
    adjusted_soc_array = duration_scernario * (soc_array - 1) / 20 + 1
    adjusted_soc_array = np.where(adjusted_soc_array < 0.9, -2, 0)

    combined_array = adjusted_impact_array * adjusted_soc_array
    mask_array = np.sign(combined_array + impact_array)

    for scenario in lc_changes_scenario:

        initial_lc_hectares_per_class = []
        final_lc_hectares_per_class = []
        lc_changes_array = []
        for source_lc_class in scenario["landTypes"]:
            # save initial total hectares per class to a list
            initial_lc_hectares_per_class.append(source_lc_class["landCoverage"]["value"])
            # save final total hectares per class to a list
            final_lc_hectares_per_class.append(source_lc_class["endLandCoverage"]["value"])

            lc_changes_row = copy.copy(lc_changes_row_format)
            for lc_changes_data in source_lc_class["breakDown"]:
                lc_changes_row[lc_changes_data["landId"]] = lc_changes_data["landCoverage"]["value"]

            lc_changes_array.append(list(lc_changes_row.values()))

        lc_changes_array = np.asarray(lc_changes_array)

        final_array = lc_changes_array * mask_array
        per_class_sum = list(np.sum(final_array, axis=1))
        per_class_sum = [int(x) for x in per_class_sum]
        total_sum = int(np.sum(final_array))

        impacts_list = []
        lc_list = []
        for idx, lc_class in enumerate(land_ids):
            impacts_per_class["landId"] = lc_class
            impacts_per_class["impact"] = per_class_sum[idx]

            impacts_list.append(copy.deepcopy(impacts_per_class))

            lc_per_class["landId"] = lc_class
            lc_per_class["landCoverage"] = final_lc_hectares_per_class[idx]

            lc_list.append(copy.deepcopy(lc_per_class))

        scenario_json["impacts"] = impacts_list
        scenario_json["final_lc_per_class"] = lc_list
        scenario_json["total_impact_sum"] = total_sum
        scenario_json["total_final_lc"] = sum(final_lc_hectares_per_class)
        scenario_json["scenarioStart"] = scenario["scenarioStart"]
        scenario_json["scenarioEnd"] = scenario["scenarioEnd"]

        scenarios_impact_list.append(copy.deepcopy(scenario_json))

    my_json["scenarios"] = scenarios_impact_list

    return my_json



def bilinear_resize_tif_dimensions_to_ref_tif(input_tif, output_tif_path, ref_height, ref_width):
    exit_code = os.system(
        "gdalwarp -ts " + str(ref_height) + " " + str(ref_width) + " -r near " + input_tif + " " + output_tif_path)
    return exit_code

app.run(host='0.0.0.0',ssl_context=('cert.pem', 'key.pem'))
