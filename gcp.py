import logging
import os
from google.cloud import compute_v1
from google.cloud import storage
from google.oauth2 import service_account
from googleapiclient import discovery
from googleapiclient.errors import HttpError
import time

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def initialize_clients():
    """
    Initialize GCP clients for Compute Engine and Cloud Storage using service account credentials.
    """
    try:
        # Path to your service account key file
        key_path = "C:\\Users\\naman\\Downloads\\watchful-slice-443014-f0-34fb313928ed.json"  # Update this path

        if not os.path.exists(key_path):
            logger.error(f"Service account key file not found at: {key_path}")
            return None, None

        # Initialize credentials
        credentials = service_account.Credentials.from_service_account_file(key_path)

        # Initialize Compute Engine client with credentials
        compute_client = compute_v1.InstancesClient(credentials=credentials)

        # Initialize Cloud Storage client with credentials and project ID
        project_id = 'watchful-slice-443014-f0'  # Replace with your actual project ID
        storage_client = storage.Client(credentials=credentials, project=project_id)

        logger.info("Successfully initialized Compute Engine and Cloud Storage clients.")
        return compute_client, storage_client
    except Exception as e:
        logger.error(f"Failed to initialize GCP clients: {e}")
        return None, None

def wait_for_operation(compute_client, project, zone, operation_name):
    """
    Wait for a Compute Engine operation to complete.

    Args:
        compute_client: Compute Engine client.
        project (str): GCP project ID.
        zone (str): Compute Engine zone.
        operation_name (str): Name of the operation.
    """
    try:
        while True:
            result = compute_client.get_zone_operation(project=project, zone=zone, operation=operation_name)
            if result.status == compute_v1.Operation.Status.DONE:
                if result.error:
                    raise Exception(result.error)
                return
            else:
                time.sleep(1)
    except Exception as e:
        logger.error(f"Error while waiting for operation {operation_name}: {e}")

def create_instance(project, zone, instance_name, machine_type, source_image, network='default'):
    """
    Create a Compute Engine instance.

    Args:
        project (str): GCP project ID.
        zone (str): Compute Engine zone.
        instance_name (str): Name of the instance.
        machine_type (str): Machine type, e.g., 'n1-standard-1'.
        source_image (str): Image to use for the instance.
        network (str): Network name.

    Returns:
        str: Instance name if created successfully, else None.
    """
    try:
        compute_client, _ = initialize_clients()
        if not compute_client:
            return None

        instance = compute_v1.Instance()
        instance.name = instance_name
        instance.machine_type = f"zones/{zone}/machineTypes/{machine_type}"

        # Configure the boot disk
        initialize_params = compute_v1.AttachedDiskInitializeParams()
        initialize_params.source_image = source_image
        initialize_params.disk_size_gb = 10

        disk = compute_v1.AttachedDisk()
        disk.boot = True
        disk.auto_delete = True
        disk.type_ = compute_v1.AttachedDisk.Type.PERSISTENT
        disk.initialize_params = initialize_params

        instance.disks = [disk]

        # Configure the network interface
        network_interface = compute_v1.NetworkInterface()
        network_interface.network = f"projects/{project}/global/networks/{network}"
        network_interface.access_configs = [compute_v1.AccessConfig(
            name="External NAT",
            type_=compute_v1.AccessConfig.Type.ONE_TO_ONE_NAT
        )]
        instance.network_interfaces = [network_interface]

        # Insert the instance
        operation = compute_client.insert(
            project=project,
            zone=zone,
            instance_resource=instance
        )
        wait_for_operation(compute_client, project, zone, operation.name)
        logger.info(f"Successfully created instance: {instance_name}")
        return instance_name
    except Exception as e:
        logger.error(f"Failed to create instance: {e}")
        return None

def list_instances(project, zone):
    """
    List all running Compute Engine instances.

    Args:
        project (str): GCP project ID.
        zone (str): Compute Engine zone.

    Returns:
        list: List of running instance names.
    """
    try:
        compute_client, _ = initialize_clients()
        if not compute_client:
            return []

        request = compute_v1.ListInstancesRequest(project=project, zone=zone)
        response = compute_client.list(request=request)

        instances = []
        for instance in response:
            if instance.status == compute_v1.Instance.Status.RUNNING:
                instances.append(instance.name)

        logger.info(f"Running instances in zone {zone}: {instances}")
        return instances
    except Exception as e:
        logger.error(f"Failed to list instances: {e}")
        return []

def terminate_instance(project, zone, instance_name):
    """
    Terminate (delete) a Compute Engine instance.

    Args:
        project (str): GCP project ID.
        zone (str): Compute Engine zone.
        instance_name (str): Name of the instance to terminate.
    """
    try:
        compute_client, _ = initialize_clients()
        if not compute_client:
            return

        operation = compute_client.delete(
            project=project,
            zone=zone,
            instance=instance_name
        )
        wait_for_operation(compute_client, project, zone, operation.name)
        logger.info(f"Successfully terminated instance: {instance_name}")
    except Exception as e:
        logger.error(f"Failed to terminate instance: {e}")

def create_storage_bucket(bucket_name, location='US', storage_class='STANDARD'):
    """
    Create a Cloud Storage bucket.

    Args:
        bucket_name (str): Name of the bucket.
        location (str): Location of the bucket, e.g., 'US', 'EU'.
        storage_class (str): Storage class, e.g., 'STANDARD', 'NEARLINE'.

    Returns:
        Bucket: The created bucket object or None if failed.
    """
    try:
        _, storage_client = initialize_clients()
        if not storage_client:
            return None

        bucket = storage_client.bucket(bucket_name)
        bucket.storage_class = storage_class
        new_bucket = storage_client.create_bucket(bucket, location=location)
        logger.info(f"Successfully created bucket: {new_bucket.name}")
        return new_bucket
    except Exception as e:
        logger.error(f"Failed to create bucket: {e}")
        return None

def list_storage_buckets():
    """
    List all Cloud Storage buckets in the project.

    Returns:
        list: List of bucket names.
    """
    try:
        _, storage_client = initialize_clients()
        if not storage_client:
            return []

        buckets = list(storage_client.list_buckets())
        bucket_names = [bucket.name for bucket in buckets]
        logger.info(f"Cloud Storage Buckets: {bucket_names}")
        return bucket_names
    except Exception as e:
        logger.error(f"Failed to list buckets: {e}")
        return []

def upload_file_to_storage(bucket_name, source_file, destination_blob_name=None):
    """
    Upload a file to a Cloud Storage bucket.

    Args:
        bucket_name (str): Name of the bucket.
        source_file (str): Path to the source file.
        destination_blob_name (str): Destination blob name. If None, uses the source file name.

    Returns:
        bool: True if uploaded successfully, else False.
    """
    try:
        _, storage_client = initialize_clients()
        if not storage_client:
            return False

        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(destination_blob_name or os.path.basename(source_file))

        blob.upload_from_filename(source_file)
        logger.info(f"Successfully uploaded {source_file} to bucket '{bucket_name}' as '{blob.name}'.")
        return True
    except Exception as e:
        logger.error(f"Failed to upload file to storage: {e}")
        return False

def delete_storage_bucket(bucket_name):
    """
    Delete a Cloud Storage bucket and all its contents.

    Args:
        bucket_name (str): Name of the bucket.
    """
    try:
        _, storage_client = initialize_clients()
        if not storage_client:
            return

        bucket = storage_client.bucket(bucket_name)
        # Delete all objects in the bucket
        blobs = list(bucket.list_blobs())
        for blob in blobs:
            blob.delete()
            logger.info(f"Deleted blob: {blob.name}")

        # Delete the bucket
        bucket.delete()
        logger.info(f"Successfully deleted bucket: {bucket_name}")
    except Exception as e:
        logger.error(f"Failed to delete bucket: {e}")

def create_load_balancer(project, bucket_name, backend_bucket_name, domain_name):
    """
    Create a load balancer with Cloud CDN enabled to serve content from a Cloud Storage bucket.

    Args:
        project (str): GCP project ID.
        bucket_name (str): Name of the Cloud Storage bucket.
        backend_bucket_name (str): Name for the backend bucket.
        domain_name (str): Domain name for the load balancer.

    Returns:
        str: Load balancer's IP address or None if failed.
    """
    try:
        service = discovery.build('compute', 'v1')

        # Step 1: Create Backend Bucket
        backend_bucket_body = {
            "name": backend_bucket_name,
            "bucketName": bucket_name,
            "enableCdn": True
        }
        service.backendBuckets().insert(project=project, body=backend_bucket_body).execute()
        logger.info(f"Backend bucket '{backend_bucket_name}' created.")

        # Step 2: Create URL Map
        url_map_body = {
            "name": "url-map-" + backend_bucket_name,
            "defaultService": f"projects/{project}/global/backendBuckets/{backend_bucket_name}"
        }
        service.urlMaps().insert(project=project, body=url_map_body).execute()
        logger.info(f"URL map 'url-map-{backend_bucket_name}' created.")

        # Step 3: Create Target HTTP Proxy
        target_http_proxy_body = {
            "name": "target-http-proxy-" + backend_bucket_name,
            "urlMap": f"projects/{project}/global/urlMaps/url-map-{backend_bucket_name}"
        }
        service.targetHttpProxies().insert(project=project, body=target_http_proxy_body).execute()
        logger.info(f"Target HTTP proxy 'target-http-proxy-{backend_bucket_name}' created.")

        # Step 4: Allocate Global Static IP
        ip_name = "ip-" + backend_bucket_name
        address_body = {
            "name": ip_name,
            "addressType": "EXTERNAL",
            "scope": "GLOBAL",
            "description": "Load balancer IP"
        }
        service.addresses().insert(project=project, region='global', body=address_body).execute()
        logger.info(f"Allocated global IP address '{ip_name}'.")

        # Step 5: Get the IP Address
        ip_address = None
        while True:
            try:
                response = service.addresses().get(project=project, region='global', address=ip_name).execute()
                ip_address = response.get('address')
                if ip_address:
                    break
            except HttpError as e:
                if e.resp.status == 404:
                    logger.info("Waiting for IP allocation...")
                    time.sleep(1)
                else:
                    raise e

        logger.info(f"Allocated IP address: {ip_address}")

        # Step 6: Create Global Forwarding Rule
        forwarding_rule_body = {
            "name": "forwarding-rule-" + backend_bucket_name,
            "IPAddress": ip_address,
            "IPProtocol": "TCP",
            "portRange": "80",
            "target": f"projects/{project}/global/targetHttpProxies/target-http-proxy-{backend_bucket_name}"
        }
        service.globalForwardingRules().insert(project=project, body=forwarding_rule_body).execute()
        logger.info(f"Forwarding rule 'forwarding-rule-{backend_bucket_name}' created.")

        # Return the IP address
        return ip_address

    except HttpError as e:
        logger.error(f"Failed to create load balancer: {e}")
        return None

def main():
    """Main function to orchestrate GCP operations."""
    # Configuration
    project = 'watchful-slice-443014-f0'  # Replace with your GCP project ID
    zone = 'us-central1-a'               # Replace with your desired zone
    instance_name = 'gcp-instance-test'
    machine_type = 'n1-standard-1'
    source_image = 'projects/debian-cloud/global/images/family/debian-11'  # Example: Debian 11
    bucket_name = 'my-gcp-bucket-party212'  # Must be globally unique
    file_to_upload = "C:\\Users\\naman\\Downloads\\hmm_flowchart.png"  # Replace with your file path
    backend_bucket_name = 'backend-bucket-party'
    domain_name = 'example.com'  # Replace with your domain name or set to empty string if not using

    # Track created resources for deletion
    created_instance = False
    created_bucket = False

    # Compute Engine Operations
    # Create an instance
    instance_id = create_instance(project, zone, instance_name, machine_type, source_image)
    if instance_id:
        created_instance = True

    # List running Compute Engine instances
    running_instances = list_instances(project, zone)

    # Terminate an instance
    # if instance_id:
    #     terminate_instance(project, zone, instance_name)

    # Cloud Storage Operations
    # Create a bucket
    bucket = create_storage_bucket(bucket_name, location='US', storage_class='STANDARD')
    if bucket:
        created_bucket = True

    # List all buckets
    buckets = list_storage_buckets()

    # Upload a file to the bucket
    if bucket and os.path.exists(file_to_upload):
        upload_success = upload_file_to_storage(bucket_name, file_to_upload)
        if upload_success:
            logger.info(f"File '{file_to_upload}' uploaded to bucket '{bucket_name}'.")
    else:
        logger.error(f"File '{file_to_upload}' does not exist or bucket creation failed.")

    # Optional: Delete a bucket (Uncomment to use)
    # delete_storage_bucket(bucket_name)

    # Cloud CDN and Load Balancing Operations
    # Note: Requires additional setup and permissions
    # load_balancer_ip = create_load_balancer(project, bucket_name, backend_bucket_name, domain_name)
    # if load_balancer_ip:
    #     logger.info(f"Access your content at: http://{load_balancer_ip}")

    # Wait for 2 minutes before deleting resources
    logger.info("Waiting for 2 minutes before deleting created resources...")
    time.sleep(120)  # Sleep for 120 seconds (2 minutes)

    # Delete the created Compute Engine instance
    if created_instance:
        terminate_instance(project, zone, instance_name)

    # Delete the created Cloud Storage bucket
    if created_bucket:
        delete_storage_bucket(bucket_name)

    logger.info("Resource cleanup completed.")

if __name__ == "__main__":
    main()
