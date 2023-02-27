# V2X-MNSM

We also provide the [English Version](./docs/README.EN.md)

##  0. 简介 
这是一个MiniNet-WiFi关于V2X通信的扩展库。[MiniNet-WiFi](https://github.com/intrig-unicamp/mininet-wifi)的原始版本也支持基本的V2X通信，但其API不是为V2X用例设计的。我们的实现更注重可靠性和实用性。更重要的是，我们部分地实现了ITS-G5协议（仅在应用层）。该文件包括库的设计和实现。如果你对进一步的工作感兴趣，请通过 gcc.personal@outlook.com 或 yxu166@jhu.edu 与我们取得联系。

为了使用此扩展库，请确保你下载了项目所需的所有东西，包括python3.6+，pip3和MiniNet-WiFi。

##  1. 安装

**下载** 此项目目前使用Github进行版本管理我们，请使用下面的命令来下载代码。

```shell
$ git clone https://github.com/mikugcc/V2X-MNSM.git
```

(注意：在你下载代码之前，请确保你被授予访问存储库的权利。）

**安装**请使用下面的命令来安装此库

```shell
$ cd the_directory_of_project
$ pip install .
```
## 2. 使用方法 

### 2.1 运行usecase 

只需使用下面的命令来运行 usecase 01，其中你可以改变`=`后面的值来指定要执行的确切usecase。

也请确保[MiniNet-WiFi](https://github.com/intrig-unicamp/mininet-wifi)已经被下载到你的设备上。

```shell 
$ make usecase=01 
```

如果有任何问题发生，请运行以下命令。

```shell 
$ make clean 
```

也可以通过一下指令代替，此指令会自动执行所有需要的命令。

```shell 
$ make uc01
```

### 2.2 配置SUMO地图

直接修改放在`usecases/sumocfg/...`目录中的文件。所有的修改将直接自动设置到SUMO环境中。

## 3. 开发文件

### 3.1 v2xmnsm

我们把大多数可重用的代码放在一个目录下，`v2xmnsm`，我们遵循那些主要用于构建工具的代码结构，如Maven和Gradle。

`v2xmnsm/test`目录用于测试，`v2xmnsm/main`是模块代码。有许多公共接口，其中最重要的两个是SumoStepListener类和V2xVehicle类。

#### 3.1.1 SumoStepListener

我们遵循SUMO traci中的`Listener`模式。具体来说，我们提供了一个抽象类`SumoStepListener`，它可以被注册到SUMO Traci中，该类中的`__step_core`方法将在每个步骤中被精确调用一次。

我们把它设计成一个抽象类的原因是性能限制。如果我们实现了自动驾驶汽车的所有逻辑，那么单个用例的模拟将过于耗时，我们无法承担。继承抽象类允许我们为每个用例单独实现并运行所需要的东西。

在 "SumoStepListener "类中，有两种方法来实现车辆逻辑。我们建议使用装饰器（在Java中称为注解），`SumoStepListener.Substep`。当一个方法被装饰器标记后，它将在监听器的每个步骤中被执行。此外，它还允许指定一个子步骤的 "优先级"。

``` py
# 下面的方法将被执行 
# 在每个模拟步骤中精确执行一次。
@SumoStepListener.Substep(priority=10)
def do_something(self) -> None: 
    ...
```

另一种方法是覆盖`__step_one`方法，这在我们的程序中也是允许的。然而，覆盖该方法将使所有子步骤方法失效。 

```py 
# 下面的方法将被执行 
# 在每个模拟步骤中精确执行一次。
def __step_one(self) -> None: 
    ...
```

#### 3.1.2 V2xVehicle

该类封装了Mininet-wifi和sumo-traci车辆中的大部分方法。它为我们提供了有关网络通信、车辆控制等方法。

```py
# 该方法将广播 
# 通过Mesh接口播送一个数据包
v2x_vlc.broadcast_by_mesh(...)
# 该方法将广播 
# 通过wifi接口广播一个数据包
v2x_vlc.broadcast_by_wifi(...)
# 也可以通过下面的property 
# 或设置车辆的速度
cur_speed = v2x_vlc.speed 
v2x_vlc.speed = 0
```

### 3.2 开发Usecases

在开始开发之前，必须用pip3 locall安装模块。它可以通过下面的命令自动完成。

```shell
$ make init
```

我们把关于一个用例的大部分代码放在`usecases`目录中。具体来说，`usecases/uc02`是针对usecase02的。下面的代码是uc02的一部分。

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
