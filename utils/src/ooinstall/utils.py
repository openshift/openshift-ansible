import logging

installer_log = logging.getLogger('installer')


def debug_env(env):
    for k in sorted(env.keys()):
        if k.startswith("OPENSHIFT") or k.startswith("ANSIBLE") or k.startswith("OO"):
            installer_log.debug("{key}: {value}".format(
                key=k, value=env[k]))
