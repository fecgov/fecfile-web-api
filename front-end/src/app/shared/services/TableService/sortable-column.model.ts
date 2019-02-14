/**
 * A model for supporting column sorting in an HTML table.
 */
export class SortableColumnModel {
	
	private colName: string;
	private descending: boolean;

	public constructor( colName: string, descending: boolean) {
		this.colName = colName;
		this.descending = descending;
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

}