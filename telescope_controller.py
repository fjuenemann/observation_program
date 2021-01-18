import http.client
import time
import yaml
import json
from astropy.time import Time
import sys
import sender

class TelescopeController(object):
    
    def __init__(self, address, port, parameter_file_name, band):
        
        self.ip = address
        self.port = port
        self.band = band
        with open(parameter_file_name, 'r') as param_file:
            param_dict = yaml.safe_load(param_file)
        self.v_max_az = param_dict['telescope']['v_max_az']  
        self.v_max_alt = param_dict['telescope']['v_max_alt'] 
        self.backend_host = param_dict['connection']['backend_host']
        self.sender_port = param_dict['connection']['sender_port']
        self.on_source_threshold = param_dict['data_logging']['on_source_threshold']
        self.on_source_rms = param_dict['data_logging']['on_source_rms']
        self.data_log_config_name = param_dict['data_logging']['data_log_config_name']
        self.data_log_config_file_name = param_dict['data_logging']['data_log_config_file_name']

    def connection(self):
        return http.client.HTTPConnection(self.ip, self.port)
    
    def get_response(self,conn):
        response = conn.getresponse()
        print(response.status, response.reason)
        time.sleep(1.)
        return response.read()
    
    def stow(self,stow_position):
        conn = self.connection()
        stow_Command = "{\"path\":\"acu.dish_management_controller.stow\",\"params\":{\"action\":\"" + stow_position + "\"}}" 
        conn.request("PUT", "/devices/command", stow_Command)
        self.get_response(conn)
    
    def initiate(self):
        conn = self.connection()
        
        print("getting command authority...")
        get_cmd_authority = "{\"path\":\"acu.command_arbiter.authority\",\"params\":{\"action\":\"1\"}}"
        conn.request("PUT", "/devices/command", get_cmd_authority)
        self.get_response(conn)
        
        print("unstowing telescope...")
        self.stow("0")
        
        
        print("activating axes...")
        conn.request("PUT", "/devices/command", "{\"path\":\"acu.azimuth.activate\"}")
        self.get_response(conn)
        conn.request("PUT", "/devices/command", "{\"path\":\"acu.elevation.activate\"}")
        self.get_response(conn)        
        time.sleep(10)
        
        print("set threshhold and averaging time for on_source...")
        on_source_str_1 = "{\"path\":\"acu.dish_management_controller.set_on_source_threshold\",\"params\":{\"threshold\":\""
        on_source_str_2 = "\", \"time_period_for_rms_calculation\":\""
        on_source_command = on_source_str_1 + str(self.on_source_threshold) + on_source_str_2 + str(self.on_source_rms) + "\"}}"
        conn.request("PUT", "/devices/command", on_source_command)
        self.get_response(conn)
        
        print("creating datalogging config...")
        with open(self.data_log_config_file_name, 'r') as file:
            datalog_path = file.read()
        conn.request("PUT", "/datalogging/config", body='{"name": "' + self.data_log_config_name + '","paths": '+ datalog_path +'}')
        self.get_response(conn)
        
    #function for moving to certain position
    def move_pos(self, az_pos, alt_pos, rel_abs):
        conn = self.connection()
        az_posString_1 = "{\"path\":\"acu.azimuth.slew_to_"+rel_abs[0:3]+"_pos\",\"params\":{\"new_axis_"+rel_abs+"_position_set_point\":\""
        az_posString_2 = "\", \"new_axis_speed_set_point_for_this_move\":\""
        az_posCommand = az_posString_1 + str(az_pos) + az_posString_2 + str(self.v_max_az) + "\"}}"
        conn.request("PUT", "/devices/command", az_posCommand)
        self.get_response(conn)
        time.sleep(1.)

        alt_posString_1 = "{\"path\":\"acu.elevation.slew_to_"+rel_abs[0:3]+"_pos\",\"params\":{\"new_axis_"+rel_abs+"_position_set_point\":\""
        alt_posString_2 = "\", \"new_axis_speed_set_point_for_this_move\":\""
        alt_posCommand = alt_posString_1 + str(alt_pos) + alt_posString_2 + str(self.v_max_alt) + "\"}}"
        conn.request("PUT", "/devices/command", alt_posCommand)
        self.get_response(conn)
        time.sleep(1.)
        
    def move_band(self):
        print("moving indexer to band...")
        conn = self.connection()
        indexer_str = "{\"path\":\"acu.dish_management_controller.move_to_band\",\"params\":{\"action\":\""
        indexer_command = indexer_str + band + "\"}}"
        conn.request("PUT", "/devices/command", indexer_command)
        self.get_response(conn)
        time.sleep(1.)
        
    def wait_for_pos_reached(self):
        conn = self.connection()
        curr_az = 9999.
        curr_az_set = 0.
        curr_alt = 9999.
        curr_alt_set = 0.
        curr_indexer = 9999.
        curr_indexer_set = 0.
        while(abs(curr_az-curr_az_set) > 0.001 and abs(curr_alt-curr_alt_set) > 0.001 and abs(curr_indexer-curr_indexer_set) > 0.001):
            conn.request("GET", "/devices/statusValue?path=acu.azimuth.p_act")
            response = self.get_response(conn).decode('utf-8')
            result = json.loads(response)
            curr_az = float(result['value'])
            conn.request("GET", "/devices/statusValue?path=acu.azimuth.p_set")
            response = self.get_response(conn).decode('utf-8')
            result = json.loads(response)
            curr_az_set = float(result['value'])
            
            conn.request("GET", "/devices/statusValue?path=acu.elevation.p_act")
            response = self.get_response(conn).decode('utf-8')
            result = json.loads(response)
            curr_alt = float(result['value'])
            conn.request("GET", "/devices/statusValue?path=acu.elevation.p_set")
            response = self.get_response(conn).decode('utf-8')
            result = json.loads(response)
            curr_alt_set = float(result['value'])
            
            conn.request("GET", "/devices/statusValue?path=acu.indexer.p_act")
            response = self.get_response(conn).decode('utf-8')
            result = json.loads(response)
            curr_indexer = float(result['value'])
            conn.request("GET", "/devices/statusValue?path=acu.indexer.p_set")
            response = self.get_response(conn).decode('utf-8')
            result = json.loads(response)
            curr_indexer_set = float(result['value'])
            
            print("alt difference: " + str(abs(curr_alt - curr_alt_set)))  
            print("az difference: " + str(abs(curr_az-curr_az_set)))
            print("indexer difference: " + str(abs(curr_indexer-curr_indexer_set)))
            time.sleep(1)
            
    def run_table(self, table, stop_time):
        print("running observation...")
        conn = self.connection()
        conn.request("PUT", "/acuska/programTrack", table)
        self.get_response(conn)
        time.sleep(10.)
        while Time.now() < stop_time:
            sys.stdout.write("\rRemaining seconds:" + str((stop_time.mjd - Time.now().mjd) * 24. * 3600.))
            sys.stdout.flush()
            time.sleep(1.)
        print("\n")
        
    def start_data_logging(self):
        
        print("starting datalogging...")
        conn = self.connection()
        conn.request("PUT", "/datalogging/start?configName=test_configuration")
        self.get_response(conn)
        
    def stop_data_logging(self):

        print("stopping datalogging...")
        conn = self.connection()
        conn.request("PUT", "/datalogging/stop")
        self.get_response(conn)
        
    def export(self, source_name, flux, ra, dec):    
        #here with try and except, because we had problems with the server not responding
        #get uuid of datalogging session
        print("getting id of datalogging session")
        conn.request("GET", "/datalogging/sessions")
        response = getResponse(conn).decode('utf-8')
        time_start_i = [i.start()+13 for i in re.finditer('"startTime"', response)]
        time_end_i = [i.start()-3 for i in re.finditer("stopTime", response)]
        times_array = [response[time_start_i[i]:time_end_i[i]] for i in range(len(time_start_i))]
        latest_time = max(times_array)
        uuid_end = response.find(str(latest_time)) - 14
        uuid_start = response.find('"uuid":',uuid_end-30, uuid_end) + 7
        uuid = response[uuid_start:uuid_end]


        #export session
        print("exporting session...")
        header  = "#" + "Source name: " + source_name + ", Source flux: " + str(flux) + ", RA: " + str(ra) + ", Dec: " + str(dec) + ", Input Parameter: " + str(sys.argv[1:]) + "\n\n"
        sender.send_log_file_info(uuid, header, self.backend_host, self.sender_port)
        
        conn.request("GET", "/datalogging/exportSession?interval_ms=100&id="+uuid)
        response = getResponse(conn).decode('utf-8')

        time_str=time.strftime("_%Y_%m_%d_%H_%M_%S")
        log_file = open(log_file_name+time_str+".txt", "w")
        log_file.write("#" + "Source name: " + source_name + ", Source flux: " + str(flux) + ", RA: " + str(ra) + ", Dec: " + str(dec) + ", Input Parameter: " + str(sys.argv[1:]) + "\n\n" + response)
        log_file.close()
        
