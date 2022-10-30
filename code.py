# import time
'''authors: Viswajith Govinda Rajan (gyx4bw), Akash Nair (asn7bf), Zoraiz Qureshi (zce5py), Zichuan Guo (zst2ym)'''

import math
import digitalio
import board
from adafruit_ble import BLERadio
from adafruit_ble.advertising import to_hex



ble = BLERadio()                                # setting ble adapter (I believe)
devices = []                                    # a list to hold unique devices
device_profile = {}                             # a dict to hold the dictionary of mac address, tx_power, rssi, distance for every nearby iBeacon detected
x = []                                          # list to store the x values of iBeacon devices
y = []                                          # list to store the y values of iBeacon devices
profile_index = 0                               # an indexing value for the device profile
distances = []                                  # list in meters for ranging equation calibration
pwr_list = []                                   # list to store power values, used in defining the ranging equation
rssi_list = []                                  # list to store rssi values, used in defining the ranging equation
ranges = []                                     # a list to store distances of nearby detected beacons
initial_scan_flag = True                        # flag to check if the scan is being performed for the very first time
button = digitalio.DigitalInOut(board.BTN_A)    # defining button A 
button.direction = digitalio.Direction.INPUT    # Button A is set as input
packet_count = 1                                # set this to 1 for distance calculation table and 15 for actual ranging calculation
adv_count = 0                                   # counter for advertisement packets during the ranging equation defining phase
dist = 0.5                                      # initial known distance measurement 0.5m
ranging_test = False                            # set to true to perform ranging test to find out the distance equation data points
c1 =  0.01                                      # 0.02333 -> value used for commented out formula
c2 = -0.21                                      # -0.41   -> value used for commented out formula

'''a dictionary of beacons with their known x and y coordinates'''
beacon_dict = {
	'c2:00:7d:00:00:52': (3.72,6.71),
	'c2:00:7d:00:00:59': (8.54,3.54),
	'c2:00:7d:00:00:9f': (7.79,9.97),
	'c2:00:7d:00:03:92': (15.58,5.08),
	'c2:00:7d:00:03:8c': (22.12,5.08),
	'c2:00:7d:00:00:97': (30.66,7.11),
	'c2:00:7d:00:00:98': (35.13,5.08),
	'c2:00:7d:00:00:64': (37.7,6.62),
	'c2:00:7d:00:00:99': (44.95,5.08),
	'c2:00:7d:00:03:8e': (52.45,3.14),
	'c2:00:7d:00:00:9d': (56.41,7.64),
	'c2:00:7d:00:00:6d': (52.18,13.46),
	'c2:00:7d:00:03:6f': (43.09,13.46),
	'c2:00:7d:00:03:6e': (49.89,16.88),
	'c2:00:7d:00:00:68': (52.11,22.56),
	'c2:00:7d:00:00:69': (57.51,18.71),
	'c2:00:7d:00:00:6f': (60.11,23.49),
	'c2:00:7d:00:00:67': (55.84,30.42),
	'c2:00:7d:00:00:76': (48.7,28.83),
	'c2:00:7d:00:00:75': (43.35,22.65),
	'c2:00:7d:00:03:70': (39.98,24.37),
	'c2:00:7d:00:00:77': (41.68,28.86),
	'c2:00:7d:00:00:78': (31.71,26.85),
	'c2:00:7d:00:03:91': (48.65,20.65),
	'c2:00:7d:00:00:8f': (31.45,24.16),
	'c2:00:7d:00:00:62': (22.13,28.86),
	'c2:00:7d:00:03:8a': (12.65,22.63),
	'c2:00:7d:00:00:61': (15.95,13.48),
	'c2:00:7d:00:00:9c': (13.59,10.01),
	'c2:00:7d:00:00:8e': (31.49,18.98),
	'c2:00:7d:00:00:6b': (37.8,10.21),
	'c2:00:7d:00:00:8d': (43.12,18.71),
	'c2:00:7d:00:00:96': (13.0,26.87),
	'c2:00:7d:00:00:63': (19.29,1.97),
	'c2:00:7d:00:00:93': (60.11,13.09),
	'c2:00:7d:00:00:6e': (54.36,22.48),
	'c2:00:7d:00:03:6a': (54.63,18.88),
	'c2:00:7d:00:00:74': (60.11,20.25),
	'c2:00:7d:00:00:72': (60.11,26.8),
	'c2:00:7d:00:00:65': (45.3,22.48),
	'c2:00:7d:00:00:71': (48.46,19.33),
	'c2:00:7d:00:00:6a': (33.79,24.2),
	'c2:00:7d:00:00:5a': (40.15,18.81),
	'c2:00:7d:00:00:5c': (19.89,13.98),
	'c2:00:7d:00:00:9b': (17.73,14.54),
	'c2:00:7d:00:00:94': (28.63,28.86),
	'c2:00:7d:00:00:95': (12.54,23.69),
	'c2:00:7d:00:00:91': (8.46,30.39),
	'c2:00:7d:00:00:92': (1.63,30.4),
	'c2:00:7d:00:00:9e': (1.5,23.2),
	'c2:00:7d:00:00:60': (1.46,16.99),
	'c2:00:7d:00:00:9a': (8.05,16.06),
	'c2:00:7d:00:03:96': (4.68,16.88),
	'c2:00:7d:00:00:5f': (5.2,10.13)
}

'''twos_comp(vals, bits) takes in the value and the bit type to return the two's complement for the given value. This is used because
the wikipedia page suggests taking the two's complement for the tx_power field.'''
def twos_comp(val, bits):
    if (val & (1 << (bits - 1))) != 0: 
        val = val - (1 << bits)        
    return val                         

'''distance_calculation() function takes rssi and tx_power of a iBeacon to return the distance it is from the receiver in meters'''
def distance_calculation(rssi, tx_power):
    distance = c1 * pow(10, ((rssi/tx_power)*c2)) # c1 * pow(math.e, ((rssi/tx_power)*c2)) -> works but curve does not fit very well
    return distance

'''mac_and_tx_pwr(addr, adv_array) takes the Advertisement.address value for every new filtered packet and returns the device's
MAC address and transmission power value'''
def mac_and_tx_pwr(addr, adv_array):
        address = repr(addr)
        mac_address = address[9:26]
        # if advert.tx_power is not None:
        #     tx_power_val =  twos_comp(int(advert.tx_power, 16), 8)
        # else:
        tx_power_val = twos_comp(int(adv_array[29], 16), 8)
        return mac_address, tx_power_val

'''compute_coordinates(devs, dists) takes in the list of all known scanned iBeacons and the list of the distances to the receiver
and uses the first two devices to compute  the receiver coordinates using 2D trilateration'''
def compute_coordinates(devs, dists):
    print(devs)
    print(dists)
    try:
        for beacon in devs:
            # print(beacon)
            if beacon in beacon_dict:
                print('xy pair for this beacon is: {}'.format(beacon_dict[beacon]))
                x.append(list(beacon_dict[beacon])[0])
                y.append(list(beacon_dict[beacon])[1])
        print(x)
        print(y)
        print('calculating coordinates')
        beacon_separation = math.sqrt(pow(x[1] - x[0], 2) + pow(y[1] - y[0], 2))    # calculate the distance between the beacons
        '''using the distance between the beacons, and the distance between the individual beacons and the receiver, compute the
        x and y coordinates of the receiver.'''
        X = (pow(dists[0], 2) - pow(dists[1], 2) + pow(beacon_separation, 2))/(2 * beacon_separation)
        Y = math.sqrt(pow(dists[1], 2) - pow(X, 2))
        return X,Y
    except:
        return 0, 0

    
print('Press Button A to start scanning\n')

while True:
    '''This block of code was used to define the ranging equation using known distances, rssi and tx_power'''
    if ranging_test:
        if button.value == 0 and initial_scan_flag == True:
            print("Button A Pressed! Scanning...\n")
            for adv in ble.start_scan():  #radio.start_scan(Advertisement, timeout=30)
                addr = adv.address
                adv_hex = to_hex(bytes(adv))
                adv_array = adv_hex.split()
                '''Filter to check if the detected beacon is an iBeacon. Apple devices are tagged with 0x004C in little endian 
                format, and the default '''
                if adv_array[1] == "ff" and adv_array[2] == "4c" and adv_array[3] == "00" \
                and adv_array[4] == "02" and adv_array[5] == "15":
                    mac, tx_power = mac_and_tx_pwr(addr, adv_array)
                    rssi = adv.rssi
                    if adv_count <= packet_count-1:    
                        if str(mac) == 'c2:00:7d:00:03:e2':
                            print(adv_count)
                            ranges.append(dist)
                            dist += 0.5
                            adv_count += 1
                            pwr_list.append(tx_power)    # grab rssi and tx values from the packet 
                            rssi_list.append(rssi)
                            print(repr(mac))
                    print('distances list is {}'.format(ranges))
                    print('tx_power list is {}'.format(pwr_list))
                    print('rssi list is {}'.format(rssi_list))
                    if adv_count == packet_count:
                        adv_count = 0
                        ble.stop_scan()
                        initial_scan_flag == False
                        print('End of scan\n')
                        break

    else:
        '''This block of code is used to identify nearby iBeacon nodes and then calculate the receiver's position relative to 
        the nodes'''
        if button.value == 0:
            print("Button A Pressed! Scanning...\n")
            for adv in ble.start_scan(timeout = 10):  #radio.start_scan(Advertisement, timeout = 30)
                addr = adv.address
                adv_hex = to_hex(bytes(adv))
                adv_array = adv_hex.split()
                '''Filter to check if the detected beacon is an iBeacon. Apple devices are tagged with 0x004C in little endian 
                format, and the default '''
                if adv_array[1] == "ff" and adv_array[2] == "4c" and adv_array[3] == "00" and adv_array[4] == "02" \
                    and adv_array[5] == "15":
                    mac, tx_power = mac_and_tx_pwr(addr, adv_array)     # find out the MAC address and Tx Power of the device
                    rssi = adv.rssi                                     # store the RSSI for this device
                    print(mac)
                    if mac not in devices and mac in beacon_dict:       # filter for unique beacons matching the beacon_list
                        devices.append(mac)
                        print('devices: {}'.format(devices))
                        distance = distance_calculation(rssi, tx_power) # calculate the distance from the beacon to receiver
                        distances.append(distance)
                        # print(profile_index)
                        device_profile[profile_index] = {'Device ID':mac, 'Tx_Power':tx_power, 'RSSI':rssi, \
                            'Distance (in m)': distance}
                        profile_index += 1
            print('Finished scanning, computing the receiver coordinates...\n')
            # print(devices)
            # print(distances)
            x, y = compute_coordinates(devices, distances)              # compute the x and y coordinate for the receiver
            if x != 0 and y != 0:
                print('your x coordinate is {}, and y coordinate is {}'.format(x, y))  # i pray for my sanity that this works because i have other things to do
            else:
                print('Not enough iBeacons found to approximate coordinates')