/**
 * A model for supporting column sorting in an HTML table.
 */
export class SortableColumnModel {

  public colName: string;
  public descending: boolean;
  public visible: boolean;
  public checked: boolean;
  public disabled: boolean;

  public constructor(colName: string, descending: boolean, visible: boolean, checked: boolean,
    disabled: boolean) {
    this.colName = colName;
    this.descending = descending;
    this.visible = visible;
    this.checked = checked;
    this.disabled = disabled;
  }
}
