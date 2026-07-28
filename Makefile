.PHONY: run stop logs clean

run:
	bash run.sh

stop:
	bash stop.sh

logs:
	docker compose logs --follow

clean:
	bash clean.sh
