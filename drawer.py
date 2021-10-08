import pandas as pd
import numpy as np
import geopandas as gpd
from shapely.geometry import Polygon, MultiPolygon, shape
from shapely import wkt
import folium
import json

import shapely
from shapely.geometry import Polygon, MultiPolygon
import matplotlib.pyplot as plt
gpd.io.file.fiona.drvsupport.supported_drivers['KML'] = 'rw'
# from shapely.ops import unary_union # unire poligons


def add_categorical_legend(folium_map, title, colors, labels):
    if len(colors) != len(labels):
        raise ValueError("colors and labels must have the same length.")

    color_by_label = dict(zip(labels, colors))
    
    legend_categories = ""     
    for label, color in color_by_label.items():
        legend_categories += f"<li><span style='background:{color}'></span>{label}</li>"
        
    legend_html = f"""
    <div id='maplegend' class='maplegend'>
      <div class='legend-title'>{title}</div>
      <div class='legend-scale'>
        <ul class='legend-labels'>
        {legend_categories}
        </ul>
      </div>
    </div>
    """
    script = f"""
        <script type="text/javascript">
        var oneTimeExecution = (function() {{
                    var executed = false;
                    return function() {{
                        if (!executed) {{
                             var checkExist = setInterval(function() {{
                                       if ((document.getElementsByClassName('leaflet-top leaflet-right').length) || (!executed)) {{
                                          document.getElementsByClassName('leaflet-top leaflet-right')[0].style.display = "flex"
                                          document.getElementsByClassName('leaflet-top leaflet-right')[0].style.flexDirection = "column"
                                          document.getElementsByClassName('leaflet-top leaflet-right')[0].innerHTML += `{legend_html}`;
                                          clearInterval(checkExist);
                                          executed = true;
                                       }}
                                    }}, 100);
                        }}
                    }};
                }})();
        oneTimeExecution()
        </script>
      """
   

    css = """

    <style type='text/css'>
      .maplegend {
        z-index:9999;
        float:right;
        background-color: rgba(255, 255, 255, 1);
        border-radius: 5px;
        border: 2px solid #bbb;
        padding: 10px;
        font-size:36px;
        positon: relative;
      }
      .maplegend .legend-title {
        text-align: left;
        margin-bottom: 15px;
        font-weight: bold;
        font-size: 90%;
        }
      .maplegend .legend-scale ul {
        margin: 0;
        margin-bottom: 5px;
        padding: 0;
        float: left;
        list-style: none;
        }
      .maplegend .legend-scale ul li {
        font-size: 70%;
        list-style: none;
        margin-left: 0;
        line-height: 18px;
        margin-bottom: 10px;
        }
      .maplegend ul.legend-labels li span {
        display: block;
        float: left;
        height: 16px;
        width: 30px;
        margin-right: 5px;
        margin-left: 0;
        border: 0px solid #ccc;
        }
      .maplegend .legend-source {
        font-size: 80%;
        color: #777;
        clear: both;
        }
      .maplegend a {
        color: #777;
        }
    </style>
    """

    folium_map.get_root().header.add_child(folium.Element(script + css))

    return folium_map

def GetSen_Poly(product_name: str, SRC_sen: pd.DataFrame)-> Polygon:
     specifications = SRC_sen[SRC_sen['Granule Name'] == product_name]     
     cy, cx = specifications["Center Lat"].values[0], specifications["Center Lon"].values[0]
     p1_y, p1_x = specifications["Near Start Lat"].values[0], specifications["Near Start Lon"].values[0]
     p2_y, p2_x = specifications["Far Start Lat"].values[0], specifications["Far Start Lon"].values[0]
     p3_y, p3_x = specifications["Near End Lat"].values[0], specifications["Near End Lon"].values[0]
     p4_y, p4_x = specifications["Far End Lat"].values[0], specifications["Far End Lon"].values[0]
     poly = Polygon([(p1_x,p1_y),(p2_x,p2_y),(p3_x,p3_y),(p4_x,p4_y)]) # create a polygon
     poly = poly.convex_hull # Get rid of points sequence
     return poly

def GetCSK_Poly(product_name: int, SRC_CSK: pd.DataFrame)-> Polygon:
     specifications = SRC_CSK[SRC_CSK['id'] == product_name]     
     footprint = specifications['footprint'].values[0]
     poly = wkt.loads(footprint) # create a polygon
     poly = poly.convex_hull # Get rid of points sequence
     return poly

def GetSAO_Poly(product_name: int, SRC_SAO: pd.DataFrame)-> Polygon:
  specifications = SRC_SAO[SRC_SAO['Product ID'] == product_name]     
  json_parse = specifications['GeoJSON'].values[0]
  geom = json.loads(json_parse)
  poly = shape(geom)
  poly = poly.convex_hull # Get rid of points sequence
  return poly



def AddPolygon_toMap(P: Polygon, m: folium.map, color:str, Name: str)-> folium.map:
    P_json = gpd.GeoSeries(P).to_json()
    geo_j = folium.GeoJson(data=P_json,
                            style_function=lambda x: {'fillColor': color})
    folium.Popup('Sentinel').add_to(geo_j)
    popup = folium.Popup(Name, show=True)
    popup.add_to(geo_j)

    geo_j.add_to(m)
    return m

def IoU(poly1: Polygon, poly2: Polygon):
     Intersection = poly1.intersection(poly2)
     Union = poly1.union(poly2)
     IoU = Intersection.area/Union.area
     return IoU

def PlotProducts( gdf: gpd.GeoDataFrame, j:int):
  P = gdf.iloc[j]['geometry']
  Names = gdf.iloc[j][['SEN','CSK']]
  M = list(P)
  m = folium.Map(location=[ P.centroid.y, P.centroid.x], zoom_start=6.5, tiles='CartoDB positron') #location: latitude and longitude
  m = add_categorical_legend(m, 'SAR Products',
                              colors = ['blue','red'],
                            labels = ['Sentinel-1', 'COSMO-SkyMed'])
                            
  AddPolygon_toMap(M[0], m, 'blue', Name=Names.SEN)
  AddPolygon_toMap(M[1], m, 'red', Name=str(Names.CSK))
  return m

def PlotProducts2( gdf: gpd.GeoDataFrame, j:int):
  P = gdf.iloc[j]['geometry']
  Names = gdf.iloc[j][['SAO','CSK']]
  M = list(P)
  m = folium.Map(location=[ P.centroid.y, P.centroid.x], zoom_start=6.5, tiles='CartoDB positron') #location: latitude and longitude
  m = add_categorical_legend(m, 'SAR Products',
                              colors = ['blue','red'],
                            labels = ['SAOCOM', 'COSMO-SkyMed'])
                            
  AddPolygon_toMap(M[0], m, 'blue', Name=Names.SAO)
  AddPolygon_toMap(M[1], m, 'red', Name=str(Names.CSK))
  return m

def PlotProducts_AOI( gdf: gpd.GeoDataFrame, j:int, aoi: Polygon)-> folium.Map:
  P = gdf.iloc[j]['geometry']
  Names = gdf.iloc[j][['SEN','CSK']]
  M = list(P)
  m = folium.Map(location=[ P.centroid.y, P.centroid.x], zoom_start=6.5, tiles='CartoDB positron') #location: latitude and longitude
  m = add_categorical_legend(m, 'SAR Products',
                              colors = ['blue','red','lightgreen'],
                            labels = ['Sentinel-1', 'COSMO-SkyMed','AOI'])
                            
  AddPolygon_toMap(M[0], m, 'blue', Name=Names.SEN)
  AddPolygon_toMap(M[1], m, 'red', Name=str(Names.CSK))
  AddPolygon_toMap(aoi, m, 'lightgreen', Name='AOI')
  return m


def PlotProducts2_AOI( gdf: gpd.GeoDataFrame, j:int, aoi: Polygon):
  P = gdf.iloc[j]['geometry']
  Names = gdf.iloc[j][['SAO','CSK']]
  M = list(P)
  m = folium.Map(location=[ P.centroid.y, P.centroid.x], zoom_start=6.5, tiles='CartoDB positron') #location: latitude and longitude
  m = add_categorical_legend(m, 'SAR Products',
                              colors = ['blue','red','lightgreen'],
                            labels = ['SAOCOM', 'COSMO-SkyMed','AOI'])
                            
  AddPolygon_toMap(M[0], m, 'blue', Name=Names.SAO)
  AddPolygon_toMap(M[1], m, 'red', Name=str(Names.CSK))
  AddPolygon_toMap(aoi, m, 'lightgreen', Name='AOI')
  return m



def get_poly_from_kml(path: str)-> Polygon:
     # Filepath to KML file
     fp = path
     polys = gpd.read_file(fp, driver='KML')
     pol = polys.geometry.values[0]
     assert(len(polys)==1)
     return pol



if __name__ == 'main':

     pass