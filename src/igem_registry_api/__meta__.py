"""Metadata for the iGEM Registry API."""

from importlib.metadata import PackageMetadata, metadata, version

__all__: list[str] = [
    "__documentation__",
    "__issues__",
    "__module__",
    "__name__",
    "__package__",
    "__repository__",
    "__version__",
]

__title__: str = "iGEM Registry API"

__package__: str = "iGEM Registry API".lower().replace(" ", "_")
__module__: str = __package__

__version__: str = version(__package__)

__metadata__: PackageMetadata = metadata(__package__)
for item in __metadata__.json["project_url"]:
    match item:
        case _ if item.startswith("Repository"):
            __repository__: str = item.split(", ", 1)[1]
        case _ if item.startswith("Documentation"):
            __documentation__: str = item.split(", ", 1)[1]
        case _ if item.startswith("Issues"):
            __issues__: str = item.split(", ", 1)[1]
