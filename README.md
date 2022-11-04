# iBeacon_based_positioning
Positioning a receiver device based on the distances to deployed iBeacon devices. 

The goal is to perform a BLE scan for a few seconds in an area and try to resolve the coordinates of the receiver device in the local frame of reference.

1. First we scan for iBeacons in a fixed spot for about 15 seconds. This value was chosen because I was not sure how often the iBeacons advertised, and I wanted to make sure I was within the advertisement frequency for at least 3 separate beaacons. 

2. Once we are done scanning for the devices, we compute the distance to each scanned beacon, and we take the first three devices as anchor devices. This is because we know the location of the iBeacons in the local frame of reference. (this step can be simplified to calculating the distance only for the first three beacons/anchor beacons).

3. Using these three anchor devices, we can resolve the location of the receiver device (a Micro:Bit in this case) in the local frame of reference using trilateration.
