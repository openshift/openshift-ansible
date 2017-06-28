#!/usr/bin/python
"""Attempt to bind to a given set of ports, or return errors encountered"""

import socket
import errno

from ansible.module_utils.basic import AnsibleModule


def main():
    """Bind to a given set of ports and return any errors this might cause."""
    module = AnsibleModule(
        argument_spec=dict(
            # ports is a list of dicts consisting of a port_name and a port field:
            #   [
            #     {
            #       "port_name": "mysql",
            #       "port": 3306,
            #     }
            #   ]
            ports=dict(type="list", required=True),
        ),
    )

    errors = list()

    ports = module.params["ports"]
    for port in ports:
        if not port.get("port"):
            continue

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.bind(('localhost', port["port"]))
        except socket.error as error:
            if error.errno == errno.EADDRINUSE:
                error = "Port is in use by another process."
            port["error"] = str(error)
            errors.append(port)
        finally:
            sock.close()

    module.exit_json(
        changed=False,
        failed=len(errors),
        error_ports=errors,
    )


if __name__ == '__main__':
    main()
