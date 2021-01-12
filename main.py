#purpose: main program for running observations with SKA MPI dish
#takes as "parameter.yaml" as parameter file

#log: created 2021.01.11.

#imported scripts
from edd_server_product_controller import EddServerProductController
from telescope_controller import TelescopeController

#imported packages
import argparse
import yaml

#main function
def main():
    
    #argument parsing
    parser = argparse.ArgumentParser(description='*** main program for running observations with SKA MPI dish ***', formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('-p_f', '--parameter_file_name', help='parameter file name, default = "parameter.yaml"', type=str, default='parameter.yaml')
    parser.add_argument('-p', '--enable_plot', help='plot telescope trajectory, default = False', action="store_true", default=False)
    parser.add_argument('-b', '--enable_backend', help='connect to, start and stop backend during observations, default = False', action="store_true", default=False)
    parser.add_argument('-http', '--enable_http', help='connect to telescope via http, and steer telescope accordingly, default = false', action="store_true", default=False)
    parser.add_argument('-sfn', '--source_file_name', help='name of file with sources in astropy table format', type=str, nargs='+')
    
    args=parser.parse_args()
    
    parameter_file_name = args.parameter_file_name
    
    #read parameter file
    param_file = open(parameter_file_name, 'r')
    param_dict = yaml.safe_load(param_file)
    param_file.close()
    
    #write argparse / parameter file input into variables
    plot_bool = args.enable_plot
    backend_bool = args.enable_backend
    http_bool = args.enable_http
    backend_host=param_dict['connection']['backend_host']
    backend_port=param_dict['connection']['backend_port']
    telescope_host=param_dict['connection']['telescope_host']
    telescope_port=param_dict['connection']['telescope_port']
    
    
    if backend_bool:
        print("Check backend connection")
        # Connect to backend (EDD master Controller)
        backend_controller = EddServerProductController("BACKEND", backend_host, backend_port)
        C = backend_controller.ping()
        if not C:
            print("CANNOT CONNECT TO BACKEND!")
            exit(-1)
    else:
        backend_controller = None
    if http_bool:
        my_telescope_controller = TelescopeController(telescope_host, telescope_port)
        my_telescope_controller.initiate()
    
if __name__ == '__main__':
    main() 
