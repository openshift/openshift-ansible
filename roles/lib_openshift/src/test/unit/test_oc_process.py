'''
 Unit tests for oc process
'''
from lib_openshift.library import oc_process

MODULE_UNDER_TEST = oc_process
CLASS_UNDER_TEST = oc_process.OCProcess

MYSQL = '''{
"kind": "Template",
"apiVersion": "v1",
"metadata": {
    "name": "mysql-ephemeral",
    "namespace": "openshift",
    "selfLink": "/oapi/v1/namespaces/openshift/templates/mysql-ephemeral",
    "uid": "fb8b5f04-e3d3-11e6-a982-0e84250fc302",
    "resourceVersion": "480",
    "creationTimestamp": "2017-01-26T14:30:27Z",
    "annotations": {
        "iconClass": "icon-mysql-database",
        "openshift.io/display-name": "MySQL (Ephemeral)",
        "tags": "database,mysql"
    }
},
"objects": [
    {
        "apiVersion": "v1",
        "kind": "Service",
        "metadata": {
            "creationTimestamp": null,
            "name": "${DATABASE_SERVICE_NAME}"
        },
        "spec": {
            "ports": [
                {
                    "name": "mysql",
                    "nodePort": 0,
                    "port": 3306,
                    "protocol": "TCP",
                    "targetPort": 3306
                }
            ],
            "selector": {
                "name": "${DATABASE_SERVICE_NAME}"
            },
            "sessionAffinity": "None",
            "type": "ClusterIP"
        },
        "status": {
            "loadBalancer": {}
        }
    },
    {
        "apiVersion": "v1",
        "kind": "DeploymentConfig",
        "metadata": {
            "creationTimestamp": null,
            "name": "${DATABASE_SERVICE_NAME}"
        },
        "spec": {
            "replicas": 1,
            "selector": {
                "name": "${DATABASE_SERVICE_NAME}"
            },
            "strategy": {
                "type": "Recreate"
            },
            "template": {
                "metadata": {
                    "creationTimestamp": null,
                    "labels": {
                        "name": "${DATABASE_SERVICE_NAME}"
                    }
                },
                "spec": {
                    "containers": [
                        {
                            "capabilities": {},
                            "env": [
                                {
                                    "name": "MYSQL_USER",
                                    "value": "${MYSQL_USER}"
                                },
                                {
                                    "name": "MYSQL_PASSWORD",
                                    "value": "${MYSQL_PASSWORD}"
                                },
                                {
                                    "name": "MYSQL_DATABASE",
                                    "value": "${MYSQL_DATABASE}"
                                }
                            ],
                            "image": " ",
                            "imagePullPolicy": "IfNotPresent",
                            "livenessProbe": {
                                "initialDelaySeconds": 30,
                                "tcpSocket": {
                                    "port": 3306
                                },
                                "timeoutSeconds": 1
                            },
                            "name": "mysql",
                            "ports": [
                                {
                                    "containerPort": 3306,
                                    "protocol": "TCP"
                                }
                            ],
                            "readinessProbe": {
                                "exec": {
                                    "command": [
                                        "/bin/sh",
                                        "-i",
                                        "-c",
                                        "MYSQL_PWD=$MYSQL_PASSWORD mysql -h 127.0.0.1 -u $MYSQL_USER -D $MYSQL_DATABASE -e 'SELECT 1'"
                                    ]
                                },
                                "initialDelaySeconds": 5,
                                "timeoutSeconds": 1
                            },
                            "resources": {
                                "limits": {
                                    "memory": "${MEMORY_LIMIT}"
                                }
                            },
                            "securityContext": {
                                "capabilities": {},
                                "privileged": false
                            },
                            "terminationMessagePath": "/dev/termination-log",
                            "volumeMounts": [
                                {
                                    "mountPath": "/var/lib/mysql/data",
                                    "name": "${DATABASE_SERVICE_NAME}-data"
                                }
                            ]
                        }
                    ],
                    "dnsPolicy": "ClusterFirst",
                    "restartPolicy": "Always",
                    "volumes": [
                        {
                            "emptyDir": {
                                "medium": ""
                            },
                            "name": "${DATABASE_SERVICE_NAME}-data"
                        }
                    ]
                }
            },
            "triggers": [
                {
                    "imageChangeParams": {
                        "automatic": true,
                        "containerNames": [
                            "mysql"
                        ],
                        "from": {
                            "kind": "ImageStreamTag",
                            "name": "mysql:${MYSQL_VERSION}",
                            "namespace": "${NAMESPACE}"
                        },
                        "lastTriggeredImage": ""
                    },
                    "type": "ImageChange"
                },
                {
                    "type": "ConfigChange"
                }
            ]
        },
        "status": {}
    }
],
"parameters": [
    {
        "name": "MEMORY_LIMIT",
        "displayName": "Memory Limit",
        "description": "Maximum amount of memory the container can use.",
        "value": "512Mi"
    },
    {
        "name": "NAMESPACE",
        "displayName": "Namespace",
        "description": "The OpenShift Namespace where the ImageStream resides.",
        "value": "openshift"
    },
    {
        "name": "DATABASE_SERVICE_NAME",
        "displayName": "Database Service Name",
        "description": "The name of the OpenShift Service exposed for the database.",
        "value": "mysql",
        "required": true
    },
    {
        "name": "MYSQL_USER",
        "displayName": "MySQL Connection Username",
        "description": "Username for MySQL user that will be used for accessing the database.",
        "generate": "expression",
        "from": "user[A-Z0-9]{3}",
        "required": true
    },
    {
        "name": "MYSQL_PASSWORD",
        "displayName": "MySQL Connection Password",
        "description": "Password for the MySQL connection user.",
        "generate": "expression",
        "from": "[a-zA-Z0-9]{16}",
        "required": true
    },
    {
        "name": "MYSQL_DATABASE",
        "displayName": "MySQL Database Name",
        "description": "Name of the MySQL database accessed.",
        "value": "sampledb",
        "required": true
    },
    {
        "name": "MYSQL_VERSION",
        "displayName": "Version of MySQL Image",
        "description": "Version of MySQL image to be used (5.5, 5.6 or latest).",
        "value": "5.6",
        "required": true
    }
],
"labels": {
    "template": "mysql-ephemeral-template"
}
}'''


def test_state_list(mock_run_cmd):
    ''' Testing a get '''
    params = {'template_name': 'mysql-ephermeral',
              'namespace': 'test',
              'content': None,
              'state': 'list',
              'reconcile': False,
              'create': False,
              'params': {'NAMESPACE': 'test', 'DATABASE_SERVICE_NAME': 'testdb'},
              'kubeconfig': '/etc/origin/master/admin.kubeconfig',
              'debug': False}

    mock_run_cmd.side_effect = [
        (0, MYSQL, '')
    ]

    results = CLASS_UNDER_TEST.run_ansible(params, False)

    assert results['changed'] is False
    assert results['results']['results'][0]['metadata']['name'] == 'mysql-ephemeral'


def test_process_no_create(mock_run_cmd):
    ''' Testing a process with no create '''
    params = {'template_name': 'mysql-ephermeral',
              'namespace': 'test',
              'content': None,
              'state': 'present',
              'reconcile': False,
              'create': False,
              'params': {'NAMESPACE': 'test', 'DATABASE_SERVICE_NAME': 'testdb'},
              'kubeconfig': '/etc/origin/master/admin.kubeconfig',
              'debug': False}

    mysqlproc = '''{
"kind": "List",
"apiVersion": "v1",
"metadata": {},
"items": [
    {
        "apiVersion": "v1",
        "kind": "Service",
        "metadata": {
            "creationTimestamp": null,
            "labels": {
                "template": "mysql-ephemeral-template"
            },
            "name": "testdb"
        },
        "spec": {
            "ports": [
                {
                    "name": "mysql",
                    "nodePort": 0,
                    "port": 3306,
                    "protocol": "TCP",
                    "targetPort": 3306
                }
            ],
            "selector": {
                "name": "testdb"
            },
            "sessionAffinity": "None",
            "type": "ClusterIP"
        },
        "status": {
            "loadBalancer": {}
        }
    },
    {
        "apiVersion": "v1",
        "kind": "DeploymentConfig",
        "metadata": {
            "creationTimestamp": null,
            "labels": {
                "template": "mysql-ephemeral-template"
            },
            "name": "testdb"
        },
        "spec": {
            "replicas": 1,
            "selector": {
                "name": "testdb"
            },
            "strategy": {
                "type": "Recreate"
            },
            "template": {
                "metadata": {
                    "creationTimestamp": null,
                    "labels": {
                        "name": "testdb"
                    }
                },
                "spec": {
                    "containers": [
                        {
                            "capabilities": {},
                            "env": [
                                {
                                    "name": "MYSQL_USER",
                                    "value": "userHJJ"
                                },
                                {
                                    "name": "MYSQL_PASSWORD",
                                    "value": "GITOAduAMaV6k688"
                                },
                                {
                                    "name": "MYSQL_DATABASE",
                                    "value": "sampledb"
                                }
                            ],
                            "image": " ",
                            "imagePullPolicy": "IfNotPresent",
                            "livenessProbe": {
                                "initialDelaySeconds": 30,
                                "tcpSocket": {
                                    "port": 3306
                                },
                                "timeoutSeconds": 1
                            },
                            "name": "mysql",
                            "ports": [
                                {
                                    "containerPort": 3306,
                                    "protocol": "TCP"
                                }
                            ],
                            "readinessProbe": {
                                "exec": {
                                    "command": [
                                        "/bin/sh",
                                        "-i",
                                        "-c",
                                        "MYSQL_PWD=$MYSQL_PASSWORD mysql -h 127.0.0.1 -u $MYSQL_USER -D $MYSQL_DATABASE -e 'SELECT 1'"
                                    ]
                                },
                                "initialDelaySeconds": 5,
                                "timeoutSeconds": 1
                            },
                            "resources": {
                                "limits": {
                                    "memory": "512Mi"
                                }
                            },
                            "securityContext": {
                                "capabilities": {},
                                "privileged": false
                            },
                            "terminationMessagePath": "/dev/termination-log",
                            "volumeMounts": [
                                {
                                    "mountPath": "/var/lib/mysql/data",
                                    "name": "testdb-data"
                                }
                            ]
                        }
                    ],
                    "dnsPolicy": "ClusterFirst",
                    "restartPolicy": "Always",
                    "volumes": [
                        {
                            "emptyDir": {
                                "medium": ""
                            },
                            "name": "testdb-data"
                        }
                    ]
                }
            },
            "triggers": [
                {
                    "imageChangeParams": {
                        "automatic": true,
                        "containerNames": [
                            "mysql"
                        ],
                        "from": {
                            "kind": "ImageStreamTag",
                            "name": "mysql:5.6",
                            "namespace": "test"
                        },
                        "lastTriggeredImage": ""
                    },
                    "type": "ImageChange"
                },
                {
                    "type": "ConfigChange"
                }
            ]
        }
    }
]
}'''

    mock_run_cmd.side_effect = [
        (0, MYSQL, ''),
        (0, MYSQL, ''),
        (0, mysqlproc, ''),
    ]

    results = CLASS_UNDER_TEST.run_ansible(params, False)

    assert results['changed'] is False
    assert results['results']['results']['items'][0]['metadata']['name'] == 'testdb'
