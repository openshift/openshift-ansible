window.OPENSHIFT_CONSTANTS.TEMPLATE_SERVICE_BROKER_ENABLED = {{ 'true' if (template_service_broker_install | default(True) and openshift_enable_service_catalog | default(True)) else 'false' }};
