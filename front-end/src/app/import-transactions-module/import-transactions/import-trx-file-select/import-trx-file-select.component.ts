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
import { UploadFileModel } from '../model/upload-file.model';
import { ImportFileStatusEnum } from '../import-file-status.enum';

/**
 * This component provides UI for selecting file to upload.
 * The actual upload will be done in the Review Component.
 */
@Component({
  selector: 'app-import-trx-file-select',
  templateUrl: './import-trx-file-select.component.html',
  styleUrls: ['./import-trx-file-select.component.scss']
})
export class ImportTrxFileSelectComponent implements OnInit {
  @ViewChild('selectFileInput')
  public selectFileInput: ElementRef;

  @Output()
  public queueEmitter: EventEmitter<any> = new EventEmitter<any>();

  public formType: string;
  public readonly f3xForm = 'F3X';
  public readonly f3lForm = 'F3L';

  private fileQueue: Array<UploadFileModel>;

  constructor(private _dialogService: DialogService) {}

  public ngOnInit() {
    this.formType = this.f3xForm;
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
    if (this._validateSelectedFiles(files)) {
      this.fileQueue = new Array<UploadFileModel>();
      let i = 0;
      for (const file of files) {
        const qFile: UploadFileModel = new UploadFileModel();
        qFile.fileName = file.name;
        qFile.status = ImportFileStatusEnum.queued;
        qFile.file = file;
        qFile.queueIndex = i;
        this.fileQueue.push(qFile);
        i++;
      }
      this.queueEmitter.emit(this.fileQueue);
      // this._uploadCsv(files[0]);
    }
  }

  /**
   * Start handling a single file selected for import
   */
  public fileSelected() {
    if (this.selectFileInput.nativeElement.files) {
      this._startImporting(this.selectFileInput.nativeElement.files);
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
   *
   * @param files the files to be validated
   * @returns true if valid
   */
  private _validateSelectedFiles(files: Array<File>): boolean {
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
