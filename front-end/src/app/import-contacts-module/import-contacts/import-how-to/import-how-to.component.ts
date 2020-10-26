import { Component, OnInit, Output, EventEmitter } from '@angular/core';
import { ImportContactsStepsEnum } from '../import-contacts-setps.enum';
import { PaginationInstance } from 'ngx-pagination';
import { duplicatesResponse } from './contacts-data';

@Component({
  selector: 'app-import-how-to',
  templateUrl: './import-how-to.component.html',
  styleUrls: ['./import-how-to.component.scss']
})
export class ImportHowToComponent implements OnInit {
  @Output()
  public returnEmitter: EventEmitter<any> = new EventEmitter<any>();

  public steps: Array<any>;
  public currentStep: ImportContactsStepsEnum;
  public readonly start = ImportContactsStepsEnum.start;
  public readonly step1Upload = ImportContactsStepsEnum.step1Upload;
  public readonly step3Clean = ImportContactsStepsEnum.step3Clean;
  public readonly step4ImportDone = ImportContactsStepsEnum.step4ImportDone;
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
      { text: 'Clean', step: this.step3Clean },
      { text: 'Import', step: this.step4ImportDone }
    ];
    this.currentStep = this.step1Upload;
    this.contacts = duplicatesResponse.contacts;
    this.config.totalItems = duplicatesResponse.totalcontactsCount;
    this.config.itemsPerPage = duplicatesResponse.itemsPerPage;
    // this.numberOfPages = duplicatesResponse.totalPages;
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
