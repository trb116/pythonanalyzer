import yaml
from copy import deepcopy
import util
from project import Project
from service import Service
from exceptions import AlaudaInputError
import os


def load_project(filepath, namespace, region):
    abspath = os.path.abspath(filepath)
    compose_data = _load_yaml(abspath)
    vertex_list = [abspath]
    edge_list = []
    resolve_extends(compose_data, abspath, vertex_list, edge_list)
    services = load_services(compose_data, namespace, region)
    project = Project(services)
    return project


def _get_linked_services(link_list):
    parsed_links = util.parse_links(link_list)
    return [x[0] for x in parsed_links]


def sort_services(compose_data):
    src_dict = compose_data.copy()
    src_keys = src_dict.keys()
    sorted_list = []
    while len(src_dict) > 0:
        for key, value in src_dict.items():
            links = _get_linked_services(value.get('links'))
            if links is None:
                sorted_list.append(key)
                del src_dict[key]
            elif not set(links).issubset(set(src_keys)):
                raise AlaudaInputError("{} has invalid link name".format(links))
            elif set(links).issubset(set(sorted_list)):
                sorted_list.append(key)
                del src_dict[key]
            else:
                continue
    return sorted_list


def toposort_services(compose_data):
    service_vertex = []
    service_edge = []
    src_keys = compose_data.keys()
    for key, value in compose_data.items():
        links = _get_linked_services(value.get('links'))
        if key not in service_vertex:
            service_vertex.append(key)
        if not set(links).issubset(set(src_keys)):
            raise AlaudaInputError("{} has invalid link name".format(links))
        else:
            for link in links:
                if link not in service_vertex:
                    service_vertex.append(link)
                service_edge.append((link, key))
    sorted_result = util.topoSort(service_vertex, service_edge)
    if sorted_result == -1:
        raise AlaudaInputError("there is a circle in your service depended list")
    return sorted_result


def load_services(compose_data, namespace, region):
    sorted_services = []
    sorted_list = toposort_services(compose_data)
    for services in sorted_list:
        service_list = []
        for service_name in services:
            service = load_service(service_name, compose_data[service_name], namespace, region)
            service_list.append(service)
        sorted_services.append(service_list)
    return sorted_services


def load_service(service_name, service_data, namespace, region):
    image = service_data.get('image')
    if not image:
        raise AlaudaInputError('Compose file must specify image')
    image_name, image_tag = util.parse_image_name_tag(image)
    ports = load_ports(service_data)
    run_command = load_command(service_data)
    links = load_links(service_data)
    volumes = load_volumes(service_data)
    envvars = load_envvars(service_data)
    domain = load_domain(service_data)
    instance_num, instance_size = load_instance(service_data)
    scaling_mode, autoscaling_config = load_scaling_info(service_data)
    service = Service(name=service_name,
                      image_name=image_name,
                      image_tag=image_tag,
                      run_command=run_command,
                      instance_envvars=envvars,
                      instance_ports=ports,
                      volumes=volumes,
                      links=links,
                      target_num_instances=instance_num,
                      instance_size=instance_size,
                      namespace=namespace,
                      scaling_mode=scaling_mode,
                      autoscaling_config=autoscaling_config,
                      custom_domain_name=domain,
                      region_name=region)
    return service


def load_domain(service_data):
    return service_data.get('domain', '')


def load_instance(service_data):
    size = service_data.get('size', 'XS')
    number = service_data.get('number', 1)
    return number, size


def load_scaling_info(service_data):
    autoscaling_config = service_data.get('autoscaling_config')
    if autoscaling_config is None:
        return util.parse_autoscale_info(None)
    return util.parse_autoscale_info((True, autoscaling_config))


def load_links(service_data):
    return util.parse_links(service_data.get('links'))


def load_ports(service_data):
    instance_ports, port_list = util.parse_instance_ports(service_data.get('ports'))
    expose_list = util.merge_internal_external_ports(port_list, service_data.get('expose', []))
    instance_ports.extend(expose_list)
    return instance_ports


def load_command(service_data):
    return service_data.get('command', '')


def load_volumes(service_data):
    return util.parse_volumes(service_data.get('volumes'))


def load_envvars(service_data):
    return util.parse_envvars(service_data.get('environment'))


def resolve_extends(compose_data, file_name, vertex_list, edge_list):
    for local_service_name, local_service_data in compose_data.items():
        if 'extends' in local_service_data.keys():
            extends = local_service_data['extends']
            extends_file_name = os.path.abspath(extends['file'])
            original_service_name = extends['service']
            if extends_file_name not in vertex_list:
                vertex_list.append(extends_file_name)
            edge = (file_name, extends_file_name)
            if edge not in edge_list:
                edge_list.append(edge)
            vertex_list_tmp = deepcopy(vertex_list)
            edge_list_tmp = deepcopy(edge_list)
            result = util.topoSort(vertex_list_tmp, edge_list_tmp)
            if result is None:
                raise AlaudaInputError('There is a circular dependency in extends definitions')
            original_compose_data = _load_yaml(extends_file_name)
            resolve_extends(original_compose_data, extends_file_name, vertex_list, edge_list)
            original_service_data = original_compose_data[original_service_name]
            for key, value in original_service_data.items():
                if key == 'links' or key == 'volumes_from':
                    continue
                elif key == 'ports':
                    merge_ports(local_service_data, value)
                elif key == 'expose':
                    merge_expose(local_service_data, value)
                elif key == 'environment':
                    merge_environment(local_service_data, value)
                elif key == 'volumes':
                    merge_volumes(local_service_data, value)
                elif key not in local_service_data.keys():
                    local_service_data[key] = value
                else:
                    continue


def merge_ports(local_service_data, original_ports):
    pass


def merge_expose(local_service_data, original_expose):
    if local_service_data.get('expose') is None:
        local_service_data['expose'] = original_expose
    else:
        local_service_data['expose'] += [v for v in original_expose if v not in local_service_data['expose']]


def merge_environment(local_service_data, original_environment):
    if local_service_data.get('environment') is None:
        local_service_data['environment'] = original_environment
    else:
        local_envs = util.parse_envvars(local_service_data['environment'])
        for env in original_environment:
            key, _ = util.parse_envvar(env)
            if key not in local_envs.keys():
                local_service_data['environment'].append(env)


def merge_volumes(local_service_data, original_volumes):
    pass


def _load_yaml(filepath):
    try:
        with open(filepath, 'r') as f:
            return yaml.safe_load(f)
    except:
        raise AlaudaInputError('Missing or invalid compose yaml file at {}.'.format(filepath))
