from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


from ansible.module_utils.basic import AnsibleModule
from ansible_collections.synthesio.ovh.plugins.module_utils.ovh import OVH, ovh_argument_spec

def run_module():
    module_args = ovh_argument_spec()
    module_args.update(dict(
        service_name=dict(required=True),
        operating_system=dict(type="str", required=True),
        hostname=dict(type="str", required=True),
        ssh_key=dict(type="str", required=True),
        storage=dict(type="list", required=True),
        customizations=dict(required=False, type="dict", default={})
    ))

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    client = OVH(module)

    service_name = module.params['service_name']
    operating_system = module.params['operating_system']
    hostname = module.params['hostname']
    ssh_key = module.params['ssh_key']
    storage = module.params['storage']
    customizations = module.params['customizations']

    customizations['sshKey'] = ssh_key
    customizations['hostname'] = hostname

    if module.check_mode:
        module.exit_json(changed=True, msg="[CHECK_MODE] Would reinstall server with provided config")

    result = client.wrap_call(
        "POST",
        f"/dedicated/server/{service_name}/reinstall",
        operatingSystem=operating_system,
        customizations=customizations,
        storage=storage
    )

    module.exit_json(msg=f"Installation in progress on {service_name} as {hostname}!", changed=True)

def main():
    run_module()

if __name__ == '__main__':
    main()
