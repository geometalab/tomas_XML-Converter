import xml.etree.ElementTree as ET
import sys, getopt
import os.path

# Dictionary of TouristicObjectTypes
provider_types = {
    'WBX00020010000100218': None, #Ferienwohnung
    'WBX00020010000100214': 'Hotel', #Hotel
    'WBX00020010000100258': 'Gruppenunterkunft', #Gruppenunterkunft
    'WBX00020010000100220': None, #Ferienhaus
    'TDS00020010011658402': None, #Gästezimmer
    'WBX00020010000100701': None, #Camping
    'TDS00020010900364614': None, #Maiensäss
    'TDS00020010079106980': None, # Chalet
    'TDS00020010059375379': 'Agrotourismus' # Agrotourismus
}

xml_name = 'tomas-gr-cc0.xml'
# Parse the xml-file with the given name
try:
    xmlTree = ET.parse(xml_name)
except FileNotFoundError:
    print(f'The file {xml_name} does not exist.')
    sys.exit()
except ET.ParseError:
    print(f'The file {xml_name} somehow cannot be parsed')
    sys.exit()
root = xmlTree.getroot()

prefix = '{http://www.tbox.ch/dms/xmlstandardexport}'

assert root.tag == f'{prefix}StandardExport'
export_date = root.attrib.get('ExportDate').split('+')[0]

# Create the output-file 
with open('output.csv', 'w') as w:
    w.write('CompanyName1,TouristicObjectType,Classification,Street,ZipCode,City:de,CountryCode,Internet,Email,Phone,Fax,Images,LastModification,ObjectID,ExportDate,Latitude,Longitude\n')
    for provider in root:
        for group in provider:
            if group.tag == 'TouristicObjectType':
                service_object_id = provider.attrib.get('ObjectID')
                last_modification = provider.attrib.get('LastModification').split('+')[0]
                touristic_object_id = group.attrib.get('ObjectID')
                touristic_object_type = provider_types.get(touristic_object_id)
                # If the type in the dictionary above has None as its value, it'll be ignored
                if touristic_object_type is None:
                    do_write = False
                    break
                else:
                    do_write = True
            elif group.tag == 'Classification':
                for value in group:
                    if value.attrib.get('LanguageCode') == 'de':
                        classification = value.text
                        break
            elif group.tag == 'Latitude':
                latitude = group.text
            elif group.tag == 'Longitude':
                longitude = group.text
            elif group.tag == 'Addresses':
                for address_data in group[0]:
                    if address_data.tag == 'CompanyName1':
                        company_name = address_data.text
                    elif address_data.tag == 'Phone':
                        phone = address_data.text
                    elif address_data.tag == 'Fax':
                        fax = address_data.text
                    elif address_data.tag == 'Email':
                        email = address_data.text
                    elif address_data.tag == 'Internet':
                        internet = address_data.text
                    elif address_data.tag == 'Street':
                        street = address_data.text
                    elif address_data.tag == 'CountryCode':
                        country_code = address_data.text
                    elif address_data.tag == 'ZipCode':
                        zip_code = address_data.text
                    elif address_data.tag == 'City':
                        for value in address_data[0]:
                            if value.attrib.get('LanguageCode') == 'de':
                                city_de = value.text
                                break
            elif group.tag == 'Images':
                images_list = []
                for image in group:
                    for image_data in image:
                        if image_data.tag == 'url':
                            images_list.append(image_data.text)
                            break
        # Save all the information into the csv-file
        if do_write:
            w.write(f'{company_name},{touristic_object_type},{classification},{street},{zip_code},{city_de},{country_code},{internet},{email},{phone},{fax},')
            string_images = ''
            for entry in images_list:
                string_images += f'{entry}&'
            w.write(f'{string_images[:-1]},{last_modification},{service_object_id},{export_date},{latitude},{longitude}\n')