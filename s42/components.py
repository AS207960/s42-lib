from . import data

__COMPONENTS = {
    data.Code.fromstring("U10.05"): "FormOfAddress",
    data.Code.fromstring("U10.06"): "GivenName",
    data.Code.fromstring("U10.08"): "Surname",
    data.Code.fromstring("U10.10.13.00"): "Qualification",
    data.Code.fromstring("U20.00"): "OrganisationName",
    data.Code.fromstring("U20.01"): "OrganisationalLegalStatus",
    data.Code.fromstring("U20.02"): "OrganisationalUnit",
    data.Code.fromstring("U20.03"): "OrganisationFunction",
    data.Code.fromstring("U40.13"): "PostCode",
    data.Code.fromstring("U40.14"): "CountryName",
    data.Code.fromstring("U40.15"): "County",
    data.Code.fromstring("U40.16"): "Town",
    data.Code.fromstring("U40.17.11.00"): "DependentLocality",
    data.Code.fromstring("U40.17.21.00"): "DoubleDependentLocality",
    data.Code.fromstring("U40.21"): "ThoroughfareName",
    data.Code.fromstring("U40.21.11.22"): "PrimaryThoroughfareType",
    data.Code.fromstring("U40.21.11.41"): "PrimaryThoroughfareName",
    data.Code.fromstring("U40.21.21.22"): "SecondaryThoroughfareType",
    data.Code.fromstring("U40.21.21.41"): "SecondaryThoroughfareName",
    data.Code.fromstring("U40.24"): "BuildingNumber",
    data.Code.fromstring("U40.26"): "BuildingName",
    data.Code.fromstring("U40.28"): "SubBuildingName",
    data.Code.fromstring("U40.29"): "BuildingWing",
    data.Code.fromstring("U40.30"): "BuildingStairwell",
    data.Code.fromstring("U40.31"): "BuildingFloor",
    data.Code.fromstring("U40.32"): "BuildingDoor",
    data.Code.fromstring("U50.50"): "Script",
    data.Code.fromstring("U50.51"): "Language",
    data.Code.fromstring("U50.53"): "DespatchingCountry",
    data.Code.fromstring("U50.54"): "DeliveringCountry",
}


def get_code_name(code):
    return __COMPONENTS.get(code)


def get_code(name):
    for k, v in __COMPONENTS.items():
        if v == name:
            return k
    return None
