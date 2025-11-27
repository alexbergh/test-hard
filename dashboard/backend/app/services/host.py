"""Host management service."""

import asyncio
from typing import Sequence

from app.config import get_settings
from app.models import Host
from app.schemas import HostCreate, HostUpdate
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

import docker

settings = get_settings()


class HostService:
    """Service for host management operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all_hosts(self, include_inactive: bool = False) -> Sequence[Host]:
        """Get all hosts."""
        query = select(Host)
        if not include_inactive:
            query = query.where(Host.is_active == True)  # noqa: E712
        query = query.order_by(Host.name)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_host_by_id(self, host_id: int) -> Host | None:
        """Get host by ID."""
        result = await self.session.execute(select(Host).where(Host.id == host_id))
        return result.scalar_one_or_none()

    async def get_host_by_name(self, name: str) -> Host | None:
        """Get host by name."""
        result = await self.session.execute(select(Host).where(Host.name == name))
        return result.scalar_one_or_none()

    async def create_host(self, host_data: HostCreate) -> Host:
        """Create a new host."""
        host = Host(
            name=host_data.name,
            display_name=host_data.display_name or host_data.name,
            description=host_data.description,
            host_type=host_data.host_type,
            address=host_data.address,
            port=host_data.port,
            ssh_user=host_data.ssh_user,
            ssh_key_path=host_data.ssh_key_path,
            os_family=host_data.os_family,
            os_version=host_data.os_version,
            enabled_scanners=host_data.enabled_scanners,
            scan_profile=host_data.scan_profile,
            tags=host_data.tags,
        )
        self.session.add(host)
        await self.session.flush()
        await self.session.refresh(host)
        return host

    async def update_host(self, host_id: int, host_data: HostUpdate) -> Host | None:
        """Update an existing host."""
        host = await self.get_host_by_id(host_id)
        if not host:
            return None

        update_data = host_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(host, field, value)

        await self.session.flush()
        await self.session.refresh(host)
        return host

    async def delete_host(self, host_id: int) -> bool:
        """Delete a host."""
        host = await self.get_host_by_id(host_id)
        if not host:
            return False
        await self.session.delete(host)
        return True

    async def check_host_status(self, host: Host) -> str:
        """Check if host is reachable and update status."""
        try:
            if host.host_type == "container":
                status = await self._check_container_status(host.name)
            elif host.host_type == "ssh":
                status = await self._check_ssh_status(host)
            else:
                status = "unknown"

            host.status = status
            await self.session.flush()
            return status
        except Exception:
            host.status = "offline"
            await self.session.flush()
            return "offline"

    async def _check_container_status(self, container_name: str) -> str:
        """Check Docker container status."""
        try:
            client = docker.from_env()
            container = client.containers.get(container_name)
            if container.status == "running":
                return "online"
            return "offline"
        except docker.errors.NotFound:
            return "offline"
        except Exception:
            return "unknown"

    async def _check_ssh_status(self, host: Host) -> str:
        """Check SSH host status via ping."""
        if not host.address:
            return "unknown"

        try:
            # Simple TCP check on SSH port
            port = host.port or 22
            _, writer = await asyncio.wait_for(
                asyncio.open_connection(host.address, port),
                timeout=5.0,
            )
            writer.close()
            await writer.wait_closed()
            return "online"
        except (asyncio.TimeoutError, OSError):
            return "offline"

    async def sync_docker_containers(self) -> list[Host]:
        """Sync hosts from running Docker containers."""
        try:
            client = docker.from_env()
            containers = client.containers.list()
            created_hosts = []

            for container in containers:
                name = container.name
                if name.startswith("target-"):
                    existing = await self.get_host_by_name(name)
                    if not existing:
                        # Detect OS from image
                        image = container.image.tags[0] if container.image.tags else ""
                        os_family = self._detect_os_family(image)

                        host = Host(
                            name=name,
                            display_name=name.replace("target-", "").title(),
                            host_type="container",
                            address=name,
                            os_family=os_family,
                            status="online" if container.status == "running" else "offline",
                        )
                        self.session.add(host)
                        created_hosts.append(host)

            await self.session.flush()
            return created_hosts
        except Exception:
            return []

    @staticmethod
    def _detect_os_family(image: str) -> str:
        """Detect OS family from Docker image name."""
        image_lower = image.lower()
        if "debian" in image_lower:
            return "debian"
        if "ubuntu" in image_lower:
            return "ubuntu"
        if "fedora" in image_lower:
            return "fedora"
        if "centos" in image_lower:
            return "centos"
        if "alt" in image_lower:
            return "alt"
        return "unknown"
