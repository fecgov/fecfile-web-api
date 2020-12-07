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
