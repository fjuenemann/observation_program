#purpose: main program for running observations with SKA MPI dish
#takes as "parameter.yaml" as parameter file

#log: created 2021.01.11.

#imported scripts
from edd_server_product_controller import EddServerProductController
from telescope_controller import TelescopeController
import observation

#imported packages
import argparse
import yaml
from astropy.table import Table
import numpy as np
from astropy.time import Time
import astropy.units as u

#main function
def main():
    
    #argument parsing
    parser = argparse.ArgumentParser(description='*** main program for running observations with SKA MPI dish ***', formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('-p_f', '--parameter_file_name', help='parameter file name, default = "parameter.yaml"', type=str, default='parameter.yaml')
    parser.add_argument('-p', '--enable_plot', help='plot telescope trajectory, default = False', action="store_true")
    parser.add_argument('-b', '--enable_backend', help='connect to, start and stop backend during observations, default = False', action="store_true")
    parser.add_argument('-http', '--enable_http', help='connect to telescope via http, and steer telescope accordingly, default = False', action="store_true")
    parser.add_argument('-sfn', '--source_file_name', help='name of file with sources in astropy table format', type=str)
    parser.add_argument('-band', '--band', help='Band for observation', type=str)
    parser.add_argument('-s', '--sort', help='sort sources by RA, default = False', action="store_true")
    parser.add_argument('-s_m', '--scan_mode', help='scanning mode used; options: "simple_track", "cross_scan" or "OTF"', type=str)
    parser.add_argument('-t_s', '--time_step', help = 'time step between points', type=float)
    parser.add_argument('-d', '--duration', help = 'Duration of simple_track or cross_scan', type=float)
    parser.add_argument('-x_l', '--x_length', help = 'length of OTF scan in x-direction', type=float)
    parser.add_argument('-y_l', '--y_length', help = 'length of OTF scan in y-direction', type=float)
    parser.add_argument('-se', '--separation', help = 'separation of points in OTF scan', type=float)
    parser.add_argument('-m_f', '--min_flux', help = 'flux minimum to observe source', type=float)
    parser.add_argument('-sta_t', '--start_time', help = 'start time of observations', type=str)
    parser.add_argument('-r', '--rotation', help = 'rotation of scan', type=float)
    parser.add_argument('-m_e', '--min_el', help = 'minimal elevation', type=float)
    parser.add_argument('-i', '--initiate', help = 'execute intiating http commands, default=True', action = 'store_false')
    parser.add_argument('-st', '--stow', help = 'stowing telescope when finished, default=False', action = 'store_true')
    parser.add_argument('-t_d', '--total_duration', help = 'latest time to start observation, from start_time in hours', type = float)
    
    args=parser.parse_args()
    
    parameter_file_name = args.parameter_file_name
    
    #read parameter file
    with open(parameter_file_name, 'r') as param_file:
        param_dict = yaml.safe_load(param_file)
    
    #write argparse / parameter file input into variables
    plot_bool = args.enable_plot
    backend_bool = args.enable_backend
    http_bool = args.enable_http
    band = args.band
    source_file_name = args.source_file_name
    sort = args.sort
    initiate_bool = args.initiate
    time_step = args.time_step
    if time_step == None:
        time_step = param_dict['observation']['time_step']
    scan_mode = args.scan_mode
    if scan_mode == None:
        scan_mode = param_dict['observation']['scan_mode']
    duration = args.duration
    if duration == None:
        duration = param_dict['observation']['duration']
    x_length = args.x_length    
    if x_length == None:
        x_length = param_dict['observation']['OTF']['x_length']
    y_length = args.y_length       
    if y_length == None:
        y_length = param_dict['observation']['OTF']['y_length']
    separation = args.separation    
    if separation == None:
        separation = param_dict['observation']['OTF']['separation']
    rotation = args.rotation    
    if rotation == None:
        rotation = param_dict['observation']['rotation']    
    min_flux = args.min_flux    
    if min_flux == None:
        min_flux = param_dict['observation']['min_flux']
    min_el = args.min_el    
    if min_el == None:
        min_el = param_dict['observation']['min_elevation']    
    if args.start_time == None:
        if param_dict['observation']['start_time']=="Time.now()":
            start_time = Time.now()
        else:    
            start_time == Time(param_dict['observation']['start_time'])
    else:
        start_time = Time(args.start_time) 
    if source_file_name == None:
        print('please enter source file name')
        exit(-1)
    if band == None:
        band = param_dict['observation']['band']
    backend_host = param_dict['connection']['backend_host']
    backend_port = param_dict['connection']['backend_port']
    telescope_host = param_dict['connection']['telescope_host']
    telescope_port = param_dict['connection']['telescope_port']
    stow_position = param_dict['telescope']['stow_position']
    stow_bool = args.stow
    if args.total_duration == None:
        stop_time = start_time + 1 * u.a
    else:
        stop_time = start_time + args.total_duration * u.h  
    
    if backend_bool:
        print('Check backend connection')
        # Connect to backend (EDD master Controller)
        my_backend_controller = EddServerProductController('BACKEND', backend_host, backend_port)
        C = my_backend_controller.ping()
        if not C:
            print('CANNOT CONNECT TO BACKEND!')
            exit(-1)
    else:
        my_backend_controller = None
    if http_bool:
        my_telescope_controller = TelescopeController(telescope_host, telescope_port, parameter_file_name, band)
        if initiate_bool:
            my_telescope_controller.initiate()
    else:
        my_telescope_controller = None    
    
    #read in sources
    sources_table = Table.read(source_file_name, format='ascii')
    if sort:
        sources_table.sort('ra[deg]')
        
    for i in range(len(sources_table)):
        if Time.now()>stop_time:
            break
        observation.observe(sources_table['sname_id'][i], sources_table['peak_flux'][i], sources_table['ra[deg]'][i], sources_table['dec[deg]'][i], min_flux, min_el, time_step, start_time, rotation, x_length, y_length, separation, parameter_file_name, http_bool, my_telescope_controller, my_backend_controller, backend_bool)
    
    if stow_bool:
        print("stowing_telescope...")
        my_telescope_controller.stow(stow_position)
    
if __name__ == '__main__':
    main() 
