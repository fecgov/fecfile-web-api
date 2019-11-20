export const schedFstaticFormFields = [
  {
    childForm: false,
    childFormTitle: null,
    colClassName: 'col col-md-4',
    seperator: false,
    cols: [
      {
        staticField: true,
        name: 'coordinated_exp_ind',
        value: null,
        validation: {
          required: true
        }
      },
      {
        staticField: true,
        preText: null,
        setEntityIdTo: 'entity_id',
        isReadonly: false,
        entityGroup: 'org-group',
        toggle: true,
        inputGroup: false,
        inputIcon: '',
        text: 'Organization Name',
        infoIcon: false,
        infoText: 'Request language from RAD',
        name: 'designating_cmte_id',
        type: 'text',
        value: null,
        scroll: false,
        height: '30px',
        width: '200px',
        validation: {
          required: true,
          max: 9,
          alphaNumeric: true
        }
      },
      {
        staticField: true,
        preText: null,
        setEntityIdTo: 'entity_id',
        isReadonly: false,
        entityGroup: 'org-group',
        toggle: true,
        inputGroup: false,
        inputIcon: '',
        text: 'Organization Name',
        infoIcon: false,
        infoText: 'Request language from RAD',
        name: 'designating_cmte_name',
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
        staticField: true,
        name: 'subordinate_cmte_id',
        value: null,
        validation: {
          required: true,
          max: 9,
          alphaNumeric: true
        }
      },
      {
        staticField: true,
        name: 'subordinate_cmte_name',
        value: null,
        validation: {
          required: true,
          max: 200,
          alphaNumeric: true
        }
      },
      {
        staticField: true,
        name: 'subordinate_cmte_street_1',
        value: null,
        validation: {
          required: true,
          max: 34,
          alphaNumeric: true
        }
      },
      {
        staticField: true,
        name: 'subordinate_cmte_street_2',
        value: null,
        validation: {
          required: false,
          max: 34,
          alphaNumeric: true
        }
      },
      {
        staticField: true,
        name: 'subordinate_cmte_city',
        value: null,
        validation: {
          required: true,
          max: 30,
          alphaNumeric: true
        }
      },
      {
        staticField: true,
        name: 'subordinate_cmte_state',
        type: 'select',
        value: null,
        validation: {
          required: true,
          max: 2,
          alphaNumeric: true
        }
      },
      {
        staticField: true,
        name: 'subordinate_cmte_zip',
        value: null,
        validation: {
          required: true,
          max: 10,
          alphaNumeric: true
        }
      }
    ]
  }
];
