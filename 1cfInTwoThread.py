# -*- coding: utf-8 -*-
#
#     ||          ____  _ __
#  +------+      / __ )(_) /_______________ _____  ___
#  | 0xBC |     / __  / / __/ ___/ ___/ __ `/_  / / _ \
#  +------+    / /_/ / / /_/ /__/ /  / /_/ / / /_/  __/
#   ||  ||    /_____/_/\__/\___/_/   \__,_/ /___/\___/
#
#  Copyright (C) 2017-2018 Bitcraze AB
#
#  Crazyflie Nano Quadcopter Client
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA  02110-1301, USA.
"""
Version of the AutonomousSequence.py example connecting to 10 Crazyflies.
The Crazyflies go straight up, hover a while and land but the code is fairly
generic and each Crazyflie has its own sequence of setpoints that it files
to.

The layout of the positions:
    x2      x1      x0

y3  10              4

            ^ Y
            |
y2  9       6       3
            |
            +------> X

y1  8       5       2



y0  7               1

"""
import time
from threading import Thread

import cflib.crtp
from cflib.crazyflie.log import LogConfig
from cflib.crazyflie.swarm import CachedCfFactory
from cflib.crazyflie.swarm import Swarm
from cflib.crazyflie.syncLogger import SyncLogger

# Change uris and sequences according to your setup
URI1 = 'radio://0/40/2M/E7E7E7E7E7'
URI2 = 'radio://0/20/2M/E7E7E7E7E7'


z0 = 0.4
z = 1.0

x0 = 0.7
x1 = 0
x2 = -0.7

y0 = -1.0
y1 = -0.4
y2 = 0.4
y3 = 1.0

#    x   y   z  time
sequence1 = [
    (x0, y0, z0, 1.0),
    (x0, y0, z, 3.0),
    (x0, y0, z0, 1.0),
]

sequence2 = [
    (x0, y1, z0, 1.0),
    (x0, y1, z, 3.0),
    (x0, y1, z0, 1.0),
]

sequence3 = [
    (x0, y2, z0, 3.0),
    (x0, y2, z, 30.0),
    (x0, y2, z0, 3.0),
]

sequence4 = [
    (x0, y3, z0, 3.0),
    (x0, y3, z, 30.0),
    (x0, y3, z0, 3.0),
]

sequence5 = [
    (x1, y1, z0, 3.0),
    (x1, y1, z, 30.0),
    (x1, y1, z0, 3.0),
]

sequence6 = [
    (x1, y2, z0, 3.0),
    (x1, y2, z, 30.0),
    (x1, y2, z0, 3.0),
]

sequence7 = [
    (x2, y0, z0, 3.0),
    (x2, y0, z, 30.0),
    (x2, y0, z0, 3.0),
]

sequence8 = [
    (x2, y1, z0, 3.0),
    (x2, y1, z, 30.0),
    (x2, y1, z0, 3.0),
]

sequence9 = [
    (x2, y2, z0, 3.0),
    (x2, y2, z, 30.0),
    (x2, y2, z0, 3.0),
]

sequence10 = [
    (x2, y3, z0, 3.0),
    (x2, y3, z, 30.0),
    (x2, y3, z0, 3.0),
]

seq_args = {
    URI1: [[sequence1,1]],
   # URI2: [sequence2],
}

# List of URIs, comment the one you do not want to fly
uris = {
    URI1,
#    URI2,
}

class PublicSWarm(Swarm):
    def get_all_scfs(self):
        return self._cfs
    
    def parallel_unblock(self, func, args_dict=None):
        """
        Execute a function for all Crazyflies in the swarm, in parallel.
        One thread per Crazyflie is started to execute the function. The
        threads are joined at the end. Exceptions raised by the threads are
        ignored.

        For a description of the arguments, see sequential()

        :param func:
        :param args_dict:
        """
        try:
            self.parallel_safe_unblock(func, args_dict)
        except Exception:
            pass

    def parallel_safe_unblock(self, func, args_dict=None):
        """
        Execute a function for all Crazyflies in the swarm, in parallel.
        One thread per Crazyflie is started to execute the function. The
        threads are joined at the end and if one or more of the threads raised
        an exception this function will also raise an exception.

        For a description of the arguments, see sequential()

        :param func:
        :param args_dict:
        """
        threads = []
        reporter = self.Reporter()

        for uri, scf in self._cfs.items():
            args = [func, reporter] + \
                self._process_args_dict(scf, uri, args_dict)

            thread = Thread(target=self._thread_function_wrapper, args=args)
            threads.append(thread)
            thread.start()


        if reporter.is_error_reported():
            raise Exception('One or more threads raised an exception when '
                            'executing parallel task')


def position_callback(timestamp, data, logconf):
    print('I m in callback')
    print(data)
    print(logconf.cf.link_uri)

def wait_for_position_estimator(scf):
    print('Waiting for estimator to find position...')

    log_config = LogConfig(name='Kalman Variance', period_in_ms=500)
    log_config.add_variable('kalman.stateX', 'float')
    log_config.add_variable('kalman.stateY', 'float')
    log_config.add_variable('kalman.stateZ', 'float')
   # import pdb; pdb.set_trace()
    scf.log.add_config(log_config)
    log_config.data_received_cb.add_callback(position_callback)
    log_config.start()

    var_y_history = [1000] * 10
    var_x_history = [1000] * 10
    var_z_history = [1000] * 10

    threshold = 0.001

    with SyncLogger(scf, log_config) as logger:
        for log_entry in logger:
            data = log_entry[1]
            log_config.add_variable('ranging.distance2', 'float')
            var_x_history.append(data['kalman.varPX'])
            var_x_history.pop(0)
            var_y_history.append(data['kalman.varPY'])
            var_y_history.pop(0)
            var_z_history.append(data['kalman.varPZ'])
            var_z_history.pop(0)

            min_x = min(var_x_history)
            max_x = max(var_x_history)
            min_y = min(var_y_history)
            max_y = max(var_y_history)
            min_z = min(var_z_history)
            max_z = max(var_z_history)

            # print("{} {} {}".
            #       format(max_x - min_x, max_y - min_y, max_z - min_z))

            if (max_x - min_x) < threshold and (
                    max_y - min_y) < threshold and (
                    max_z - min_z) < threshold:
                break


def wait_for_param_download(scf):
    while not scf.cf.param.is_updated:
        time.sleep(1.0)
    print('Parameters downloaded for', scf.cf.link_uri)


def reset_estimator(scf):
    cf = scf.cf
    cf.param.set_value('kalman.resetEstimation', '1')
    time.sleep(0.1)
    cf.param.set_value('kalman.resetEstimation', '0')

    wait_for_position_estimator(cf)


def take_off(cf, position):
    take_off_time = 1.0
    sleep_time = 0.1
    steps = int(take_off_time / sleep_time)
    vz = position[2] / take_off_time

    print(vz)

    for i in range(steps):
        cf.commander.send_velocity_world_setpoint(0, 0, vz, 0)
        time.sleep(sleep_time)


def land(cf, position):
    landing_time = 1.0
    sleep_time = 0.1
    steps = int(landing_time / sleep_time)
    vz = -position[2] / landing_time

    print(vz)

    for i in range(steps):
        cf.commander.send_velocity_world_setpoint(0, 0, vz, 0)
        time.sleep(sleep_time)

    cf.commander.send_setpoint(0, 0, 0, 0)
    # Make sure that the last packet leaves before the link is closed
    # since the message queue is not flushed before closing
    time.sleep(0.1)


def run_sequence(scf, sequence):
    try:
        cf = scf.cf
        '''
        cf.param.set_value('flightmode.posSet', '1')
        log_config = LogConfig(name='runsequencelog', period_in_ms=500)
        log_config.add_variable('stabilizer.roll', 'float')
        log_config.add_variable('kalman.stateY', 'float')
        log_config.add_variable('kalman.stateZ', 'float')
       # import pdb; pdb.set_trace()
        cf.log.add_config(log_config)
        log_config.data_received_cb.add_callback(position_callback)
        log_config.start()
        '''
        for i in range(0,5):
            print('run sequence',i)
            time.sleep(1)
        print('The second param is', sequence[1])
    except Exception as e:
        print(e)


if __name__ == '__main__':
    # logging.basicConfig(level=logging.DEBUG)
    cflib.crtp.init_drivers(enable_debug_driver=False)

    factory = CachedCfFactory(rw_cache='./cache')
    with PublicSWarm(uris, factory=factory) as swarm:
        # If the copters are started in their correct positions this is
        # probably not needed. The Kalman filter will have time to converge
        # any way since it takes a while to start them all up and connect. We
        # keep the code here to illustrate how to do it.
        swarm.parallel(reset_estimator)

        # The current values of all parameters are downloaded as a part of the
        # connections sequence. Since we have 10 copters this is clogging up
        # communication and we have to wait for it to finish before we start
        # flying.
        print('Waiting for parameters to be downloaded...')
        swarm.parallel(wait_for_param_download)

        swarm.parallel_unblock(run_sequence, args_dict=seq_args)
        scfs = swarm.get_all_scfs()
        localuri = scfs[URI1].cf.link_uri
        print(localuri)
        