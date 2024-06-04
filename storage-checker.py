from kubernetes import client, config
from kubernetes.client.rest import ApiException
import time
import logging

# Load the in-cluster configuration
config.load_incluster_config()

v1 = client.CoreV1Api()
storage_v1 = client.StorageV1Api()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def list_storage_classes():
    try:
        scs = storage_v1.list_storage_class()
        return scs.items
    except ApiException as e:
        logger.error("Exception when listing storage classes: %s", e)
        return []

def create_pvc(storage_class_name):
    pvc_manifest = {
        "apiVersion": "v1",
        "kind": "PersistentVolumeClaim",
        "metadata": {"name": f"test-pvc-{storage_class_name}"},
        "spec": {
            "accessModes": ["ReadWriteOnce"],
            "resources": {"requests": {"storage": "1Gi"}},
            "storageClassName": storage_class_name,
        },
    }

    try:
        pvc = v1.create_namespaced_persistent_volume_claim(namespace="monitoring", body=pvc_manifest)
        return pvc
    except ApiException as e:
        logger.error("Exception when creating PVC for storage class %s: %s", storage_class_name, e)
        return None

def check_pvc_bound(pvc_name):
    try:
        pvc = v1.read_namespaced_persistent_volume_claim(name=pvc_name, namespace="default")
        return pvc.status.phase == "Bound"
    except ApiException as e:
        logger.error("Exception when reading PVC %s: %s", pvc_name, e)
        return False

def delete_pvc(pvc_name):
    try:
        v1.delete_namespaced_persistent_volume_claim(name=pvc_name, namespace="default")
    except ApiException as e:
        logger.error("Exception when deleting PVC %s: %s", pvc_name, e)

def main():
    storage_classes = list_storage_classes()
    if not storage_classes:
        logger.info("No storage classes found.")
        return

    for sc in storage_classes:
        sc_name = sc.metadata.name
        logger.info("Testing storage class: %s", sc_name)

        pvc = create_pvc(sc_name)
        if pvc:
            time.sleep(10)  # Wait a bit for PVC to get bound

            if check_pvc_bound(pvc.metadata.name):
                logger.info("PVC for storage class %s is bound.", sc_name)
            else:
                logger.info("PVC for storage class %s is not bound.", sc_name)

            delete_pvc(pvc.metadata.name)
            logger.info("PVC for storage class %s deleted.", sc_name)
        else:
            logger.error("Failed to create PVC for storage class %s.", sc_name)

if __name__ == "__main__":
    main()
