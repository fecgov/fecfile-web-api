import { Component, OnInit, Output, EventEmitter } from '@angular/core';
import { ImportTransactionsService } from '../service/import-transactions.service';
import * as FileSaver from 'file-saver';
import { UploadContactsService } from 'src/app/import-contacts-module/import-contacts/upload-contacts/service/upload-contacts.service';

@Component({
  selector: 'app-import-trx-start',
  templateUrl: './import-trx-start.component.html',
  styleUrls: ['./import-trx-start.component.scss']
})
export class ImportTrxStartComponent implements OnInit {
  @Output()
  public beginFileSelectEmitter: EventEmitter<any> = new EventEmitter<any>();

  private readonly downloadDocDir = 'transactions/download_docs/';
  private readonly xlsxType = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;charset=UTF-8';
  private readonly csvType = 'text/csv;charset=utf-8';

  constructor(
    private _importTransactionsService: ImportTransactionsService,
    private _uploadContactsService: UploadContactsService
  ) {}

  ngOnInit() {}

  public beginUpload() {
    this.beginFileSelectEmitter.emit();
  }

  public viewFormatSpecs(fileName: string) {
    this._importTransactionsService.getSpecAndTemplate(fileName).subscribe((res: any) => {
      const type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;charset=UTF-8';
      const blob: Blob = new Blob([res], { type: type });
      FileSaver.saveAs(blob, 'Import Contacts Specs and Template.xlsx');
    });
  }

  public downloadFormatSpecs() {
    const files = [
      'F3L - Schedule A_Format Specs_Import Trasactions_FINAL.xlsx',
      'F3L - Schedule B_Format Specs_Import Trasactions_FINAL.xlsx',
      'F3X - Schedule A_Format Specs_Import Transactions_FINAL.xlsx',
      'F3X - Schedule B_Format Specs_Import Transactions_FINAL.xlsx',
      'F3X - Schedule E_Format Specs_Import Transactions_FINAL.xlsx',
      'F3X - Schedule F_Format Specs_Import Transactions_FINAL.xlsx',
      'F3X - Schedule H3_Format Specs_Import Transactions_FINAL.xlsx',
      'F3X - Schedule H4_Format Specs_Import Transactions_FINAL.xlsx',
      'F3X - Schedule H5_Format Specs_Import Transactions_FINAL.xlsx',
      'F3X - Schedule H6_Format Specs_Import Transactions_FINAL.xlsx',
      'F3X - Schedule LA_Format Specs_Import Transactions_FINAL.xlsx',
      'F3X - Schedule LB_Format Specs_Import Transactions_FINAL.xlsx'
    ];
    for (const file of files) {
      const fileMetaData: any = {};
      fileMetaData.dir = this.downloadDocDir + 'format_specs/';
      fileMetaData.type = this.xlsxType;
      fileMetaData.fileName = file;
      this._downloadFile(fileMetaData);
    }
  }

  public downloadF3xTemplate() {
    const fileMetaData: any = {};
    fileMetaData.dir = this.downloadDocDir;
    fileMetaData.type = this.xlsxType;
    fileMetaData.fileName = 'F3X - Tempate  Schedule Specs_Import Transactions.xlsx';
    this._downloadFile(fileMetaData);
  }

  public downloadF3lTemplate() {
    const fileMetaData: any = {};
    fileMetaData.dir = this.downloadDocDir;
    fileMetaData.type = this.xlsxType;
    fileMetaData.fileName = 'F3L - Template  Schedule Specs_Import Transactions.xlsx';
    this._downloadFile(fileMetaData);
  }

  public downloadUniqueTransactionIdentifiers() {
    const fileMetaData: any = {};
    fileMetaData.dir = this.downloadDocDir;
    fileMetaData.type = this.xlsxType;
    fileMetaData.fileName = 'F3X  F3L Transaction Types - Unique Identifiers.xlsx';
    this._downloadFile(fileMetaData);
  }

  public downloadReportCodes() {
    const fileMetaData: any = {};
    fileMetaData.dir = this.downloadDocDir;
    fileMetaData.type = this.xlsxType;
    fileMetaData.fileName = 'F3X & F3L - Report Codes.xlsx';
    this._downloadFile(fileMetaData);
  }

  public downloadCsvTemplate() {
    const fileMetaData: any = {};
    fileMetaData.dir = this.downloadDocDir;
    fileMetaData.type = this.csvType;
    fileMetaData.fileName = 'Template.csv';
    this._downloadFile(fileMetaData);
  }

  public downloadTransactionTypes() {
    const fileMetaData: any = {};
    fileMetaData.dir = this.downloadDocDir;
    fileMetaData.type = this.xlsxType;
    fileMetaData.fileName = 'Transactions Types + Identifiers.xlsx';
    this._downloadFile(fileMetaData);
  }

  private _downloadFile(fileMetaData: any) {
    const dir = fileMetaData.dir;
    const fileName = fileMetaData.fileName;
    const type = fileMetaData.type;

    this._uploadContactsService.getObject(dir + fileName).subscribe(res => {
      const blob: Blob = new Blob([res.Body], { type: type });
      FileSaver.saveAs(blob, fileName);
    });
  }

  public foo_Util_get_csv_file(fileName: string) {
    this._uploadContactsService.getObject('transactions/' + fileName).subscribe(res => {
      const type = 'text/plain;charset=utf-8';
      const blob: Blob = new Blob([res.Body], { type: type });
      FileSaver.saveAs(blob, 'sample_import_transactions.csv');

      var file = new File([res], 'hello world.txt', { type: 'text/plain;charset=utf-8' });
      FileSaver.saveAs(file);
    });
  }
}
