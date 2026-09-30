PROTO_ROOT := ../../proto
PROTO_FILES := $(shell find $(PROTO_ROOT) -name '*.proto')
OUT := src/ai_service/gen

.PHONY: install proto run demo demo-offline test lint clean

install:                ## create the venv and install everything
	uv sync

proto: install          ## regenerate gRPC stubs from the shared .proto files
	@mkdir -p $(OUT)
	@touch $(OUT)/__init__.py
	uv run python -m grpc_tools.protoc \
		-I$(PROTO_ROOT) \
		--python_out=$(OUT) \
		--pyi_out=$(OUT) \
		--grpc_python_out=$(OUT) \
		$(PROTO_FILES)
	@# protoc emits absolute package imports; rewrite them to be relative to
	@# this package so the stubs import cleanly from src layout.
	@find $(OUT) -name '*_pb2_grpc.py' -exec sed -i '' \
		's/^from hireassist/from ai_service.gen.hireassist/' {} +
	@echo "stubs generated in $(OUT)"

run: proto              ## start the gRPC server
	uv run python -m ai_service

demo: proto             ## walk through the three operations against a running server
	uv run python demo/demo_client.py

demo-offline: proto     ## start a server with canned answers, run the demo, stop it
	@AI_SERVICE_PROVIDER=canned uv run python -m ai_service & echo $$! > /tmp/ai-demo.pid; \
	sleep 3; \
	uv run python demo/demo_client.py; \
	status=$$?; \
	kill `cat /tmp/ai-demo.pid` 2>/dev/null; rm -f /tmp/ai-demo.pid; \
	exit $$status

test: proto             ## run the tests
	uv run pytest -q

lint:                   ## check formatting and lint
	uv run ruff check .
	uv run ruff format --check .

clean:
	rm -rf $(OUT) .venv .pytest_cache
