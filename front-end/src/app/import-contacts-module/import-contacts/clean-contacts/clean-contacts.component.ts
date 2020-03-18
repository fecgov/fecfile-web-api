import { Component, OnInit, ViewEncapsulation } from '@angular/core';
import { trigger, transition, style, animate } from '@angular/animations';
import { ContactModel } from 'src/app/contacts/model/contacts.model';
import { ImportContactsService } from '../service/import-contacts.service';
import { PaginationInstance } from 'ngx-pagination';

@Component({
  selector: 'app-clean-contacts',
  templateUrl: './clean-contacts.component.html',
  styleUrls: ['./clean-contacts.component.scss'],
  encapsulation: ViewEncapsulation.None
})
export class CleanContactsComponent implements OnInit {

  // public contacts: Array<ContactModel>;
  public contacts: Array<any>;

  // ngx-pagination config
  public maxItemsPerPage = 10;
  public directionLinks = false;
  public autoHide = true;
  public config: PaginationInstance;
  public numberOfPages = 0;

  constructor(private importContactsService: ImportContactsService) { }

  ngOnInit() {
    const config: PaginationInstance = {
      id: 'clean_contacts__table-pagination',
      itemsPerPage: this.maxItemsPerPage,
      currentPage: 1
    };
    this.config = config;
    this.getContacts(1);
  }

  public getContacts(page: number) {
    this.config.currentPage = page;
    this.importContactsService.getDuplicates().subscribe((res: any) => {
      this.contacts = res.duplicates;
      this.config.totalItems = res.totalCount ? res.totalCount : 0;
      this.config.itemsPerPage = res.itemsPerPage ? res.itemsPerPage : this.maxItemsPerPage;
      this.numberOfPages = res.totalPages;
    });
  }

  public cleanContact(contact: any) {
    alert('clean contact not yet supported');
  }

  /**
   * Determine if pagination should be shown.
   */
  public showPagination(): boolean {
    if (this.config.totalItems > this.config.itemsPerPage) {
      return true;
    }
    // otherwise, no show.
    return false;
  }

}
