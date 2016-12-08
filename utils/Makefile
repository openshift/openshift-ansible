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
TESTPACKAGE := oo-install
SHORTNAME := ooinstall

# This doesn't evaluate until it's called. The -D argument is the
# directory of the target file ($@), kinda like `dirname`.
ASCII2MAN = a2x -D $(dir $@) -d manpage -f manpage $<
MANPAGES := docs/man/man1/atomic-openshift-installer.1
VERSION := 1.3

sdist: clean
	python setup.py sdist
	rm -fR $(SHORTNAME).egg-info

clean:
	@find . -type f -regex ".*\.py[co]$$" -delete
	@find . -type f \( -name "*~" -or -name "#*" \) -delete
	@rm -fR build dist rpm-build MANIFEST htmlcov .coverage cover ooinstall.egg-info oo-install


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
venv: oo-installenv/bin/activate
oo-installenv/bin/activate: test-requirements.txt
	@echo "#############################################"
	@echo "# Creating a virtualenv"
	@echo "#############################################"
	test -d venv || virtualenv $(NAME)env
	. $(NAME)env/bin/activate && pip install setuptools==17.1.1
	. $(NAME)env/bin/activate && pip install -r test-requirements.txt
	touch $(NAME)env/bin/activate
#       If there are any special things to install do it here
#       . $(NAME)env/bin/activate && INSTALL STUFF

ci-unittests:
	@echo "#############################################"
	@echo "# Running Unit Tests in virtualenv"
	@echo "#############################################"
	. $(NAME)env/bin/activate && python setup.py nosetests --cover-erase
	@echo "VIEW CODE COVERAGE REPORT WITH 'xdg-open cover/index.html' or run 'make viewcover'"

ci-pylint:
	@echo "#############################################"
	@echo "# Running PyLint Tests in virtualenv"
	@echo "#############################################"
	. $(NAME)env/bin/activate && python -m pylint --rcfile ../git/.pylintrc $(shell find ../ -name $(NAME)env -prune -o -name test -prune -o -name "*.py" -print) 2>&1 | grep -E -v '(locally-disabled|file-ignored)'

ci-list-deps:
	@echo "#############################################"
	@echo "# Listing all pip deps"
	@echo "#############################################"
	. $(NAME)env/bin/activate && pip freeze

ci-flake8:
	@echo "#############################################"
	@echo "# Running Flake8 Compliance Tests in virtualenv"
	@echo "#############################################"
	. $(NAME)env/bin/activate && flake8 --config=setup.cfg ../ --exclude="utils,../inventory"
	. $(NAME)env/bin/activate && python setup.py flake8

ci: clean venv ci-list-deps ci-unittests ci-flake8 ci-pylint
	@echo
	@echo "##################################################################################"
	@echo "VIEW CODE COVERAGE REPORT WITH 'xdg-open cover/index.html' or run 'make viewcover'"
	@echo "To clean your test environment run 'make clean'"
	@echo "Other targets you may run with 'make': 'ci-pylint', 'ci-unittests', 'ci-flake8'"
