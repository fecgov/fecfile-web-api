import { OrderByPipe } from './../../pipes/order-by/order-by.pipe';
import { Injectable } from '@angular/core';
import { SortableColumnModel } from './sortable-column.model';



@Injectable({
  providedIn: 'root'
})
export class TableService {

  constructor(private _orderByPipe: OrderByPipe) { }


  /**
	 * Determine if a given column is currently sorted and style the UI accordingly.
	 *
	 * @param colName the column to check if sorted
	 * @param currentSortedColumn the column currently sorted
	 * @param sortableColumns all possible columns to sort
	 * @returns a string of classes for CSS styling the column "colName" as sorted or not. Class "fec_sortable_col"
	 * 			is given to all columns that may be sorted.  Class "sort-true" will style the sort as descending.
	 * 			Class "sort-false" will style as ascending and false will show no sort.
	 */
  public getSortClass(colName: string, currentSortedColumn: string, sortableColumns: SortableColumnModel[]): string {

    const col: SortableColumnModel = this.getColumnByName(currentSortedColumn, sortableColumns);
    let sortCol = '';

    if (col) {
      // if the colName is the currently sorted column, determing the sort direction and return either sort-true or sort-false
      // for ascending and descending respectively.  Otherwise return false for no sort direction as the column is not sorted.
      sortCol = (colName === col.colName) ? 'sort-' + col.descending : 'false';
    }
    return 'table__sortable_col ' + sortCol;
  }


  /**
	 * Set the column to indicate it is sorted in a specific direction.
	 *
	 * @param colName the column name to set as sorted
	 * @param sortableColumns all possible columns to sort
	 * @param descending sort direction will be descending if true
	 * @returns the name of sorted column or empty string if the column is not in the sortableColumns array
	 */
  public setSortDirection(colName: string, sortableColumns: SortableColumnModel[], descending: boolean): string {

    for (const col of sortableColumns) {
      if (col.colName === colName) {
        col.descending = descending;
        return colName;
      }
    }
    return '';
  }


  /**
	 * Change the sort direction on a given column.
	 *
	 * Typical usage of this
	 * method is in the template on the <th> cell of the column.  When clicked,
	 * this method will change the direction of the column in the sortableColumns.
	 *
	 * @param colName the column name of the column to sort
	 * @param sortableColumns all possible columns to sort
	 * @returns a string of the column name sorted or an empty string
	 * 			if colName is not found in sortableColumns.
	 */
  public changeSortDirection(colName: string, sortableColumns: SortableColumnModel[]): string {

    for (const col of sortableColumns) {
      if (col.colName === colName) {
        col.descending = !col.descending;
        return colName;
      }
    }
    // not found
    return '';
  }


  /**
  * Given a column name find it's SortableColumnModel object in the array of columns.
  *
  * @param columnName the column name to find
  * @param sortableColumns all possible columns
  * @returns the SortableColumnModel of the columnName
  */
  public getColumnByName(columnName: string, sortableColumns: SortableColumnModel[]): SortableColumnModel {
    for (const col of sortableColumns) {
      if (col.colName === columnName) {
        return col;
      }
    }
  }

  /**
   * Returns true if direction of the selected column is descending, and false if ascending
   * @param columnName the column to find
   * @param sortableColumns  all possible columns
   * @returns true if direction of the selected column is descending, and false if ascending
   */
  public getBinarySortDirection(columnName: string, sortableColumns: SortableColumnModel[]): boolean {
    for (const col of sortableColumns) {
      if (col.colName === columnName) {
        return col.descending;
      }
    }
  }

  /**
 *
 * @param array
 * @param sortColumnName
 * @param descending
 */
  public sort(array: any, sortColumnName: string, descending: boolean) {
    const direction = descending ? -1 : 1;
    this._orderByPipe.transform(array, { property: sortColumnName, direction: direction });
    return array;
  }

}
