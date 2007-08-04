SSDIR=sharedstate.git
SSGIT=git://dev.laptop.org/projects/sharedstate

all: update_ss

clean:
	rm -rf ${SSDIR} sharedstate

update_ss:
	./update_sharedstate
