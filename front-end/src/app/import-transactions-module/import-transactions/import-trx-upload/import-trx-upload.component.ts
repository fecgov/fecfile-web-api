import { Component, OnInit, Input, OnDestroy, Output, EventEmitter } from '@angular/core';
import { S3 } from 'aws-sdk/clients/all';
import { ConfirmModalComponent } from 'src/app/shared/partials/confirm-modal/confirm-modal.component';
import { timer, Subject, throwError } from 'rxjs';
import { takeUntil } from 'rxjs/operators';
import { UploadTrxService } from '../import-trx-upload/service/upload-trx.service';
import { DialogService } from 'src/app/shared/services/DialogService/dialog.service';
import CryptoJS from 'crypto-js';
import { UploadFileModel } from '../model/upload-file.model';
import { ImportFileStatusEnum } from '../import-file-status.enum';
import { ImportTransactionsService } from '../service/import-transactions.service';
import { NgbModal } from '@ng-bootstrap/ng-bootstrap';

@Component({
  selector: 'app-import-trx-upload',
  templateUrl: './import-trx-upload.component.html',
  styleUrls: ['./import-trx-upload.component.scss']
})
export class ImportTrxUploadComponent implements OnInit, OnDestroy {
  @Input()
  public uploadFile: UploadFileModel;

  @Output()
  public resultsEmitter: EventEmitter<any> = new EventEmitter<any>();

  public progressPercent: number;
  public uploadingText: string;

  private onDestroy$: Subject<any>;
  private uploadProcessing$: Subject<any>;
  private checkSum: string;
  private committeeId: string;

  constructor(
    private _uploadTrxService: UploadTrxService,
    private _modalService: NgbModal,
    private _importTransactionsService: ImportTransactionsService
  ) {}

  ngOnInit() {
    // this.uploadFile.status = ImportFileStatusEnum.uploading;
    this.committeeId = null;
    if (localStorage.getItem('committee_details') !== null) {
      const cmteDetails: any = JSON.parse(localStorage.getItem(`committee_details`));
      this.committeeId = cmteDetails.committeeid;
    }
    this.progressPercent = 0;
    this.onDestroy$ = new Subject();
    this.getProgress();
    this._uploadFile();
  }

  public ngOnDestroy() {
    this.onDestroy$.next();
    if (this.uploadProcessing$) {
      this.uploadProcessing$.next();
    }
  }

  // private _uploadFile() {
  //   const file = this.uploadFile.file;
  //   // const checkSum = this._createFileCheckSum(file);

  //   // TODO convert this to a method returning observable or promise
  //   // TODO this will perform better if API generates it but requires upload to do so.
  //   // TODO if not done in API, check for faster front end library option
  //   const fileReader = new FileReader();
  //   fileReader.onload = e => {
  //     console.log('start MD5 = ' + new Date());
  //     const fileData = fileReader.result;
  //     const hash = CryptoJS.MD5(CryptoJS.enc.Latin1.parse(fileData));
  //     const md5 = hash.toString(CryptoJS.enc.Hex);
  //     this.checkSum = md5;
  //     console.log('end MD5 = ' + new Date());

  //     // this is checking for duplicate files on S3.
  //     // It will be replaced by API call to check for processed files
  //     // as we don't know retention policy for S3 files

  //     // this._uploadTrxService.listObjects(this.committeeId).subscribe((data: S3.Types.ListObjectsV2Output) => {
  //     //   for (const s3Obj of data.Contents) {
  //     //     // remove double quotes from eTag
  //     //     let eTagEdited = s3Obj.ETag;
  //     //     if (s3Obj.ETag) {
  //     //       if (s3Obj.ETag.length > 1) {
  //     //         if (s3Obj.ETag.startsWith('"') && s3Obj.ETag.endsWith('"')) {
  //     //           eTagEdited = s3Obj.ETag.substring(1, s3Obj.ETag.length - 1);
  //     //         }
  //     //       }
  //     //     }ss

  //     //     if (this.checkSum === eTagEdited) {
  //     //       this._dialogService
  //     //         .confirm(
  //     //           'This file has been uploaded before!  TODO show Review Screen',
  //     //           ConfirmModalComponent,
  //     //           'Warning!',
  //     //           false
  //     //         )
  //     //         .then(res => {});
  //     //     }
  //     //   }
  //     // });

  //     this.progressPercent = 0;
  //     this.uploadingText = 'Uploading...';
  //     this._uploadTrxService
  //       .uploadFile(file, this.checkSum, this.committeeId)
  //       .takeUntil(this.onDestroy$)
  //       .subscribe((data: any) => {
  //         if (data === false) {
  //           return;
  //         }
  //         this._checkForProcessingProgress();
  //       });

  //     // alert('fake for no internet conn');
  //     // this.resultsEmitter.emit({
  //     //   resultType: 'success',
  //     //   uploadFile: this.uploadFile
  //     // });
  //   };
  //   fileReader.readAsText(file);
  // }

  private _uploadFile() {
    const file = this.uploadFile.file;
    this.progressPercent = 0;
    this.uploadingText = 'Uploading...';
    this._uploadTrxService
    .uploadFile(this.uploadFile, this.committeeId)
    .takeUntil(this.onDestroy$)
    .subscribe((data: any) => {
      if (data === false) {
        return;
      }
      this._checkForProcessingProgress();
    });

    // // read the first record to get sched type
    // const fileReader = new FileReader();
    // fileReader.onload = e => {
    //   const chunkData = fileReader.result;
    //   const lines = chunkData.toString().split('\n', 2);
    //   if (!lines) {
    //     return;
    //   }
    //   if (!(lines.length > 1)) {
    //     return;
    //   }
    //   const firstRec = lines[1];
    //   console.log(firstRec);
    //   const fields = firstRec.split(',');
    //   if (!(fields.length > 2)) {
    //     return;
    //   }
    //   const scheduleType = this._updateFileNameWithSchedule(fields[2]);
    //   this.uploadFile.scheduleType = scheduleType;

    //   this._uploadTrxService
    //   .uploadFile(this.uploadFile, this.committeeId)
    //   .takeUntil(this.onDestroy$)
    //   .subscribe((data: any) => {
    //     if (data === false) {
    //       return;
    //     }
    //     this._checkForProcessingProgress();
    //   });
    // };
    // // read a chunk of the file large enough to include the header and 1st transaction rec
    // const chunk: Blob = file.slice(0, 20480);
    // fileReader.readAsText(chunk);
  }

  /**
   * Check for processing progress now that upload is complete.
   */
  private _checkForProcessingProgress() {
    // Ensure Upload complete message and spnner appear simultaneously using delay.
    const timer1 = timer(300);
    const timerSubject = new Subject<any>();
    const timerSubscription = timer1.pipe(takeUntil(timerSubject)).subscribe(() => {
      this.uploadingText = 'Upload complete!';
      if (timerSubscription) {
        timerSubscription.unsubscribe();
      }
      timerSubject.next();
      timerSubject.complete();

      // // TODO get Schedule Type from file on S3 and rename file to include it for API
      // this._uploadTrxService
      //   .readCsvRecords(this.uploadFile.file, 1, this.committeeId)
      //   .subscribe((records: Array<any>) => {
      //     if (records) {
      //       if (records.length > 0) {
      //         const rec = records[0];
      //         const scheduleType = rec['SCHEDULE NAME'];
      //         this._updateFileNameWithSchedule(scheduleType);
      //       }
      //     }
      //   });

      this.resultsEmitter.emit({
        resultType: 'success',
        uploadFile: this.uploadFile
      });
    });

    // this.hideProcessingProgress = false;
    // const progressPoller = interval(500);
    // this.uploadProcessing$ = new Subject();
    // progressPoller.takeUntil(this.uploadProcessing$);
    // this.processingPercent = 0;
    // progressPoller.subscribe(val => {
    //   this.uploadContactsService.checkUploadProcessing().takeUntil(this.uploadProcessing$).subscribe(res => {
    //     this.processingPercent += res;
    //     if (this.processingPercent > 99) {
    //       this.uploadProcessing$.next();
    //       this.uploadProcessing$.complete();
    //       // Using setTimeout to avoid another subject but should use RxJs (try delay or interval)
    //       // The purpose here is to allow the user to see the 100% completion before switching view.
    //       setTimeout(() => {
    //         // this.emitUserContacts();
    //       }, 1000);
    //     }
    //   });
    // });
  }

  public getProgress() {
    this._uploadTrxService
      .getProgressPercent()
      .takeUntil(this.onDestroy$)
      .subscribe((percent: number) => {
        this.progressPercent = percent;
        if (this.progressPercent >= 100) {
          // this.uploadingText = 'Upload complete!';
        }
      });
  }
}
