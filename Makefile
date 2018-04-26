IMAGE_NAME := lucid

run:
	PYTHONPATH=~/g/conu nvim -u ./vimrc -c "call LucidRun()"

build-container-image:
	docker build --network=host --tag=$(IMAGE_NAME) .

run-in-container:
	docker run -ti --rm \
		--net=host \
		-v /var/lib/containers:/var/lib/containers \
		-v $(CURDIR):/src:Z \
		-v /var/run/docker.sock:/var/run/docker.sock \
		$(IMAGE_NAME)


check:
	PYTHONPATH=$(CURDIR)/rplugin/python3 pytest-3 tests/
