# V2X 2021 Fall Yichao's Branch 

## 0. Preparation 

To use the packet, please ensure that you download all things required for the project, including python3.6+, pip3, and MiniNet-WiFi. 

##  1. Install

**Download.** Because we currently did not release our code online, you have to download the code from the bitbucket repository. Please use the command below to download the code. 
```shell
$ git clone git@bitbucket.org:projectV2X/v2x-fall-2021.git
```

(NOTICE: before you download the codes, please ensure you are granted to access the repository)

**Install.** Please use the command below to install the packets. 
```shell
$ cd the_directory_of_project
$ pip install .
```
## 2. Usage 

### 2.1 Run the usecase 

Simply use the command below to run the usecase 01, in which you can change the value after `=` to specify the exact usecase to execute. 

Please also make sure the MiniNet-Wifi has already been downloaded to your device. 

```shell 
$ make usecase=01 
```

If there are any issue occurred, please run the following command. 

```shell 
$ make clean 
```

Optionally, you can run them together each time. 

```shell 
$ make uc01
```

### 2.2 Configure SUMO Map

Directly modified the file put in the `usecases/sumocfg/...` directory. All changes will directly and automatically set to the SUMO environment. 

## 3. Dev Doc

### 3.1 V2XMNSM

We put most reusable codes into a directory, `v2xmnsm`, where we follow the codes structure of those that are mostly used in the build tools such as Maven and Gradle. 

The directory `v2xmnsm/test` is for testing, and `v2xmnsm/main` is the module codes. There are many public interfaces, in which most important two are the SumoStepListener class and V2xVehicle class. 

#### 3.1.1 SumoStepListener

We follow the `Listener` pattern in SUMO traci. Specifically, we provide an abstract class `SumoStepListener`, which can be registered to the SUMO Traci, and the `__step_core` method in the class will be invoked exactly once in each step. 

The reason why we design it as an abstract class is performance limit. If we implement all logic of an autonomous vehicle, the simulation for a single usecase will be too time-consuming to afford. The abstract class allow us to implement what we need for each usecase. 

There are two ways to implement vehicle logic in the `SumoStepListener` class. We suggest to use the decorator (or called as annotation in Java), `SumoStepListener.Substep`. When a method is marked by the decorator, it will be executed in each step of the listener. Besides, it also allow to specify the `priority` of a substep. 

``` py
# The method below will be executed 
# exactly once in each simulation step.
@SumoStepListener.Substep(priority=10)
def do_something(self) -> None: 
    ...
```

Another way is to override the `__step_one` method, which is also allowable in our program. However, overriding the method will make all substep methods disabled.  

```py 
# The method below will be executed 
# exactly once in each simulation step.
def __step_one(self) -> None: 
    ...
```

#### 3.1.2 V2xVehicle

The class encapsulates most methods in the Mininet-wifi and the sumo-traci vehicle. It provides us with methods about network communicating, vehicle controlling, etc.

```py
# The method will broadcast 
# a packet by mesh interface
v2x_vlc.broadcast_by_mesh(...)
# The method will broadcast 
# a packet by wifi interface
v2x_vlc.broadcast_by_wifi(...)
# It is also possible to get  
# or set the speed of a vehicle
cur_speed = v2x_vlc.speed 
v2x_vlc.speed = 0
```

### 3.2 Usecases

Before starting the development, it is essential to install the module by pip3 locall. It can be done automatically by the command below. 

```shell
$ make init
```

We put most codes about a usecase into the directory `usecases`. Specifically, the `usecases/uc02` is for usecase02. Codes below are part of the uc02. 

```py 
# Implement of `SumoStepListener`
class UC02CarController(SumoStepListener): 

    def __init__(self, v2x_vlc: V2xVehicle, speed: int = 13):
        self.__cur_lane = 1 # lane of the vehicle
        self.__cur_speed = speed # speed of the vehicle
        self.__v2x_vlc = v2x_vlc # object of V2xVehicle

    # a substep method, which will be executed once a step
    # the priority of the method is 9
    @SumoStepListener.Substeps(priority=9)
    def __send_CAM(self) -> None:
        '''
        The method will create a CAM packet 
        and broadcast the packet by mesh interface
        '''
        vlc_cam = CAM(
            car_id = self.__v2x_vlc.name, 
            lane = self.__v2x_vlc.lane, 
            leader = self.__v2x_vlc.get_leader_with_distance()[0], 
            speed = self.__v2x_vlc.speed, 
            position = self.__v2x_vlc.position, 
            timestamp = self.cur_time
        )
        self.__v2x_vlc.broadcast_by_mesh(vlc_cam)
        return None
    
    # a substep method, which will also be executed once a step
    # However, the priority of the method is 1. It means the 
    # method will be executed at the end of each step.
    @SumoStepListener.Substeps(priority=1)
    def __update_state(self) -> None:
        self.__v2x_vlc.lane = self.__cur_lane
        self.__v2x_vlc.speed = self.__cur_speed
        return None
```