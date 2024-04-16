import json
from pydantic_core import ValidationError
from rocrate.rocrate import ROCrate
from rocrate.model.person import Person
from zenodo_client import Creator, Metadata, ensure_zenodo


def build_zenodo_creator_list(authors: list[Person] | Person) -> list[Creator]:
    """Given an RO-Crate author or list of authors, build a list of "creators"
    to use in Zenodo upload."""
    if isinstance(authors, list):
        return [Creator(name=a["name"]) for a in authors]
    else:
        # single author
        return [Creator(name=authors["name"])]


def build_zenodo_metadata_from_crate(crate: ROCrate) -> Metadata:
    """Given an RO-Crate, collect the metadata to use in Zenodo upload"""
    # retrieve author(s)
    authors = crate.root_dataset.get("author")
    creators = build_zenodo_creator_list(authors)

    # retrieve title
    title = crate.root_dataset.get("name")
    description = crate.root_dataset.get("description")

    # Define the metadata that will be used on initial upload
    # Metadata is a Pydantic model that provides some type validation
    try:
        data = Metadata(
            title=title,
            upload_type="dataset",
            description=description,
            creators=creators,
        )
    except ValidationError as exception:
        errors = json.loads(exception.json())
        msg = (
            "The RO-Crate metadata could not be converted to Zenodo metadata. "
            "Encountered the following errors:\n"
        )
        for e in errors:
            # TODO: replace Metadata field with corresponding RO-Crate field
            field = ", ".join(e["loc"])
            msg += f"Field {field}: {e['msg']}\n"
        raise RuntimeError(msg)

    return data


def ensure_crate_zipped(crate: ROCrate) -> str:
    """Returns a path to the zipped crate."""
    # TODO - use original crate path if it was a zip
    # TODO - save zipped crate to crate parent directory
    zip_path = "/tmp/crate.zip"
    zipped = crate.write_zip(zip_path)
    return zipped


def upload_crate_to_zenodo(crate_zip_path: str, metadata: Metadata):
    """Upload a zipped crate and its metadata to Zenodo.

    This will publish a record when run, so it's recommended to keep
    sandbox=True until a publish toggle is added to zenodo-client."""
    res = ensure_zenodo(
        # this is a unique key you pick that will be used to store
        # the numeric deposition ID on your local system's cache
        key="ro-crate-uploader",
        data=metadata,
        paths=[
            crate_zip_path,
        ],
        sandbox=True,  # remove this when you're ready to upload to real Zenodo
    )

    return res.json()


# included for convenience, remove or update this as code expands
if __name__ == "__main__":
    crate_path = "test/test_data/demo_crate"
    crate = ROCrate(crate_path)

    metadata = build_zenodo_metadata_from_crate(crate)
    crate_zip_path = ensure_crate_zipped(crate)
    print(crate_zip_path, metadata)
    # record = upload_crate_to_zenodo(crate_zip_path, metadata)
    # print(record)
