IMAGE ?= inat-etl
ENV_FILE ?= .env
MANUAL_STATE_FILE ?= app/store/data-MANUAL.json

.PHONY: manual-update manual-update-persist

manual-update:
	@test -f "$(ENV_FILE)" || (echo "Missing $(ENV_FILE). Create it first." && exit 1)
	@test -f "$(MANUAL_STATE_FILE)" || (echo "Missing $(MANUAL_STATE_FILE). Create it first." && exit 1)
	docker build -t "$(IMAGE)" .
	docker run --rm --env-file "$(ENV_FILE)" \
		-v "$$(pwd)/$(MANUAL_STATE_FILE):/app/store/data-MANUAL.json" \
		"$(IMAGE)" production manual true 5

manual-update-persist:
	@test -f "$(ENV_FILE)" || (echo "Missing $(ENV_FILE). Create it first." && exit 1)
	@test -f "$(MANUAL_STATE_FILE)" || (echo "Missing $(MANUAL_STATE_FILE). Create it first." && exit 1)
	docker build -t "$(IMAGE)" .
	@container_id=$$(docker run -d --env-file "$(ENV_FILE)" \
		-v "$$(pwd)/$(MANUAL_STATE_FILE):/app/store/data-MANUAL.json" \
		--entrypoint /bin/sh \
		"$(IMAGE)" -c 'python3 /app/entrypoint.py production manual true 5; echo "Manual update finished. Container kept alive."; tail -f /dev/null'); \
	echo "Container started: $$container_id"; \
	echo "Open a shell: docker exec -it $$container_id /bin/sh"; \
	echo "Stop when done: docker stop $$container_id"
