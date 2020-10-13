import { MessageService } from 'src/app/shared/services/MessageService/message.service';
import { Router } from '@angular/router';
import { Component, Input, OnInit, ViewEncapsulation, ViewChild, OnDestroy , ChangeDetectionStrategy } from '@angular/core';
import { style, animate, transition, trigger } from '@angular/animations';
import { PaginationInstance } from 'ngx-pagination';
import { ModalDirective } from 'ngx-bootstrap/modal';
import { ContactModel } from '../model/contacts.model';
import { SortableColumnModel } from 'src/app/shared/services/TableService/sortable-column.model';
import { ContactsService, GetContactsResponse } from '../service/contacts.service';
import { TableService } from 'src/app/shared/services/TableService/table.service';
import { UtilService } from 'src/app/shared/utils/util.service';
import { ActiveView } from '../contacts.component';
import { ContactsMessageService } from '../service/contacts-message.service';
import { Subscription } from 'rxjs/Subscription';
import { ConfirmModalComponent, ModalHeaderClassEnum } from 'src/app/shared/partials/confirm-modal/confirm-modal.component';
import { DialogService } from 'src/app/shared/services/DialogService/dialog.service';
import { ContactFilterModel } from '../model/contacts-filter.model';
import { CONTEXT_NAME } from '@angular/compiler/src/render3/view/util';
import { AuthService} from '../../shared/services/AuthService/auth.service';
import {NgbModal} from '@ng-bootstrap/ng-bootstrap';
import {ContactDetailsModalComponent} from '../contact-details-modal/contact-details-modal.component';
import {InputDialogService} from '../../shared/service/InputDialogService/input-dialog.service';

@Component({
  selector: 'app-contacts-table',
  templateUrl: './contacts-table.component.html',
  styleUrls: [
    './contacts-table.component.scss'
  ],
  encapsulation: ViewEncapsulation.None,
  /* animations: [
    trigger('fadeInOut', [
      transition(':enter', [
        style({ opacity: 0 }),
        animate(500, style({ opacity: 1 }))
      ]),
      transition(':leave', [
        animate(0, style({ opacity: 0 }))
      ])
    ])
  ] */
})
export class ContactsTableComponent implements OnInit, OnDestroy {

  dummyData = {
    'contactLog': [
      {
        'dateTime': '03/05/2020, 4:35pm',
        'info': '156 Jupiter Lan',
        'user': 'Smith, John'
      },
      {
        'dateTime': '03/05/2020, 4:30pm',
        'info': '156 Jupit',
        'user': 'Smith, John'
      },
       {
        'dateTime': '03/05/2020, 4:15pm',
        'info': '156 Jupit',
        'user': 'Smith, John'
      },
       {
        'dateTime': '03/05/2020, 4:35pm',
        'info': '15',
        'user': 'Smith, John'
      },
    ]
  };
  @ViewChild('columnOptionsModal')
  public columnOptionsModal: ModalDirective;

  @Input()
  public formType: string;

  @Input()
  public reportId: string;

  @Input()
  public tableType: string;

  public contactsModel: Array<ContactModel>;
  public totalAmount: number;
  public contactsView = ActiveView.contacts;
  public recycleBinView = ActiveView.recycleBin;
  public bulkActionDisabled = true;
  public bulkActionCounter = 0;

  // ngx-pagination config
  public pageSizes: number[] = UtilService.PAGINATION_PAGE_SIZES;
  public maxItemsPerPage: number = this.pageSizes[0];
  public paginationControlsMaxSize: number = 10;
  public directionLinks: boolean = false;
  public autoHide: boolean = true;
  public config: PaginationInstance;
  public numberOfPages: number = 0;
  public pageNumbers: number[] = [];
  public gotoPage: number = 1;

  private filters: ContactFilterModel;
  // private keywords = [];
  private firstItemOnPage = 0;
  private lastItemOnPage = 0;


  // Local Storage Keys
  private readonly contactSortableColumnsLSK =
    'contacts.ctn.sortableColumn';
  private readonly recycleSortableColumnsLSK =
    'contacts.recycle.sortableColumn';
  private readonly contactCurrentSortedColLSK =
    'contacts.ctn.currentSortedColumn';
  private readonly recycleCurrentSortedColLSK =
    'contacts.recycle.currentSortedColumn';
  private readonly contactPageLSK =
    'contacts.ctn.page';
  private readonly recyclePageLSK =
    'contacts.recycle.page';
  private readonly filtersLSK =
    'contacts.filters';

  /**.
	 * Array of columns to be made sortable.
	 */
  private sortableColumns: SortableColumnModel[] = [];

  /**
	 * A clone of the sortableColumns for reverting user
   * column options on a Cancel.
	 */
  private cloneSortableColumns: SortableColumnModel[] = [];

  /**
	 * Identifies the column currently sorted by name.
	 */
  private currentSortedColumnName: string;

  /**
   * Subscription for messags sent from the parent component to show the PIN Column
   * options.
   */
  private showPinColumnsSubscription: Subscription;


  /**
   * Subscription for running the keyword and filter search
   * to the contacts obtained from the server.
   */
  private keywordFilterSearchSubscription: Subscription;

  private columnOptionCount = 0;
  public maxColumnOption = 5;
  public allContactsSelected: boolean;

  constructor(
    private _contactsService: ContactsService,
    private _contactsMessageService: ContactsMessageService,
    private _tableService: TableService,
    private _utilService: UtilService,
    private _dialogService: DialogService,
    private _authService: AuthService,
    private _router: Router,
    private _messageService: MessageService,
    private contactModal: InputDialogService,
  ) {
    this.showPinColumnsSubscription = this._contactsMessageService.getShowPinColumnMessage()
      .subscribe(
        message => {
          this.showPinColumns();
        }
      );

    this.keywordFilterSearchSubscription = this._contactsMessageService.getDoKeywordFilterSearchMessage()
      .subscribe(
        (filters: ContactFilterModel) => {
          if (filters) {
            this.filters = filters;
            /*if (filters.formType) {
              this.formType = filters.formType;
            }*/
          }
          this.getPage(this.config.currentPage);
        }
      );

    this._messageService.getMessage().subscribe(data => {
      if (data) {
        if (data.messageFrom === 'contactDetails' && data.message === 'updateContact' && data.contact ) {
          this.contactsModel.forEach((e) => {
          if (e.id === data.contact.entity_id) {
             const index = this.contactsModel.indexOf(e);
             const updatedContact = this._contactsService.convertRowToModelPut(data.contact);
             this.contactsModel[index] = updatedContact;
            }
          });
        }
      }
    });
  }


  /**
   * Initialize the component.
   */
  public ngOnInit(): void {
    const paginateConfig: PaginationInstance = {
      id: 'forms__ctn-table-pagination',
      itemsPerPage: this.maxItemsPerPage,
      currentPage: 1
    };
    this.config = paginateConfig;
    // this.config.currentPage = 1;

    this.getCachedValues();
    this.cloneSortableColumns = this._utilService.deepClone(this.sortableColumns);

    for (const col of this.sortableColumns) {
      if (col.checked) {
        this.columnOptionCount++;
      }
    }


    this.getPage(this.config.currentPage);
  }


  /**
   * A method to run when component is destroyed.
   */
  public ngOnDestroy(): void {
    this.setCachedValues();
    this.showPinColumnsSubscription.unsubscribe();
    this.keywordFilterSearchSubscription.unsubscribe();
  }


  /**
	 * The Contacts for a given page.
	 *
	 * @param page the page containing the contacts to get
	 */
  public getPage(page: number): void {

    this.bulkActionCounter = 0;
    this.bulkActionDisabled = true;
    this.gotoPage = page;

    switch (this.tableType) {
      case this.contactsView:
        this.getContactsPage(page);
        break;
      case this.recycleBinView:
        this.getRecyclingPage(page);
        this.maxColumnOption = 6;
        break;
      default:
        break;
    }
  }

  /**
   * onChange for maxItemsPerPage.
   *
   * @param pageSize the page size to get
   */
  public onMaxItemsPerPageChanged(pageSize: number): void {
    this.config.currentPage = 1;
    this.gotoPage = 1;
    this.config.itemsPerPage = pageSize;
    this.getPage(this.config.currentPage);
  }

  /**
   * onChange for gotoPage.
   *
   * @param page the page to get
   */
  public onGotoPageChange(page: number): void {
    if (this.config.currentPage == page) {
      return;
    }
    this.config.currentPage = page;
    this.getPage(this.config.currentPage);
  }

  /**
	 * The Contacts for a given page.
	 *
	 * @param page the page containing the contacts to get
	 */
  public getContactsPage(page: number): void {

    this.config.currentPage = page;

    let sortedCol: SortableColumnModel =
      this._tableService.getColumnByName(this.currentSortedColumnName, this.sortableColumns);

    if (!sortedCol) {
      this.setSortDefault();
      sortedCol = this._tableService.getColumnByName(this.currentSortedColumnName, this.sortableColumns);
    }

    if (sortedCol) {
      if (sortedCol.descending === undefined || sortedCol.descending === null) {
        sortedCol.descending = false;
      }
    } else {
      sortedCol = new SortableColumnModel('', false, false, false, false);
    }

    const serverSortColumnName = this._contactsService.
      mapToSingleServerName(this.currentSortedColumnName);

    this._contactsService.getContacts(this.formType, this.reportId,
        page, this.config.itemsPerPage,
        serverSortColumnName, sortedCol.descending, this.filters)
      .subscribe((res: GetContactsResponse) => {
        //console.log(" getContactsPage res =", res)
        this.contactsModel = [];

        // fixes an issue where no items shown when current page != 1 and new filter
        // result has only 1 page.
        if (res.totalPages === 1) {
          this.config.currentPage = 1;
        }

        this._contactsService.addUIFileds(res);
        this._contactsService.mockApplyFilters(res, this.filters);
        const contactsModelL = this._contactsService.mapFromServerFields(res.contacts);
        this.contactsModel = contactsModelL;

        this.contactsModel.forEach((e) => {
          e.setContactLog(this.dummyData.contactLog);
        });
        this.config.totalItems = res.totalcontactsCount ? res.totalcontactsCount : 0;
        this.numberOfPages = res.totalPages;

        this.pageNumbers = Array.from(new Array(this.numberOfPages), (x, i) => i + 1).sort((a, b) => b - a);
        this.allContactsSelected = false;
      });
  }


  /**
	 * The Contacts for the recycling bin.
	 *
	 * @param page the page containing the contacts to get
	 */
  public getRecyclingPage(page: number): void {

    this.config.currentPage = page;

    let sortedCol: SortableColumnModel =
      this._tableService.getColumnByName(this.currentSortedColumnName, this.sortableColumns);

    // smahal: quick fix for sortCol issue not retrived from cache
    if (!sortedCol) {
      this.setSortDefault();
      sortedCol = this._tableService.getColumnByName(this.currentSortedColumnName, this.sortableColumns);
    }

    if (sortedCol) {
      if (sortedCol.descending === undefined || sortedCol.descending === null) {
        sortedCol.descending = false;
      }
    } else {
      sortedCol = new SortableColumnModel('', false, false, false, false);
    }

    // const serverSortColumnName = this._contactsService.
    //   mapToSingleServerName(this.currentSortedColumnName);

    this._contactsService.getUserDeletedContacts(page, this.config.itemsPerPage,
      this.currentSortedColumnName,
      sortedCol.descending, this.filters)
      .subscribe((res: GetContactsResponse) => {
        //console.log(" getRecyclingPage res =", res)
        this.contactsModel = [];

        // fixes an issue where no items shown when current page != 1 and new filter
        // result has only 1 page.
        if (res.totalPages === 1) {
          this.config.currentPage = 1;
        }

        this._contactsService.addUIFileds(res);

        this.contactsModel = res.contacts;

        this._contactsService.addUIFileds(res);
        this._contactsService.mockApplyFilters(res, this.filters);
        const contactsModelL = this._contactsService.mapFromServerFields(res.contacts);
        this.contactsModel = contactsModelL;

        // handle non-numeric amounts
        // TODO handle this server side in API
        // for (const model of this.contactsModel) {
        //   model.amount = model.amount ? model.amount : 0;
        //   model.aggregate = model.aggregate ? model.aggregate : 0;
        // }

        this.config.totalItems = res.totalcontactsCount ? res.totalcontactsCount : 0;
        this.numberOfPages = res.totalPages;

        this.pageNumbers = Array.from(new Array(this.numberOfPages), (x, i) => i + 1).sort((a, b) => b - a);
        this.allContactsSelected = false;



      });
  }


  /**
	 * Wrapper method for the table service to set the class for sort column styling.
	 *
	 * @param colName the column to apply the class
	 * @returns string of classes for CSS styling sorted/unsorted classes
	 */
  public getSortClass(colName: string): string {
    return this._tableService.getSortClass(colName, this.currentSortedColumnName, this.sortableColumns);
  }


  /**
	 * Change the sort direction of the table column.
	 *
	 * @param colName the column name of the column to sort
	 */
  public changeSortDirection(colName: string): void {
    this.currentSortedColumnName = this._tableService.changeSortDirection(colName, this.sortableColumns);

    // TODO this could be done client side or server side.
    // call server for page data in new direction
    this.getPage(this.config.currentPage);
  }


  /**
   * Get the SortableColumnModel by name.
   *
   * @param colName the column name in the SortableColumnModel.
   * @returns the SortableColumnModel matching the colName.
   */
  public getSortableColumn(colName: string): SortableColumnModel {
    for (const col of this.sortableColumns) {
      if (col.colName === colName) {
        return col;
      }
    }
    return new SortableColumnModel('', false, false, false, false);
  }


  /**
   * Determine if the column is to be visible in the table.
   *
   * @param colName
   * @returns true if visible
   */
  public isColumnVisible(colName: string): boolean {
    const sortableCol = this.getSortableColumn(colName);
    if (sortableCol) {
      return sortableCol.visible;
    } else {
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
    const sortableCol = this.getSortableColumn(colName);
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
    const sortableCol = this.getSortableColumn(colName);
    if (sortableCol) {
      sortableCol.checked = checked;
    }
  }


  /**
   *
   * @param colName Determine if the checkbox column option should be disabled.
   */
  public disableOption(colName: string): boolean {
    const sortableCol = this.getSortableColumn(colName);
    if (sortableCol) {
      if (!sortableCol.checked && this.columnOptionCount >
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
    if (e.target.checked === true) {
      this.columnOptionCount = 0;
      for (const col of this.sortableColumns) {
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
    } else {
      this.columnOptionCount--;
    }

    this.applyDisabledColumnOptions();
  }


  /**
   * Disable the unchecked column options if the max is met.
   */
  private applyDisabledColumnOptions() {
    if (this.columnOptionCount > (this.maxColumnOption - 1)) {
      for (const col of this.sortableColumns) {
        col.disabled = !col.checked;
      }
    } else {
      for (const col of this.sortableColumns) {
        col.disabled = false;
      }
    }
  }


  /**
   * Save the columns to show selected by the user.
   */
  public saveColumnOptions() {

    for (const col of this.sortableColumns) {
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
    const checked = (e.target.checked) ? true : false;
    for (const col of this.sortableColumns) {
      this.setColumnVisible(col.colName, checked);
    }
  }


  /**
	 * Determine if pagination should be shown.
	 */
  public showPagination(): boolean {
    if (!this.autoHide) {
      return true;
    }
    if (this.config.totalItems > this.config.itemsPerPage) {
      return true;
    }
    // otherwise, no show.
    return false;
  }


  /**
   * View all contacts selected by the user.
   */
  public viewAllSelected(): void {
    alert('View all contacts is not yet supported');
  }


  /**
   * Print all contacts selected by the user.
   */
  public printAllSelected(): void {
    alert('Print all contacts is not yet supported');
  }


  /**
   * Export all contacts selected by the user.
   */
  public exportAllSelected(): void {
    alert('Export all contacts is not yet supported');
  }


  /**
   * Link all contacts selected by the user.
   */
  public linkAllSelected(): void {
    alert('Link multiple contact requirements have not been finalized');
  }


  /**
   * Trash all contacts selected by the user.
   */
  public trashAllSelected(): void {
    let conIds = '';
    const selectedContacts: Array<ContactModel> = [];
    for (const con of this.contactsModel) {
      if (con.selected && con.activeTransactionsCnt === 0) {
        selectedContacts.push(con);
        conIds += con.id + ', ';
      }
    }

    conIds = conIds.substr(0, conIds.length - 2);

    this._dialogService
      .confirm('You are about to delete these contacts.   ' + conIds, ConfirmModalComponent, 'Warning!')
      .then(res => {
        if (res === 'okay') {
          this._contactsService
            .trashOrRestoreContacts('trash', selectedContacts)
            .subscribe((res: GetContactsResponse) => {
              this.getContactsPage(this.config.currentPage);

              let afterMessage = '';
              if (selectedContacts.length === 1) {
                afterMessage = `Transaction ${selectedContacts[0].id}
                  has been successfully deleted and sent to the recycle bin.`;
              } else {
                afterMessage = 'Transactions have been successfully deleted and sent to the recycle bin.   ' + conIds;
              }

              this._dialogService.confirm(
                afterMessage,
                ConfirmModalComponent,
                'Success!',
                false,
                ModalHeaderClassEnum.successHeader
              );
            });
        } else if (res === 'cancel') {
        }
      });

  }


  /**
   * Clone the contact selected by the user.
   *
   * @param ctn the Contact to clone
   */
  public cloneContact(ctn: ContactModel): void {
    alert('Clone Contact is not yet supported');
  }


  /**
   * Link the contact selected by the user.
   *
   * @param ctn the Contact to link
   */
  public linkContact(ctn: ContactModel): void {
    alert('Link requirements have not been finalized');
  }


  /**
   * View the contact selected by the user.
   *
   * @param ctn the Contact to view
   */
  public viewContact(ctn: ContactModel): void {
    alert('View Contact is not yet supported');
  }

/**
   * View the contact selected by the user.
   *
   * @param ctn the Contact to view
   */
  public viewActivity(ctn: ContactModel): void {
    let entityList :ContactModel[] = [];
    entityList.push(ctn);
    this.setContactsListAndNavigateToAllTransactions(entityList);
  }

  public viewActivityAllSelected(): void {
    this.setContactsListAndNavigateToAllTransactions(null);
  }

  private setContactsListAndNavigateToAllTransactions(entityList: ContactModel[]) {
    if (!entityList) {
      entityList = this.getAllSelectedContacts();
    }
    this._contactsService.entityListToFilterBy = entityList;
    this._router.navigate([`/forms/form/global`], {
      queryParams: { step: 'transactions', transactionCategory: 'receipts', allTransactions: true, entityFilter: true }
    });
  }

  private getAllSelectedContacts() {
    return this.contactsModel.filter(contact => {
      return contact.selected;
    });
  }



  /**
   * Edit the contact selected by the user.
   *
   * @param ctn the Contact to edit
   */
  public editContact(ctn: ContactModel): void {
    this._contactsMessageService.sendEditContactMessage(ctn);
  }


  /**
   * Trash the contact selected by the user.
   *
   * @param ctn the Contact to trash
   */
  public trashContact(ctn: ContactModel): void {
    this._dialogService
      .confirm('You are about to delete this contact ' + ctn.id + '.', ConfirmModalComponent, 'Warning!')
      .then(res => {
        if (res === 'okay') {
          this._contactsService
            .trashOrRestoreContacts('trash', [ctn])
            .subscribe((res: GetContactsResponse) => {
              if (res['result'] === 'success') {
                this.getContactsPage(this.config.currentPage);
                this._dialogService.confirm(
                  'Contact has been successfully deleted and sent to recycle bin. ' + ctn.id,
                  ConfirmModalComponent,
                  'Success!',
                  false,
                  ModalHeaderClassEnum.successHeader
                );
              } else {
                this._dialogService.confirm(
                  'Contact has not been successfully deleted and sent to recycle bin. ' + ctn.id,
                  ConfirmModalComponent,
                  'Warning!',
                  false,
                  ModalHeaderClassEnum.errorHeader
                );
              }
            });
        } else if (res === 'cancel') {
        }
      });
  }



  /**
   * Restore a trashed contact from the recyle bin.
   *
   * @param ctn the Contact to restore
   */
  public restoreContact(ctn: ContactModel): void {
    this._dialogService
      .confirm('You are about to restore contact ' + ctn.id + '.', ConfirmModalComponent, 'Warning!')
      .then(res => {
        if (res === 'okay') {
          // this._transactionsService.restoreTransaction(trx)
          //   .subscribe((res: GetTransactionsResponse) => {
          this._contactsService
            .trashOrRestoreContacts('restore', [ctn])
            .subscribe((res: GetContactsResponse) => {
              this.getRecyclingPage(this.config.currentPage);
              this._dialogService.confirm(
                'Contact ' + ctn.id + ' has been restored!',
                ConfirmModalComponent,
                'Success!',
                false,
                ModalHeaderClassEnum.successHeader
              );
            });
        } else if (res === 'cancel') {
        }
      });
  }

  /**
   * Delete selected contacts from the the recyle bin.
   *
   * @param ctn the Contact to delete
   */
  public deleteRecyleBin(): void {

    let beforeMessage = '';
    // if (this.bulkActionCounter === 1) {
    //   let id = '';
    //   for (const ctn of this.contactsModel) {
    //     if (ctn.selected) {
    //       id = ctn.id;
    //     }
    //   }
    //   beforeMessage = (id !== '') ?
    //     'Are you sure you want to permanently delete Contact ' + id + '?' :
    //     'Are you sure you want to permanently delete this Contact?';
    // } else {
    //   beforeMessage = 'Are you sure you want to permanently delete these contacts?';
    // }

    let cntIds = '';
    const selectedContacts: Array<ContactModel> = [];
    for (const ctn of this.contactsModel) {
      if (ctn.selected) {
        selectedContacts.push(ctn);
        cntIds += ctn.id + ', ';
      }
    }

    cntIds = cntIds.substr(0, cntIds.length - 2);

    if (selectedContacts.length === 1) {
      beforeMessage = 'Are you sure you want to permanently delete Contact ' +
        selectedContacts[0].id + '?';
    } else {
      beforeMessage = 'Are you sure you want to permanently delete these contacts?' + cntIds;
    }

    this._dialogService
      .confirm(beforeMessage,
        ConfirmModalComponent,
        'Caution!')
      .then(res => {
        if (res === 'okay') {
          this._contactsService.deleteRecycleBinContact(selectedContacts)
            .subscribe((res: GetContactsResponse) => {
              this.getRecyclingPage(this.config.currentPage);

              let afterMessage = '';
              if (selectedContacts.length === 1) {
                  afterMessage = `Contact ${selectedContacts[0].id} has been successfully deleted`;
              } else {
                afterMessage = 'Contacts have been successfully deleted.' + cntIds;
              }
              this._dialogService
                .confirm(afterMessage,
                  ConfirmModalComponent, 'Success!', false, ModalHeaderClassEnum.successHeader);
           });
        } else if (res === 'cancel') {
        }
      });
  }



  /**
   * Determine the item range shown by the server-side pagination.
   */
  public determineItemRange(): string {

    let start = 0;
    let end = 0;
    // this.numberOfPages = 0;
    this.config.currentPage = this._utilService.isNumber(this.config.currentPage) ?
      this.config.currentPage : 1;

    if (!this.contactsModel) {
      return '0';
    }

    if (this.config.currentPage > 0 && this.config.itemsPerPage > 0
      && this.contactsModel.length > 0) {
      // this.calculateNumberOfPages();

      if (this.config.currentPage === this.numberOfPages) {
        // end = this.contactsModel.length;
        end = this.config.totalItems;
        start = (this.config.currentPage - 1) * this.config.itemsPerPage + 1;
      } else {
        end = this.config.currentPage * this.config.itemsPerPage;
        start = (end - this.config.itemsPerPage) + 1;
      }
      // // fix issue where last page shown range > total items (e.g. 11-20 of 19).
      // if (end > this.contactsModel.length) {
      //   end = this.contactsModel.length;
      // }
    }
    this.firstItemOnPage = start;
    this.lastItemOnPage = end;
    return start + ' - ' + end;
  }

  public showPageSizes(): boolean {
    if (this.config && this.config.totalItems && this.config.totalItems > 0) {
      return true;
    }
    return false;
  }

  /**
   * Show the option to select/deselect columns in the table.
   */
  public showPinColumns() {
    this.applyDisabledColumnOptions();
    this.columnOptionsModal.show();
  }


  /**
   * Check/Uncheck all contacts in the table.
   */
  public changeAllContactsSelected() {

    // TODO Iterating over the trsnactionsModel and setting the selected prop
    // works when we have server-side pagination as the model will only contain
    // contacts for the current page.

    // Until the server is ready for pagination,
    // we are getting the entire set of tranactions (> 500)
    // and must only count and set the selected prop for the items
    // on the current page.

    this.bulkActionCounter = 0;
    // for (const t of this.contactsModel) {
    //   t.selected = this.allContactsSelected;
    //   if (this.allContactsSelected) {
    //     this.bulkActionCounter++;
    //   }
    // }

    // TODO replace this with the commented code above when server pagination is ready.
    for (let i = (this.firstItemOnPage - 1); i <= (this.lastItemOnPage - 1); i++) {
      this.contactsModel[i].selected = this.allContactsSelected;
      if (this.allContactsSelected) {
        this.bulkActionCounter++;
      }
    }
    this.bulkActionDisabled = !this.allContactsSelected;
  }


  /**
   * Check if the view to show is Contacts.
   */
  public isContactViewActive() {
    return this.tableType === this.contactsView ? true : false;
  }


  /**
   * Check if the view to show is Recycle Bin.
   */
  public isRecycleBinViewActive() {
    return this.tableType === this.recycleBinView ? true : false;
  }


  /**
   * Check for multiple rows checked in the table
   * and disable/enable the bulk action button
   * accordingly.
   *
   * @param the event payload from the click
   */
  public checkForMultiChecked(e: any): void {

    if (e.target.checked) {
      this.bulkActionCounter++;
    } else {
      this.allContactsSelected = false;
      if (this.bulkActionCounter > 0) {
        this.bulkActionCounter--;
      }
    }

    // Contact View shows bulk action when more than 1 checked
    // Recycle Bin shows delete action when 1 or more checked.
    const count = this.isContactViewActive() ? 1 : 0;
    this.bulkActionDisabled = (this.bulkActionCounter > count) ? false : true;
  }


  /**
   * Get cached values from session.
   */
  private getCachedValues() {
    this.applyFiltersCache();
    switch (this.tableType) {
      case this.contactsView:
        this.applyColCache(this.contactSortableColumnsLSK);
        this.applyCurrentSortedColCache(this.contactCurrentSortedColLSK);
        this.applyCurrentPageCache(this.contactPageLSK);
        break;
      case this.recycleBinView:
        this.applyColCache(this.recycleSortableColumnsLSK);
        this.applyColumnsSelected();
        this.applyCurrentSortedColCache(this.recycleCurrentSortedColLSK);
        this.applyCurrentPageCache(this.recyclePageLSK);
        break;
      default:
        break;
    }
  }


  /**
   * Columns selected in the PIN dialog from the contacts view
   * need to be applied to the Recycling Bin table.
   */
  private applyColumnsSelected() {
    const key = this.contactSortableColumnsLSK;
    const sortableColumnsJson: string | null = localStorage.getItem(key);
    if (localStorage.getItem(key) != null) {
      const ctnCols: SortableColumnModel[] = JSON.parse(sortableColumnsJson);
      for (const col of ctnCols) {
        this._tableService.getColumnByName(col.colName,
          this.sortableColumns).visible = col.visible;
      }
    }
  }


  /**
   * Apply the filters from the cache.
   */
  private applyFiltersCache() {
    const filtersJson: string | null = localStorage.getItem(this.filtersLSK);
    if (filtersJson != null) {
      this.filters = JSON.parse(filtersJson);
    } else {
      // Just in case cache has an unexpected issue, use default.
      this.filters = null;
    }
  }


  /**
   * Get the column and their settings from the cache and apply it to the component.
   * @param key the key to the value in the local storage cache
   */
  private applyColCache(key: string) {
    const sortableColumnsJson: string | null = localStorage.getItem(key);
    if (localStorage.getItem(key) != null) {
      this.sortableColumns = JSON.parse(sortableColumnsJson);
    } else {
      // Just in case cache has an unexpected issue, use default.
      this.setSortableColumns();
    }
  }


  /**
   * Get the current sorted column from the cache and apply it to the component.
   * @param key the key to the value in the local storage cache
   */
  private applyCurrentSortedColCache(key: string) {
    const currentSortedColumnJson: string | null =
      localStorage.getItem(key);
    let currentSortedColumnL: SortableColumnModel = null;
    if (currentSortedColumnJson) {
      currentSortedColumnL = JSON.parse(currentSortedColumnJson);

      // sort by the column direction previously set
      this.currentSortedColumnName = this._tableService.setSortDirection(currentSortedColumnL.colName,
        this.sortableColumns, currentSortedColumnL.descending);
    } else {
      this.setSortDefault();
    }
  }


  /**
   * Get the current page from the cache and apply it to the component.
   * @param key the key to the value in the local storage cache
   */
  private applyCurrentPageCache(key: string) {
    const currentPageCache: string =
      localStorage.getItem(key);
      if (currentPageCache) {
        if (this._utilService.isNumber(currentPageCache)) {
          this.config.currentPage = this._utilService.toInteger(currentPageCache);
        } else {
          this.config.currentPage = 1;
        }
      } else {
        this.config.currentPage = 1;
      }
  }


  /**
   * Retrieve the cahce values from local storage and set the
   * component's class variables.
   */
  private setCachedValues() {

    switch (this.tableType) {
      case this.contactsView:
        this.setCacheValuesforView(this.contactSortableColumnsLSK,
          this.contactCurrentSortedColLSK, this.contactPageLSK);
          this.contactPageLSK
        break;
      case this.recycleBinView:
        this.setCacheValuesforView(this.recycleSortableColumnsLSK,
          this.recycleCurrentSortedColLSK, this.recyclePageLSK);
          this.recyclePageLSK
        break;
      default:
        break;
    }
  }

 /**
   * Set the currently sorted column and current page in the cache.
   *
   * @param columnsKey the column settings key for the cache
   * @param sortedColKey currently sorted column key for the cache
   * @param pageKey current page key from the cache
   */
  private setCacheValuesforView(columnsKey: string, sortedColKey: string,
    pageKey: string) {

    // shared between ctn and recycle tables
    localStorage.setItem(columnsKey,
      JSON.stringify(this.sortableColumns));

    // shared between ctn and recycle tables
    localStorage.setItem(this.filtersLSK,
      JSON.stringify(this.filters));

    const currentSortedCol = this._tableService.getColumnByName(
      this.currentSortedColumnName, this.sortableColumns);
    localStorage.setItem(sortedColKey, JSON.stringify(this.sortableColumns));

    if (currentSortedCol) {
      localStorage.setItem(sortedColKey, JSON.stringify(currentSortedCol));
    }
    localStorage.setItem(pageKey, this.config.currentPage.toString());
  }


  /**
   * Set the Table Columns model.
   */
  private setSortableColumns(): void {

    const defaultSortColumns = ['name', 'entity_type', 'employer', 'occupation'];
    const otherSortColumns = ['id', 'street', 'city', 'state', 'zip', 'candOffice', 'candOfficeState', 'candOfficeDistrict', 'candCmteId', 'deletedDate'];

    this.sortableColumns = [];
    for (const field of defaultSortColumns) {
      this.sortableColumns.push(new SortableColumnModel(field, false, true, true, false));
    }

    for (const field of otherSortColumns) {
      this.sortableColumns.push(new SortableColumnModel(field, false, false, false, true));
    }

    //this.sortableColumns.push(new SortableColumnModel('deletedDate', false, true, false, false));
  }


  /*private setSortableColumns(): void {
    const defaultSortColumns = ['type', 'name', 'date', 'memoCode', 'amount', 'aggregate'];
    const otherSortColumns = [
      'transactionId',
      'street',
      'city',
      'state',
      'zip',
      'purposeDescription',
      'contributorEmployer',
      'contributorOccupation',
      'memoText'
    ];

    this.sortableColumns = [];
    for (const field of defaultSortColumns) {
      this.sortableColumns.push(new SortableColumnModel(field, false, true, true, false));
    }
    for (const field of otherSortColumns) {
      this.sortableColumns.push(new SortableColumnModel(field, false, false, false, true));
    }
    this.sortableColumns.push(new SortableColumnModel('deletedDate', false, true, false, false));
  }*/


  /**
   * Set the UI to show the default column sorted in the default direction.
   */
  private setSortDefault(): void {
    // this.currentSortedColumnName = this._tableService.setSortDirection('name',
    //   this.sortableColumns, false);

    // this.currentSortedColumnName = this._tableService.setSortDirection('default',
    //   this.sortableColumns, false);

    // When default, the backend will sort by name and contact date
    this.currentSortedColumnName = 'default';
  }


  private calculateNumberOfPages(): void {
    if (this.config.currentPage > 0 && this.config.itemsPerPage > 0) {
      if (this.contactsModel && this.contactsModel.length > 0) {
        this.numberOfPages = this.contactsModel.length / this.config.itemsPerPage;
        this.numberOfPages = Math.ceil(this.numberOfPages);
      }
    }
  }


  toggleContactLog(cnt: ContactModel) {
    cnt.toggleLog = !cnt.toggleLog;
  }

  showContactDetails(contact: ContactModel) {
    console.log('Showing Modal for contact details fe');

    const data = {
      contact: contact
    };
    const modalRef = this.contactModal.openContactDetails(data);
    modalRef.then((res) => {
      if (res === 'agree') {

      } else if (res === 'decline') {
      }

    }).catch(e => {
      // do nothing stay on the same page
    });
  }
}
