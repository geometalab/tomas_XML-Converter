import xml.etree.ElementTree as ET
import sys, getopt
import os.path

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

xml = '.xml'
csv = '.csv'
xml_name = ''
csv_name = ''
allow_overwrite = False
dict_is_default = True
help = '\nRun script with option -? | --help for clarification.'

# Display options and some examples
def show_help():
    print('''Converts a tomas-xml-file to a csv-file

python tomasConverter.py -x | --xml input [-c | --csv output] [-t | --types types] [-o | --overwrite]
\t-> for converting
python tomasConverter.py [-? | --help]
\t-> for help
Options in brackets are optional.

  -x, --xml\t\tOption which specifies the following argument as the xml-file to parse.
  input\t\t\tSpecifies the xml-file to convert. Required after the -x | --xml option.
  -c, --csv\t\tOption which specifies the following argument as the csv-output-file.
  output\t\tSpecifies the name of the csv-output-file. Required after the -c | --csv option.
  -t, --types\t\tOption which specifies the following argument as a list of touristic object types to convert.
  types\t\t\tList of touristic object types separated by commas.
  \t\t\tFW=Ferienwohnung, H=Hotel, GU=Gruppenunterkunft, FH=Ferienhaus, GZ=Gästezimmer, C=Camping,
  \t\t\tM=Maiensäss, CH=Chalet, A=Agrotourismus.
  -o | --overwrite\tOption which allows any existing csv-file to get overwritten.

Examples on how to use tomasConverter.py

  python tomasConverter.py -x example.xml
  \t-> Parse the file "example.xml" and create "example.csv", convert all touristic object types.
  python tomasConverter.py -x example.xml -t H,CH,A
  \t-> Parse the file "example.xml" and create "example.csv", convert only Hotels, Chalet, Agrotourismus.
  python tomasConverter.py -x example.xml -c different.csv -o
  \t-> Parse the file "example.xml" and overwrite already existing "different.csv".''')

# Controll which touristic object types will get converted
def create_dictionary(arguments):
    if arguments == '':
        arguments = 'FW,H,GU,FH,GZ,C,M,CH,A'
    argument_list = arguments.split(',')
    for arg in argument_list:
        touple = touple_dictionary.get(arg)
        if touple is None:
            print(f'Only use suitable arguments for the option -t | --types.{help}')
            sys.exit()
        provider_types[touple[0]] = touple[1]

# Main-function: Conversion of the xml-file
def convert(xml_name, csv_name):
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
    with open(csv_name, 'w') as w:
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

# Specifies which options are allowed
argv = sys.argv[1:]
try:
    opts, args = getopt.getopt(argv,'?x:c:t:o',['help', 'xml', 'csv', 'types', 'overwrite'])
except getopt.GetoptError:
    print(f'Use options correctly.{help}')
    sys.exit(2)

# Handle the given options
if not opts or opts[0][0] in ('-?', '--help'):
    show_help()
elif len(opts) > 4:
    print(f'Too many options.{help}')
else:
    for option in opts:
        if option[0] in ('-x', '--xml'):
            if option[1][-4:] == xml:
                xml_name = option[1]
            else:
                print(f'After the -x | --xml option, a xml-file should follow.{help}')
                sys.exit()
        elif option[0] in ('-c', '--csv'):
            if len(option[1]) > 4:
                if option[1][-4:] == csv:
                    csv_name = option[1]
                else:
                    print(f'After the -c | --csv option, a csv-file should follow.{help}')
                    sys.exit()
            else:
                print(f'After the -c | --csv option, a csv-file should follow.{help}')
                sys.exit()
        elif option[0] in ('-t', '--types'):
            create_dictionary(option[1].upper())
            dict_is_default = False
        elif option[0] in ('-o', '--overwrite'):
            allow_overwrite = True
    if xml_name == '':
        print(f'The -x | --xml option is required.{help}')
        sys.exit()
    if csv_name == '':
        csv_name = xml_name.split('.')[0] + csv
    if dict_is_default:
        create_dictionary('')
    if os.path.isfile(csv_name) and not allow_overwrite:
        print(f'{csv_name} already exists. Use the -o | --overwrite option to allow overwriting.{help}')
    else:
        try:
            convert(xml_name, csv_name)
            print(f'Conversion complete. New file {csv_name} created')
        except:
            print('Conversion failed.')