import { Component, OnInit, Input, Output, EventEmitter, OnDestroy } from '@angular/core';
import { UploadFileModel } from '../model/upload-file.model';
import { ImportFileStatusEnum } from '../import-file-status.enum';
import { Observable, BehaviorSubject, Subject } from 'rxjs';
import { PaginationInstance } from 'ngx-pagination';
import { NgbModal } from '@ng-bootstrap/ng-bootstrap';
import { UtilService } from 'src/app/shared/utils/util.service';
import { ImportTransactionsService } from '../service/import-transactions.service';

@Component({
  selector: 'app-import-trx-clean',
  templateUrl: './import-trx-clean.component.html',
  styleUrls: ['./import-trx-clean.component.scss']
})
export class ImportTrxCleanComponent implements OnInit, OnDestroy {
  @Input()
  public fileName: string;

  @Output()
  public dupeProceedEmitter: EventEmitter<any> = new EventEmitter<any>();

  @Output()
  public dupeCancelEmitter: EventEmitter<any> = new EventEmitter<any>();

  @Output()
  public saveStatusEmitter: EventEmitter<any> = new EventEmitter<any>();

  public contacts: Array<any>;
  public contacts$: Observable<Array<any>>;

  // ngx-pagination config for the duplicates table of contacts
  public maxItemsPerPage = 4;
  public directionLinks = false;
  public autoHide = true;
  public config: PaginationInstance;
  public numberOfPages = 0;
  public allDupesSelected: boolean;

  private contactsSubject: BehaviorSubject<Array<any>>;
  private onDestroy$ = new Subject();

  @Input()
  public uploadFile: UploadFileModel;

  constructor(
    private _modalService: NgbModal,
    private _utilService: UtilService,
    private _importTransactionsService: ImportTransactionsService
  ) {}

  ngOnInit() {
    this.contacts = [];
    this.contactsSubject = new BehaviorSubject<any>([]);
    this.contacts$ = this.contactsSubject.asObservable();
    const config: PaginationInstance = {
      id: 'clean_contacts__table-pagination',
      itemsPerPage: this.maxItemsPerPage,
      currentPage: 1
    };
    this.config = config;
    this.checkDuplicates(1);
    // this.mergePage = 1;
    this.allDupesSelected = false;
  }

  ngOnDestroy(): void {
    this.onDestroy$.next(true);
    this.contactsSubject.unsubscribe();
  }

  public checkDuplicates(page: number) {
    this.config.currentPage = page;

    // // this._importContactsService.checkDuplicates(page).takeUntil(this.contactsSubject).subscribe((res: any) => {
    // this._duplicateContactsService.getDuplicates_mock(page).subscribe((res: any) => {
    //   this.contactsSubject.next(res.duplicates);
    //   // this.contactsSubject.next(this.duplicates);
    //   this.config.totalItems = res.totalCount ? res.totalCount : 0;
    //   this.config.itemsPerPage = res.itemsPerPage ? res.itemsPerPage : this.maxItemsPerPage;
    //   this.numberOfPages = res.totalPages;
    // });

    this._importTransactionsService.getDuplicates(this.fileName, page).subscribe((res: any) => {
      // // temp to set selected to false until api does
      // for (const contact of res.contacts) {
      //   for (const dupe of contact.contacts_from_db) {
      //     // TEMP CODE
      //     // response contacts the contact from DB the user may have identified as one to merge.
      //     // If user has done this, the user_selected_value on th CONTACT not the DUPE CONTACT
      //     // will contain the entity id of the selected contact.
      //     // Set a field on the DUPLICATE CONTACT for the UI
      //     // TODO change API to set select on the dupe. For now just set the first one for devl.
      //     dupe.user_selected_value = false;
      //     if (contact.user_selected_option !== 'add') {
      //       contact.contacts_from_db[0].user_selected_value = true;
      //     }
      //     // TEMP CDE END
      //   }
      // }

      this.contacts = res.duplicates;
      this.config.totalItems = res.totalcontactsCount;
      this.config.itemsPerPage = res.itemsPerPage;
      this.numberOfPages = res.totalPages;
      this.allDupesSelected = res.allDone;
    });
  }

  public handleCheckedDupe($event: any, dupe: any, contact: any) {
    dupe.user_selected_value = $event.target.checked;
    // Existing contact must be selected for action "existing" and "update".
    contact.enableAllActions = true;
  }

  public formatName(contact: any): string {
    let name = '';
    if (contact.entity_type === 'IND') {
      // TODO handle suffix and prefix
      name = `${contact.last_name}, ${contact.first_name}`;
    } else if (contact.entity_type === 'ORG') {
      name = contact.entity_name;
    }
    return name;
  }

  // public cleanContact(contact: any, modal: any) {
  //   this.prepareContactToClean(contact);
  //   this._modalService.open(modal, { size: 'lg', centered: true, backdrop: 'static' });
  // }

  /**
   * Determine if pagination should be shown.
   */
  public showPagination(): boolean {
    if (this.config.totalItems > this.config.itemsPerPage) {
      return true;
    }
    // otherwise, no show.
    return false;
  }

  public proceed() {
    this.dupeProceedEmitter.emit({
      resultType: 'success',
      uploadFile: this.uploadFile
    });
  }
}
