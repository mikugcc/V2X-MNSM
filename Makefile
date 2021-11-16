SUMO_HOME := $(shell pip show mininet_wifi | grep -Eo /usr.*)
SUMO_DATA := ${SUMO_HOME}/mn_wifi/sumo/data
SUMO_CFG_FILES := ${SUMO_DATA}/*.sumocfg
ENV_PATH := $(PWD)/scripts:$(PATH)

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

uc03a: init clean 
	sudo -E env PATH=$(ENV_PATH) python src/usecase3a.py

uc03b: init clean 
	sudo -E env PATH=$(ENV_PATH) python src/usecase3b.py

clean: 
	sudo rm mn* || true
	sudo rm .echo* || true
	sudo rm position-* || true
	sudo rm -rdf tmp || true
	sudo rm -rdf  */**/__pycache__ || true
	sudo mn -c

stopOts: 
	sudo pkill -9 make
