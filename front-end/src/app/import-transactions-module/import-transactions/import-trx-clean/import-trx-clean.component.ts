import { Component, OnInit, Input, Output, EventEmitter } from '@angular/core';
import { UploadFileModel } from '../model/upload-file.model';
import { ImportFileStatusEnum } from '../import-file-status.enum';

@Component({
  selector: 'app-import-trx-clean',
  templateUrl: './import-trx-clean.component.html',
  styleUrls: ['./import-trx-clean.component.scss']
})
export class ImportTrxCleanComponent implements OnInit {

  @Input()
  public uploadFile: UploadFileModel;

  @Output()
  public resultsEmitter: EventEmitter<any> = new EventEmitter<any>();

  constructor() { }

  ngOnInit() {
    this.uploadFile.status = ImportFileStatusEnum.clean;
  }

  public proceed() {
    this.resultsEmitter.emit({
      resultType: 'success',
      uploadFile: this.uploadFile
    });
  }
}
