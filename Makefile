SUMO_HOME := $(shell pip show mininet_wifi | grep -Eo /usr.*)
SUMO_DATA := ${SUMO_HOME}/mn_wifi/sumo/data
SUMO_CFG_FILES := ${SUMO_DATA}/*.sumocfg
ENV_PATH := $(PWD)/src/scripts:$(PATH)

export PATH=$(ENV_PATH)

init: 
	@[ -d sumocfg ] || mkdir sumocfg
	@[ -d output ] || mkdir output

config: 
	$(info All data in sumo_config will be put into sumo_home)
	sudo cp sumocfg/* ${SUMO_DATA}


uc01: init clean 
	sudo -E env PATH=$(ENV_PATH) python src/usecase1.py

uc02: init clean 
	sudo -E env PATH=$(ENV_PATH) python src/usecase2.py

uc03: init clean 
	sudo -E env PATH=$(ENV_PATH) python src/usecase3.py

clean: 
	sudo mn -c
	sudo rm -f mn* || true
	sudo rm -rdf ./tmp || true
	sudo rm -f .echo* || true
	sudo rm -f position* || true
	sudo rm -rdf  */**/__pycache__ || true

stopOts: 
	sudo pkill -9 make
