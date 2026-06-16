from pydantic import BaseModel

from app.link_metadata.application.service import LinkMetadata


class LinkMetadataResponse(BaseModel):
    title: str | None = None
    description: str | None = None
    icon_url: str | None = None

    @classmethod
    def from_metadata(cls, metadata: LinkMetadata) -> "LinkMetadataResponse":
        return cls(
            title=metadata.title,
            description=metadata.description,
            icon_url=metadata.icon_url,
        )
