
/**
 * Use if spec and template XLS download is created as a Workbook in the front end.
 * This may be replaces by API downloading a fully formatted Excel file as a Blob
 * See /contact/template
 */
export const importContactsSpec: any = [
  {
    'COL SEQ': 'A',
    'FIELD DESCRIPTION': 'COMMITTEE ID',
    'TYPE OF CHARACTERS': 'A/N-9',
    'REQUIRED FIELDS': 'Required',
    'SAMPLE DATA': 'C98765431',
    'VALUE REFERENCE': 'Committee ID of the Committee Importing Contacts'
  },
  {
    'COL SEQ': 'B',
    'FIELD DESCRIPTION': 'ENTITY TYPE',
    'TYPE OF CHARACTERS': 'A/N-3',
    'REQUIRED FIELDS': 'Required',
    'SAMPLE DATA': 'IND',
    'VALUE REFERENCE': 'Individual - IND'
  },
  {
    'COL SEQ': 'C',
    'FIELD DESCRIPTION': 'ORGANIZATION NAME',
    'TYPE OF CHARACTERS': 'A/N-200',
    'REQUIRED FIELDS': 'Required if ORG',
    'SAMPLE DATA': 'John Smith & Co.',
    'VALUE REFERENCE': ''
  },
  {
    'COL SEQ': 'D',
    'FIELD DESCRIPTION': 'LAST NAME',
    'TYPE OF CHARACTERS': 'A/N-30',
    'REQUIRED FIELDS': 'Required if IND',
    'SAMPLE DATA': 'Smith',
    'VALUE REFERENCE': ''
  },
  {
    'COL SEQ': 'E',
    'FIELD DESCRIPTION': 'FIRST NAME',
    'TYPE OF CHARACTERS': 'A/N-20',
    'REQUIRED FIELDS': 'Required if IND',
    'SAMPLE DATA': 'John',
    'VALUE REFERENCE': ''
  },
  {
    'COL SEQ': 'F',
    'FIELD DESCRIPTION': 'MIDDLE NAME',
    'TYPE OF CHARACTERS': 'A/N-20',
    'REQUIRED FIELDS': 'Optional',
    'SAMPLE DATA': 'W',
    'VALUE REFERENCE': ''
  },
  {
    'COL SEQ': 'G',
    'FIELD DESCRIPTION': 'PREFIX',
    'TYPE OF CHARACTERS': 'A/N-10',
    'REQUIRED FIELDS': 'Optional',
    'SAMPLE DATA': 'Dr',
    'VALUE REFERENCE': ''
  },
  {
    'COL SEQ': 'H',
    'FIELD DESCRIPTION': 'SUFFIX',
    'TYPE OF CHARACTERS': 'A/N-10',
    'REQUIRED FIELDS': 'Optional',
    'SAMPLE DATA': 'Jr',
    'VALUE REFERENCE': ''
  },
  {
    'COL SEQ': 'I',
    'FIELD DESCRIPTION': 'STREET 1',
    'TYPE OF CHARACTERS': 'A/N-34',
    'REQUIRED FIELDS': 'Required',
    'SAMPLE DATA': '123 Main Street',
    'VALUE REFERENCE': ''
  },
  {
    'COL SEQ': 'J',
    'FIELD DESCRIPTION': 'STREET 2',
    'TYPE OF CHARACTERS': 'A/N-34',
    'REQUIRED FIELDS': 'Required',
    'SAMPLE DATA': '',
    'VALUE REFERENCE': ''
  },
  {
    'COL SEQ': 'K',
    'FIELD DESCRIPTION': 'CITY',
    'TYPE OF CHARACTERS': 'A/N-30',
    'REQUIRED FIELDS': 'Required',
    'SAMPLE DATA': 'Any town',
    'VALUE REFERENCE': ''
  },
  {
    'COL SEQ': 'L',
    'FIELD DESCRIPTION': 'STATE',
    'TYPE OF CHARACTERS': 'A/N-2',
    'REQUIRED FIELDS': 'Required',
    'SAMPLE DATA': 'WA',
    'VALUE REFERENCE': 'AK,AL,...ZZ'
  },
  {
    'COL SEQ': 'M',
    'FIELD DESCRIPTION': 'ZIP',
    'TYPE OF CHARACTERS': 'A/N-9',
    'REQUIRED FIELDS': 'Required',
    'SAMPLE DATA': '981110123',
    'VALUE REFERENCE': ''
  },
  {
    'COL SEQ': 'N',
    'FIELD DESCRIPTION': 'EMPLOYER',
    'TYPE OF CHARACTERS': 'A/N-38',
    'REQUIRED FIELDS': 'Optional',
    'SAMPLE DATA': '',
    'VALUE REFERENCE': ''
  },
  {
    'COL SEQ': 'O',
    'FIELD DESCRIPTION': 'OCCUPATION',
    'TYPE OF CHARACTERS': 'A/N-38',
    'REQUIRED FIELDS': 'Optional',
    'SAMPLE DATA': '',
    'VALUE REFERENCE': ''
  }
];

export const importContactsTemplate = [
  {
    'COMMITTEE ID': '',
    'ENTITY TYPE': '',
    'ORGANIZATION NAME': '',
    'LAST NAME': '',
    'FIRST NAME': '',
    'MIDDLE NAME': '',
    PREFIX: '',
    SUFFIX: '',
    'STREET 1': '',
    'STREET 2': '',
    CITY: '',
    STATE: '',
    ZIP: '',
    EMPLOYER: '',
    OCCUPATION: ''
  }
];
