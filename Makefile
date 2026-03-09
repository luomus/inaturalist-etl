IMAGE ?= inat-etl
ENV_FILE ?= .env
MANUAL_STATE_FILE ?= app/store/data-MANUAL.json

.PHONY: manual-update

manual-update:
	@test -f "$(ENV_FILE)" || (echo "Missing $(ENV_FILE). Create it first." && exit 1)
	@test -f "$(MANUAL_STATE_FILE)" || (echo "Missing $(MANUAL_STATE_FILE). Create it first." && exit 1)
	docker build -t "$(IMAGE)" .
	docker run --rm --env-file "$(ENV_FILE)" \
		-v "$$(pwd)/$(MANUAL_STATE_FILE):/app/store/data-MANUAL.json" \
		"$(IMAGE)" production manual true 5
