import docker
import time
import psutil
import requests
import atexit

client = docker.from_env()
lb_url = "http://localhost:80"  # Load balancer URL

# Thresholds
T_UPPER = 70  # 70%
T_LOWER = 30  # 30%
MAX_CONTAINERS = 5
MIN_CONTAINERS = 1

max_cpu_cores = 10

def get_container_stats(container):
    try:
        stats = container.stats(stream=False)
        cpu_usage = 0
        try:
            if all(key in stats["cpu_stats"] for key in ["cpu_usage", "online_cpus"]) and \
               all(key in stats["precpu_stats"] for key in ["cpu_usage"]) and \
               "total_usage" in stats["cpu_stats"]["cpu_usage"] and \
               "total_usage" in stats["precpu_stats"]["cpu_usage"]:
                
                if "system_cpu_usage" in stats["cpu_stats"] and "system_cpu_usage" in stats["precpu_stats"]:
                    cpu_delta = stats["cpu_stats"]["cpu_usage"]["total_usage"] - stats["precpu_stats"]["cpu_usage"]["total_usage"]
                    system_delta = stats["cpu_stats"]["system_cpu_usage"] - stats["precpu_stats"]["system_cpu_usage"]
                    
                    if system_delta > 0:
                        cpu_usage = (cpu_delta / system_delta) * 100.0 * stats["cpu_stats"]["online_cpus"]
                else:
                    cpu_delta = stats["cpu_stats"]["cpu_usage"]["total_usage"] - stats["precpu_stats"]["cpu_usage"]["total_usage"]
                    
                    online_cpus = stats["cpu_stats"].get("online_cpus", 1)
                    cpu_usage = (cpu_delta / (10**9)) * 100.0  
        except (KeyError, ZeroDivisionError) as e:
            print(f"Error calculating CPU usage for {container.name}: {e}")
            cpu_usage = 0
        
        mem_usage = 0
        try:
            if "memory_stats" in stats and "usage" in stats["memory_stats"] and "limit" in stats["memory_stats"]:
                if stats["memory_stats"]["limit"] > 0:  # Avoid division by zero
                    mem_usage = (stats["memory_stats"]["usage"] / stats["memory_stats"]["limit"]) * 100.0
        except (KeyError, ZeroDivisionError) as e:
            print(f"Error calculating memory usage for {container.name}: {e}")
            mem_usage = 0
        
        print(f"Stats:: Container {container.name} (ID: {container.short_id}) - CPU: {cpu_usage:.2f}%, Memory: {mem_usage:.2f}%")
        return cpu_usage, mem_usage
    
    except Exception as e:
        print(f"Fatal error getting stats for {container.name}: {e}")
        return T_LOWER + 10, T_LOWER + 10
    


def update_load_balancer():
    containers = client.containers.list(filters={"ancestor": "prime-service"})
    print(f"current containers : ", containers)
    ports = [f'http://localhost:{c.attrs["HostConfig"]["PortBindings"]["5000/tcp"][0]["HostPort"]}' for c in containers]
    requests.post(f"{lb_url}/update_containers", json=ports)

def scale_containers():
    containers = client.containers.list(filters={"ancestor": "prime-service"})
    current_count = len(containers)
    
    print(f"Current containers count ({current_count}):")
    for c in containers:
        print(f"  - {c.name} (ID: {c.short_id})")

    scaling_action_taken = False
    
    for container in containers:
        cpu, mem = get_container_stats(container)
        
        # Scale UP
        if (cpu > T_UPPER or mem > T_UPPER) and current_count < MAX_CONTAINERS:
            try:
                new_container = client.containers.run(
                    "prime-service", 
                    detach=True, 
                    ports={'5000/tcp': None},
                    environment={"CONTAINER_ID": f"container_{current_count+1}"}
                )
                current_count += 1
                scaling_action_taken = True
                print(f"Created new container: {new_container.name} (ID: {new_container.short_id})")
                print(f"Total containers now: {current_count}")
                print(f"Scaling reason: CPU={cpu:.2f}%, Memory={mem:.2f}%")
            except Exception as e:
                print(f"Error creating new container: {e}")
        
        # Scale DOWN
        elif cpu < T_LOWER and mem < T_LOWER and current_count > MIN_CONTAINERS:
            try:
                container_name = container.name
                container_id = container.short_id
                container.stop()
                container.remove() 
                current_count -= 1
                scaling_action_taken = True
                print(f"Stopped and removed container: {container_name} (ID: {container_id})")
                print(f"Total containers now: {current_count}")
                print(f"Scaling reason: CPU={cpu:.2f}%, Memory={mem:.2f}%")
            except Exception as e:
                print(f"Error stopping container: {e}")

    if scaling_action_taken:
        try:
            update_load_balancer()
            print("Load balancer updated with new container configuration")
        except Exception as e:
            print(f"Error updating load balancer: {e}")
    
    print("-" * 50)

def cleanup_containers():
    containers = client.containers.list(filters={"ancestor": "prime-service"})
    for container in containers:
        try:
            container.stop()
            container.remove()
            print(f"Stopped and removed container: {container.name} (ID: {container.short_id})")
        except Exception as e:
            print(f"Error stopping/removing container {container.name}: {e}")

# Register the cleanup function to be called when the script exits
atexit.register(cleanup_containers)

if __name__ == '__main__':
    try:
        client.containers.run(
            "prime-service",
            detach=True, 
            ports={'5000/tcp': 5000},
            environment={"CONTAINER_ID": "container_1"}
        )

        update_load_balancer()
        
        while True:
            scale_containers()
            time.sleep(1)
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        # Ensure cleanup is called even if there's an exception in the main loop
        cleanup_containers()