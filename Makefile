SUMO_HOME := $(shell pip show mininet_wifi | grep -Eo /usr.*)
SUMO_DATA := ${SUMO_HOME}/mn_wifi/sumo/data
SUMO_CFG_FILES := ${SUMO_DATA}/*.sumocfg
ENV_PATH := $(PWD)/src/scripts:$(PATH)

uc ?= 01

usecase: clean
	sudo -E env PATH=$(ENV_PATH) python3 ./usecases/uc$(uc)/main.py

config: 
	$(info All data in sumo_config will be put into sumo_home)
	sudo cp sumocfg/* ${SUMO_DATA}

test: 
clean: 
	sudo rm mn* || true
	sudo rm .echo* || true
	sudo rm position-* || true
	sudo rm -rdf tmp || true
	find . -type d -name __pycache__ | sudo rm -rdf
	sudo mn -c

init: 
	@[ -d sumocfg ] || mkdir sumocfg
	@[ -d output ] || mkdir output
	pip3 install -e .

stop: 
	sudo pkill -9 make
	sudo pkill -9 wmediumd

