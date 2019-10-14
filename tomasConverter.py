import xml.etree.ElementTree as ET
import sys, getopt
import os.path
import argparse
from pathlib import Path

# Dictionary of TouristicObjectTypes, to be filled
provider_types = {
    'WBX00020010000100218': None, #Ferienwohnung
    'WBX00020010000100214': None, #Hotel
    'WBX00020010000100258': None, #Gruppenunterkunft
    'WBX00020010000100220': None, #Ferienhaus
    'TDS00020010011658402': None, #Gästezimmer
    'WBX00020010000100701': None, #Camping
    'TDS00020010900364614': None, #Maiensäss
    'TDS00020010079106980': None, #Chalet
    'TDS00020010059375379': None  #Agrotourismus
}

# The in the argument after option -t given keys fill the dictionary provider_types with values
touple_dictionary = {
    'FW': ('WBX00020010000100218', 'Ferienwohnung'),
    'H': ('WBX00020010000100214', 'Hotel'),
    'GU': ('WBX00020010000100258', 'Gruppenunterkunft'),
    'FH': ('WBX00020010000100220', 'Ferienhaus'),
    'GZ': ('TDS00020010011658402', 'Gästezimmer'),
    'C': ('WBX00020010000100701', 'Camping'),
    'M': ('TDS00020010900364614', 'Maiensäss'),
    'CH': ('TDS00020010079106980', 'Chalet'),
    'A': ('TDS00020010059375379', 'Agrotourismus')
}

address_dictionary = {
    'CompanyName1': None,
    'Phone': None,
    'Fax': None,
    'Email': None,
    'Internet': None,
    'Street': None,
    'CountryCode': None,
    'ZipCode': None
}

examples = '''Touristic object types:

  FW=Ferienwohnung, H=Hotel, GU=Gruppenunterkunft, FH=Ferienhaus, GZ=Gästezimmer, C=Camping,
  M=Maiensäss, CH=Chalet, A=Agrotourismus , D=Default.
  if d or D is given, all the object-types will be included

Examples on how to use tomasConverter.py

  python tomasConverter.py example.xml D
  \t-> Parse the file "example.xml" and create "example.csv", convert all touristic object types.
  python tomasConverter.py example.xml H,CH,A
  \t-> Parse the file "example.xml" and create "example.csv", convert only Hotels, Chalet, Agrotourismus.
  python tomasConverter.py example.xml D different.csv -o
  \t-> Parse the file "example.xml" and overwrite already existing "different.csv".'''

def main():
    args = parse_arguments()
    input_file = Path(args.input)
    output_file = input_file.parent / f'{input_file.stem}.csv' if args.output is None else Path(args.output)
    create_dictionary(args.types.upper())
    if output_file.exists() and not args.overwrite:
        print(f'{output_file} already exists. Use -o or --overwrite to allow overwriting.')
        sys.exit(1)
    try:
        convert(input_file, output_file)
        print(f'Conversion complete. New file {output_file} created')
    except:
        print('Conversion failed.')

def parse_arguments():
    parser = argparse.ArgumentParser(description='Converts a tomas XML file to a csv file', epilog=examples, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('input', type=str, help='the XML file to convert')
    parser.add_argument('types', type=str, help='list of touristic object types separated by commas. For more information, see below')
    parser.add_argument('output', type=str, nargs='?', help='the name of the csv output file')
    parser.add_argument('-o', '--overwrite', action='store_true', help='if given, overwrite an existing csv file if present')
    return parser.parse_args()

# Controll which touristic object types will get converted
def create_dictionary(arguments):
    if arguments == 'D':
        arguments = 'FW,H,GU,FH,GZ,C,M,CH,A'
    argument_list = arguments.split(',')
    for arg in argument_list:
        touple = touple_dictionary.get(arg)
        if touple is None:
            print(f'Only use suitable arguments for the option -t | --types.{help}')
            sys.exit()
        provider_types[touple[0]] = touple[1]

def convert(input_file, output_file):
    root = parse_xml(input_file)
    write_csv(root, output_file)

def parse_xml(input_file):                
    try:
        xmlTree = ET.parse(input_file)
    except FileNotFoundError:
        print(f'The file {input_file} does not exist')
        sys.exit()
    except ET.ParseError:
        print(f'The file {input_file} somehow cannot be parsed')
        sys.exit()
    return xmlTree.getroot()

def write_csv(root, output_file):
    prefix = '{http://www.tbox.ch/dms/xmlstandardexport}'
    assert root.tag == f'{prefix}StandardExport'
    export_date = root.attrib.get('ExportDate').split('+')[0]

    # Create the output-file 
    with open(output_file, 'w') as w:
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
                        if address_data.tag == 'City':
                            for value in address_data[0]:
                                if value.attrib.get('LanguageCode') == 'de':
                                    city_de = value.text
                                    break
                        elif address_data.tag in ['CompanyName1','Phone','Fax','Email','Internet','Street','CountryCode','ZipCode']:
                            address_dictionary[address_data.tag] = address_data.text
                elif group.tag == 'Images':
                    images_list = []
                    for image in group:
                        for image_data in image:
                            if image_data.tag == 'url':
                                images_list.append(image_data.text)
                                break
            # Save all the information into the csv-file
            if do_write:
                company_name = address_dictionary.get('CompanyName1')
                street = address_dictionary.get('Street')
                zip_code = address_dictionary.get('ZipCode')
                country_code = address_dictionary.get('CountryCode')
                internet = address_dictionary.get('Internet')
                email = address_dictionary.get('Email')
                phone = address_dictionary.get('Phone')
                fax = address_dictionary.get('Fax')
                w.write(f'{company_name},{touristic_object_type},{classification},{street},{zip_code},{city_de},{country_code},{internet},{email},{phone},{fax},')
                string_images = ''
                for entry in images_list:
                    string_images += f'{entry}&'
                w.write(f'{string_images[:-1]},{last_modification},{service_object_id},{export_date},{latitude},{longitude}\n')

if __name__ == '__main__':
    main()