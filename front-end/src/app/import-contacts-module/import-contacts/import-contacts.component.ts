import { Component, OnInit, ChangeDetectionStrategy, OnDestroy, ViewChild } from '@angular/core';
import { ImportContactsStepsEnum } from './import-contacts-setps.enum';
import { DialogService } from 'src/app/shared/services/DialogService/dialog.service';
import { ConfirmModalComponent } from 'src/app/shared/partials/confirm-modal/confirm-modal.component';
import { TimeoutMessageService } from 'src/app/shared/services/TimeoutMessageService/timeout-message-service.service';
import { Subject } from 'rxjs';
import { ImportContactsService } from './service/import-contacts.service';
import { NgbModal } from '@ng-bootstrap/ng-bootstrap';
import { ErrorContactsComponent } from './clean-contacts/error-contacts/error-contacts.component';
import { ModalDirective } from 'ngx-bootstrap';

@Component({
  selector: 'app-import-contacts',
  templateUrl: './import-contacts.component.html',
  styleUrls: ['./import-contacts.component.scss'],
  // changeDetection: ChangeDetectionStrategy.OnPush
})
export class ImportContactsComponent implements OnInit, OnDestroy {

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

  private unsavedData: boolean;
  private onDestroy$ = new Subject();
  private validationErrorsExist: boolean;
  private duplicatesExist: boolean;

  constructor(
    private _importContactsService: ImportContactsService,
    private _dialogService: DialogService,
    // private _modalService: NgbModal,
    private _timeoutMessageService: TimeoutMessageService
  ) {
    _timeoutMessageService.getTimeoutMessage().takeUntil(this.onDestroy$).subscribe(message => {
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
  }

  ngOnDestroy() {
    this.onDestroy$.next();
  }

  public showInfo(): void {
    alert('Not yet supported');
  }

  public beginUpload() {
    this.currentStep = this.step1Upload;
  }

  public viewFormatSpecs(): void {
    alert('Not yet supported');
  }

  public viewCsvTemplate(): void {
    alert('Not yet supported');
  }

  public showNextStep() {
    switch (this.currentStep) {
      case this.step1Upload:
        this.currentStep = this.step3Clean;
        // this.currentStep = this.step2Review;
        // this.currentStep = this.step4ImportDone;
        break;
      // case this.step2Configure:
      //   this.currentStep = this.step3Clean;
      //   break;
      case this.step3Clean:
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

  public noErrorsAcknowleged() {
    this.noErrorslModal.hide();
    this.showNextStep();
  }

  public receiveDupeCancel() {
    // this.cancelEmitter.emit();
  }

  public receiveUploadResult(userContactsMessage: any) {
    this.fileName = userContactsMessage.fileName;
    this.unsavedData = false;
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
    this._dialogService
      .confirm(message, ConfirmModalComponent, 'Caution!', false)
      .then(res => {
        if (res === 'okay') {
          this.unsavedData = false;
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
   * Determines ability for a person to leave a page with a form on it.
   *
   * @return     {boolean}  True if able to deactivate, False otherwise.
   */
  public async canDeactivate(): Promise<boolean> {

    return true;

    // if (this.unsavedData) {
    //   let result: boolean = null;
    //   result = await this._dialogService.confirm('', ConfirmModalComponent).then(res => {
    //     let val: boolean = null;

    //     if (res === 'okay') {
    //       val = true;
    //     } else if (res === 'cancel') {
    //       val = false;
    //     }

    //     return val;
    //   });

    //   return result;
    // } else {
    //   return true;
    // }

  }

}
