#!/usr/bin/env python3
from pathlib import Path
import os
import psutil
partitions = psutil.disk_partitions()

f=Path('/limitedio')
mountpoint = None
device = None
major = None
minor = None
for p in partitions:
    if str(f).startswith(p.mountpoint):
        print('-'*20)
        print(p.device)
        devicePath = Path(p.device)
        print('a'*60)
        print(devicePath.name)
        baseDevice = devicePath.name
        for dev in Path('/dev').iterdir():
            if baseDevice.startswith(dev.name):
                print('xxx')
                print(dev)
                print(dev.name)
                # must not choose NVME management device:
                if os.major(dev.lstat().st_rdev) != 248:
                    baseDevice = dev.name
if baseDevice is not None:
    print('='*20)
    print(baseDevice)
    drive = Path('/dev/') / baseDevice
    props = drive.lstat()
    print(os.major(props.st_rdev))
    print(os.minor(props.st_rdev))
    print(p.mountpoint, psutil.disk_usage(p.mountpoint).percent)
    print(p.mountpoint)
    print(len(p.mountpoint))
    if mountpoint is None:
        mountpoint = p.mountpoint
        major = os.major(props.st_rdev)
        minor = os.minor(props.st_rdev)
        device = baseDevice
        print('1')
    elif len(p.mountpoint) > len(mountpoint):
        print('2')
        mountpoint = p.mountpoint
        major = os.major(props.st_rdev)
        minor = os.minor(props.st_rdev)
        device = baseDevice

    print(mountpoint)
    print(device)
    print(major)
    print(minor)

    cgdir = Path('/sys/fs/cgroup/throttle_arangodb')
    if not cgdir.exists():
        cgdir.mkdir()

    iomax = cgdir / 'io.max'
    val = f"{major}:{minor} rbps=1048576 wiops=1048576"
    print(val)
    print(iomax)
    iomax.write_text(val)
else:
    print("Mountpoint not found")

# add shell in there:
# echo $$ > /sys/fs/cgroup/throttle_arangodb/tasks
