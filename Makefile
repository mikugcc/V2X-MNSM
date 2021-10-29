SUMO_HOME := $(shell pip show mininet_wifi | grep -Eo /usr.*)
SUMO_DATA := ${SUMO_HOME}/mn_wifi/sumo/data
SUMO_CFG_FILES := ${SUMO_DATA}/*.sumocfg
ENV_PATH := $(PWD)/src/scripts:$(PATH)

init: 
	mkdir sumocfg
config: 
	$(info All data in sumo_config will be put into sumo_home)
	sudo cp sumocfg/* ${SUMO_DATA}
uc01: clean 
	sudo -E env PATH=${ENV_PATH} python src/usecase1.py
uc02: clean 
	sudo -E env PATH=${ENV_PATH} python src/usecase2.py
clean: 
	sudo mn -c
	@[ -f mn* ] && sudo rm -f mn* || true
	@[ -f .echo* ] && sudo rm -f .echo* || true
	@[ -d ./tmp ] && sudo rm -rdf ./tmp || true
	@[ -d */**/__pycache__ ] && sudo rm -rdf  */**/__pycache__ || true
stopOts: 
	pkill -9 make

