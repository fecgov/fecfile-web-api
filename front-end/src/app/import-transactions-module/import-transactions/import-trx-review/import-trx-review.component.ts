import { Component, OnInit, Input, OnDestroy, Output, EventEmitter } from '@angular/core';
import { S3 } from 'aws-sdk/clients/all';
import { ConfirmModalComponent } from 'src/app/shared/partials/confirm-modal/confirm-modal.component';
import { timer, Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';
import { UploadTrxService } from '../import-trx-upload/service/upload-trx.service';
import { DialogService } from 'src/app/shared/services/DialogService/dialog.service';
import CryptoJS from 'crypto-js';
import { UploadFileModel } from '../model/upload-file.model';
import { ImportFileStatusEnum } from '../import-file-status.enum';
import { ImportTransactionsService } from '../service/import-transactions.service';

@Component({
  selector: 'app-import-trx-review',
  templateUrl: './import-trx-review.component.html',
  styleUrls: ['./import-trx-review.component.scss']
})
export class ImportTrxReviewComponent implements OnInit, OnDestroy {
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
    private _dialogService: DialogService,
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

  // Requirements for UI have Upload as file selection and the upload occuring
  // as part of the review.  This is why the upload to S3 is in this component.
  // Another option is to add a new step to the train stops called "file select".
  // The component supporting it will just handle selection files from client.
  // The next step "upload" will handle S3 followed by "review".

  private _uploadFile() {
    const file = this.uploadFile.file;
    // const checkSum = this._createFileCheckSum(file);

    // TODO convert this to a method returning observable or promise
    // TODO this will perform better if API generates it but requires upload to do so.
    // TODO if not done in API, check for faster front end library option
    const fileReader = new FileReader();
    fileReader.onload = e => {
      console.log('start MD5 = ' + new Date());
      const fileData = fileReader.result;
      const hash = CryptoJS.MD5(CryptoJS.enc.Latin1.parse(fileData));
      const md5 = hash.toString(CryptoJS.enc.Hex);
      this.checkSum = md5;
      console.log('end MD5 = ' + new Date());

      // this is checking for duplicate files on S3.
      // It will be replaced by API call to check for processed files
      // as we don't know retention policy for S3 files

      // this._uploadTrxService.listObjects(this.committeeId).subscribe((data: S3.Types.ListObjectsV2Output) => {
      //   for (const s3Obj of data.Contents) {
      //     // remove double quotes from eTag
      //     let eTagEdited = s3Obj.ETag;
      //     if (s3Obj.ETag) {
      //       if (s3Obj.ETag.length > 1) {
      //         if (s3Obj.ETag.startsWith('"') && s3Obj.ETag.endsWith('"')) {
      //           eTagEdited = s3Obj.ETag.substring(1, s3Obj.ETag.length - 1);
      //         }
      //       }
      //     }ss

      //     if (this.checkSum === eTagEdited) {
      //       this._dialogService
      //         .confirm(
      //           'This file has been uploaded before!  TODO show Review Screen',
      //           ConfirmModalComponent,
      //           'Warning!',
      //           false
      //         )
      //         .then(res => {});
      //     }
      //   }
      // });

      this.progressPercent = 0;
      this.uploadingText = 'Uploading...';
      this._uploadTrxService
        .uploadFile(file, this.checkSum, this.committeeId)
        .takeUntil(this.onDestroy$)
        .subscribe((data: any) => {
          if (data === false) {
            return;
          }
          this._checkForProcessingProgress();
        });
    };
    fileReader.readAsText(file);
  }

  private _startReview() {
    this.uploadFile.status = ImportFileStatusEnum.review;
    const file = this.uploadFile.file;
    this._importTransactionsService.processingUploadedTransactions(file.name, this.checkSum).subscribe((res: any) => {
      let hasValidationErrors = false;
      let hasDupeFile = false;
      if (res.error_list) {
        if (res.error_list.length > 0) {
          hasValidationErrors = true;
        }
      }
      if (res.duplicate_file_list) {
        if (res.duplicate_file_list.length > 0) {
          hasDupeFile = true;
        }
      }
      if (hasValidationErrors) {
        this.uploadFile.status = ImportFileStatusEnum.failed;
        this.resultsEmitter.emit({
          resultType: 'validation-error',
          uploadFile: this.uploadFile
        });
      } else if (hasDupeFile) {
        alert('dupe file detected');
      } else {
        this.resultsEmitter.emit({
          resultType: 'success',
          uploadFile: this.uploadFile
        });
      }
    });
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
      this._startReview();
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
