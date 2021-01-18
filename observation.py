import yaml
import track
import plot
import transform
from telescope_controller import TelescopeController
from edd_server_product_controller import EddServerProductController

       
def observe(source_name, flux, ra, dec, min_flux, min_el, time_step, start_time, rotation, x_length, y_length, separation, parameter_file_name, http_bool, my_telescope_controller, my_backend_controller, backend_bool):
    
    print("observing source \"" + source_name + "\", flux = " + str(flux) +" Jy, ra = " + str(ra) +" deg, dec = " + str(dec) + " deg")
    
    if flux < min_flux:
        print("flux below min_flux, observation skipped")
        return
    
    print('calculating schedule')
    ra_dec_list = track.OTF(ra, dec, time_step, start_time, rotation, x_length, y_length, separation, parameter_file_name)
    #plot.plot(ra_dec_list)
    alt_az_list = transform.transform(ra_dec_list, parameter_file_name)
    
    if min(alt_az_list[1]) < min_el:
        print("at least part of scan is below minimal elevation, observation is skipped")
        return
    
    start_az = alt_az_list[0][0]
    start_alt = alt_az_list[1][0]
    
    if http_bool:
        my_telescope_controller.start_data_logging()
        
        print("moving to start position")
        my_telescope_controller.move_pos(start_az, start_alt, "absolute")
        my_telescope_controller.wait_for_pos_reached()
        
        print('recalculating schedule')
        ra_dec_list = track.OTF(ra, dec, time_step, start_time, rotation, x_length, y_length, separation, parameter_file_name)
        stop_time = ra_dec_list[2][-1]
        alt_az_list = transform.transform(ra_dec_list, parameter_file_name)
        table = alt_az_list[3]
        
        if min(alt_az_list[1]) < min_el:
            print("at least part of scan is below minimal elevation, observation is skipped")
            return
        if backend_bool:
            print("Preparing measuremnt")
            my_backend_controller.measurement_prepare({"new_file":"True"})

            #start backend
            print("Starting measuremnt")
            my_backend_controller.measurement_start()
        my_telescope_controller.run_table(table, stop_time)
        if backend_bool:
            #stop backend
            print("Stopping measuremnt")
            my_backend_controller.measurement_stop()
        my_telescope_controller.stop_data_logging()
        my_telescope_controller.export(source_name, flux, ra, dec)
    
    #track.OTF(ra, dec, time_step, start_time, prototype_dish, rotation, x_length, y_length, seperation, plot)'''
    
    
