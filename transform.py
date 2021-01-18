from astropy.coordinates import SkyCoord, EarthLocation, AltAz
from astroplan import Observer
import yaml
import astropy.units as u
import sys

def transform(ra_dec_list, parameter_file_name):
    
    with open(parameter_file_name, 'r') as param_file:
        param_dict = yaml.safe_load(param_file)
    prototype_dish = EarthLocation(lat = param_dict['telescope']['antenna_position']['latitude'] * u.deg, lon = param_dict['telescope']['antenna_position']['longitude'] * u.deg, height = param_dict['telescope']['antenna_position']['height'] * u.m)
    
    ra_list = ra_dec_list[0]
    dec_list = ra_dec_list[1]
    v_time = ra_dec_list[2]
    
    sc = SkyCoord(ra_list, dec_list, unit='deg', frame="icrs")
    prototype_dish_observer = Observer(location=prototype_dish)
    grid_altaz = sc.transform_to(AltAz(obstime=v_time, location=prototype_dish))
    
    az_list = [grid_altaz[i].az.value for i in range(len(grid_altaz))]
    alt_list = [grid_altaz[i].alt.value for i in range(len(grid_altaz))]
    parallactic_angle_list = prototype_dish_observer.parallactic_angle(time = v_time, target = sc).deg
    
    table = ""
    for i in range(len(az_list)):
        table_line="{0} {1:3.8f} {2:3.8f} {3} {4}".format(v_time[i].mjd, az_list[i], alt_list[i], 1, parallactic_angle_list[i], file = sys.stdout, flush = True)
        table+=table_line+"\n"
    
    return[az_list, alt_list, v_time, table]
