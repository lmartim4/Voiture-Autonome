from rplidar import RPLidar

lidar = RPLidar("/dev/ttyUSB0", baudrate=115200)

print(lidar.get_info())
print(lidar.get_health())

try:
    for scan in lidar.iter_scans():
        print(len(scan))
except KeyboardInterrupt:
    lidar.stop()
    lidar.disconnect()
