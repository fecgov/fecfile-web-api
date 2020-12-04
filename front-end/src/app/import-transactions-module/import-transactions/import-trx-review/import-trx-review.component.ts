import { Component, OnInit, Input, OnDestroy, Output, EventEmitter } from '@angular/core';
import { S3 } from 'aws-sdk/clients/all';
import {
  ConfirmModalComponent,
  ModalHeaderClassEnum
} from 'src/app/shared/partials/confirm-modal/confirm-modal.component';
import { timer, Subject } from 'rxjs';
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
export class ImportTrxReviewComponent implements OnInit, OnDestroy {
  @Input()
  public uploadFile: UploadFileModel;

  @Output()
  public resultsEmitter: EventEmitter<any> = new EventEmitter<any>();

  public progressPercent: number;
  public uploadingText: string;
  public hasDupeFile: boolean;
  public duplicateFileList: Array<any>;
  public startUpload: boolean;

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
    this._startReview();
    this.hasDupeFile = false;
    this.startUpload = false;
    this.duplicateFileList = [];
  }

  public ngOnDestroy() {}

  public proceed() {
    this.resultsEmitter.emit({
      resultType: 'proceed',
      uploadFile: this.uploadFile
    });
  }

  public cancelImport() {
    this.resultsEmitter.emit({
      resultType: 'cancel-file',
      file: this.uploadFile
    });
  }

  // private _readFileChunk(chunk: Blob) {
  //   const fileReader = new FileReader();
  //   fileReader.onload = e => {
  //     const chunkData = fileReader.result;
  //     // console.log(chunkData);
  //   };
  //   fileReader.readAsText(chunk);
  // }

  private async _startReview() {
    const file: File = this.uploadFile.file;
    // const chunk: Blob = file.slice(0, 2048);
    // this._readFileChunk(chunk);

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

        this._importTransactionsService
          .checkDuplicateFile(file.name, this.uploadFile.checkSum, this.uploadFile.formType)
          .subscribe((res: any) => {
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
      };
      fileReader.readAsText(file);
    }
  }

  public receiveUploadResults($event: any) {
    alert('check for validation errors');
  }
}
