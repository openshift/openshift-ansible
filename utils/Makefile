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

PEPEXCLUDES := E501,E121,E124

sdist: clean
	python setup.py sdist
	rm -fR $(SHORTNAME).egg-info

clean:
	@find . -type f -regex ".*\.py[co]$$" -delete
	@find . -type f \( -name "*~" -or -name "#*" \) -delete
	@rm -fR build dist rpm-build MANIFEST htmlcov .coverage cover ooinstall.egg-info oo-install
	@rm -fR $(NAME)env


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

virtualenv:
	@echo "#############################################"
	@echo "# Creating a virtualenv"
	@echo "#############################################"
	virtualenv $(NAME)env
	 . $(NAME)env/bin/activate && pip install setuptools==17.1.1
	. $(NAME)env/bin/activate && pip install -r test-requirements.txt
#       If there are any special things to install do it here
#       . $(NAME)env/bin/activate && INSTALL STUFF

ci-unittests:
	@echo "#############################################"
	@echo "# Running Unit Tests in virtualenv"
	@echo "#############################################"
	. $(NAME)env/bin/activate && nosetests -v --with-coverage --cover-html --cover-min-percentage=70 --cover-package=$(SHORTNAME) test/
	@echo "VIEW CODE COVERAGE REPORT WITH 'xdg-open cover/index.html' or run 'make viewcover'"

ci-pylint:
	@echo "#############################################"
	@echo "# Running PyLint Tests in virtualenv"
	@echo "#############################################"
	. $(NAME)env/bin/activate && python -m pylint --rcfile ../git/.pylintrc src/ooinstall/cli_installer.py src/ooinstall/oo_config.py src/ooinstall/openshift_ansible.py src/ooinstall/variants.py ../callback_plugins/openshift_quick_installer.py ../roles/openshift_certificate_expiry/library/openshift_cert_expiry.py

ci-list-deps:
	@echo "#############################################"
	@echo "# Listing all pip deps"
	@echo "#############################################"
	. $(NAME)env/bin/activate && pip freeze

ci-pyflakes:
	@echo "#################################################"
	@echo "# Running Pyflakes Compliance Tests in virtualenv"
	@echo "#################################################"
	. $(NAME)env/bin/activate && pyflakes src/ooinstall/*.py
	. $(NAME)env/bin/activate && pyflakes ../callback_plugins/openshift_quick_installer.py
	. $(NAME)env/bin/activate && pyflakes ../roles/openshift_certificate_expiry/library/openshift_cert_expiry.py

ci-pep8:
	@echo "#############################################"
	@echo "# Running PEP8 Compliance Tests in virtualenv"
	@echo "#############################################"
	. $(NAME)env/bin/activate && pep8 --ignore=$(PEPEXCLUDES) src/$(SHORTNAME)/
	. $(NAME)env/bin/activate && pep8 --ignore=$(PEPEXCLUDES) ../callback_plugins/openshift_quick_installer.py
# This one excludes E402 because it is an ansible module and the
# boilerplate import statement is expected to be at the bottom
	. $(NAME)env/bin/activate && pep8 --ignore=$(PEPEXCLUDES),E402 ../roles/openshift_certificate_expiry/library/openshift_cert_expiry.py

ci: clean virtualenv ci-list-deps ci-pep8 ci-pylint ci-pyflakes ci-unittests
	:
