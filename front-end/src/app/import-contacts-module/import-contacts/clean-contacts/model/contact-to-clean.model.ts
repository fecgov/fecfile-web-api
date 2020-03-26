export class ContactToCleanModel {
  name: string;
  displayName: string;
  existingEntry: {
    value: string,
    selected: boolean,
    disabled: boolean
  };
  newEntry: {
    value: string,
    selected: boolean,
    disabled: boolean,
    originallyEmpty: boolean;
  };
  finalEntry: string;
}
