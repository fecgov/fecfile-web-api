/**
 * A model for supporting column sorting in an HTML table.
 */
export class SortableColumnModel {
	
	public colName: string;
	public descending: boolean;
	public visible: boolean;
	public checked: boolean;
	public disabled: boolean;

	public constructor( colName: string, descending: boolean, visible: boolean, checked: boolean,
			disabled: boolean) {
		this.colName = colName;
		this.descending = descending;
		this.visible = visible;
		this.checked = checked;
		this.disabled = disabled;
	}
	

	// public getColName() : string {
	// 	return this.colName;
	// }

  	// public setColName(colName: string) {
	// 	this.colName = colName;
	// } 

	// public isDescending() : boolean {
	// 	return this.descending;
	// } 

  	// public setDescending(descending: boolean) {
	// 	this.descending = descending;
	// }   
	
	// public isVisible() : boolean {
	// 	return this.visible;
	// }

  	// public setVisible(visible: boolean) {
	// 	this.visible = visible;
	// }	

}