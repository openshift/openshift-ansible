# pylint: disable=missing-docstring
from openshift_checks import OpenShiftCheck, get_var


class PortAvailability(OpenShiftCheck):
    """Check that required ports are not in use by another process."""

    name = "port_availability"
    tags = ["preflight"]

    @classmethod
    def is_active(cls, task_vars):
        return super(PortAvailability, cls).is_active(task_vars)

    def run(self, tmp, task_vars):
        required_ports = [{
            "port_name": "dnsmasq",
            "port": 53,
        }]

        args = {
            "ports": required_ports,
        }

        check_ports = self.execute_module("portavail", args, task_vars)
        if check_ports["failed"]:
            failed_ports = check_ports.get("error_ports", [])
            msg = ("The following ports are required for a successful OpenShift installation,\n"
                   "but an error occurred attempting to verify their availability:\n\n{}\n\n{}")

            msg = msg.format(
                "\n".join(
                    [
                        '  - {} (required by "{}")\n    error: {}\n'.format(
                            str(p.get("port", "n/a")),
                            p.get("port_name", "n/a"),
                            p.get("error", "n/a"),
                        )
                        for p in failed_ports
                    ]
                ),
                ('Please refer to the following article for more information\n'
                 'on freeing the required ports listed above:\n\n'
                 'https://access.redhat.com/solutions/45294')
            )

            return {"failed": True, "msg": msg}

        return {}
