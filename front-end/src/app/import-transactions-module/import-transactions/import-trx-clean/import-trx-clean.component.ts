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
  public uploadFile: UploadFileModel;

  @Output()
  public resultsEmitter: EventEmitter<any> = new EventEmitter<any>();

  @Output()
  public saveStatusEmitter: EventEmitter<any> = new EventEmitter<any>();

  public contacts: Array<any>;
  public contacts$: Observable<Array<any>>;

  // ngx-pagination config for the duplicates table of contacts
  public maxItemsPerPage = 1000000; // set to 4 once server side supports pagination.
  public directionLinks = false;
  public autoHide = true;
  public config: PaginationInstance;
  public numberOfPages = 0;
  public allDupesSelected: boolean;

  private contactsSubject: BehaviorSubject<Array<any>>;
  private onDestroy$ = new Subject();

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
      id: 'trx_clean_contacts_pgn',
      itemsPerPage: this.maxItemsPerPage,
      currentPage: 1
    };
    this.config = config;

    this._importTransactionsService.generateContactCsv(this.uploadFile).subscribe((res: any) => {
      this._importTransactionsService.processContactCsv(this.uploadFile).subscribe((res: any) => {
        this.checkDuplicates(1);
      });
    });
    // this.mergePage = 1;
    this.allDupesSelected = false;
  }

  ngOnDestroy(): void {
    this.onDestroy$.next(true);
    this.contactsSubject.unsubscribe();
  }

  public changePageClientSide(page: number) {
    this.config.currentPage = page;
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

    this._importTransactionsService.getDuplicates(this.uploadFile.fileName, page).subscribe((res: any) => {
      // until API supports duplicate contacts, make it empty.
      this.contacts = res.contacts;
      // this.contacts = [];

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
    this.resultsEmitter.emit({
      resultType: 'proceed',
      uploadFile: this.uploadFile
    });
  }

  // ////////////////////////
  // // merge modal methods
  // ////////////////////////

  // public confirmFinalizeMerge(modal: any) {
  //   this._modalService.open(modal, { centered: true, backdrop: 'static' });
  // }

  // public cancelFinalizeMerge(modal: any) {
  //   modal.close('cancel it');
  // }

  // public merge(modal: any) {
  //   modal.close('close it');
  //   // TODO call API to save merge data for the file ID. use this.contactToClean
  //   // Either get the page data again from API removing the merged contact
  //   // or slice the merged contact out of the array.  Former is preferred.
  // }

  /////////////////////////
  // import all modal methods
  /////////////////////////

  public confirmFinalizeImportAll(modal: any) {
    this._modalService.open(modal, { centered: true, backdrop: 'static' });
  }

  public cancelFinalizeImportAll(modal: any) {
    modal.close('cancel it');
  }

  public importAll(modal: any) {
    modal.close('close it');
    this.resultsEmitter.emit({
      resultType: 'ignore_dupe_save',
      file: this.uploadFile
    });
    this.saveStatusEmitter.emit(true);
  }

  /////////////////////////
  // merge modal methods
  /////////////////////////

  public confirmFinalizeMergeAll(modal: any) {
    this._modalService.open(modal, { centered: true, backdrop: 'static' });
  }

  public cancelFinalizeMergeAll(modal: any) {
    modal.close('cancel it');
  }

  public mergeAll(modal: any) {
    modal.close('close it');

    // temp code: passing contacts array when merge option is needed
    // until pagination and server side saving of user selections is supported
    // as it is with import-contact module.  Until then, pass the
    // full array of duplicates containing user selctions for the merge.
    this.uploadFile.contacts = this.contacts;

    this.resultsEmitter.emit({
      resultType: 'merge_dupe_save',
      file: this.uploadFile
    });
    this.saveStatusEmitter.emit(true);
  }

  /////////////////////////
  // cancel import modal methods
  /////////////////////////

  public confirmCancelImport(modal: any) {
    this._modalService.open(modal, { centered: true, backdrop: 'static' });
  }

  public cancelImportCancel(modal: any) {
    modal.close('cancel it');
  }

  public cancelImport(modal: any) {
    modal.close('close it');
    this.resultsEmitter.emit({
      resultType: 'cancel-file',
      file: this.uploadFile
    });
    this._importTransactionsService.cancelImport(this.uploadFile.fileName).subscribe((res: any) => {});

    // On User cancel, unsaved changes are no longer retained.
    this.saveStatusEmitter.emit(true);
  }

  /**
   * For possible duplicates with the incoming contact and the existing contacts in the system,
   * apply the users decision on how to handle.
   *
   * @param contact the contact to merge
   * @param userAction the merge action selected by the user
   */
  public applyMergeSelection(contact: any, userAction: string) {
    contact.user_selected_option = userAction;

    let count = 0;
    for (const dupe of this.contacts) {
      if (dupe.user_selected_option) {
        count++;
      }
    }
    this.allDupesSelected = this.contacts.length === count;

    this._importTransactionsService.saveUserMergeSelection(this.uploadFile.fileName, contact).subscribe((res: any) => {
      // Until pagination in place and API supports saving user selection accross pages, do this.
      // this.allDupesSelected = res.allDone;
      // this.checkDuplicates(this.config.currentPage);
    });
  }
}
