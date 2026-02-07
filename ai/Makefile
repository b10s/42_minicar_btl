ADDRESS ?= 10.98.196.194
REMOTE_DIR ?= /home/pi/refactor
PYTHON ?= python
VENV_ACTIVATE ?= .venv/bin/activate

.PHONY: sync input-devices tool-%

sync:
	rsync -r --exclude .venv --exclude "*.jsonl" . pi@$(ADDRESS):$(REMOTE_DIR)

devices:
	cat /proc/bus/input/devices | grep -i "controller"

tool-%:
	if [ -f "$(VENV_ACTIVATE)" ]; then . "$(VENV_ACTIVATE)"; fi; \
	$(PYTHON) -m tools.$*
