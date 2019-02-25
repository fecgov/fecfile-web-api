import { Component, Input, NgZone, OnInit, Output, ViewEncapsulation, ViewChild, TemplateRef, OnDestroy } from '@angular/core';
import { FormBuilder, FormGroup, NgForm, Validators } from '@angular/forms';
import { ActivatedRoute, NavigationEnd,  Router } from '@angular/router';
import { style, animate, transition, trigger } from '@angular/animations';
import { TransactionModel } from './model/transaction.model';
import { TransactionsService, GetTransactionsResponse } from './service/transactions.service';
import { TableService } from 'src/app/shared/services/TableService/table.service';
import { SortableColumnModel } from 'src/app/shared/services/TableService/sortable-column.model';
import { PaginationInstance } from 'ngx-pagination';
import { NgbModal } from '@ng-bootstrap/ng-bootstrap';
import { BsModalService, BsModalRef, ModalDirective } from 'ngx-bootstrap/modal';
import { UtilService } from 'src/app/shared/utils/util.service';


@Component({
  selector: 'app-transactions',
  templateUrl: './transactions.component.html',
  styleUrls: ['./transactions.component.scss'],
  encapsulation: ViewEncapsulation.None,
  animations: [
		trigger('fadeInOut', [
			transition(':enter', [
				style({opacity:0}),
				animate(1000, style({opacity:1})) 
      ]),
				transition(':leave', [
				animate(10, style({opacity:0})) 
			])
		])
	]
})
export class TransactionsComponent implements OnInit, OnDestroy {

  @ViewChild('columnOptionsModal')
  public columnOptionsModal: ModalDirective; 

  public transactionsModel: Array<TransactionModel>;
  public totalAmount: number;
  private _formType: string = '';
  public formType: string = '';
  //public formTransactions: FormGroup;
  //public formSubmitted: boolean = false;
  public appliedFilterNames: Array<string> = [];

  private sortableColumnLocalStoragesKey: string = "sortableColumnLocalStoragesKey";

  /**
	 * Array of columns to be made sortable.
	 */
  private sortableColumns: SortableColumnModel[] = [];
  
  /**
	 * A clone of the sortableColumns for reverting user
   * column options on a Cancel.
	 */
	private cloneSortableColumns: SortableColumnModel[] = [];  
	
	/**
	 * Identifies the column currently sorted. 
	 */
	private currentSortedColumn: string;

  // ngx-pagination config
  public maxItemsPerPage: number = 100;
  public directionLinks: boolean = false;
  public autoHide: boolean = true;	
  public config: PaginationInstance;
  
  private columnOptionCount: number = 0;
  private readonly maxColumnOption = 5;

  private allTransactionsSelected: boolean;

  constructor(
    private _fb: FormBuilder,
    private _router: Router,
    private _activatedRoute: ActivatedRoute,
    private _modalService: BsModalService,
    private _transactionsService: TransactionsService,
    private _tableService: TableService,
    private _utilService: UtilService
  ) { }


  /**
   * Initialize the component.
   */
  public ngOnInit(): void {

    this._formType = this._activatedRoute.snapshot.paramMap.get('form_id');
    this.formType = this._formType;
    console.log("transactions for form " + this._formType);

		let paginateConfig: PaginationInstance = {
			// must be a unique id for all each table
			id: 'forms__trx-table-pagination',
			itemsPerPage: 5,
			currentPage: 1
		};	
		this.config = paginateConfig;  

    this.getPage(1);

    // If cached sortableColumns settings in local storage, use it.
    let sortableColumnsJson: string|null = localStorage.getItem(this.sortableColumnLocalStoragesKey);
    if (localStorage.getItem(this.sortableColumnLocalStoragesKey) != null) {
      this.sortableColumns = JSON.parse(sortableColumnsJson);
    }
    else {
      // sort column names must match the domain model names
      let defaultSortColumns = ['type', 'transactionId', 'name', 'date', 'amount'];
      let otherSortColumns = ['state', 'zip', 'aggregate', 'purposeDescription',  
        'contributorEmployer', 'contributorOccupation', 'memoCode', 'memoText',];

      this.sortableColumns = [];
      for (let field of defaultSortColumns) {
        this.sortableColumns.push(new SortableColumnModel(field, false, true, true, false));
      }  
      for (let field of otherSortColumns) {
        this.sortableColumns.push(new SortableColumnModel(field, false, false, false, true));
      } 
    }
    this.cloneSortableColumns = this._utilService.deepClone(this.sortableColumns);

    for (let col of this.sortableColumns) {
      if(col.checked) {
        this.columnOptionCount++;
      }
    }

    // push an applied filter for test
    this.appliedFilterNames.push("Filter " + this.appliedFilterNames.length + 1);
  }


  /**
   * When component is destroyed, save off user column options to be applied upon return.
   */
  public ngOnDestroy(): void {
    localStorage.setItem(this.sortableColumnLocalStoragesKey, JSON.stringify(this.sortableColumns));
  }


  /**
	 * The Transactions for a given page.
	 * 
	 * @param page the page containing the transactions to get
	 */
	public getPage(page: number) : void {
    this.config.currentPage = page;
    this._transactionsService.getFormTrnsactions(this.formType).subscribe( (res:GetTransactionsResponse) => {
      this.transactionsModel = res.transactions;
      this.totalAmount = res.totalAmount;
      this.config.totalItems = res.totalTransactionCount;
      this.allTransactionsSelected = false;
    });  
  }


	/**
	 * Wrapper method for the table service to set the class for sort column styling.
	 * 
	 * @param colName the column to apply the class
	 * @returns string of classes for CSS styling sorted/unsorted classes
	 */
  public getSortClass(colName: string): string {
		return this._tableService.getSortClass(colName, this.currentSortedColumn, this.sortableColumns);
  }  


	/**
	 * Change the sort direction of the table column.
	 * 
	 * @param colName the column name of the column to sort
	 */
	public changeSortDirection(colName: string) : void {
		this.currentSortedColumn = this._tableService.changeSortDirection(colName, this.sortableColumns);
    
    // call server for page data in new direction
    //this.getPage(this.config.currentPage);
  }  
  

  /**
   * Get the SortableColumnModel by name.
   * 
   * @param colName the column name in the SortableColumnModel.
   * @returns the SortableColumnModel matching the colName.
   */
  public getSortableColumn(colName: string) : SortableColumnModel {
    for (let col of this.sortableColumns) {
			if (col.colName == colName) {
				return col;
			}
		}
		return null;
  }


  /**
   * Determine if the column is to be visible in the table.
   * 
   * @param colName 
   * @returns true if visible
   */
  public isColumnVisible(colName: string) : boolean {
    let sortableCol = this.getSortableColumn(colName);
    if (sortableCol) {
      return sortableCol.visible;
    }
    else{
      return false;
    }
  }  


  /**
   * Set the visibility of a column in the table.
   * 
   * @param colName the name of the column to make shown
   * @param visible is true if the columns should be shown
   */
  public setColumnVisible(colName: string, visible: boolean) {
    let sortableCol = this.getSortableColumn(colName);
    if (sortableCol) {
      sortableCol.visible = visible;
    }
  }  


  /**
   * Set the checked property of a column in the table.
   * The checked is true if the column option settings
   * is checked for the column.
   * 
   * @param colName the name of the column to make shown
   * @param checked is true if the columns should be shown
   */
  private setColumnChecked(colName: string, checked: boolean) {
    let sortableCol = this.getSortableColumn(colName);
    if (sortableCol) {
      sortableCol.checked = checked;
    }
  }  


  /**
   * 
   * @param colName Determine if the checkbox column option should be disabled.
   */
  public disableOption(colName: string) : boolean {
    let sortableCol = this.getSortableColumn(colName);
    if (sortableCol) {
      if(!sortableCol.checked && this.columnOptionCount > 
          (this.maxColumnOption - 1)) {
        return true;
      } 
    }
    return false;
  }


  /**
   * Toggle the visibility of a column in the table.
   * 
   * @param colName the name of the column to toggle
   * @param e the click event 
   */
  public toggleVisibility(colName: string, e: any) {

    if (!this.sortableColumns) {
      return;
    }

    // only permit 5 checked at a time
    if (e.target.checked == true) {
      this.columnOptionCount = 0;
      for (let col of this.sortableColumns) {
        if (col.checked) {
          this.columnOptionCount++;
        }
        if (this.columnOptionCount > 5) {
          this.setColumnChecked(colName, false);
          e.target.checked = false;
          this.columnOptionCount--;
          return;
        }
      }
    }
    else {
      this.columnOptionCount--;
    }

    this.applyDisabledColumnOptions();
  }  


  /**
   * Disable the unchecked column options if the max is met.
   */
  private applyDisabledColumnOptions() {
    if (this.columnOptionCount > (this.maxColumnOption - 1)) {
      for (let col of this.sortableColumns) {
        col.disabled = !col.checked;
      }
    }
    else {
      for (let col of this.sortableColumns) {
        col.disabled = false;
      } 
    }
  }


  /**
   * Save the columns to show selected by the user. 
   */
  public saveColumnOptions() {

    for (let col of this.sortableColumns) {
      this.setColumnVisible(col.colName, col.checked);
    }
    this.cloneSortableColumns = this._utilService.deepClone(this.sortableColumns);
    this.columnOptionsModal.hide();
  }


  /**
   * Cancel the request to save columns options.
   */
  public cancelColumnOptions() {
    this.columnOptionsModal.hide();
    this.sortableColumns = this._utilService.deepClone(this.cloneSortableColumns);
  }
  

  /**
   * Toggle checking all types.
   * 
   * @param e the click event 
   */
  public toggleAllTypes(e: any) {
    let checked = (e.target.checked) ? true : false;
    for (let col of this.sortableColumns) {
      this.setColumnVisible(col.colName, checked);
    }    
  }


	/**
	 * Determine if pagination should be shown.
	 */
	public showPagination() : boolean {
		if (this.config.totalItems > this.config.itemsPerPage) {
			return true;
		}
		// otherwise, no show.
		return false;
  }  





  /**
   * View all transactions selected by the user.
   */
  public viewAllSelected() : void {
    alert("View all transactions is not yet supported");
  } 


  /**
   * Print all transactions selected by the user.
   */
  public printAllSelected() : void {
    alert("Print all transactions is not yet supported");
  }  


  /**
   * Export all transactions selected by the user.
   */
  public exportAllSelected() : void {
    alert("Export all transactions is not yet supported");
  }

  /**
   * Link all transactions selected by the user.
   */
  public linkAllSelected() : void {
    alert("Link multiple transaction requirements have not been finalized");
  }


  /**
   * Trash all transactions selected by the user.
   */
  public trashAllSelected() : void {
    alert("Trash all transactions is not yet supported");
  }  


  /**
   * Clone the transaction selected by the user.
   * 
   * @param trx the Transaction to clone
   */
  public cloneTransaction(trx: TransactionModel) : void {
    alert("Clone transaction is not yet supported");
  }


  /**
   * Link the transaction selected by the user.
   * 
   * @param trx the Transaction to link
   */
  public linkTransaction(trx: TransactionModel) : void {
    alert("Link requirements have not been finalized");
  }


  /**
   * View the transaction selected by the user.
   * 
   * @param trx the Transaction to view
   */
  public viewTransaction(trx: TransactionModel) : void {
    alert("View transaction is not yet supported");
  } 


  /**
   * Edit the transaction selected by the user.
   * 
   * @param trx the Transaction to edit
   */
  public editTransaction(trx: TransactionModel) : void {
    alert("Edit transaction is not yet supported");
  }  


  /**
   * Trash the transaction selected by the user.
   * 
   * @param trx the Transaction to trash
   */
  public trashTransaction(trx: TransactionModel) : void {
    alert("Trash transaction is not yet supported");
  }  


  /**
   * Determine the item range shown by the server-side pagination.
   */
  public determineItemRange() : string {
    let start = 0;
    let end = 0;
    if (this.config.currentPage > 0 && this.config.itemsPerPage > 0) {
      
      end = this.config.currentPage * this.config.itemsPerPage;
      start = (end - this.config.itemsPerPage) + 1;
    }
    return start + " - " + end;
  }


  /**
   * Show the option to select/deselect columns in the table.
   */
  public showPinColumns() {
    this.applyDisabledColumnOptions();
    this.columnOptionsModal.show();
  }


  /**
   * Check/Uncheck all transactions in the table.
   */
  public changeAllTransactionsSelected() {
    for (let t of this.transactionsModel) {
      t.selected = this.allTransactionsSelected;
    }
  }

}
