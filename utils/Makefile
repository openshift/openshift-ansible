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

sdist: clean
	python setup.py sdist
	rm -fR $(SHORTNAME).egg-info

clean:
	@find . -type f -regex ".*\.py[co]$$" -delete
	@find . -type f \( -name "*~" -or -name "#*" \) -delete
	@rm -fR build dist rpm-build MANIFEST htmlcov .coverage cover ooinstall.egg-info oo-install
	@rm -fR $(NAME)env

virtualenv:
	@echo "#############################################"
	@echo "# Creating a virtualenv"
	@echo "#############################################"
	virtualenv $(NAME)env
	. $(NAME)env/bin/activate && pip install -r requirements.txt
	. $(NAME)env/bin/activate && pip install pep8 nose coverage mock flake8 PyYAML click

#       If there are any special things to install do it here
#       . $(NAME)env/bin/activate && INSTALL STUFF

ci-unittests:
	@echo "#############################################"
	@echo "# Running Unit Tests in virtualenv"
	@echo "#############################################"
#	. $(NAME)env/bin/activate && nosetests -v --with-cover --cover-html --cover-min-percentage=80 --cover-package=$(TESTPACKAGE) test/
	. $(NAME)env/bin/activate && nosetests -v test/

ci-pylint:
	@echo "#############################################"
	@echo "# Running PyLint Tests in virtualenv"
	@echo "#############################################"
	python -m pylint --rcfile ../git/.pylintrc src/ooinstall/cli_installer.py src/ooinstall/oo_config.py src/ooinstall/openshift_ansible.py src/ooinstall/variants.py

ci-list-deps:
	@echo "#############################################"
	@echo "# Listing all pip deps"
	@echo "#############################################"
	. $(NAME)env/bin/activate && pip freeze

ci-pep8:
	@echo "#############################################"
	@echo "# Running PEP8 Compliance Tests in virtualenv"
	@echo "#############################################"
	@echo "Skipping PEP8 tests until we clean them up"
# . $(NAME)env/bin/activate && pep8 --ignore=E501,E121,E124 src/$(SHORTNAME)/

ci-pep8-real:
	@echo "#############################################"
	@echo "# Running PEP8 Compliance Tests in virtualenv"
	@echo "#############################################"
	. $(NAME)env/bin/activate && pep8 --ignore=E501,E121,E124 src/$(SHORTNAME)/


ci: clean virtualenv ci-list-deps ci-pylint ci-pep8 ci-unittests
	:
