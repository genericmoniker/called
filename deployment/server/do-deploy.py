# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "cloudflare",
#     "pydo",
#     "python-dotenv",
# ]
# ///
"""Deploy the server to a DigitalOcean droplet and update Cloudflare DNS.

Droplet sizes: https://slugs.do-api.dev
"""

# ruff: noqa: T201
import os
import traceback
from dataclasses import dataclass
from pathlib import Path
from time import sleep

from cloudflare import Cloudflare
from cloudflare.types.dns.record_list_params import Name
from dotenv import load_dotenv
from pydo import Client


def main() -> None:
    """Create the server."""
    load_dotenv()
    try:
        print("Creating server")
        config = Config.from_env()
        ip_address = create_server(config)
        update_dns(config, ip_address)
        print("✔  Done")
    except Exception as e:  # noqa: BLE001
        print(f"❌ Error: {e}")
        print()
        traceback.print_exception(e)


@dataclass
class Config:
    """Configuration for creating the server."""

    hostname: str
    droplet_size: str
    root_ssh_key: str
    digitalocean_token: str
    cloudflare_zone_id: str
    cloudflare_api_token: str

    @classmethod
    def from_env(cls) -> "Config":
        """Create a Config instance from environment variables."""
        return cls(
            hostname=cls._get_env("SERVER_HOSTNAME"),
            droplet_size=cls._get_env("SERVER_DROPLET_SIZE"),
            root_ssh_key=cls._get_env("SERVER_ROOT_SSH_KEY_FINGERPRINT", ""),
            digitalocean_token=cls._get_env("DIGITALOCEAN_TOKEN"),
            cloudflare_zone_id=cls._get_env("CLOUDFLARE_ZONE_ID"),
            cloudflare_api_token=cls._get_env("CLOUDFLARE_API_TOKEN"),
        )

    @staticmethod
    def _get_env(name: str, default: str | None = None) -> str:
        value = os.environ.get(name, default)
        if value is None:
            msg = f"Missing environment variable: {name}"
            raise ValueError(msg)
        return value


def create_server(config: Config) -> str:
    """Create a new Digital Ocean droplet for the server.

    Returns the IP address of the new droplet.
    """
    print(f"Creating droplet {config.hostname}")
    client = Client(config.digitalocean_token)

    # Warn if there is an existing droplet with the same name.
    resp = client.droplets.list(name=config.hostname)
    existing_droplets = resp["droplets"]
    if existing_droplets:
        print(
            f"⚠  A Droplet named '{config.hostname}' already exists. "
            "Still continuing to create another one..."
        )

    here = Path(__file__).parent
    cloud_config_path = here / "cloud-config.yaml"
    cloud_config = cloud_config_path.read_text().format(
        domain=config.hostname,
    )

    req = {
        "name": config.hostname,
        "region": "sfo3",
        "size": config.droplet_size,
        "image": "ubuntu-24-04-x64",
        "ssh_keys": [config.root_ssh_key],
        "backups": True,
        "ipv6": False,
        "monitoring": True,
        "user_data": cloud_config,
    }

    resp = client.droplets.create(body=req)
    droplet_id = resp["droplet"]["id"]
    print(f"Created droplet {droplet_id}, waiting for it to become active")
    while True:
        print(".", end="", flush=True)
        resp = client.droplets.get(droplet_id)
        if resp["droplet"]["status"] == "active":
            break
        sleep(1)
    print()

    ip_address = resp["droplet"]["networks"]["v4"][0]["ip_address"]
    print(f"Droplet {droplet_id} is active with IP address {ip_address}")
    return ip_address


def update_dns(config: Config, ip_address: str) -> None:
    """Create or update the Cloudflare DNS record for the server."""
    print("Configuring DNS")
    client = Cloudflare(api_token=config.cloudflare_api_token)
    name = Name(exact=config.hostname)
    resp = client.dns.records.list(zone_id=config.cloudflare_zone_id, name=name)
    if not resp.result:
        print("Creating new DNS record")
        client.dns.records.create(
            zone_id=config.cloudflare_zone_id,
            type="A",
            name=config.hostname,
            content=ip_address,
            ttl=1,  # 1 = automatic
            proxied=False,
        )
    else:
        record_id = resp.result[0].id
        client.dns.records.edit(
            dns_record_id=record_id,
            zone_id=config.cloudflare_zone_id,
            name=config.hostname,
            type="A",
            content=ip_address,
        )

    print(f"DNS record for {config.hostname} set to {ip_address}")


if __name__ == "__main__":
    main()
