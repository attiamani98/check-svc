import asyncio
import socket
from kubernetes import client, config
import logging
from prometheus_client import start_http_server, Gauge, Counter

# Load Kubernetes configuration
config.load_incluster_config()
v1 = client.CoreV1Api()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Prometheus metrics
# Prometheus metrics
service_status_gauge = Gauge('service_status', 'Service check status', ['service', 'namespace', 'port', 'check_type'])
log_counter = Counter('service_log_count', 'Number of log entries', ['service', 'namespace', 'level'])

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

    # Assuming logs are retrieved from Kubernetes API or some other method
    logs = fetch_logs_for_service(name, namespace)  # Replace with your method to fetch logs

    for log in logs.split("\n"):
        if "WARNING" in log:
            log_counter.labels(service=name, namespace=namespace, level='warning').inc()
        elif "INFO" in log:
            log_counter.labels(service=name, namespace=namespace, level='info').inc()
        # Add more conditions as needed for different log levels or types

    if service.spec.ports is not None:
        for port_spec in service.spec.ports:
            port = port_spec.port
            hostname_check = await check_connection(cluster_local_hostname, port)
            ip_check = await check_connection(ip_address, port)

            service_status_gauge.labels(service=name, namespace=namespace, port=port, check_type='hostname').set(int(hostname_check))
            service_status_gauge.labels(service=name, namespace=namespace, port=port, check_type='ip').set(int(ip_check))

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
    start_http_server(8000)  # Start the Prometheus metrics server on port 8000

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
