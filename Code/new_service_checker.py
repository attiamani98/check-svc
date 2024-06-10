import asyncio
import socket
from kubernetes import client, config
import logging
from flask import Flask, Response
from prometheus_client import Gauge, generate_latest, CollectorRegistry, CONTENT_TYPE_LATEST

# Load Kubernetes configuration
config.load_incluster_config()
v1 = client.CoreV1Api()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Create Flask app
app = Flask(__name__)

# Prometheus metrics
registry = CollectorRegistry()
successful_checks = Gauge('successful_checks', 'Number of successful service checks', ['service', 'namespace', 'port'], registry=registry)
failed_checks = Gauge('failed_checks', 'Number of failed service checks', ['service', 'namespace', 'port'], registry=registry)

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

            if hostname_check and ip_check:
                successful_checks.labels(service=name, namespace=namespace, port=port).inc()
            else:
                failed_checks.labels(service=name, namespace=namespace, port=port).inc()

            results['ports'].append({
                'port': port,
                'hostname_check': hostname_check,
                'ip_check': ip_check
            })
    else:
        logging.warning(f"No ports defined for service {name} in namespace {namespace}")

    logging.info(f"Check results for service {name} in namespace {namespace}: {results}")
    return results

@app.route('/metrics')
def metrics():
    return Response(generate_latest(registry), mimetype=CONTENT_TYPE_LATEST)

@app.route('/')
async def main():
    services = v1.list_service_for_all_namespaces().items
    tasks = [check_service(service) for service in services]
    results = await asyncio.gather(*tasks)

    for result in results:
        logging.info(result)

    return "ok is working"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
