import { Component, OnInit, Input, ViewEncapsulation } from '@angular/core';

@Component({
  selector: 'app-configure-contacts',
  templateUrl: './configure-contacts.component.html',
  styleUrls: ['./configure-contacts.component.scss'],
  encapsulation: ViewEncapsulation.None
})
export class ConfigureContactsComponent implements OnInit {

  @Input()
  public userContactFields: Array<string>;

  public appContactFields: Array<any>;
  public appContactFieldsUnmapped: Array<any>;

  private userToAppFieldMap: Map<string, string>;

  constructor() { }

  ngOnInit() {
    this.appContactFields = [
      { text: 'Last Name', name: 'last_name' },
      { text: 'First Name', name: 'first_name' },
      { text: 'Middle Name', name: 'middle_name' },
      { text: 'Prefix (Optional)', name: 'prefix' },
      { text: 'Suffix (Optional)', name: 'suffix' },
      { text: 'Organization', name: 'entity_name' },
      { text: 'Address 1', name: 'street_1' },
      { text: 'Address 2 (Optional)', name: 'street_2' },
      { text: 'City', name: 'city' },
      { text: 'State', name: 'state' },
      { text: 'Zip Code', name: 'zip_code' },
      { text: 'Phone Telephone (Optional)', name: 'phone_number' },
      { text: 'Employer (Optional)', name: 'employer' },
      { text: 'Occupation (Optional)', name: 'occupation' }
    ];

    this.appContactFieldsUnmapped = this.appContactFields;
    this.userToAppFieldMap = new Map();
    for (const appField of this.appContactFields) {
      this.userToAppFieldMap.set(appField.name, null);
    }
  }

  public handleSelect(selectedAppField: any, index: number, userField: string) {
    const fields = [];

    if (selectedAppField) {
      // User has assigned a value
      this.userToAppFieldMap.set(selectedAppField.name, userField);
    } else {
      // User has removed an assigned a value
      // Find the selectedAppField using the userField and set it to null.
      this.userToAppFieldMap.forEach((value, key) => {
        if (value === userField) {
          this.userToAppFieldMap.set(key, null);
        }
      });
    }
    // Any null entries in the map will be added to the unmapped array.
    this.userToAppFieldMap.forEach((value, key) => {
      if (!value) {
        this.appContactFields.filter(appField => {
          if (appField.name === key) {
            fields.push(appField);
          }
        });
      }
    });
    this.appContactFieldsUnmapped = fields;
  }

}
