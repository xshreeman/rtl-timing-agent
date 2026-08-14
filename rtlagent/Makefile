.PHONY: help env smoke test run report clean cdc
IMAGE := rtl-agent:pinned

help:
	@grep -E '^[a-z-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN{FS=":.*?## "}{printf "  \033[36m%-10s\033[0m %s\n",$$1,$$2}'

env:      ## build the pinned container
	docker build -t $(IMAGE) .

smoke:    ## 20-line design -> real slack number. MUST pass on day 1.
	docker run --rm -v $$PWD:/work $(IMAGE) python3 -m flowharness.smoke

test:     ## unit tests across all modules
	docker run --rm -v $$PWD:/work $(IMAGE) pytest -q tests/ src/cdcguard/tests/

cdc:      ## run the flagship standalone on golden vs a candidate
	docker run --rm -v $$PWD:/work $(IMAGE) \
	  python3 -m cdcguard.cli certify \
	    --golden runs/golden/cdc_manifest.json \
	    --revised runs/$(CAND)/cdc_manifest.json

run:      ## full optimisation loop on the damaged benchmark
	docker run --rm -v $$PWD:/work $(IMAGE) python3 -m orchestrator.run \
	    --rtl rtl/damaged/v1 --sdc rtl/shell/constraints.sdc --budget 20

report:   ## regenerate EVERY number and figure in the paper
	docker run --rm -v $$PWD:/work $(IMAGE) python3 -m evaluate.all

clean:
	rm -rf runs/* build dist **/__pycache__
