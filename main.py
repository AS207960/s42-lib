import glob
import os.path
import xml.etree.ElementTree
import pprint
import s42.data
import s42.template

S42_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), 's42-data'))

TEMPLATE_DIR = os.path.join(S42_DIR, 'TEMPLATES')
TEMPLATE_FILENAME = "S42-{0}-{1}-template-*.xml"

DATA_DIR = os.path.join(S42_DIR, 'DATA')
DATA_FILENAME = "S53-{0}-{1}-ENAD.v.2.3.xml"


def get_template(country_code, s42_version='8'):
    src = TEMPLATE_FILENAME.format(s42_version, country_code.upper())
    src = glob.glob(os.path.join(TEMPLATE_DIR, src))[0]
    return s42.template.Template.from_file_path(src)


def get_data(country_code, s53_version='2'):
    src = DATA_FILENAME.format(s53_version, country_code.upper())
    with open(os.path.join(DATA_DIR, src), 'rb') as f:
        doc = f.read()
    return xml.etree.ElementTree.fromstring(doc)


if __name__ == "__main__":
    for country in ("gb", "de", "us", "nl",):
        template = get_template(country)

        data = get_data(country)

        for item in data.findall('./GroupData/GroupItems/Item'):
            dto = {}
            for component in item.findall('./Representation/Components/*'):
                dto[component.tag] = component.text

            lines = item.findall('./Representation/RenditionData/AddressLineBlock/LineData')
            expected = "\n".join(map(lambda a: a.text, lines))

            dto = s42.data.AddressDTO.fromdict(dto)
            render = template.render(dto, fail_on_missing=False)
            actual = str(render)

            if expected != actual:
                print("-- EXPECTED --")
                print(expected)
                print("--  ACTUAL  --")
                print(actual)
                # pprint.pprint(render._candidates)
                pprint.pprint(render._lines)
