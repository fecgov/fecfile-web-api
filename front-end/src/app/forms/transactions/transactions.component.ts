import { Component, Input, NgZone, OnInit, Output, ViewEncapsulation, ViewChild } from '@angular/core';
import { FormBuilder, FormGroup, NgForm, Validators } from '@angular/forms';
import { ActivatedRoute, NavigationEnd,  Router } from '@angular/router';
import { Observable, of } from 'rxjs';
import { TransactionModel } from './model/transaction.model';
import { TransactionsService, GetTransactionsResponse } from './service/transactions.service';
import { TableService } from 'src/app/shared/services/TableService/table.service';
import { SortableColumnModel } from 'src/app/shared/services/TableService/sortable-column.model';
import { PaginationInstance } from 'ngx-pagination';


@Component({
  selector: 'app-transactions',
  templateUrl: './transactions.component.html',
  styleUrls: ['./transactions.component.scss'],
  encapsulation: ViewEncapsulation.None
})
export class TransactionsComponent implements OnInit {
  
  public transactionsModel: Array<TransactionModel>;
  public totalAmount: number;
  public currentStep: string = 'step_1';
  public step: string = '';
  private _formType: string = '';
  public formType: string = '';
  public formTransactions: FormGroup;
  public formSubmitted: boolean = false;
  public appliedFilterNames: Array<string> = [];

  /**
	 * Array of columns to be made sortable.
	 */
	private sortableColumns: SortableColumnModel[];
	
	/**
	 * Identifies the column currently sorted. 
	 */
	private currentSortedColumn: string;

  // ngx-pagination config
  public maxItemsPerPage: number = 100;
  public directionLinks: boolean = false;
  public autoHide: boolean = true;	
	public config: PaginationInstance;

  constructor(
    private _fb: FormBuilder,
    private _router: Router,
    private _activatedRoute: ActivatedRoute,
    private _transactionsService: TransactionsService,
    private _tableService: TableService
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

		// sort column names must match the domain model names
    let sortColumns = ['type', 'transactionId', 'name', 'date', 'amount'];

		this.sortableColumns = [];
		for (let field of sortColumns) {
			this.sortableColumns.push(new SortableColumnModel(field, false));
    }  

    this.formTransactions = this._fb.group({
      // transactionCategory: [null, [
      //   Validators.required
      // ]],
      // transactionType: [null, [
      //   Validators.required
      //]]
    });

    // push an applied filter for test
    this.appliedFilterNames.push("Filter " + this.appliedFilterNames.length + 1);
  }


  /**
	 * The Transactions for a given page.
	 * 
	 * @param page the page containing the transactions to get
	 */
	public getPage(page: number) {
    this.config.currentPage = page;
    this._transactionsService.getFormTrnsactions(this.formType).subscribe( (res:GetTransactionsResponse) => {
      this.transactionsModel = res.transactions;
      this.totalAmount = res.totalAmount;
      this.config.totalItems = res.totalTransactionCount;
    });  
  }


  /**
   * Validate the form. 
   */
  public doValidateTransaction() {
    console.log('doValidateTransaction: ');
    console.log('this.formTransactions: ', this.formTransactions);
    console.log("save transactions not yet supported in backend");

    this.formSubmitted = true;

    if(this.formTransactions.valid) {
      this.formSubmitted = false;
    }
    return;
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
	public changeSortDirection(colName: string) {
		this.currentSortedColumn = this._tableService.changeSortDirection(colName, this.sortableColumns);
    
    // call server for page data in new direction
    //this.getPage(this.config.currentPage);
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
  

}
