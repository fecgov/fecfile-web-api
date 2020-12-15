import { Component, OnDestroy, OnInit, ViewChild } from '@angular/core';
import { NgbModal } from '@ng-bootstrap/ng-bootstrap';
import * as FileSaver from 'file-saver';
import { ModalDirective } from 'ngx-bootstrap';
import { Subject } from 'rxjs';
import { ConfirmModalComponent } from 'src/app/shared/partials/confirm-modal/confirm-modal.component';
import { DialogService } from 'src/app/shared/services/DialogService/dialog.service';
import { ExportService } from 'src/app/shared/services/ExportService/export.service';
import { TimeoutMessageService } from 'src/app/shared/services/TimeoutMessageService/timeout-message-service.service';
import { CancelImportConfirmComponent } from '../../import-contacts-module/import-contacts/cancel-import-confirm/cancel-import-confirm.component';
import { DuplicateContactsService } from '../../import-contacts-module/import-contacts/clean-contacts/duplicate-contacts/service/duplicate-contacts.service';
import { ImportContactsStepsEnum } from '../../import-contacts-module/import-contacts/import-contacts-setps.enum';
import { ImportContactsService } from '../../import-contacts-module/import-contacts/service/import-contacts.service';

@Component({
  selector: 'app-import-fecfile',
  templateUrl: './import-fecfile.component.html',
  styleUrls: ['./import-fecfile.component.scss']
  // changeDetection: ChangeDetectionStrategy.OnPush
})
export class ImportFecFileComponent implements OnInit, OnDestroy {
  @ViewChild('errorsModal')
  public errorsModal: ModalDirective;

  @ViewChild('noErrorslModal')
  public noErrorslModal: ModalDirective;

  public contactErrors: Array<any>;
  public fileName: string;
  public steps: Array<any>;
  public currentStep: ImportContactsStepsEnum;
  public readonly start = ImportContactsStepsEnum.start;
  public readonly step1Upload = ImportContactsStepsEnum.step1Upload;
  public readonly step2Review = ImportContactsStepsEnum.step2Review;
  public readonly step3Clean = ImportContactsStepsEnum.step3Clean;
  public readonly step4ImportDone = ImportContactsStepsEnum.step4ImportDone;
  public userContactFields: Array<string>;
  public duplicateContacts: Array<any>;
  public forceChangeDetectionUpload: Date;
  public duplicateFile: any;
  public importDoneAction: string;
  public isShowInfo: boolean;

  private unsavedData: boolean;
  private onDestroy$ = new Subject();
  private validationErrorsExist: boolean;
  private duplicatesExist: boolean;
  successResponse: any;

  constructor(
    private _dialogService: DialogService,
    // private _modalService: NgbModal,
    private _timeoutMessageService: TimeoutMessageService,
    private _exportService: ExportService,
    private _importContactsService: ImportContactsService,
    private _modalService: NgbModal,
    private _duplicateContactsService: DuplicateContactsService
  ) {
    _timeoutMessageService
      .getTimeoutMessage()
      .takeUntil(this.onDestroy$)
      .subscribe(message => {
        // There may be a race condition between the receipt of this message
        // and the timeout navigatingto login.  Id true, the canDeacivate method here
        // may need to check browser cache for timeout property.
        this.unsavedData = false;
      });
  }

  ngOnInit() {
    this.steps = [
      { text: 'Upload', step: this.step1Upload },
      // { text: 'Review', step: this.step2Review },
      { text: 'Clean', step: this.step3Clean },
      { text: 'Import', step: this.step4ImportDone }
    ];
    this.currentStep = this.start;
    // removing warning until fix is made for not showing it when the system navigates
    // to login screen on session timeout.
    // this.unsavedData = true;
    this.onDestroy$ = new Subject();
    this.validationErrorsExist = false;
    this.duplicatesExist = false;
    this.isShowInfo = false;
    this.unsavedData = false;
  }

  ngOnDestroy() {
    this.onDestroy$.next();
  }

  public showInfo(): void {
    // alert('Not yet supported');
    this.isShowInfo = true;
  }

  public receiveReturnFromHowTo() {
    this.isShowInfo = false;
  }

  public beginUpload() {
    this.currentStep = this.step1Upload;
  }

  public viewFormatSpecs(): void {
    this._importContactsService.getSpecAndTemplate().subscribe((res: any) => {
      const type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;charset=UTF-8';
      // const type = 'application/vnd.ms.excel';
      const blob: Blob = new Blob([res], { type: type });
      FileSaver.saveAs(blob, 'Import Contacts Specs and Template.xlsx');
    });

    // // this._exportService.exportExcel(sheet1, 'Import Contacts Specs and Template');
    // const ws1: XLSX.WorkSheet = XLSX.utils.json_to_sheet(importContactsSpec);
    // const ws2: XLSX.WorkSheet = XLSX.utils.json_to_sheet(importContactsTemplate);
    // ws1['!cols'] = [{ width: 10 }, { width: 25 }, { width: 20 }, { width: 20 }, { width: 15 }, { width: 30 }];
    // ws1['!rows'] = [
    //   { hpx: 50 },
    //   { hpx: 20 },
    //   { hpx: 20 },
    //   { hpx: 20 },
    //   { hpx: 20 },
    //   { hpx: 20 },
    //   { hpx: 20 },
    //   { hpx: 20 },
    //   { hpx: 20 },
    //   { hpx: 20 },
    //   { hpx: 20 },
    //   { hpx: 20 },
    //   { hpx: 20 },
    //   { hpx: 20 },
    //   { hpx: 20 },
    //   { hpx: 20 }
    // ];

    // const wb: XLSX.WorkBook = {
    //   Sheets: { 'Contact Fields Specs': ws1, Template: ws2 },
    //   SheetNames: ['Contact Fields Specs', 'Template']
    // };
    // const excelBuffer: any = XLSX.write(wb, { bookType: 'xlsx', type: 'array' });
    // // this._exportServsice.saveExcelFile(excelBuffer, 'Import Contacts Specs and Template');
  }

  public viewCsvTemplate(): void {
    alert('Not yet supported');
  }

  public showNextStep() {
    switch (this.currentStep) {
      case this.step1Upload:
        this.currentStep = this.step4ImportDone;
        break;
      default:
        this.currentStep = this.step1Upload;
    }
  }

  public showPreviousStep() {
    switch (this.currentStep) {
      case this.step4ImportDone:
        this.currentStep = this.step3Clean;
        break;
      case this.step3Clean:
        this.currentStep = this.step2Review;
        break;
      case this.step2Review:
        this.currentStep = this.step1Upload;
        break;
      default:
    }
  }

  public errorsAcknowleged() {
    this.errorsModal.hide();
    this.currentStep = this.start;
  }

  public noErrorsAcknowleged(res:any) {
    this.successResponse = res;
    if(this.noErrorslModal) {
      this.noErrorslModal.hide();
    }
    this.showNextStep();
    console.log(this.successResponse);
  }

  public receiveDupeProceed(importDoneAction: string) {
    this.importDoneAction = importDoneAction;
    this.showNextStep();
  }

  public receiveDupeCancel() {
    // TODO call cancel API
    // this.cancelEmitter.emit();
    this.currentStep = this.start;
  }

  public receiveUploadResult(userContactsMessage: any) {
    this.fileName = userContactsMessage.fileName;
    // this.unsavedData = false;
    let errorCount = 0;
    if (Array.isArray(userContactsMessage.error_list)) {
      errorCount = userContactsMessage.error_list.length;
    }

    if (errorCount > 0) {
      // const modalRef = this._modalService.open(ErrorContactsComponent);
      // modalRef.componentInstance.errorContacts = userContactsMessage.error_list;
      // modalRef.result.then(result => {
      //   this.unsavedData = false;
      //   this.currentStep = this.step1Upload;
      // });

      this.contactErrors = userContactsMessage.error_list;
      this.errorsModal.show();
    } else {
      this.noErrorslModal.show();
    }

    // if (userContactsMessage.duplicateContacts) {
    //   this.duplicateContacts = this._importContactsService.mapAllDupesFromServerFields(userContactsMessage.duplicateContacts);
    // }

    // if (userContactsMessage.duplicateFile) {
    //   this.duplicateFile = userContactsMessage.duplicateFile;
    // }

    // // ???? temp
    // let dupeTemp = [];
    // if (userContactsMessage.duplicates) {
    //   // console.log('true dupes exist');
    //   dupeTemp = userContactsMessage.duplicates;
    // } else {
    //   // console.log('false no duplicates');
    // }

    // if (userContactsMessage.duplicateCount > 0) {
    //   this.duplicatesExist = true;
    // }
    // if (userContactsMessage.validationErrorCount > 0) {
    //   this.validationErrorsExist = true;
    // }
    // if (this.validationErrorsExist || this.duplicatesExist) {
    //   const message = `${userContactsMessage.contactsSaved} contact(s) were imported. ${userContactsMessage.duplicateCount} contact(s) were identified as duplicates and ${userContactsMessage.validationErrorCount} contained errors - these were not imported."`;
    // "1 contact(s) were imported. XXX contact(s) were identified as duplicates and XXX contained errors - these were not imported."

    // if (this.validationErrorsExist && this.duplicatesExist) {
    //   if (userContactsMessage.duplicateCount > 1 && userContactsMessage.validationErrorCount > 1) {
    //     message = `${userContactsMessage.duplicateCount} contacts were identified as duplicates ` +
    //       `and ${userContactsMessage.validationErrorCount} were found in error.  They have been excluded from the ` +
    //       `import.`;
    //   } else if (userContactsMessage.duplicateCount > 1 && userContactsMessage.validationErrorCount === 1) {
    //     message = `${userContactsMessage.duplicateCount} contacts were identified as duplicates ` +
    //       `and ${userContactsMessage.validationErrorCount} was found in error.  They have been excluded from the ` +
    //       `import.`;
    //   } else if (userContactsMessage.duplicateCount === 1 && userContactsMessage.validationErrorCount > 1) {
    //     message = `${userContactsMessage.duplicateCount} contact was identified as a duplicate ` +
    //       `and ${userContactsMessage.validationErrorCount} were found in error.  They have been excluded from the ` +
    //       `import.`;
    //   }
    // } else if (this.duplicatesExist) {
    //   if (userContactsMessage.duplicateCount > 1) {
    //     message = `${userContactsMessage.duplicateCount} contacts were identified as duplicates. ` +
    //       `They have been excluded from the import.`;
    //   } else {
    //     message = `${userContactsMessage.duplicateCount} contact was identified as a duplicate. ` +
    //       `It has been excluded from the import.`;
    //   }
    // } else if (this.validationErrorsExist) {
    //   if (userContactsMessage.validationErrorCount > 1) {
    //     message = `${userContactsMessage.validationErrorCount} contacts were found in error.  ` +
    //       `They have been excluded from the import.`;
    //   } else {
    //     message = `${userContactsMessage.validationErrorCount} contact was found in error.  ` +
    //       `It has been excluded from the import.`;
    //   }
    // }
    // const savedMessage = `${userContactsMessage.contactsSaved} contacts were saved. `;
    // this.confirmProceedWithrrors(message);
    // } else {
    //   this.unsavedData = false;
    //   this.showNextStep();
    // }

    // if (this.validationErrorsExist) {
    //   const message = `${userContactsMessage.validationErrorCount} contacts were found in error.  ` +
    //     ` They will be excluded from the import if you coose to proceed.`;
    //   this.confirmProceedWithrrors(message);
    // } else {
    //   this.unsavedData = false;
    //   this.showNextStep();
    // }
  }

  private confirmProceedWithrrors(message: string) {
    this._dialogService.confirm(message, ConfirmModalComponent, 'Caution!', false).then(res => {
      if (res === 'okay') {
        // this.unsavedData = false;
        this.showNextStep();
      }
      // else if (res === 'cancel') {
      //   this.currentStep = this.step1Upload;
      //   this.forceChangeDetectionUpload = new Date();
      // }
    });
  }

  public receiveReviewAction(action: string) {
    if (action === 'proceed') {
      this.currentStep = this.step3Clean;
    }
    if (action === 'cancel') {
      this.currentStep = this.start;
    }
  }

  public receiveCleanCancel() {
    this.currentStep = this.start;
  }

  /**
   * Receive save status of the file from child components.
   *
   * @param saveStatus save status of the file
   */
  public receiveSavedStatus(saveStatus: boolean): void {
    this.unsavedData = !saveStatus;
  }

  /**
   * Determines ability for a person to leave a page with a form on it.
   *
   * @return     {boolean}  True if able to deactivate, False otherwise.
   */
  public async canDeactivate(): Promise<boolean> {
    // return true;

    if (this.unsavedData) {
      let result: boolean = null;
      // result = await this._dialogService.confirm('If you leave this page the importing process ' +
      //   'will be cancelled and no data will be added. ' +
      //   'Click Cancel to cancel the import or Continue if you want the import process to finish.',
      //   ConfirmModalComponent).then(res => {
      //   let val: boolean = null;

      //   if (res === 'okay') {
      //     val = true;
      //   } else if (res === 'cancel') {
      //     val = false;
      //   }

      //   return val;
      // });

      const modalRef = this._modalService.open(CancelImportConfirmComponent);
      result = await modalRef.result.then(res => {
        if (res === 'continue') {
          return false;
        } else if ('cancel') {
          this._duplicateContactsService.cancelImport(this.fileName).subscribe((res: any) => {});
          this.unsavedData = false;
          // canDeactivate is true to let user nav to new location
          return true;
        }
      });

      return result;
    } else {
      return true;
    }
  }
}
