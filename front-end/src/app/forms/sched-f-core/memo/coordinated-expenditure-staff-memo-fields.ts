export class CoordinatedExpenditureStaffMemoFields {
  public readonly coordinatedExpenditureStaffMemoFields = {
    data: {
      formFields: [
        {
          childForm: false,
          childFormTitle: null,
          colClassName: 'col col-md-5',
          seperator: false,
          cols: [
            {
              preText: null,
              setEntityIdTo: 'entity_id',
              isReadonly: false,
              entityGroup: null,
              toggle: false,
              inputGroup: false,
              inputIcon: null,
              text: 'Entity Type',
              infoIcon: true,
              infoText:
                  'CAN Candidate \\n\n           CCM Candidate Committee  \\n\n            COM Committee \\n\n            IND Individual (a person) \\n\n            ORG Organization (not a committee and not a person) \\n\n            PAC Political Action Committee\\n\n            PTY Party Organization',
              name: 'entity_type',
              type: 'select',
              value: 'IND',
              scroll: false,
              height: '30px',
              width: '450px',
              validation: {
                required: true,
                max: 3,
                alphaNumeric: true
              }
            }
          ]
        },
        {
          childForm: false,
          childFormTitle: null,
          colClassName: 'col col-md-4',
          seperator: false,
          cols: [
            {
              preText: null,
              setEntityIdTo: 'entity_id',
              isReadonly: false,
              entityGroup: 'org-group',
              toggle: true,
              inputGroup: false,
              inputIcon: null,
              text: 'Organization Name',
              infoIcon: false,
              infoText: 'Request language from RAD',
              name: 'entity_name',
              type: 'text',
              value: null,
              scroll: false,
              height: '30px',
              width: '200px',
              validation: {
                required: true,
                max: 200,
                alphaNumeric: true
              }
            },
            {
              preText: null,
              setEntityIdTo: 'entity_id',
              isReadonly: false,
              entityGroup: 'ind-group',
              toggle: true,
              inputGroup: false,
              inputIcon: null,
              text: 'Last Name',
              infoIcon: false,
              infoText: null,
              name: 'last_name',
              type: 'text',
              value: null,
              scroll: false,
              height: '30px',
              width: '197px',
              validation: {
                required: true,
                max: 30,
                alphaNumeric: true
              }
            },
            {
              preText: null,
              setEntityIdTo: 'entity_id',
              isReadonly: false,
              entityGroup: 'ind-group',
              toggle: true,
              inputGroup: false,
              inputIcon: null,
              text: 'First Name',
              infoIcon: false,
              infoText: null,
              name: 'first_name',
              type: 'text',
              value: null,
              scroll: false,
              height: '30px',
              width: '197px',
              validation: {
                required: true,
                max: 20,
                alphaNumeric: true
              }
            },
            {
              preText: null,
              setEntityIdTo: 'entity_id',
              isReadonly: false,
              entityGroup: 'ind-group',
              toggle: true,
              inputGroup: false,
              inputIcon: null,
              text: 'Middle Name',
              infoIcon: false,
              infoText: null,
              name: 'middle_name',
              type: 'text',
              value: null,
              scroll: false,
              height: '30px',
              width: '197px',
              validation: {
                required: false,
                max: 20,
                alphaNumeric: true
              }
            }
          ]
        },
        {
          childForm: false,
          childFormTitle: null,
          colClassName: 'col col-md-4',
          seperator: true,
          cols: [
            {
              preText: null,
              setEntityIdTo: 'entity_id',
              isReadonly: false,
              entityGroup: 'ind-group',
              toggle: true,
              inputGroup: false,
              inputIcon: null,
              text: 'Prefix',
              infoIcon: false,
              infoText: null,
              name: 'prefix',
              type: 'text',
              value: null,
              scroll: false,
              height: '30px',
              width: '98.35px',
              validation: {
                required: false,
                max: 10,
                alphaNumeric: true
              }
            },
            {
              preText: null,
              setEntityIdTo: 'entity_id',
              isReadonly: false,
              entityGroup: 'ind-group',
              toggle: true,
              inputGroup: false,
              inputIcon: null,
              text: 'Suffix',
              infoIcon: false,
              infoText: null,
              name: 'suffix',
              type: 'text',
              value: null,
              scroll: false,
              height: '30px',
              width: '98.35px',
              validation: {
                required: false,
                max: 10,
                alphaNumeric: true
              }
            }
          ]
        },
        {
          childForm: false,
          childFormTitle: null,
          colClassName: 'col col-md-4',
          seperator: false,
          cols: [
            {
              preText: null,
              setEntityIdTo: 'entity_id',
              isReadonly: false,
              entityGroup: null,
              toggle: false,
              inputGroup: false,
              inputIcon: null,
              text: 'Street 1',
              infoIcon: false,
              infoText: null,
              name: 'street_1',
              type: 'text',
              value: null,
              scroll: false,
              height: '30px',
              width: '275px',
              validation: {
                required: true,
                max: 34,
                alphaNumeric: true
              }
            },
            {
              preText: null,
              setEntityIdTo: 'entity_id',
              isReadonly: false,
              entityGroup: null,
              toggle: false,
              inputGroup: false,
              inputIcon: null,
              text: 'Street 2',
              infoIcon: false,
              infoText: null,
              name: 'street_2',
              type: 'text',
              value: null,
              scroll: false,
              height: '30px',
              width: '275px',
              validation: {
                required: false,
                max: 34,
                alphaNumeric: true
              }
            }
          ]
        },
        {
          childForm: false,
          childFormTitle: null,
          colClassName: 'col col-md-4',
          seperator: true,
          cols: [
            {
              preText: null,
              setEntityIdTo: 'entity_id',
              isReadonly: false,
              entityGroup: null,
              toggle: false,
              inputGroup: false,
              inputIcon: null,
              text: 'City',
              infoIcon: false,
              infoText: null,
              name: 'city',
              type: 'text',
              value: null,
              scroll: false,
              height: '30px',
              width: '197px',
              validation: {
                required: true,
                max: 30,
                alphaNumeric: true
              }
            },
            {
              preText: null,
              setEntityIdTo: 'entity_id',
              isReadonly: false,
              entityGroup: null,
              toggle: false,
              inputGroup: false,
              inputIcon: null,
              text: 'State',
              infoIcon: false,
              infoText: null,
              name: 'state',
              type: 'select',
              value: null,
              scroll: false,
              height: '30px',
              width: '235px',
              validation: {
                required: true,
                max: 2,
                alphaNumeric: true
              }
            },
            {
              preText: null,
              setEntityIdTo: 'entity_id',
              isReadonly: false,
              entityGroup: null,
              toggle: false,
              inputGroup: false,
              inputIcon: null,
              text: 'Zip Code',
              infoIcon: false,
              infoText: null,
              name: 'zip_code',
              type: 'text',
              value: null,
              scroll: false,
              height: '30px',
              width: '98px',
              validation: {
                required: true,
                max: 10,
                alphaNumeric: true
              }
            }
          ]
        },
        {
          childForm: false,
          childFormTitle: null,
          colClassName: 'col col-md-4',
          seperator: false,
          cols: [
            {
              preText: null,
              setEntityIdTo: 'entity_id',
              isReadonly: false,
              entityGroup: null,
              toggle: false,
              inputGroup: true,
              inputIcon: 'calendar-icon',
              text: 'Expenditure Date',
              infoIcon: true,
              infoText: 'Request language from RAD',
              name: 'expenditure_date',
              type: 'date',
              value: null,
              scroll: false,
              height: '30px',
              width: '154px',
              validation: {
                required: true,
                max: null,
                date: true
              }
            }
          ]
        },
        {
          childForm: false,
          childFormTitle: null,
          colClassName: 'col col-md-4',
          seperator: false,
          cols: [
            {
              preText: null,
              setEntityIdTo: 'entity_id',
              isReadonly: false,
              entityGroup: null,
              toggle: false,
              inputGroup: true,
              inputIcon: 'dollar-sign-icon',
              text: 'Expenditure Amount',
              infoIcon: true,
              infoText: 'Request language from RAD',
              name: 'expenditure_amount',
              type: 'text',
              value: null,
              scroll: false,
              height: '30px',
              width: '154px',
              validation: {
                required: true,
                max: 12,
                dollarAmount: true
              }
            },
            {
              preText: null,
              setEntityIdTo: 'entity_id',
              isReadonly: true,
              entityGroup: null,
              toggle: false,
              inputGroup: true,
              inputIcon: 'dollar-sign-icon',
              text: 'Aggregate General Election Expended',
              infoIcon: true,
              infoText: 'Request language from RAD',
              name: 'aggregate_general_elec_exp',
              type: 'text',
              value: null,
              scroll: false,
              height: '30px',
              width: '154px',
              validation: {
                required: true,
                max: 12,
                dollarAmount: true
              }
            },
            {
              preText: null,
              setEntityIdTo: 'entity_id',
              isReadonly: true,
              entityGroup: null,
              toggle: false,
              inputGroup: false,
              inputIcon: null,
              text: 'Memo Code',
              infoIcon: true,
              infoText: 'Request language from RAD',
              name: 'memo_code',
              type: 'checkbox',
              value: 'X',
              scroll: false,
              height: '24px',
              width: '24px',
              validation: {
                required: false,
                max: 1,
                alphaNumeric: true
              }
            }
          ]
        },
        {
          childForm: false,
          childFormTitle: null,
          colClassName: 'col col-md-5',
          seperator: true,
          cols: [
            {
              preText: 'Staff Reimbursement Memo',
              setEntityIdTo: 'entity_id',
              isReadonly: false,
              entityGroup: null,
              toggle: false,
              inputGroup: true,
              inputIcon: '',
              text: 'Purpose of Disbursement',
              infoIcon: true,
              infoText: 'Request language from RAD',
              name: 'purpose',
              type: 'text',
              value: null,
              scroll: true,
              height: '30px',
              width: '340px',
              validation: {
                required: false,
                max: 100,
                alphaNumeric: true
              }
            },
            {
              preText: null,
              setEntityIdTo: 'entity_id',
              isReadonly: false,
              entityGroup: null,
              toggle: false,
              inputGroup: false,
              inputIcon: null,
              text: 'Memo Text',
              infoIcon: true,
              infoText: 'Request language from RAD',
              name: 'memo_text',
              type: 'text',
              value: null,
              scroll: true,
              height: '30px',
              width: '380px',
              validation: {
                required: false,
                max: 100,
                alphaNumeric: true
              }
            }
          ]
        },
        {
          childForm: false,
          childFormTitle: null,
          colClassName: 'col col-md-4',
          seperator: false,
          cols: [
            {
              preText: null,
              setEntityIdTo: 'entity_id',
              isReadonly: false,
              entityGroup: null,
              toggle: false,
              inputGroup: false,
              inputIcon: null,
              text: 'Committee FEC ID',
              infoIcon: false,
              infoText: null,
              name: 'payee_cmte_id',
              type: 'text',
              value: null,
              scroll: false,
              height: '30px',
              width: '197px',
              validation: {
                required: false,
                max: 9,
                alphaNumeric: true
              }
            }
          ]
        },
        {
          childForm: true,
          childFormTitle: 'Candidate Information:',
          colClassName: 'col col-md-12 fieldset childForm',
          seperator: false,
          cols: null
        },
        {
          childForm: false,
          childFormTitle: null,
          colClassName: 'col col-md-4',
          seperator: false,
          cols: [
            {
              preText: null,
              setEntityIdTo: 'entity_id',
              isReadonly: false,
              entityGroup: null,
              toggle: false,
              inputGroup: false,
              inputIcon: null,
              text: 'Last Name',
              infoIcon: false,
              infoText: null,
              name: 'cand_last_name',
              type: 'text',
              value: null,
              scroll: false,
              height: '30px',
              width: '197px',
              validation: {
                required: true,
                max: 30,
                alphaNumeric: true
              }
            },
            {
              preText: null,
              setEntityIdTo: 'entity_id',
              isReadonly: false,
              entityGroup: null,
              toggle: false,
              inputGroup: false,
              inputIcon: null,
              text: 'First Name',
              infoIcon: false,
              infoText: null,
              name: 'cand_first_name',
              type: 'text',
              value: null,
              scroll: false,
              height: '30px',
              width: '197px',
              validation: {
                required: true,
                max: 20,
                alphaNumeric: true
              }
            },
            {
              preText: null,
              setEntityIdTo: 'entity_id',
              isReadonly: false,
              entityGroup: null,
              toggle: false,
              inputGroup: false,
              inputIcon: null,
              text: 'Middle Name',
              infoIcon: false,
              infoText: null,
              name: 'cand_middle_name',
              type: 'text',
              value: null,
              scroll: false,
              height: '30px',
              width: '197px',
              validation: {
                required: false,
                max: 20,
                alphaNumeric: true
              }
            }
          ]
        },
        {
          childForm: false,
          childFormTitle: null,
          colClassName: 'col col-md-4',
          seperator: false,
          cols: [
            {
              preText: null,
              setEntityIdTo: 'entity_id',
              isReadonly: false,
              entityGroup: null,
              toggle: false,
              inputGroup: false,
              inputIcon: null,
              text: 'Prefix',
              infoIcon: false,
              infoText: null,
              name: 'cand_prefix',
              type: 'text',
              value: null,
              scroll: false,
              height: '30px',
              width: '98.35px',
              validation: {
                required: false,
                max: 10,
                alphaNumeric: true
              }
            },
            {
              preText: null,
              setEntityIdTo: 'entity_id',
              isReadonly: false,
              entityGroup: null,
              toggle: false,
              inputGroup: false,
              inputIcon: null,
              text: 'Suffix',
              infoIcon: false,
              infoText: null,
              name: 'cand_suffix',
              type: 'text',
              value: null,
              scroll: false,
              height: '30px',
              width: '98.35px',
              validation: {
                required: false,
                max: 10,
                alphaNumeric: true
              }
            }
          ]
        },
        {
          childForm: false,
          childFormTitle: null,
          colClassName: 'col col-md-4',
          seperator: false,
          cols: [
            {
              preText: null,
              setEntityIdTo: 'entity_id',
              isReadonly: false,
              entityGroup: null,
              toggle: false,
              inputGroup: false,
              inputIcon: null,
              text: 'Candidate FEC ID',
              infoIcon: false,
              infoText: null,
              name: 'beneficiary_cand_id',
              type: 'text',
              value: null,
              scroll: false,
              height: '30px',
              width: '197px',
              validation: {
                required: true,
                max: 9,
                alphaNumeric: true
              }
            }
          ]
        },
        {
          childForm: false,
          childFormTitle: null,
          colClassName: 'col col-md-4',
          seperator: true,
          cols: [
            {
              preText: null,
              setEntityIdTo: 'entity_id',
              isReadonly: false,
              entityGroup: null,
              toggle: false,
              inputGroup: false,
              inputIcon: null,
              text: 'Office',
              infoIcon: true,
              infoText: 'Request language from RAD',
              name: 'cand_office',
              type: 'select',
              value: null,
              scroll: false,
              height: '30px',
              width: '200px',
              validation: {
                required: true,
                max: 38,
                alphaNumeric: true
              }
            },
            {
              preText: null,
              setEntityIdTo: 'entity_id',
              isReadonly: false,
              entityGroup: null,
              toggle: false,
              inputGroup: false,
              inputIcon: null,
              text: 'State',
              infoIcon: true,
              infoText: 'Request language from RAD',
              name: 'cand_office_state',
              type: 'select',
              value: null,
              scroll: false,
              height: '30px',
              width: '200px',
              validation: {
                required: true,
                max: 38,
                alphaNumeric: true
              }
            },
            {
              preText: null,
              setEntityIdTo: 'entity_id',
              isReadonly: false,
              entityGroup: null,
              toggle: false,
              inputGroup: false,
              inputIcon: null,
              text: 'District',
              infoIcon: true,
              infoText: 'Request language from RAD',
              name: 'cand_office_district',
              type: 'text',
              value: null,
              scroll: false,
              height: '30px',
              width: '200px',
              validation: {
                required: true,
                max: 2,
                alphaNumeric: true
              }
            }
          ]
        }
      ],
      hiddenFields: [
        {
          type: 'hidden',
          name: 'api_call',
          value: '/sf/schedF'
        },
        {
          type: 'hidden',
          name: 'beneficiary_cand_entity_id',
          value: null
        },
        {
          type: 'hidden',
          name: 'line_number',
          value: '24'
        },
        {
          type: 'hidden',
          name: 'transaction_id',
          value: null
        },
        {
          type: 'hidden',
          name: 'back_ref_transaction_id',
          value: null
        },
        {
          type: 'hidden',
          name: 'back_ref_sched_name',
          value: null
        },
        {
          type: 'hidden',
          name: 'transaction_type',
          value: '24E'
        },
        {
          type: 'hidden',
          name: 'transaction_type_identifier',
          value: 'COEXP_STAF_REIM_MEMO'
        }
      ],
      states: [
        {
          name: 'Alabama',
          code: 'AL'
        },
        {
          name: 'Alaska',
          code: 'AK'
        },
        {
          name: 'Arizona',
          code: 'AZ'
        },
        {
          name: 'Arkansas',
          code: 'AR'
        },
        {
          name: 'California',
          code: 'CA'
        },
        {
          name: 'Colorado',
          code: 'CO'
        },
        {
          name: 'Connecticut',
          code: 'CT'
        },
        {
          name: 'Delaware',
          code: 'DE'
        },
        {
          name: 'District Of Columbia',
          code: 'DC'
        },
        {
          name: 'Florida',
          code: 'FL'
        },
        {
          name: 'Georgia',
          code: 'GA'
        },
        {
          name: 'Guam',
          code: 'GU'
        },
        {
          name: 'Hawaii',
          code: 'HI'
        },
        {
          name: 'Idaho',
          code: 'ID'
        },
        {
          name: 'Illinois',
          code: 'IL'
        },
        {
          name: 'Indiana',
          code: 'IN'
        },
        {
          name: 'Iowa',
          code: 'IA'
        },
        {
          name: 'Kansas',
          code: 'KS'
        },
        {
          name: 'Kentucky',
          code: 'KY'
        },
        {
          name: 'Louisiana',
          code: 'LA'
        },
        {
          name: 'Maine',
          code: 'ME'
        },
        {
          name: 'Maryland',
          code: 'MD'
        },
        {
          name: 'Massachusetts',
          code: 'MA'
        },
        {
          name: 'Michigan',
          code: 'MI'
        },
        {
          name: 'Minnesota',
          code: 'MN'
        },
        {
          name: 'Mississippi',
          code: 'MS'
        },
        {
          name: 'Missouri',
          code: 'MO'
        },
        {
          name: 'Montana',
          code: 'MT'
        },
        {
          name: 'Nebraska',
          code: 'NE'
        },
        {
          name: 'Nevada',
          code: 'NV'
        },
        {
          name: 'New Hampshire',
          code: 'NH'
        },
        {
          name: 'New Jersey',
          code: 'NJ'
        },
        {
          name: 'New Mexico',
          code: 'NM'
        },
        {
          name: 'New York',
          code: 'NY'
        },
        {
          name: 'North Carolina',
          code: 'NC'
        },
        {
          name: 'North Dakota',
          code: 'ND'
        },
        {
          name: 'Ohio',
          code: 'OH'
        },
        {
          name: 'Oklahoma',
          code: 'OK'
        },
        {
          name: 'Oregon',
          code: 'OR'
        },
        {
          name: 'Pennsylvania',
          code: 'PA'
        },
        {
          name: 'Puerto Rico',
          code: 'PR'
        },
        {
          name: 'Rhode Island',
          code: 'RI'
        },
        {
          name: 'South Carolina',
          code: 'SC'
        },
        {
          name: 'South Dakota',
          code: 'SD'
        },
        {
          name: 'Tennessee',
          code: 'TN'
        },
        {
          name: 'Texas',
          code: 'TX'
        },
        {
          name: 'Utah',
          code: 'UT'
        },
        {
          name: 'Vermont',
          code: 'VT'
        },
        {
          name: 'Virginia',
          code: 'VA'
        },
        {
          name: 'U.S. Virgin Islands',
          code: 'VI'
        },
        {
          name: 'Washington',
          code: 'WA'
        },
        {
          name: 'West Virginia',
          code: 'WV'
        },
        {
          name: 'Wisconsin',
          code: 'WI'
        },
        {
          name: 'Wyoming',
          code: 'WY'
        },
        {
          name: 'Foreign Countries',
          code: 'ZZ'
        },
        {
          name: 'American Samoa',
          code: 'AS'
        },
        {
          name: 'Northern Mariana Islands',
          code: 'MP'
        },
        {
          name: 'United States',
          code: 'US'
        },
        {
          name: 'Armed Forces Americas',
          code: 'AA'
        },
        {
          name: 'Armed Forces Europe',
          code: 'AE'
        },
        {
          name: 'Armed Forces Pacific',
          code: 'AP'
        }
      ],
      titles: null,
      entityTypes: [
        {
          entityType: 'ORG',
          entityTypeDescription: 'Organization',
          group: 'org-group',
          selected: true
        },
        {
          entityType: 'IND',
          entityTypeDescription: 'Individual',
          group: 'ind-group',
          selected: false
        },
      ],
      electionTypes: [
        {
          electionType: 'P',
          electionTypeDescription: 'Primary'
        },
        {
          electionType: 'G',
          electionTypeDescription: 'General'
        },
        {
          electionType: 'R',
          electionTypeDescription: 'Runoff'
        },
        {
          electionType: 'S',
          electionTypeDescription: 'Special General'
        },
        {
          electionType: 'SP',
          electionTypeDescription: 'Special Primary'
        },
        {
          electionType: 'SR',
          electionTypeDescription: 'Special Runoff'
        },
        {
          electionType: 'C',
          electionTypeDescription: 'Convention'
        },
        {
          electionType: 'O',
          electionTypeDescription: 'Other'
        }
      ],
      committeeTypeEvents: [
        {
          committeeTypeCategory: 'PAC',
          eventTypes: [
            {
              eventType: 'PC',
              eventTypeDescription: 'Public Communications Referring Only to Party (made by PAC)',
              scheduleType: 'sched_h1',
              activityEventTypes: null
            },
            {
              eventType: 'AD',
              eventTypeDescription: 'Administrative',
              scheduleType: 'sched_h1',
              activityEventTypes: null
            },
            {
              eventType: 'GV',
              eventTypeDescription: 'Generic Voter Drive',
              scheduleType: 'sched_h1',
              activityEventTypes: null
            },
            {
              eventType: 'DC',
              eventTypeDescription: 'Direct Candidate Support',
              scheduleType: 'sched_h2',
              activityEventTypes: null
            },
            {
              eventType: 'DF',
              eventTypeDescription: 'Direct Fundraising',
              scheduleType: 'sched_h2',
              activityEventTypes: null
            }
          ]
        },
        {
          committeeTypeCategory: 'PTY',
          eventTypes: [
            {
              eventType: 'EA',
              eventTypeDescription: 'Exempt Activities',
              scheduleType: 'sched_h1',
              activityEventTypes: null
            },
            {
              eventType: 'AD',
              eventTypeDescription: 'Administrative',
              scheduleType: 'sched_h1',
              activityEventTypes: null
            },
            {
              eventType: 'GV',
              eventTypeDescription: 'Generic Voter Drive',
              scheduleType: 'sched_h1',
              activityEventTypes: null
            },
            {
              eventType: 'DC',
              eventTypeDescription: 'Direct Candidate Support',
              scheduleType: 'sched_h2',
              activityEventTypes: null
            },
            {
              eventType: 'DF',
              eventTypeDescription: 'Direct Fundraising',
              scheduleType: 'sched_h2',
              activityEventTypes: null
            }
          ]
        },
        {
          committeeTypeCategory: 'H6',
          eventTypes: [
            {
              eventType: 'VR',
              eventTypeDescription: 'Voter Registration',
              scheduleType: 'sched_h6',
              activityEventTypes: null
            },
            {
              eventType: 'GO',
              eventTypeDescription: 'GOTV',
              scheduleType: 'sched_h6',
              activityEventTypes: null
            },
            {
              eventType: 'VI',
              eventTypeDescription: 'Voter ID',
              scheduleType: 'sched_h6',
              activityEventTypes: null
            },
            {
              eventType: 'GC',
              eventTypeDescription: 'Generic Campaign',
              scheduleType: 'sched_h6',
              activityEventTypes: null
            }
          ]
        }
      ],
      subTransactions: [
        {
          transactionType: 'COEXP_STAF_REIM',
          transactionTypeDescription: 'CE Staff Reimbursement',
          scheduleType: 'sched_f_core',
          subTransactionType: 'COEXP_STAF_REIM_MEMO',
          subScheduleType: 'sched_f_core',
          subTransactionTypeDescription: 'CE Staff Reimbursement Memo',
          api_call: '/sf/schedF',
          isParent: false,
          isEarmark: false
        }
      ],
      jfMemoTypes: null
    }
  };


}
