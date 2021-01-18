import yaml
import numpy as np
from functools import reduce
import operator
from astropy import wcs
import astropy.units as u

def OTF(source_ra, source_dec, time_step, start_time, rotation, x_length, y_length, separation, parameter_file_name):
    
    #function to append points, needed for OTF scan
    def _append(x, y, z, x_append, y_append, z_append, rotation):
        a, b = rotate((x_append, y_append), rotation)
        x.append(a)
        y.append(b)
        z.append(z_append)

    #function to rotate points, needed for OTF scan
    def rotate(point, angle):
        """
        Rotate a point counterclockwise by a given angle around a given origin.
        The angle should be given in degrees.
        """
        ox, oy = 0, 0
        px, py = point

        qx = ox + np.cos(np.deg2rad(angle)) * (px - ox) - \
            np.sin(np.deg2rad(angle)) * (py - oy)
        qy = oy + np.sin(np.deg2rad(angle)) * (px - ox) + \
            np.cos(np.deg2rad(angle)) * (py - oy)
        return qx, qy


    #function to unpack tuple, needed for OTF scan
    def unpackTuple(tup):

        return (reduce(operator.add, tup))

    #function for converting pixel coordinates, needed for OTF scan
    def convert_pixel_coordinate_to_equatorial(pixel_coordinates, source_ra, source_dec):
        """
        https://heasarc.gsfc.nasa.gov/docs/fcg/standard_dict.html
        CRVAL: coordinate system value at reference pixel
        CRPIX: coordinate system reference pixel
        CDELT: coordinate increment along axis
        CTYPE: name of the coordinate axis
        """
        step = 1 / 10000000000.

        wcs_properties = wcs.WCS(naxis=2)
        wcs_properties.wcs.crpix = [0, 0]
        wcs_properties.wcs.cdelt = [step, step]
        wcs_properties.wcs.crval = (source_ra, source_dec)
        wcs_properties.wcs.ctype = ["RA---TAN", "DEC--TAN"]
        scaled_pixel_coordinats = np.array(pixel_coordinates) / step
        equatorial_coodinates = wcs_properties.wcs_pix2world(
            scaled_pixel_coordinats, 0)
        return equatorial_coodinates
    
    
    with open(parameter_file_name, 'r') as param_file:
        param_dict = yaml.safe_load(param_file)
    slow_down_time = param_dict['observation']['OTF']['slow_down_time']
    slow_down_step_number = int(slow_down_time / time_step)
    turn_speed_factor = param_dict['observation']['OTF']['turn_speed_factor']
    
    step_y = int(np.ceil((y_length / separation)))
    step_x = int(np.ceil((x_length / separation)))
    start_x = int(step_x / 2 - step_x - 1)
    end_x = int(step_x / 2 + 2)
    start_y = int(step_y / 2 - step_y)
    end_y = int(step_y / 2 + 1)
    pixel_coordinates_x = []
    pixel_coordinates_y = []
    pixel_coordinates_z = []
    reverse = 0
    for j in range(start_y, end_y):
        x = []
        y = []
        z = []

        for i in range(start_x, end_x):
            if i == start_x and j == start_y and j % 2 == 0:
                _append(x, y, z, i - 1, j, 0, rotation)
            else:
                pass
            if i == start_x and j % 2 == 0 and j != start_y:
                #slowdown
                for k in range(slow_down_step_number):
                    _append(x, y, z, i - 1 - 0.9*k + 0.1*k**2, j - 1, 0, rotation)
                for k in range(1,8):
                    _append(x, y, z, i - 3 - 0.5 * np.sin(k*np.pi/8.), j - 0.5 - 0.5*np.cos(k*np.pi/8.), 0, rotation)
                #accelerate
                for k in range(slow_down_step_number):
                    _append(x, y, z, i - 1 - 0.9*(4-k) + 0.1*(4-k)**2, j , 0, rotation)
            if i == start_x or i == end_x - 1:
                #print("i am at {} start_x + 1 = {}, start_x = {}".format(i, start_x + 1, start_x))
                _append(x, y, z, i, j, 0, rotation)
            else:
                _append(x, y, z, i, j, 1, rotation)
            if i == end_x - 1 and j % 2 != 0 and reverse != 0:
                
                #print("I am here")
                _append(x, y, z, i + 1, j, 0, rotation)
                #slowdown
                for k in range(slow_down_step_number):
                    _append(x, y, z, i + 1 + 0.9*k - 0.1*k**2, j, 0, rotation)
                for k in range(1,8):
                    _append(x, y, z, i + 3 + 0.5 * np.sin(k*np.pi/8.), j - 0.5 + 0.5*np.cos(k*np.pi/8.), 0, rotation)
                #accelerate
                for k in range(slow_down_step_number):
                    _append(x, y, z, i + 1 + 0.9*(4-k) - 0.1*(4-k)**2, j -1 , 0, rotation)
        if j % 2 != 0:
            x.reverse()
            y.reverse()
            z.reverse()
            reverse = 0
            pixel_coordinates_x.append(x)
            pixel_coordinates_y.append(y)
            pixel_coordinates_z.append(z)

        else:
            reverse = 1
            pixel_coordinates_x.append(x)
            pixel_coordinates_y.append(y)
            pixel_coordinates_z.append(z)

    x = unpackTuple(pixel_coordinates_x)
    y = unpackTuple(pixel_coordinates_y)
    z = unpackTuple(pixel_coordinates_z)
    x[:] = [x * separation for x in x]
    y[:] = [y * separation for y in y]
    pixel_coordinates = list(zip(x, y))

    data = convert_pixel_coordinate_to_equatorial(
        pixel_coordinates, source_ra, source_dec)

    x_val = [x[0] for x in data]
    y_val = [x[1] for x in data]

    v_time = [start_time + i * u.s * time_step for i in range(0, len(x_val))]

    return [x_val,y_val,v_time]
