import os

import numpy as np
import rasterio as rio
import geopandas as gpd
import cartopy.crs as ccrs
import matplotlib.pyplot as plt
from shapely.ops import unary_union
from shapely.geometry.polygon import Polygon
from cartopy.feature import ShapelyFeature
import matplotlib.patches as mpatches


def percentile_stretch(img, pmin=0., pmax=100.):
    '''
    This is where you should write a docstring.
    '''
    # here, we make sure that pmin < pmax, and that they are between 0, 100
    if not 0 <= pmin < pmax <= 100:
        raise ValueError('0 <= pmin < pmax <= 100')
    # here, we make sure that the image is only 2-dimensional
    if not img.ndim == 2:
        raise ValueError('Image can only have two dimensions (row, column)')

    minval = np.percentile(img, pmin)
    maxval = np.percentile(img, pmax)

    stretched = (img - minval) / (maxval - minval)  # stretch the image to 0, 1
    stretched[img < minval] = 0  # set anything less than minval to the new minimum, 0.
    stretched[img > maxval] = 1  # set anything greater than maxval to the new maximum, 1.

    return stretched


def img_display(img, ax, bands, stretch_args=None, **imshow_args):
    '''
    This is where you should write a docstring.
    '''
    dispimg = img.copy().astype(np.float32)  # make a copy of the original image,
    # but be sure to cast it as a floating-point image, rather than an integer

    for b in range(img.shape[0]):  # loop over each band, stretching using percentile_stretch()
        if stretch_args is None:  # if stretch_args is None, use the default values for percentile_stretch
            dispimg[b] = percentile_stretch(img[b])
        else:
            dispimg[b] = percentile_stretch(img[b], *stretch_args)

    # next, we transpose the image to re-order the indices
    dispimg = dispimg.transpose([1, 2, 0])

    # finally, we display the image
    handle = ax.imshow(dispimg[:, :, bands], **imshow_args)

    return handle, ax


# ------------------------------------------------------------------------
# note - rasterio's open() function works in much the same way as python's - once we open a file,
# we have to make sure to close it. One easy way to do this in a script is by using the with statement shown
# below - once we get to the end of this statement, the file is closed.
with rio.open('data_files/NI_Mosaic.tif') as dataset:
    img = dataset.read()
    xmin, ymin, xmax, ymax = dataset.bounds

# your code goes here!
# start by loading the outlines and point data to add to the map
ni_utm = ccrs.UTM(29) # note that this matches with the CRS of our image
fig, ax = plt.subplots(1, 1, figsize=(10, 10), subplot_kw=dict(projection=ni_utm))

# next, create the figure and axis objects to add the map to
ax.imshow(img[3], cmap='gray', vmin=200, vmax=5000, transform=ni_utm, extent=[xmin, xmax, ymin, ymax])
ax.set_extent([xmin, xmax, ymin, ymax], crs=ni_utm) # set the extent to the image boundary



# now, add the satellite image to the map
disp_kwargs = {'extent': [xmin, xmax, ymin, ymax],
               'transform': ni_utm}

stretch = [0.1, 99.9] # a list of percentile values

h, ax = img_display(img, ax, [2, 1, 0], stretch_args=stretch, **disp_kwargs)

fig.savefig('map.png', bbox_inches='tight', dpi=300)

# next, add the county outlines to the map
counties = gpd.read_file(os.path.abspath('data_files/Counties.shp'))
county_names = list(counties.CountyName.unique())
county_names.sort()

for ii, name in enumerate(county_names):
    feat = ShapelyFeature(counties.loc[counties['CountyName'] == name, 'geometry'], # first argument is the geometry
                          ccrs.CRS(counties.crs), # second argument is the CRS
                          edgecolor='red', # outline the feature in black
                          linewidth=1, # set the outline width to be 1 pt
                          alpha=0.2) # set the alpha (transparency) to be 0.4 (out of 1)
    ax.add_feature(feat)
# then, add the town and city points to the map, but separately
#create separate lists for towns and cities
towns = gpd.read_file(os.path.abspath('data_files/Towns.shp'))
cityL = towns.loc[towns['town_city'] == 1]
townL = towns.loc[towns['town_city'] == 0]
town_handle = ax.plot(townL.geometry.x, townL.geometry.y, 's', color='k', ms=6, transform=ccrs.PlateCarree())
city_handle = ax.plot(cityL.geometry.x, cityL.geometry.y, 'o', color='w', ms=6, transform=ccrs.PlateCarree())


# finally, try to add a transparent overlay to the map
# note: one way you could do this is to combine the individual county shapes into a single shape, then
# use a geometric operation, such as a symmetric difference, to create a hole in a rectangle.
# then, you can add the output of the symmetric difference operation to the map as a semi-transparent feature.


# last but not least, add gridlines to the map
gridlines = ax.gridlines(draw_labels=True, # draw  labels for the grid lines
                         xlocs=[-8, -7.5, -7, -6.5, -6, -5.5], # add longitude lines at 0.5 deg intervals
                         ylocs=[54, 54.5, 55, 55.5]) # add latitude lines at 0.5 deg intervals
gridlines.left_labels = False # turn off the left-side labels
gridlines.bottom_labels = False # turn off the bottom labels


# and of course, save the map!

fig.savefig('map2.png', bbox_inches='tight', dpi=300)