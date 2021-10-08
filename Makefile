SUMO_HOME := $(shell pip show mininet_wifi | grep -Eo /usr.*)
SUMO_DATA := ${SUMO_HOME}/mn_wifi/sumo/data
SUMO_CFG_FILES := ${SUMO_DATA}/*.sumocfg

init: 
	mkdir sumocfg
config: 
	$(info All data in sumo_config will be put into sumo_home)
	$(info SUMO_HOME is in ${SUMO_DATA})
	sudo cp sumocfg/* ${SUMO_DATA}
uc01: config
	sudo -E env PATH=$(PATH) python src/usecase1.py
clean: 
	sudo mn -c
	@[ -f .echo* ] && sudo rm -f .echo* || true
	@[ -d ./tmp ] && sudo rm -rdf ./tmp || true
	@[ -d */**/__pycache__ ] && sudo rm -rdf  */**/__pycache__ || true

