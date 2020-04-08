export class FieldEntryModel {
  value: string;
  selected: boolean;
  disabled: boolean;
  originallyEmpty: boolean;

  public constructor() {
    this.value = null;
    this.selected = false;
    this.disabled = false;
    this.originallyEmpty = false;
  }
}
