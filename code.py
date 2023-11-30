'''author: Viswajith Govinda Rajan'''
import math
# import statistics
import digitalio
import board
from adafruit_ble import BLERadio
from adafruit_ble.advertising import to_hex
import secrets



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
beacon_dict = secrets.beacon_dict

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
        tx_power_val = twos_comp(int(adv_array[29], 16), 8)
        return mac_address, tx_power_val

'''compute_coordinates(devs, dists) takes in the list of all known scanned iBeacons and the list of the distances to the receiver
and uses the first two devices to compute  the receiver coordinates using 2D trilateration'''
def compute_coordinates(devs, dists):
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
        B = 2*y2 - 2*y1
        C = d1**2 - d2**2 - x1**2 + x2**2 - y1**2 + y2**2
        D = 2*x3 - 2*x2
        E = 2*y3 - 2*y2
        F = d2**2 - d3**2 - x2**2 + x3**2 - y2**2 + y3**2
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
        TO = None if ranging_test else 15        # set timeout to None if trying to derive distance equation, else set to 15 seconds
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
                            ranges.append(dist)
                            dist += 0.5
                            adv_count += 1
                            pwr_list.append(tx_power)    # grab rssi and tx values from the packet 
                            rssi_list.append(rssi)
                            print(repr(mac))
                    # print('distances list is {}'.format(ranges))
                    # print('rssi list is {}'.format(rssi_list))
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
            # print('The Ranging equation used was {}'.format(EQN)) 
        else:
            print('Not enough iBeacons found to approximate coordinates')