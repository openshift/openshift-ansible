########################################################

# Makefile for OpenShift: Atomic Quick Installer
#
# useful targets (not all implemented yet!):
#   make clean               -- Clean up garbage
#   make ci ------------------- Execute CI steps (for travis or jenkins)

########################################################

# > VARIABLE = value
#
# Normal setting of a variable - values within it are recursively
# expanded when the variable is USED, not when it's declared.
#
# > VARIABLE := value
#
# Setting of a variable with simple expansion of the values inside -
# values within it are expanded at DECLARATION time.

########################################################


NAME := oo-install
VENV := $(NAME)env
TESTPACKAGE := oo-install
SHORTNAME := ooinstall

# This doesn't evaluate until it's called. The -D argument is the
# directory of the target file ($@), kinda like `dirname`.
ASCII2MAN = a2x -D $(dir $@) -d manpage -f manpage $<
MANPAGES := docs/man/man1/atomic-openshift-installer.1
# slipped into the manpage template before a2x processing
VERSION := 1.4

# YAMLFILES: Skipping all '/files/' folders due to conflicting yaml file definitions
YAMLFILES = $(shell find ../ -name $(VENV) -prune -o -name .tox -prune -o \( -name '*.yml' -o -name '*.yaml' \) ! -path "*/files/*" -print 2>&1)
PYFILES = $(shell find ../ -name $(VENV) -prune -o -name ooinstall.egg-info -prune -o -name test -prune -o -name .tox -prune -o -name "*.py" -print)

sdist: clean
	python setup.py sdist
	rm -fR $(SHORTNAME).egg-info

clean:
	@find . -type f -regex ".*\.py[co]$$" -delete
	@find . -type f \( -name "*~" -or -name "#*" \) -delete
	@rm -fR build dist rpm-build MANIFEST htmlcov .coverage cover ooinstall.egg-info oo-install
	@rm -fR $(VENV)


# To force a rebuild of the docs run 'touch' on any *.in file under
# docs/man/man1/
docs: $(MANPAGES)

# Regenerate %.1.asciidoc if %.1.asciidoc.in has been modified more
# recently than %.1.asciidoc.
%.1.asciidoc: %.1.asciidoc.in
	sed "s/%VERSION%/$(VERSION)/" $< > $@

# Regenerate %.1 if %.1.asciidoc or VERSION has been modified more
# recently than %.1. (Implicitly runs the %.1.asciidoc recipe)
%.1: %.1.asciidoc
	$(ASCII2MAN)

viewcover:
	xdg-open cover/index.html

# Conditional virtualenv building strategy taken from this great post
# by Marcel Hellkamp:
# http://blog.bottlepy.org/2012/07/16/virtualenv-and-makefiles.html
$(VENV): $(VENV)/bin/activate
$(VENV)/bin/activate: test-requirements.txt
	@echo "#############################################"
	@echo "# Creating a virtualenv"
	@echo "#############################################"
	test -d $(VENV) || virtualenv $(VENV)
	. $(VENV)/bin/activate && pip install setuptools==17.1.1
	. $(VENV)/bin/activate && pip install -r test-requirements.txt
	touch $(VENV)/bin/activate
#       If there are any special things to install do it here
#       . $(VENV)/bin/activate && INSTALL STUFF

ci-unittests: $(VENV)
	@echo "#############################################"
	@echo "# Running Unit Tests in virtualenv"
	@echo "#############################################"
	. $(VENV)/bin/activate && tox -e py27-unit
	. $(VENV)/bin/activate && tox -e py35-unit
	@echo "VIEW CODE COVERAGE REPORT WITH 'xdg-open cover/index.html' or run 'make viewcover'"

ci-pylint: $(VENV)
	@echo "#############################################"
	@echo "# Running PyLint Tests in virtualenv"
	@echo "#############################################"
	. $(VENV)/bin/activate && python -m pylint --rcfile ../git/.pylintrc $(PYFILES)

ci-yamllint: $(VENV)
	@echo "#############################################"
	@echo "# Running yamllint Tests in virtualenv"
	@echo "#############################################"
	@. $(VENV)/bin/activate && yamllint -c ../git/.yamllint $(YAMLFILES)

ci-list-deps: $(VENV)
	@echo "#############################################"
	@echo "# Listing all pip deps"
	@echo "#############################################"
	. $(VENV)/bin/activate && pip freeze

ci-flake8: $(VENV)
	@echo "#############################################"
	@echo "# Running Flake8 Compliance Tests in virtualenv"
	@echo "#############################################"
	. $(VENV)/bin/activate && tox -e py27-flake8
	. $(VENV)/bin/activate && tox -e py35-flake8

ci-tox:
	. $(VENV)/bin/activate && tox

ci: ci-list-deps ci-tox ci-pylint ci-yamllint
	@echo
	@echo "##################################################################################"
	@echo "VIEW CODE COVERAGE REPORT WITH 'xdg-open cover/index.html' or run 'make viewcover'"
	@echo "To clean your test environment run 'make clean'"
	@echo "Other targets you may run with 'make': 'ci-pylint', 'ci-tox', 'ci-unittests', 'ci-flake8', 'ci-yamllint'"
