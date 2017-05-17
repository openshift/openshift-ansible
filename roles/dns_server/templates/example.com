; {{ dns_domain }} {{ view_type }} view
@		IN SOA	dns.{{ dns_domain }}. hostmaster.{{ dns_domain }}. (
				{{ zone_serial }} ; serial
				60         ; refresh (1 minute)
				15         ; retry (15 seconds)
				1800       ; expire (30 minutes)
				10         ; minimum (10 seconds)
				)
			NS	dns.{{ dns_domain }}.
			MX	10 mail.{{ dns_domain }}.

$TTL 600	; 10 minutes

{% for host in groups['all'] %}
{% if view_type == 'internal' %}
{{ hostvars[host].openshift.common.hostname }}. IN A    {{ hostvars[host].openshift.common.ip }}
{% else %}
{{ hostvars[host].openshift.common.hostname }}. IN A    {{ hostvars[host].openshift.common.public_ip }}
{% endif %}
{% endfor %}

; This is where the router(s) run
; FIXME: who do we point to by default
*.apps		IN CNAME	ose3-node2
