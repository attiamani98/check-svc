import asyncio
import socket
from kubernetes import client, config
import logging

# Load Kubernetes configuration
config.load_incluster_config()
v1 = client.CoreV1Api()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

async def check_connection(hostname, port):
    try:
        reader, writer = await asyncio.open_connection(hostname, port)
        writer.close()
        await writer.wait_closed()
        return True
    except Exception as e:
        return False

async def check_service(service):
    namespace = service.metadata.namespace
    name = service.metadata.name
    cluster_local_hostname = f'{name}.{namespace}.svc.cluster.local'
    ip_address = service.spec.cluster_ip

    results = {
        'service': name,
        'namespace': namespace,
        'hostname': cluster_local_hostname,
        'ip_address': ip_address,
        'ports': []
    }

    if service.spec.ports is not None:
        for port_spec in service.spec.ports:
            port = port_spec.port
            hostname_check = await check_connection(cluster_local_hostname, port)
            ip_check = await check_connection(ip_address, port)
            results['ports'].append({
                'port': port,
                'hostname_check': hostname_check,
                'ip_check': ip_check
            })
    else:
        logging.warning(f"No ports defined for service {name} in namespace {namespace}")

    logging.info(f"Check results for service {name} in namespace {namespace}: {results}")
    return results

async def main():
    while True:
        services = v1.list_service_for_all_namespaces().items
        tasks = [check_service(service) for service in services]
        results = await asyncio.gather(*tasks)

        for result in results:
            logging.info(result)

        # Wait for 5 minutes before checking again
        await asyncio.sleep(300)

if __name__ == '__main__':
    asyncio.run(main())
