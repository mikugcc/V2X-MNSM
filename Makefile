SUMO_HOME := $(shell pip show mininet_wifi | grep -Eo /usr.*)
SUMO_DATA := ${SUMO_HOME}/mn_wifi/sumo/data
SUMO_CFG_FILES := ${SUMO_DATA}/*.sumocfg

init: 
	mkdir sumocfg
config: 
	$(info All data in sumo_config will be put into sumo_home)
	sudo cp sumocfg/* ${SUMO_DATA}
uc01: config
	sudo -E env PATH=$(PWD)/src/scripts:$(PATH) python src/usecase1.py
clean: 
	sudo mn -c
	@[ -f .echo* ] && sudo rm -f .echo* || true
	@[ -d ./tmp ] && sudo rm -rdf ./tmp || true
	@[ -d */**/__pycache__ ] && sudo rm -rdf  */**/__pycache__ || true
stopOts: 
	pkill -9 make

