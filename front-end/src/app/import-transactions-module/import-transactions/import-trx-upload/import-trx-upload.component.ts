import {
  Component,
  OnInit,
  ViewChild,
  ElementRef,
  Output,
  EventEmitter,
  OnDestroy,
  Input,
  SimpleChanges,
  OnChanges
} from '@angular/core';
import * as XLSX from 'xlsx';
import { timer, Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';
import { UtilService } from 'src/app/shared/utils/util.service';
import CryptoJS from 'crypto-js';
import { S3 } from 'aws-sdk/clients/all';
import { ModalDirective } from 'ngx-bootstrap/modal/ngx-bootstrap-modal';
import { ConfirmModalComponent } from 'src/app/shared/partials/confirm-modal/confirm-modal.component';
import { DialogService } from 'src/app/shared/services/DialogService/dialog.service';
import { ImportTransactionsService } from '../service/import-transactions.service';
import { UploadTrxService } from './service/upload-trx.service';
import { hasOwnProp } from 'ngx-bootstrap/chronos/utils/type-checks';
import { AnyLengthString } from 'aws-sdk/clients/comprehendmedical';

@Component({
  selector: 'app-import-trx-upload',
  templateUrl: './import-trx-upload.component.html',
  styleUrls: ['./import-trx-upload.component.scss']
})
export class ImportTrxUploadComponent implements OnInit, OnDestroy, OnChanges {
  @ViewChild('selectFileInput')
  public selectFileInput: ElementRef;

  @Input()
  public forceChangeDetection: Date;

  @Output()
  public uploadResultEmitter: EventEmitter<any> = new EventEmitter<any>();

  @Output()
  public queueEmitter: EventEmitter<any> = new EventEmitter<any>();

  @Output()
  public saveStatusEmitter: EventEmitter<any> = new EventEmitter<any>();

  public userContacts: Array<any>;
  public showUpload: boolean;
  public progressPercent: number;
  public processingPercent: number;
  public hideProcessingProgress: boolean;
  public showSpinner: boolean;
  public uploadingText: string;
  public processingText: string;
  public duplicateFile: any;

  private onDestroy$: Subject<any>;
  private uploadProcessing$: Subject<any>;
  private checkSum: string;
  private committeeId: string;
  private fileQueue: Array<any>;

  constructor(
    private _importTransactionsService: ImportTransactionsService,
    private _uploadTrxService: UploadTrxService,
    private _utilService: UtilService,
    private _dialogService: DialogService
  ) {}

  public ngOnInit() {
    this.committeeId = null;
    if (localStorage.getItem('committee_details') !== null) {
      const cmteDetails: any = JSON.parse(localStorage.getItem(`committee_details`));
      this.committeeId = cmteDetails.committeeid;
    }

    this.onDestroy$ = new Subject();
    this.showUpload = true;
    this.hideProcessingProgress = true;
    this.showSpinner = false;
    this.progressPercent = 0;
    this.processingPercent = 0;
    this.getProgress();
  }

  public ngOnDestroy() {
    this.onDestroy$.next();
    if (this.uploadProcessing$) {
      this.uploadProcessing$.next();
    }
  }

  public ngOnChanges(changes: SimpleChanges) {
    this.ngOnInit();
  }

  /**
   * An event handler when files are dropped into the file drop area for adding files to the queue.
   *
   * @param $event the drop event
   */
  public drop($event: any) {
    $event.preventDefault();
    const items = $event.dataTransfer.items;
    const dropFiles = $event.dataTransfer.files;
    this._startImporting(dropFiles);

    // const promise = this._parseDataTransferItems(items).then((files: Array<File>) => {
    //   this._startImporting(files);
    // });

    // for (const item of items) {
    //   if (item.kind === 'file') {
    //     const entry = item.webkitGetAsEntry();
    //     // this.scanFiles(entry);
    //     if (entry.isFile) {
    //       const promise = this._parseFileEntry(entry).then(file => {
    //         // this._v(file);
    //       });
    //     }
    //   }
    // }
  }

  private _startImporting(files: Array<File>) {
    if (this._validateSelctedFiles(files)) {
      this.fileQueue = [];
      let i = 0;
      for (const file of files) {
        const qFile: any = {};
        qFile.fileName = file.name;
        if (i === 0) {
          qFile.status = 'Uploading';
        } else {
          qFile.status = 'Queued';
        }
        this.fileQueue.push(qFile);
        i++;
      }
      this.queueEmitter.emit(this.fileQueue);
      this._uploadCsv(files[0]);
    }
  }

  /**
   * Start handling a single file selected for import
   */
  public fileSelected() {
    if (this.selectFileInput.nativeElement.files) {
      this._startImporting(this.selectFileInput.nativeElement.files);

      // if (this.selectFileInput.nativeElement.files[0]) {
      //   const file: File = this.selectFileInput.nativeElement.files[0];
      //   if (!this._validateFileType(file)) {
      //     this._showInvalidFileType();
      //   } else {
      //     this.saveStatusEmitter.emit(false);
      //     const qFile: any = {};
      //     qFile.fileName = file.name;
      //     qFile.status = 'Uploading';
      //     this.fileQueue = [qFile];
      //     this.queueEmitter.emit(this.fileQueue);
      //     this._uploadCsv(file);
      //   }
      // }
    }
  }

  /**
   * Programatically trigger a click event on the select file element.
   */
  public triggerSelectFileInputClick(): void {
    this.selectFileInput.nativeElement.click();
  }

  public onClick(event) {
    event.target.value = '';
  }

  /**
   * Determine if user selected files are valid.  Show error message if not.
   * @param files the files to be validated
   * @returns true if valid
   */
  private _validateSelctedFiles(files: Array<File>): boolean {
    if (files.length > 10) {
      this._dialogService
        .confirm(
          'You can only import 10 CSV files at one time.  ' +
            'If you have more than 10, please import the additional files at a later time.',
          ConfirmModalComponent,
          'Warning!',
          false
        )
        .then(res => {});
      return false;
    }
    for (const file of files) {
      if (!this._validateFileType(file)) {
        this._showInvalidFileType();
        return false;
      }
    }
    return true;
  }

  private _validateFileType(file: File): boolean {
    const fileExtention = this._getFileExtention(file.name);
    if (!fileExtention) {
      return false;
    }
    if (fileExtention.toLocaleLowerCase() !== 'csv') {
      return false;
    }
    return true;
  }

  private _showInvalidFileType(): void {
    this._dialogService
      .confirm(
        'You can only import CSV files. If your file is a ' + 'different type, please convert your data file to a CSV.',
        ConfirmModalComponent,
        'Warning!',
        false
      )
      .then(res => {});
  }

  private _getFileExtention(fileName: string): string {
    let fileExtention = '';
    if (!fileName.includes('.')) {
      return fileExtention;
    }
    fileExtention = fileName.split('.').pop();
    return fileExtention;
  }

  private _uploadCsv(file: File) {
    // const checkSum = this._createFileCheckSum(file);

    // TODO convert this to a method returning observable or promise
    // TODO this will perform better if API generates it but requires upload to do so.
    // TODO if not done in API, check for faster front end library option
    const fileReader = new FileReader();
    fileReader.onload = e => {
      const fileData = fileReader.result;
      const hash = CryptoJS.MD5(CryptoJS.enc.Latin1.parse(fileData));
      const md5 = hash.toString(CryptoJS.enc.Hex);
      this.checkSum = md5;

      this._uploadTrxService.listObjects(this.committeeId).subscribe((data: S3.Types.ListObjectsV2Output) => {
        console.log('');
        for (const s3Obj of data.Contents) {
          // remove double quotes from eTag
          let eTagEdited = s3Obj.ETag;
          if (s3Obj.ETag) {
            if (s3Obj.ETag.length > 1) {
              if (s3Obj.ETag.startsWith('"') && s3Obj.ETag.endsWith('"')) {
                eTagEdited = s3Obj.ETag.substring(1, s3Obj.ETag.length - 1);
              }
            }
          }

          if (this.checkSum === eTagEdited) {
            this._dialogService
              .confirm(
                'This file has been uploaded before!  TODO show Review Screen',
                ConfirmModalComponent,
                'Warning!',
                false
              )
              .then(res => {});
          }
        }
      });

      this.progressPercent = 0;
      this.showUpload = false;
      this.uploadingText = 'Uploading...';
      this._uploadTrxService
        .uploadFile(file, this.checkSum, this.committeeId)
        .takeUntil(this.onDestroy$)
        .subscribe((data: any) => {
          if (data === false) {
            console.log('false');
            return;
          }
          this._checkForProcessingProgress();
          this._uploadTrxService.processingUploadedTransactions(file.name, this.checkSum).subscribe((res: any) => {
            this.showSpinner = false;
            // this.emitUploadResults(res);
          });
          // this.uploadContactsService.validateContacts(file.name).subscribe((res: any) => {
          //   this.showSpinner = false;
          //   this.emitUploadResults(res);
          // });
        });
    };
    fileReader.readAsText(file);
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
      this.showSpinner = true;
      if (timerSubscription) {
        timerSubscription.unsubscribe();
      }
      timerSubject.next();
      timerSubject.complete();
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

  /**
   * Convert a DataTransferItemList into an array of Files.
   * MDN uses file() returning a Promise.  This method will
   * return an array of Promises and waits until each Promise in the array has
   * been fullfilled.
   *
   * @param items the DataTransferItemList containing files dropped.
   * @returns an array of Promises where each item in the array is a File.
   */
  private _parseDataTransferItems(items: DataTransferItemList): Promise<Array<File>> {
    // convert DataTransferItemList to array
    const dataTransferItemArray = [];
    // for (const item of items.) {
    for (let i = 0; i < items.length; i++) {
      const item: DataTransferItem = items[i];
      if (item.kind === 'file') {
        // check for getAsEntry() if webkitGetAsEntry() does not exist.  See MDN web docs.
        let entry: any = null;
        const itemMask: any = item;
        if (typeof item.webkitGetAsEntry === 'function') {
          entry = item.webkitGetAsEntry();
        } else if (typeof itemMask.getAsEntry === 'function') {
          entry = itemMask.getAsEntry();
        }
        if (entry.isFile) {
          dataTransferItemArray.push(entry);
        }
      }
    }
    const promiseArray = dataTransferItemArray.map((item: any) => {
      return this._parseFileEntry(item);
    });
    return Promise.all(promiseArray);
  }

  /**
   * Convert FileEntry to a File object.
   *
   * @param fileEntry the FileSystemFileEntry object to convert.
   */
  private _parseFileEntry(fileEntry): Promise<File> {
    return new Promise((resolve, reject) => {
      fileEntry.file(
        (file: File) => {
          resolve(file);
        },
        err => {
          reject(err);
        }
      );
    });
  }

  /**
   * An event handler when files are dragged into the file drop area for adding files to the queue.
   *
   * @param event the dragenter event
   */
  public dragEnter(event) {
    // indicates valid drop data
    // false allows drop
    return Array.prototype.every.call(event.dataTransfer.items, item => item.kind !== 'file');
  }

  /**
   * An event handler when files are dragged over the file drop area
   * for adding files to the queue.
   *
   * @param event the dragover event
   */
  public dragOver(event) {
    // indicates valid drop data
    // false allows drop
    return Array.prototype.every.call(event.dataTransfer.items, item => item.kind !== 'file');
  }

  private _createFileCheckSum(file: File) {
    const prom = new Promise(resolve => {
      const fileReader = new FileReader();
      fileReader.onload = e => {
        const fileData = fileReader.result;
        const hash = CryptoJS.MD5(CryptoJS.enc.Latin1.parse(fileData));
        const md5 = hash.toString(CryptoJS.enc.Hex);
        const output = 'MD5 (' + file.name + ') = ' + md5;
        console.log(output);
        resolve(md5);
      };
      fileReader.readAsText(file);
    });
    prom.then(res => {
      return res;
    });
  }
}
