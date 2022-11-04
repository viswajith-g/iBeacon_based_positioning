'''author: Viswajith Govinda Rajan'''
import math
# import statistics
import digitalio
import board
from adafruit_ble import BLERadio
from adafruit_ble.advertising import to_hex



ble = BLERadio()                                # setting ble adapter (I believe)
initial_scan_flag = True                        # flag to check if the scan is being performed for the very first time
button = digitalio.DigitalInOut(board.BTN_A)    # defining button A 
button.direction = digitalio.Direction.INPUT    # Button A is set as input
packet_count = 1                                # set this to 1 for distance calculation table and 15 for actual ranging calculation
adv_count = 0                                   # counter for advertisement packets during the ranging equation defining phase
ranging_test = False                            # set to true to perform ranging test to find out the distance equation data points
'''constants for the distance equations'''
c1 = 0.055 
c2 = 3.8 
c3 = 0.21
c4 = 0.02
c5 = -0.0675
c6 = 0.01
c7 = -0.21

EQN = 2                                           # choose which range calculation equation to use. 0 is eqn1, 1 is eqn2 and 2 is eqn3


def init():
    global devices, device_profile, x, y, profile_index, distances, pwr_list, rssi_list, ranges, dist
    devices = []                                    # a list to hold unique devices
    device_profile = {}                             # a dict to hold the dictionary of mac address, tx_power, rssi, distance for every nearby iBeacon detected
    x = []                                          # list to store the x values of iBeacon devices
    y = []                                          # list to store the y values of iBeacon devices
    profile_index = 0                               # an indexing value for the device profile
    distances = []                                  # list in meters for ranging equation calibration
    pwr_list = []                                   # list to store power values, used in defining the ranging equation
    rssi_list = []                                  # list to store rssi values, used in defining the ranging equation
    ranges = []                                     # a list to store distances of nearby detected beacons
    dist = 0.5                                      # initial known distance measurement 0.5m


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
def distance_calculation(signal_strength, transmission_power):
    '''chooses which equation and set of constants to use based on the EQN constant'''
    eqns = [(c1 * pow(10,(((signal_strength-transmission_power)/(-10 * c2))-c3))), (c4 * pow(math.e, c5 * (signal_strength-transmission_power))), (c6 * pow(10, c7 * (signal_strength/transmission_power)))]
    distance = eqns[EQN]
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
    # print(devs)
    # print(dists)
    # anchor_beacon = devs[0]
    # x_anchor = list(beacon_dict[anchor_beacon])[0]
    # y_anchor = list(beacon_dict[anchor_beacon])[1]
    # for beacon in devs:
    #     if beacon in beacon_dict:
    #         # print('xy pair for beacon {} is: {}'.format(beacon, beacon_dict[beacon]))
    #         x.append(list(beacon_dict[beacon])[0])
    #         y.append(list(beacon_dict[beacon])[1])
    # beacon_separation = math.sqrt(pow(x[1] - x[0], 2) + pow((y[1] - y[0]), 2))    # calculate the distance between the beacons
    # '''using the distance between the beacons, and the distance between the individual beacons and the receiver, compute the
    # x and y coordinates of the receiver.'''
    #     print('range to beacon {} is {}m, range to beacon {} is {}m'.format(devs[0], dists[0], devs[1], dists[1]))
    #     X = (pow(dists[0], 2) - pow(dists[1], 2) + pow(beacon_separation, 2))/(2 * beacon_separation)
    #     Y = math.sqrt(abs(pow(dists[1], 2) - pow(X, 2)))
    # try:
    #     X = X + x_anchor
    #     Y = Y + y_anchor
    '''using the distance between the beacons, and the distance between the individual beacons and the receiver, compute the
    # x and y coordinates of the receiver.'''
    try:
        x1 = list(beacon_dict[devs[0]])[0]
        y1 = list(beacon_dict[devs[0]])[1]
        d1 = dists[0]
        # print('The beacon {} has coordinates {} and {} and is at a distance of {}m from the receiver'.format(devs[0], x1, y1, d1))

        x2 = list(beacon_dict[devs[1]])[0]
        y2 = list(beacon_dict[devs[1]])[1]
        d2 = dists[1]
        # print('The beacon {} has coordinates {} and {} and is at a distance of {}m from the receiver'.format(devs[1], x2, y2, d2))

        x3 = list(beacon_dict[devs[2]])[0]
        y3 = list(beacon_dict[devs[2]])[1]
        d3 = dists[2]
        # print('The beacon {} has coordinates {} and {} and is at a distance of {}m from the receiver'.format(devs[2], x3, y3, d3))

        A = 2*x2 - 2*x1
        # print('A = {}'.format(A))
        B = 2*y2 - 2*y1
        # print('B = {}'.format(B))
        C = d1**2 - d2**2 - x1**2 + x2**2 - y1**2 + y2**2
        # print('C = {}'.format(C))
        D = 2*x3 - 2*x2
        # print('D = {}'.format(D))
        E = 2*y3 - 2*y2
        # print('E = {}'.format(E))
        F = d2**2 - d3**2 - x2**2 + x3**2 - y2**2 + y3**2
        # print('F = {}'.format(F))
        X = (C*E - F*B) / (E*A - B*D)
        Y = (C*D - A*F) / (B*D - A*E)
        return X,Y
    except:
        return 0, 0

    
print('Press Button A to start scanning\n')

while True:
    '''This block of code was used to define the ranging equation using known distances, rssi and tx_power'''
    if button.value == 0 and initial_scan_flag == True:
        init()
        print("Button A Pressed! Scanning...\n")
        TO = None if ranging_test else 15
        for adv in ble.start_scan(timeout = TO): #radio.start_scan(Advertisement, timeout=30)
            addr = adv.address
            adv_hex = to_hex(bytes(adv))
            adv_array = adv_hex.split()
            '''Filter to check if the detected beacon is an iBeacon. Apple devices are tagged with 0x004C in little endian 
            format, and the default '''
            if adv_array[1] == "ff" and adv_array[2] == "4c" and adv_array[3] == "00" \
            and adv_array[4] == "02" and adv_array[5] == "15":
                mac, tx_power = mac_and_tx_pwr(addr, adv_array)
                rssi = adv.rssi
                if ranging_test:
                    if adv_count <= packet_count-1:    
                        if str(mac) == 'c2:00:7d:00:03:e2':
                            # print(adv_count)
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
                    if mac not in devices and mac in beacon_dict:       # filter for unique beacons matching the beacon_list
                        devices.append(mac)
                        # print('devices: {}'.format(devices))
                        distance = distance_calculation(rssi, tx_power) # calculate the distance from the beacon to receiver
                        distances.append(distance)
        print('Finished scanning, computing the receiver coordinates...\n')
        x, y = compute_coordinates(devices, distances)              # compute the x and y coordinate for the receiver
        if x != 0 and y != 0:
            '''i pray for my sanity that this works because i have other things to do'''
            print('Your x coordinate is {}, and y coordinate is {}. The anchor beacons were {}, {} and {}.'.format(x, y, devices[0], devices[1], devices[2])) 
            print('The Ranging equation used was {}'.format(EQN)) 
        else:
            print('Not enough iBeacons found to approximate coordinates')