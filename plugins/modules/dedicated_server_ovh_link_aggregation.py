#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function

__metaclass__ = type

from ansible.module_utils.basic import AnsibleModule
import time

DOCUMENTATION = """
---
module: dedicated_server_ovh_link_aggregation
short_description: manage OLA
description:
    - manage OVHcloud Link Aggregation 
author: Synthesio SRE Team
requirements:
    - ovh >= 0.5.0
options:
    service_name:
        required: true
        description:
        - The server to manage
    state:
        required: false
        default: private_aggragation
        choices: ['private_aggragation','reset']
        description: OLA request

"""

EXAMPLES = r"""
- name: manage OVHcloud Link Aggregation
  synthesio.ovh.dedicated_server_ovh_link_aggregation:
    service_name: "{{ service_name }}"
    state: "{{ ovh_ola_request | default("private_aggragation")}}"
  delegate_to: localhost
"""

RETURN = """ # """

from ansible_collections.synthesio.ovh.plugins.module_utils.ovh import (OVH, ovh_argument_spec)


def get_virtual_network_interfaces(service_name: str, client: OVH) -> list[str]:
    return client.wrap_call("GET", f"/dedicated/server/{service_name}/virtualNetworkInterface")


def run_ola_private_aggrgation(service_name: str, client: OVH, virtual_network_ifaces: list[str]) -> int:
    result = client.wrap_call(
        "POST",
        f"/dedicated/server/{service_name}/ola/aggregation",
        name="OLA",
        virtualNetworkInterfaces=virtual_network_ifaces)
    return result['taskId']


def run_ola_reset(service_name: str, client: OVH, virtual_network_iface: str) -> int:
    result = client.wrap_call(
        "POST",
        f"/dedicated/server/{service_name}/ola/reset",
        virtualNetworkInterface=virtual_network_iface)
    return result['taskId']


def check_task_is_done(service_name: str, task_id: int, client: OVH) -> bool:
    is_done: bool = False
    while not is_done:
        result = client.wrap_call("GET", f"/dedicated/server/{service_name}/task/{task_id}")
        if (result is not None) and (str("done").__eq__(result['status'])):
            is_done = True
            break
        time.sleep(5)
    return is_done


def run_module():
    module_args = ovh_argument_spec()
    module_args.update(
        dict(
            service_name=dict(required=True),
            state=dict(choices=['private_aggragation', 'reset'], default='private_aggragation')
        )
    )

    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)
    client = OVH(module)

    service_name = module.params["service_name"]
    state = module.params['state']
    changed = False
    ola_request_name = "private aggregation"

    if state.__eq__("reset"):
        ola_request_name = "reset"

    virtual_network_ifaces = get_virtual_network_interfaces(service_name, client)

    if len(virtual_network_ifaces) == 2 and state.__eq__("private_aggragation"):
        task_id = run_ola_private_aggrgation(service_name, virtual_network_ifaces=virtual_network_ifaces, client=client)
        changed = check_task_is_done(service_name, task_id, client)

    elif len(virtual_network_ifaces) == 1 and state.__eq__("reset"):
        task_id = run_ola_reset(service_name, client, virtual_network_ifaces[0])
        changed = check_task_is_done(service_name, task_id, client)

    elif len(virtual_network_ifaces) == 1 and state.__eq__("private_aggragation"):
        module.exit_json(
            msg="OLA {} request has already been done on dedicated server {}".format(ola_request_name, service_name), changed=changed
        )

    elif len(virtual_network_ifaces) == 2 and state.__eq__("reset"):
        module.fail_json(
            msg="OLA {} request can not be executed on dedicated server {}. " \
            "OLA private aggregation request should be requested before reset one"
            .format(ola_request_name, service_name)
        )

    else: 
        module.fail_json(
            msg="OLA {} request can not be executed on dedicated server {}. " \
            "No Virtual Network Interfaces detected"
            .format(ola_request_name, service_name)
        )

    module.exit_json(
        msg="OLA {} request is done on dedicated server {}".format(ola_request_name, service_name), changed=changed
    )


def main():
    run_module()


if __name__ == "__main__":
    main()
