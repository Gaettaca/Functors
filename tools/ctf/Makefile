default:
	@echo "usage: make deploy"

H=root@best-cpp-course-ever.ru

deploy:
	ssh $(H) systemctl stop ctf
	rsync --exclude runlocal.sh \
              --exclude ctf.conf \
              --exclude ctf.service \
              --exclude env \
              -r . $(H):/opt/ctf
	ssh $(H) systemctl start ctf

.PHONY: deploy default

