import os
import sys

# extend sys.path so that tests can import openshift_checks
sys.path.insert(1, os.path.dirname(os.path.dirname(__file__)))
