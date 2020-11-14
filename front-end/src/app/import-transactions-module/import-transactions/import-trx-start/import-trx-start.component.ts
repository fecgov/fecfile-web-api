import { Component, OnInit, Output, EventEmitter } from '@angular/core';
import { ImportTransactionsService } from '../service/import-transactions.service';
import * as FileSaver from 'file-saver';

@Component({
  selector: 'app-import-trx-start',
  templateUrl: './import-trx-start.component.html',
  styleUrls: ['./import-trx-start.component.scss']
})
export class ImportTrxStartComponent implements OnInit {
  @Output()
  public beginFileSelectEmitter: EventEmitter<any> = new EventEmitter<any>();

  constructor(private _importTransactionsService: ImportTransactionsService) {}

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
}
