# V2X 2021 Fall Yichao's Branch 

##  1. Intro

This is Yichao's branch for V2X project. I focused on to implement the usecases by both MiniNet-Wifi and SUMO. We might change to Vein in future. 

## 2. Usage 

### 2.1 Run the usecase 
Simply use the command below to run the usecase. Please also make sure the MiniNet-Wifi has already been downloaded in your device. 

```shell 
$ make uc01 
```

If there are any issue occurred, please run the following command. 

```shell 
$ make clean 
```

Optionally, you can run them together each time. 

```shell 
$ make clean uc01
```

### 2.2 Configure SUMO Map

Directly modified the file put in the `sumocfg` directory. All changes will directly and automatically set to the SUMO environment. If you want to do that manually, please execute the command below: 

```shell
$ make config
```

## 3. Structure
...