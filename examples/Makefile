# Change this to your fortran vendor; see
# fwrapc.py --help-fcompiler
FCOMP = gnu95

DIRS = arrays \
	   scalars \
	   intents \
	   functions \
	   kinds \

all: arrays_ext scalars_ext intents_ext functions_ext kinds_ext

clean:
	@for dir in $(DIRS) ;\
	do \
	    rm -r "$${dir}/$${dir}_ext" ;\
	done

arrays_ext:
	../fwrapc.py arrays/source.f90 --build --fcompiler=$(FCOMP) \
	--name=arrays_ext --out_dir=arrays --override

scalars_ext:
	../fwrapc.py scalars/source.f90 --build --fcompiler=$(FCOMP) \
	--name=scalars_ext --out_dir=scalars --override

intents_ext:
	../fwrapc.py intents/source.f90 --build --fcompiler=$(FCOMP) \
	--name=intents_ext --out_dir=intents --override

functions_ext:
	../fwrapc.py functions/source.f90 --build --fcompiler=$(FCOMP) \
	--name=functions_ext --out_dir=functions --override

kinds_ext:
	../fwrapc.py kinds/source.f90 --build --fcompiler=$(FCOMP) \
	--name=kinds_ext --out_dir=kinds --override

