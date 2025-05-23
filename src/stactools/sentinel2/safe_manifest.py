import os
from typing import Optional

import pystac

from stactools.core.io import ReadHrefModifier
from stactools.core.io.xml import XmlElement
from stactools.sentinel2.constants import SAFE_MANIFEST_ASSET_KEY


class ManifestError(Exception):
    pass


class SafeManifest:
    def __init__(
        self, granule_href: str, read_href_modifier: Optional[ReadHrefModifier] = None
    ):
        self.granule_href = granule_href
        self.href = os.path.join(granule_href, "manifest.safe")

        if not os.path.isdir(self.granule_href):
            self.href = self.granule_href
            self.granule_href = os.path.dirname(self.granule_href)
        else:
            self.granule_href = granule_href
            self.href = os.path.join(granule_href, "manifest.safe")


        root = XmlElement.from_file(self.href, read_href_modifier)
        self._data_object_section = root.find("dataObjectSection")
        if self._data_object_section is None:
            raise ManifestError(
                f"Manifest at {self.href} does not have a dataObjectSection"
            )

    def _find_href(self, xpaths: list[str]) -> Optional[str]:
        file_path = None
        for xpath in xpaths:
            file_path = self._data_object_section.find_attr("href", xpath)
            if file_path is not None:
                break

        if file_path is None:
            return None
        else:
            # Remove relative prefix that some paths have
            file_path = file_path.strip("./")
            return os.path.join(self.granule_href, file_path)

    @property
    def product_metadata_href(self) -> Optional[str]:
        return self._find_href(
            [
                'dataObject[@ID="S2_Level-1C_Product_Metadata"]/byteStream/fileLocation',
                'dataObject[@ID="S2_Level-2A_Product_Metadata"]/byteStream/fileLocation',
            ]
        )

    @property
    def inspire_metadata_href(self) -> Optional[str]:
        return self._find_href(
            ['dataObject[@ID="INSPIRE_Metadata"]/byteStream/fileLocation']
        )

    @property
    def datastrip_metadata_href(self) -> Optional[str]:
        return self._find_href(
            [
                'dataObject[@ID="S2_Level-1C_Datastrip1_Metadata"]/byteStream/fileLocation',
                'dataObject[@ID="S2_Level-2A_Datastrip1_Metadata"]/byteStream/fileLocation',
            ]
        )

    @property
    def granule_metadata_href(self) -> Optional[str]:
        granule_metadata = os.path.join(self.granule_href, 'MTD_TL.xml')
        if os.path.exists(granule_metadata):
            return granule_metadata
        else:
            return self._find_href(
                [
                    'dataObject[@ID="S2_Level-2A_Tile1_Data"]/byteStream/fileLocation',
                    'dataObject[@ID="S2_Level-1C_Tile1_Metadata"]/byteStream/fileLocation',
                    'dataObject[@ID="S2_Level-2A_Tile1_Metadata"]/byteStream/fileLocation',
                ]
            )

    def create_asset(self) -> tuple[str, pystac.Asset]:
        asset = pystac.Asset(
            href=self.href, media_type=pystac.MediaType.XML, roles=["metadata"]
        )
        return SAFE_MANIFEST_ASSET_KEY, asset
