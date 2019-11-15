export const schedFstaticFormFields = [
  {
    childForm: false,
    childFormTitle: null,
    colClassName: 'col col-md-4',
    seperator: false,
    cols: [
      {
        staticField: true,
        name: 'coord_expenditure_yn',
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
        name: 'designated_com_id',
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
        name: 'designated_com_name',
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
        name: 'subordinate_com_id',
        value: null,
        validation: {
          required: true,
          max: 9,
          alphaNumeric: true
        }
      },
      {
        staticField: true,
        name: 'subordinate_com_name',
        value: null,
        validation: {
          required: true,
          max: 200,
          alphaNumeric: true
        }
      },
      {
        staticField: true,
        name: 'street_1_co_exp',
        value: null,
        validation: {
          required: true,
          max: 34,
          alphaNumeric: true
        }
      },
      {
        staticField: true,
        name: 'street_2_co_exp',
        value: null,
        validation: {
          required: false,
          max: 34,
          alphaNumeric: true
        }
      },
      {
        staticField: true,
        name: 'city_co_exp',
        value: null,
        validation: {
          required: true,
          max: 30,
          alphaNumeric: true
        }
      },
      {
        staticField: true,
        name: 'state_co_exp',
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
        name: 'zip_co_exp',
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
