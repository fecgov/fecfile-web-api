import { Component, OnInit, Input, OnDestroy, Output, EventEmitter, OnChanges, SimpleChanges } from '@angular/core';
import { S3 } from 'aws-sdk/clients/all';
import {
  ConfirmModalComponent,
  ModalHeaderClassEnum
} from 'src/app/shared/partials/confirm-modal/confirm-modal.component';
import { timer, Subject, throwError } from 'rxjs';
import { takeUntil } from 'rxjs/operators';
import { UploadTrxService } from '../import-trx-upload/service/upload-trx.service';
import { DialogService } from 'src/app/shared/services/DialogService/dialog.service';
import CryptoJS from 'crypto-js';
import { UploadFileModel } from '../model/upload-file.model';
import { ImportFileStatusEnum } from '../import-file-status.enum';
import { ImportTransactionsService } from '../service/import-transactions.service';
import { NgbModal } from '@ng-bootstrap/ng-bootstrap';
import { UploadCompleteMessageComponent } from './upload-complete-message/upload-complete-message.component';

@Component({
  selector: 'app-import-trx-review',
  templateUrl: './import-trx-review.component.html',
  styleUrls: ['./import-trx-review.component.scss']
})
export class ImportTrxReviewComponent implements OnInit, OnDestroy, OnChanges {
  @Input()
  public uploadFile: UploadFileModel;

  @Input()
  public forceChangeDetection: Date;

  @Output()
  public resultsEmitter: EventEmitter<any> = new EventEmitter<any>();

  public progressPercent: number;
  public uploadingText: string;
  public hasDupeFile: boolean;
  public duplicateFileList: Array<any>;
  public startUpload: boolean;
  public showSpinner: boolean;

  private onDestroy$: Subject<any>;
  private uploadProcessing$: Subject<any>;
  // private checkSum: string;
  private committeeId: string;

  constructor(
    private _dialogService: DialogService,
    private _modalService: NgbModal,
    private _importTransactionsService: ImportTransactionsService
  ) {}

  ngOnInit() {
    this.committeeId = null;
    if (localStorage.getItem('committee_details') !== null) {
      const cmteDetails: any = JSON.parse(localStorage.getItem(`committee_details`));
      this.committeeId = cmteDetails.committeeid;
    }
    this._startReview();
    this.hasDupeFile = false;
    this.startUpload = false;
    this.showSpinner = false;
    this.duplicateFileList = [];

    // test code for schedule
    // const scheds = ['SA111', 'SB111', 'SE111', 'SF111', 'H3111', 'H4111', 'H5111', 'H6111', 'SLA111', 'SLB11'];
    // for (const s of scheds) {
    //   console.log(`Sched code = ${s} / Sched Name = ${this._formatScheduleName(s)}`);
    // }
  }

  public ngOnChanges(changes: SimpleChanges): void {
    if (changes.forceChangeDetection !== undefined) {
      if (
        changes.forceChangeDetection.currentValue !== changes.forceChangeDetection.previousValue &&
        changes.forceChangeDetection.firstChange === false
      ) {
        this.ngOnInit();
      }
    }
  }

  public ngOnDestroy() {}

  public proceed() {
    // move receiveUploadResults into here.  No longer event emitted.
    this.receiveUploadResults('');
    // this.resultsEmitter.emit({
    //   resultType: 'proceed',
    //   uploadFile: this.uploadFile
    // });
  }

  public cancelImport() {
    this.resultsEmitter.emit({
      resultType: 'cancel-file',
      file: this.uploadFile
    });
  }

  private async _startReview() {
    const file: File = this.uploadFile.file;
    const maxClientSideSize = 2000000000; // 2,000,000,000 = 2GB
    if (file.size > maxClientSideSize) {
      // TODO call API to gen md5 checksum and check for duplicates
    } else {
      const fileReader = new FileReader();
      fileReader.onload = e => {
        // tested with 1 GB ~.01s
        console.log('start MD5 = ' + new Date());
        const fileData = fileReader.result;
        const hash = CryptoJS.MD5(CryptoJS.enc.Latin1.parse(fileData));
        const md5 = hash.toString(CryptoJS.enc.Hex);
        this.uploadFile.checkSum = md5;
        console.log('end MD5 = ' + new Date());

        this._readFileForScheduleType();
      };
      fileReader.readAsText(file);
    }
  }

  private _checkForDuplicateFiles() {
    this._importTransactionsService.checkDuplicateFile(this.uploadFile).subscribe((res: any) => {
      // let hasValidationErrors = false;
      // if (res.error_list) {
      //   if (res.error_list.length > 0) {
      //     hasValidationErrors = true;
      //   }
      // }
      if (res.duplicate_file_list) {
        if (res.duplicate_file_list.length > 0) {
          this.hasDupeFile = true;
          this.duplicateFileList = res.duplicate_file_list;
        }
      }
      // if (hasValidationErrors) {
      //   this.uploadFile.status = ImportFileStatusEnum.failed;
      //   const message =
      //     'The system found errors within the import file, ' +
      //     'and will not be able to complete the import. ' +
      //     'Please check your file and ensure formatting is correct.';
      //   this._dialogService
      //     .confirm(message, ConfirmModalComponent, 'Import Failed!', false, ModalHeaderClassEnum.errorHeader)
      //     .then(res => {
      //       this.resultsEmitter.emit({
      //         resultType: 'validation-error',
      //         uploadFile: this.uploadFile
      //       });
      //     });
      // } else
      if (this.hasDupeFile) {
        // already handled above
      } else {
        // this._modalService.open(UploadCompleteMessageComponent).result.then((resp: string) => {
        //   if (resp === 'continue') {
        //     this.resultsEmitter.emit({
        //       resultType: 'success',
        //       uploadFile: this.uploadFile
        //     });
        //   }
        // });

        // Do S3 upload
        this.startUpload = true;
      }
    });
  }

  private _readFileForScheduleType() {
    // read the first record to get sched type
    const fileReader = new FileReader();
    fileReader.onload = e => {
      const chunkData = fileReader.result;
      const lines = chunkData.toString().split('\n', 2);
      if (!lines) {
        console.error(new Error('no data in first 2 lines'));
        return;
      }
      if (!(lines.length > 1)) {
        console.error(new Error('no data in line 2'));
        return;
      }
      const firstRec = lines[1];
      console.log(firstRec);
      const fields = firstRec.split(',');
      if (!(fields.length > 2)) {
        console.error(new Error('1st record missing fields for schedule in pos 3'));
        return;
      }
      const scheduleType = this._formatScheduleName(fields[2]);
      this.uploadFile.scheduleType = scheduleType;
      this.uploadFile.fecFileName = this._importTransactionsService.formatFecFileName(
        this.uploadFile,
        this.committeeId
      );

      this._checkForDuplicateFiles();
    };
    // read a chunk of the file large enough to include the header and 1st transaction rec
    const file = this.uploadFile.file;
    const chunk: Blob = file.slice(0, 20480);
    fileReader.readAsText(chunk);
  }

  // private _determineErrorFileName(errorFilePath: string): string {
  //   let fileName = 'error_file.csv';
  //   const nameSplit = errorFilePath.split('/');
  //   let fecFileName = '';
  //   if (nameSplit.length) {
  //     if (nameSplit.length > 2) {
  //       fecFileName = nameSplit[3];
  //     }
  //   }
  //   return fileName;
  // }

  public receiveUploadResults($event: any) {
    this.showSpinner = true;
    this._importTransactionsService.checkForValidationErrors(this.uploadFile).subscribe((res: any) => {
      this.showSpinner = false;
      // if (res.validation_failed === true) {
      let validationFailed = true;
      if (res.errorfilename) {
        if (res.errorfilename.toLowerCase() === 'file_not_found') {
          validationFailed = false;
        }
      }
      if (validationFailed) {
        // this.uploadFile.errorFileName = res.error_file;
        this.uploadFile.errorFileName = res.errorfilename;
        this.uploadFile.status = ImportFileStatusEnum.failed;
        const message =
          'The system found errors within the import file, ' +
          'and will not be able to complete the import. ' +
          'Please check your file and ensure formatting is correct.';
        this._dialogService
          .confirm(message, ConfirmModalComponent, 'Import Failed!', false, ModalHeaderClassEnum.errorHeader)
          .then(res => {
            this.resultsEmitter.emit({
              resultType: 'validation-error',
              uploadFile: this.uploadFile
            });
          });
      } else {
        this._modalService.open(UploadCompleteMessageComponent).result.then((resp: string) => {
          if (resp === 'continue') {
            this.resultsEmitter.emit({
              resultType: 'success',
              uploadFile: this.uploadFile
            });
            this._importTransactionsService.generateContactCsv(this.uploadFile).subscribe((res: any) => {
              this._importTransactionsService.processContactCsv(this.uploadFile).subscribe((res: any) => {
              });
            });
          }
        });
      }
    });
  }

  /**
   * API requires file renamed with schedule name.
   * TODO do this server side.
   * @param scheduleType code for the schedule
   */
  private _formatScheduleName(scheduleType: string): string {
    let scheduleName: string = null;
    let schedCode: string = null;
    if (scheduleType) {
      if (scheduleType.length > 1) {
        schedCode = scheduleType.substring(0, 2);
      }
    }
    if (!schedCode) {
      throwError('invalid schedule name of ' + scheduleType);
      return;
    }
    // SA - ScheduleA
    // SB - ScheduleB
    // SE - ScheduleSE
    // SF - ScheduleSF
    // SLA - ScheduleLA
    // SLB - ScheduleLB

    const prefix = 'Schedule';
    if (schedCode === 'H3' || schedCode === 'H4' || schedCode === 'H5' || schedCode === 'H6') {
      scheduleName = prefix + schedCode;
    } else {
      const schedPos2 = schedCode.substring(1);
      if (schedPos2 === 'A' || schedPos2 === 'B') {
        scheduleName = prefix + schedPos2;
      } else if (schedPos2 === 'E' || schedPos2 === 'F') {
        scheduleName = prefix + 'S' + schedPos2;
      } else if (schedCode === 'SL') {
        scheduleName = prefix + scheduleType.substring(1, 3);
      }
    }
    // console.log('rename file to include ' + scheduleName);
    return scheduleName;
  }
}
