import { Component, OnInit, Output, EventEmitter } from '@angular/core';
import { ImportTransactionsStepsEnum } from '../import-transactions-steps.enum';
import { PaginationInstance } from 'ngx-pagination';
import { duplicatesResponse } from 'src/app/import-contacts-module/import-contacts/import-how-to/contacts-data';

@Component({
  selector: 'app-import-trx-how-to',
  templateUrl: './import-trx-how-to.component.html',
  styleUrls: ['./import-trx-how-to.component.scss']
})
export class ImportTrxHowToComponent implements OnInit {
  @Output()
  public returnEmitter: EventEmitter<any> = new EventEmitter<any>();

  public steps: Array<any>;
  public currentStep: ImportTransactionsStepsEnum;
  public readonly start = ImportTransactionsStepsEnum.start;
  public readonly step1Upload = ImportTransactionsStepsEnum.step1Upload;
  public readonly step2Review = ImportTransactionsStepsEnum.step2Review;
  public readonly step3Clean = ImportTransactionsStepsEnum.step3Clean;
  public readonly step4ImportDone = ImportTransactionsStepsEnum.step4ImportDone;
  public contacts: Array<any>;
  public config: PaginationInstance = {
    id: 'how_to__table-pagination',
    itemsPerPage: 4,
    currentPage: 1
  };

  constructor() {}

  ngOnInit() {
    this.steps = [
      { text: 'Upload', step: this.step1Upload },
      { text: 'Review', step: this.step2Review },
      { text: 'Clean', step: this.step3Clean },
      { text: 'Import', step: this.step4ImportDone }
    ];
    this.currentStep = this.start;
    this.contacts = duplicatesResponse.contacts;
    this.config.totalItems = duplicatesResponse.totalcontactsCount;
    this.config.itemsPerPage = duplicatesResponse.itemsPerPage;
  }

  public returnToImport() {
    this.returnEmitter.emit();
  }

  public formatName(contact: any): string {
    let name = '';
    if (contact.entity_type === 'IND') {
      // TODO handle suffix and prefix
      name = `${contact.last_name}, ${contact.first_name}`;
    } else if (contact.entity_type === 'ORG') {
      name = contact.entity_name;
    }
    return name;
  }
}
