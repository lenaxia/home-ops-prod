import argparse
import logging
import os
from copy import deepcopy
from ruamel.yaml import YAML
import logging
import sys

LOG = logging.getLogger('app-template-upgrade')

helmReleaseNames = ["helmrelease.yaml", "helm-release.yaml"]


class MyDumper(YAML):
    def increase_indent(self, flow=False, indentless=False):
        return super(MyDumper, self).increase_indent(flow, False)

def setup_logging():
    LOG.setLevel(logging.DEBUG)
    if not LOG.handlers:  # Check if the logger already has handlers to avoid duplicate messages
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        ch.setFormatter(formatter)
        LOG.addHandler(ch)

def load_yaml_file(filepath):
    yaml = YAML()
    yaml.preserve_quotes = True
    with open(filepath, 'r') as file:
        return yaml.load(file)


def save_yaml_file(filepath, data):
    yaml = YAML()
    yaml.preserve_quotes = True
    yaml.indent(mapping=2, sequence=4, offset=2)
    with open(filepath, 'w') as file:
        yaml.dump(data, file)


def load_key(data, path):
    value = data
    for key in path.split('.'):
        if key not in value:
            return None  # Return None if the key is missing
        value = value[key]
    return value


def set_key(data, path, value):
    node = data
    split_path = path.split('.')
    index = 0
    while index < len(split_path) - 1:
        key = split_path[index]
        if not node.get(key, None):
            node[key] = {}
        node = node[key]
        index += 1

    node[split_path[index]] = value

def should_process(args, filepath, data):
    #if args.skip_version_check:
    #    LOG.info(f'Probably already upgraded as "controllers" key exists, skipping {filepath}')
    #    return False
    return load_key(data, 'spec.chart.spec.chart') == 'app-template' and load_key(data, 'spec.chart.spec.version') < '3.2.0'


def main():
    parser = argparse.ArgumentParser('app-template-upgrade')
    parser.add_argument('d', help='Directory to scan')
    parser.add_argument('-s', '--skip-version-check', action='store_true', help='Skip app-template version check, checks if key "controllers" exists')
    parser.add_argument('-y', '--yeet', help='YOLO the upgrade and process every template', action='store_true')
    args = parser.parse_args()

    for root, _, files in os.walk(args.d):
        for file in files:
            if file not in helmReleaseNames:
                continue
            filepath = os.path.join(root, file)
            try:
                data = load_yaml_file(filepath)
            except Exception as exc:
                LOG.error(f'failed to process: {filepath}, script is not good enough - will need manual intervention')
                LOG.error(f'{exc}')
                continue
            if data['kind'] != 'HelmRelease':
                continue

            LOG.info(f"Assessing {filepath}")
            if should_process(args, filepath, data):
                try:
                    LOG.info(f"Trying to process {filepath}")
                    process(filepath, data)
                except Exception as exc:
                    LOG.error(f'failed to process: {filepath}, script is not good enough - will need manual intervention', exc_info=exc)
                    LOG.error(f'{exc}')
                    continue
                if not args.yeet:
                    return


def process(filepath, data):
    new = deepcopy(data)
    new['spec']['chart']['spec']['version'] = '3.1.0'
    helm_values = new['spec'].pop('values')
    new_helm_values = deepcopy(helm_values)

    # Update ingress
    ingress_values = new_helm_values.pop('ingress', None)
    if ingress_values is not None:
        new_helm_values['ingress'] = process_ingress(ingress_values, data)

    # Update service
    service_values = new_helm_values.pop('service', None)
    if service_values is not None:
        new_helm_values['service'] = process_service(service_values, data)

    # Update persistence
    persistence_values = new_helm_values.pop('persistence', None)
    if persistence_values is not None:
        new_helm_values['persistence'] = process_persistence(persistence_values, data)

    # Update controllers
    controller_values = new_helm_values.pop('controllers', None)
    if controller_values is not None:
        new_helm_values['controllers'] = process_controllers(controller_values, data)


    new['spec']['values'] = set_key_order(new_helm_values)
    LOG.info(f"Replacing Original file: {filepath}")
    save_yaml_file(filepath, new)


def process_controllers(data, full_data):
    processed_data = {}
    for controller_name, controller_value in data.items():
        processed_init_containers = process_init_container(controller_value.get('initContainers', {}), full_data)
        if processed_init_containers:  # Check if processed_init_containers is not empty
            controller_value['initContainers'] = processed_init_containers
        processed_data[controller_name] = controller_value
    return processed_data




def process_ingress(data, full_data):
    ingress_main = data.pop('main', None)
    if ingress_main is None:
        return data

    service_identifiers = {
        svc['name']: svc for svc in full_data.get('service', {}).values()
    }

    ingress_main['hosts'] = [
        {
            'host': host_data.get('host'),
            'paths': [
                {
                    'path': path_data.get('path'),
                    'pathType': path_data.get('pathType'),
                    'service': {
                        'identifier': path_data.get('service', {}).get('name', 'main'),
                        'port': path_data.get('service', {}).get('port')
                    },
                } for path_data in host_data.get('paths', [])
            ],
        } for host_data in ingress_main.get('hosts', [])
    ]

    for host in ingress_main['hosts']:
        for path in host['paths']:
            service = path['service']
            if service['identifier'] in service_identifiers:
                service_obj = service_identifiers[service['identifier']]
                service['identifier'] = service_obj['identifier'] if 'identifier' in service_obj else service_obj['name']
            else:
                service['identifier'] = 'main'

    data['main'] = ingress_main
    return data


def process_service(data, full_data):
    controllers = full_data.get('spec', {}).get('values', {}).get('controllers', {})
    processed_data = {}

    primary_exists = False  # Flag to check if any service is marked as primary

    for service_name, service_data in data.items():
        primary = service_data.pop('primary', False)
        ports = service_data.pop('ports', {})
        processed_ports = {}

        for port_name, port_settings in ports.items():
            port = port_settings.get('port', None)  # Get port or None as default

            processed_port_info = {
                'port': port,
            }
            if 'enabled' in port_settings:
                processed_port_info['enabled'] = port_settings['enabled']
            processed_ports[port_name] = processed_port_info

        # Add the processed ports data back to the service data
        if processed_ports:
            service_data['ports'] = processed_ports
        # Add the primary key back to the service data
        service_data['primary'] = primary

        # Determine the controller for each service
        controller = service_data.pop('controller', service_name)  # Default to service name
        if controller not in controllers:
            # If specified controller does not exist, default to 'main', 'app', or the first available controller
            controller = 'main' if 'main' in controllers else 'app' if 'app' in controllers else next(iter(controllers), None)
        service_data['controller'] = controller

        # Determine the correct controller based on available controllers
        if service_name in controllers:
            controller = service_name
        elif 'main' in controllers:
            controller = 'main'
        elif 'app' in controllers:
            controller = 'app'
        else:
            controller = next(iter(controllers), None)  # Default to the first controller if none match
        service_data['controller'] = controller


        # Add the service data to the processed data
        processed_data[service_name] = service_data

        if primary:  # If this service is marked as primary
            primary_exists = True

    if not primary_exists:  # If no service was marked as primary
        if 'main' in processed_data:
            processed_data['main']['primary'] = True
        elif 'app' in processed_data:
            processed_data['app']['primary'] = True
        else:  # If neither 'main' nor 'app' exist, mark the first service as primary
            first_service_name = next(iter(processed_data))
            processed_data[first_service_name]['primary'] = True

    return processed_data





def process_persistence(data, full_data):
    allowed_keys = {
        "persistentVolumeClaim": {"enabled", "type", "accessMode", "annotations", "dataSource", "dataSourceRef",
                                  "labels", "nameOverride", "retain", "size", "storageClass", "volumeName",
                                  "existingClaim", "advancedMounts", "globalMounts"},
        "configMap": {"enabled", "type", "name", "identifier", "defaultMode", "items", "advancedMounts", "globalMounts"},
        "secret": {"enabled", "type", "name", "identifier", "defaultMode", "items", "advancedMounts", "globalMounts"},
        "nfs": {"enabled", "type", "path", "server", "advancedMounts", "globalMounts"},
        "emptyDir": {"enabled", "type", "medium", "sizeLimit", "advancedMounts", "globalMounts"},
        "hostPath": {"enabled", "type", "hostPath", "hostPathType", "advancedMounts", "globalMounts"},
        "custom": {"enabled", "type", "volumeSpec", "advancedMounts", "globalMounts"}
    }

    required_keys = {
        "persistentVolumeClaim": {"accessMode", "size"},
        "configMap": set(),
        "secret": set(),
        "nfs": {"server", "path"},
        "emptyDir": set(),
        "hostPath": set(),
        "custom": {"volumeSpec"}
    }

    conditional_required_keys = {
        "configMap": {"name", "identifier"},
        "secret": {"name", "identifier"}
    }

    controllers = full_data.get('spec', {}).get('values', {}).get('controllers', {})

    for persistence_name, persistence_values in data.items():
        if persistence_values.get('enabled', True) is False:
            continue

        if 'existingClaim' in persistence_values:
            persistence_values['type'] = 'persistentVolumeClaim'
            required_keys["persistentVolumeClaim"].discard('accessMode')
            required_keys["persistentVolumeClaim"].discard('size')
            persistence_values.pop('accessMode', None)
            persistence_values.pop('size', None)

        persistence_type = persistence_values.get("type", "custom")

        valid_keys = allowed_keys.get(persistence_type, set())
        keys_to_remove = [key for key in persistence_values if key not in valid_keys]
        for key in keys_to_remove:
            del persistence_values[key]

        missing_keys = required_keys.get(persistence_type, set()) - set(persistence_values.keys())
        for key in missing_keys:
            persistence_values.setdefault(key, None)

        if persistence_type in conditional_required_keys:
            conditional_keys = conditional_required_keys[persistence_type]
            if not any(key in persistence_values for key in conditional_keys):
                persistence_values[conditional_keys.pop()] = None

        # Access advanced_mounts directly from persistence_values
        advanced_mounts = persistence_values.setdefault("advancedMounts", {})
        advanced_mounts_updated = False
        for controller_name, controller_info in controllers.items():
            for container_type in ['initContainers', 'containers']:
                for container_name, container_details in controller_info.get(container_type, {}).items():
                    for volume_mount in container_details.get('volumeMounts', []):
                        if volume_mount['name'] == persistence_name:
                            mount_config = {"path": volume_mount["mountPath"]}
                            if "readOnly" in volume_mount:
                                mount_config["readOnly"] = volume_mount["readOnly"]
                            if "subPath" in volume_mount:
                                mount_config["subPath"] = volume_mount["subPath"]

                            controller_mounts = advanced_mounts.setdefault(controller_name, {})
                            container_mounts = controller_mounts.setdefault(container_name, [])
                            container_mounts.append(mount_config)
                            advanced_mounts_updated = True

        # Eliminate the redundant assignment
        if not advanced_mounts_updated and "advancedMounts" in persistence_values:
            del persistence_values["advancedMounts"]

    return data




def process_init_container(init_containers, full_data):
    processed_init_containers = {}
    controller_name = full_data.get('controller_name', 'main')  # Assuming default controller is 'main'
    for container_name, container_value in init_containers.items():
        data = container_value
        image = data.get('image')

        # Process image field
        if isinstance(image, str):
            image_split = image.split(':', 1)
            if len(image_split) == 2:
                data['image'] = {
                    'repository': image_split[0],
                    'tag': image_split[1],
                }
            else:
                LOG.error(f'Image format incorrect, expected "repository:tag", got: {image}')
        elif isinstance(image, dict):
            if 'repository' not in image or 'tag' not in image:
                LOG.error('Image is incorrectly formatted. Expected keys "repository" and "tag"')
        else:
            LOG.error(f'Unexpected image data type: {type(image).__name__}')

            
        # Check volumeMounts
        if 'volumeMounts' in data:
            persistence = full_data.get('persistence', {})

            all_mounts_transferred = True
            for volume_name, volume_data in persistence.items():  # Iterate over volumes in persistence
                if 'advancedMounts' in volume_data:
                    if controller_name in volume_data['advancedMounts']:
                        for volume_mount in data['volumeMounts']:
                            if volume_mount['name'] == volume_name:  # Check if volume name matches
                                if container_name in volume_data['advancedMounts'][controller_name]:
                                    if any(mount['path'] == volume_mount['mountPath'] for mount in volume_data['advancedMounts'][controller_name][container_name]):
                                        LOG.debug(f"Mount check passed for {volume_name} at {volume_mount['mountPath']}")
                                        continue  # This mount is okay
                                    else:
                                        LOG.warning(f"No matching mount path found for {volume_name} at {volume_mount['mountPath']} in advancedMounts")
                                else:
                                    LOG.warning(f"Container {container_name} not found in advancedMounts for {volume_name}")
                            else:
                                LOG.warning(f"Volume {volume_name} not found in volumeMounts data")
                                all_mounts_transferred = False
                                break
                        if not all_mounts_transferred:
                            break

            if all_mounts_transferred:
                LOG.info(f"All volume mounts for {container_name} were successfully transferred to advancedMounts. Removing volumeMounts from init container.")
                data.pop('volumeMounts')
            else:
                LOG.error(f'Not all volume mounts for {container_name} were transferred to advancedMounts.')

        processed_init_containers[container_name] = data
    return processed_init_containers


def set_key_order(data):
    order = ['defaultPodOptions', 'controllers', 'service', 'ingress', 'persistence']
    new_data = {}
    for key in order:
        if key in data:
            new_data[key] = data.pop(key)
    new_data.update(data)
    return new_data


if __name__ == "__main__":
    setup_logging()
    LOG.warning('💣 WARNING! This script may not work for everything, but will put keys into the right spot for the most part...')
    LOG.warning('💣 WARNING! Use at your own risk')
    main()
