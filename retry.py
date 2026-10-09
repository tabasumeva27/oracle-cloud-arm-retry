import os
import sys
import time
import datetime
import random
import oci

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "oci_config")
SUBNET_ID = "ocid1.subnet.oc1.ap-singapore-1.aaaaaaaaqesajln3v423zppzd3gz6ro5oqjdi65jhwincwnz4gpqflx3enla"
IMAGE_ID = "ocid1.image.oc1.ap-singapore-1.aaaaaaaaw75ef2chh5goomskvdznqz36cadczqelqvndbqcozc5icyig57za"
AVAILABILITY_DOMAIN = "MJQR:AP-SINGAPORE-1-AD-1"
SSH_PUBLIC_KEY = "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDkk/r6bKUvVZvV5FxTOxVt1715dQz5QsAl9RBAAIrCIXc8QJ8C85L1aE2NiU//0070EBZf1ikNGVWUx0uuxAtxZigr/YRs4OI4OJ+ShgsQWD7hCUWeaN69jleE7m+KAPuMUi2bBdwKAJiXYrEcUnNy5vEtQbKD8HV4TqDPD3bbXjXbqtTcs9VSrCE/UuI5mALvYbybAJrqXkbjdwCK1T/c/oBwuG3WFM23tbkOrgrBgWEugTO7UojrL4qgm8mK0czXGCajrUWN5kd6IUlW43SB6jRZ9DPJpL9oBMvYtHvuCCKiAVHtwE4c7H5FG+geiuLL8C1sxW9kXRBerRP+IQ0B"

def main():
    print("=" * 65)
    print("  GITHUB ACTIONS 24/7 ORACLE CLOUD ALWAYS-FREE PROVISIONER")
    print("  Target: 4 OCPU, 24 GB RAM, 50 GB Storage (100% Free Tier)")
    print("  Region: Singapore (AD-1) | OS: Ubuntu 24.04 LTS (ARM)")
    print("=" * 65)

    config = oci.config.from_file(CONFIG_PATH, "DEFAULT")
    core_client = oci.core.ComputeClient(config)
    compartment_id = config["tenancy"]

    launch_details = oci.core.models.LaunchInstanceDetails(
        availability_domain=AVAILABILITY_DOMAIN,
        compartment_id=compartment_id,
        shape="VM.Standard.A1.Flex",
        shape_config=oci.core.models.LaunchInstanceShapeConfigDetails(
            ocpus=4.0,
            memory_in_gbs=24.0
        ),
        display_name="my-ai-server",
        image_id=IMAGE_ID,
        metadata={
            "ssh_authorized_keys": SSH_PUBLIC_KEY
        },
        source_details=oci.core.models.InstanceSourceViaImageDetails(
            image_id=IMAGE_ID,
            boot_volume_size_in_gbs=50
        ),
        create_vnic_details=oci.core.models.CreateVnicDetails(
            subnet_id=SUBNET_ID,
            assign_public_ip=True,
            display_name="primary-vnic"
        )
    )

    attempt = 1
    # Max run time: 5 hours (18000s) per GitHub Action session
    start_time = time.time()
    max_duration = 5 * 3600

    while time.time() - start_time < max_duration:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [Attempt #{attempt}] Sending request for 4 OCPU / 24 GB RAM...")

        try:
            response = core_client.launch_instance(launch_details)
            instance = response.data
            print("\n" + "*" * 65)
            print("SUCCESS! SERVER HAS BEEN CREATED SUCCESSFULLY!")
            print(f"Instance ID: {instance.id}")
            print(f"Display Name: {instance.display_name}")
            print(f"Lifecycle State: {instance.lifecycle_state}")
            print("*" * 65 + "\n")
            
            with open("SUCCESS.txt", "w") as f:
                f.write(f"ID={instance.id}\nSTATE={instance.lifecycle_state}\nTIME={timestamp}")
            sys.exit(0)

        except oci.exceptions.ServiceError as e:
            if "Out of host capacity" in str(e.message) or "Out of capacity" in str(e.message) or e.status == 500:
                delay = random.randint(90, 120)
                print(f" -> Slot currently full in Singapore. Auto-retrying in {delay}s...")
                time.sleep(delay)
            elif "TooManyRequests" in str(e.code) or e.status == 429:
                delay = random.randint(150, 180)
                print(f" -> Oracle API rate limit. Backing off for {delay}s...")
                time.sleep(delay)
            else:
                print(f" -> Oracle API Response: [{e.code}] {e.message}")
                time.sleep(90)

        except Exception as e:
            print(f" -> Unexpected error: {e}")
            time.sleep(90)

        attempt += 1

    print("Session reached 5 hours limit. Workflow will cleanly exit and restart next schedule.")

if __name__ == "__main__":
    main()
