from kubernetes import client, config, watch
config.load_kube_config()
v1 = client.CoreV1Api()
def main():
    # Configs can be set in Configuration class directly or using helper
    # utility. If no argument provided, the config will be loaded from
    # default location.

    count = 10
    w = watch.Watch()
    for event in w.stream(v1.list_namespace, timeout_seconds=10):
        print("Event: %s %s" % (event['type'], event['object'].metadata.name))
        count -= 1
        if not count:
            w.stop()
    print("Finished namespace stream.")

    for event in w.stream(v1.list_pod_for_all_namespaces, timeout_seconds=10):
        print("Event: %s %s %s" % (
            event['type'],
            event['object'].kind,
            event['object'].metadata.name)
        )
        count -= 1
        if not count:
            w.stop()
    print("Finished pod stream.")

def get_pods():  
    test = v1.list_namespaced_service
    print(test)
    pod_list = v1.list_namespaced_pod("default")
    for pod in pod_list.items:
        print("%s\t%s\t%s" % (pod.metadata.name,
                              pod.status.phase,
                              pod.status.pod_ip))
        
def get_services():
    services = v1.list_service_for_all_namespaces(watch=False)
    for svc in services.items:
        if svc.spec.selector:
            # convert the selector dictionary into a string selector
            # for example: {"app":"redis"} => "app=redis"
            selector = ''
            for k,v in svc.spec.selector.items():
                selector += k + '=' + v + ','
            selector = selector[:-1]

            # Get the pods that match the selector
            pods = v1.list_pod_for_all_namespaces(label_selector=selector)
            for pod in pods.items:
                print(pod.metadata.name)
if __name__ == '__main__':
   get_pods()