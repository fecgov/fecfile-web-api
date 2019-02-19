/**
 * A model for supporting column sorting in an HTML table.
 */
export class SortableColumnModel {
	
	private colName: string;
	private descending: boolean;
	public visible: boolean;

	public constructor( colName: string, descending: boolean, visible: boolean) {
		this.colName = colName;
		this.descending = descending;
		this.visible = visible;
	}
	

	public getColName() : string {
		return this.colName;
	}

  public setColName(colName: string) {
		this.colName = colName;
	} 

	public isDescending() : boolean {
		return this.descending;
	} 

  public setDescending(descending: boolean) {
		this.descending = descending;
	}   
	
	public isVisible() : boolean {
		return this.visible;
	}

  public setVisible(visible: boolean) {
		this.visible = visible;
	}	

}