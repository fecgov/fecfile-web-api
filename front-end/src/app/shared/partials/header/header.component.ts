import { Subscription } from 'rxjs/Subscription';
import { Component, ViewEncapsulation, OnInit, OnDestroy, Input, OnChanges, ViewChild } from '@angular/core';
import { Router, NavigationEnd } from '@angular/router';
import { NgbModal, ModalDismissReasons } from '@ng-bootstrap/ng-bootstrap';
import { environment } from '../../../../environments/environment';
import { MessageService } from '../../services/MessageService/message.service';
import { AuthService } from '../../services/AuthService/auth.service';
import { ConfirmModalComponent } from '../confirm-modal/confirm-modal.component';
import { FormsService } from '../../services/FormsService/forms.service';
import { DialogService } from '../../services/DialogService/dialog.service';
import { NotificationsService } from 'src/app/notifications/notifications.service';
import { CashOnHandComponent } from '../../../forms/form-3x/cash-on-hand/cash-on-hand.component';
import { ContactsService } from 'src/app/contacts/service/contacts.service';
import { ExportService } from '../../services/ExportService/export.service';

declare global {
  interface Window { Usersnap: any; }
}

window.Usersnap = window.Usersnap || {};

@Component({
  selector: 'app-header',
  templateUrl: './header.component.html',
  styleUrls: ['./header.component.scss'],
  encapsulation: ViewEncapsulation.None
})
export class HeaderComponent implements OnInit, OnDestroy, OnChanges {
  @ViewChild('content') content: any;
  @Input() formType: string;

  public menuActive: boolean = false;
  routerSubscription: Subscription;
  notificationsCount: number;
  modalRef: any;

  constructor(
    private _messageService: MessageService,
    private _formService: FormsService,
    private _dialogService: DialogService,
    private _router: Router,
    public _authService: AuthService,
    public _notificationsService: NotificationsService,
    private modalService: NgbModal,
    private _contactsService: ContactsService,
    private _exportService: ExportService
  ) {}

  ngOnInit(): void {
    this.routerSubscription = this._router.events.subscribe(val => {
      if (val instanceof NavigationEnd) {
        if (val.url.indexOf('/logout') === 0) {
          let arr: any = [];

          for (let i = 0; i < localStorage.length; i++) {
            arr.push(localStorage.key(i));
          }

          for (let i = 0; i < arr.length; i++) {
            localStorage.removeItem(arr[i]);
          }

          this._messageService.sendMessage({
            loggedOut: true,
            msg: `You have successfully logged out of the ${environment.appTitle} application.`
          });

          this._authService.doSignOut();
        }
      }
    });

    // Get notification count
    this._notificationsService.getTotalCount().subscribe(response => {
      this.notificationsCount = response.notification_count;
    });
  }

  ngOnChanges(): void {
    // TODO Once parent passes form without F prefix, this can be removed.
    if (this.formType) {
      if (this.formType.startsWith('F')) {
        this.formType = this.formType.substr(1, this.formType.length - 1).toString();
      }
    }
  }

  public notImplemented() {
    alert('Page/Feature not implemented yet');
  }

  ngOnDestroy(): void {
    this.routerSubscription.unsubscribe();
  }
  
  public toggleMenu(): void {
    if (this.menuActive) {
      this.menuActive = false;
    } else {
      this.menuActive = true;
    }
  }

  /**
   * Determines ability for a person to leave a page with a form on it.
   *
   * @return     {boolean}  True if able to deactivate, False otherwise.
   */
  public async canDeactivate(): Promise<boolean> {
    if (this._formService.formHasUnsavedData(this.formType)) {
      let result: boolean = null;
      result = await this._dialogService.confirm('', ConfirmModalComponent).then(res => {
        let val: boolean = null;

        if (res === 'okay') {
          val = true;
        } else if (res === 'cancel') {
          val = false;
        }

        return val;
      });

      return result;
    } else {
      return true;
    }
  }

  public viewAllTransactions(): void {
    this.canDeactivate().then(result => {
      if (result === true) {
        localStorage.removeItem(`form_${this.formType}_saved`);
        this._router.navigate([`/forms/form/global`], {
          queryParams: { step: 'transactions', transactionCategory: 'receipts', allTransactions: true }
        });
      }
    });
  }

  openCOHModal(){
    const modalRef = this.modalService.open(CashOnHandComponent);
    modalRef.result.then(result => {
      console.log('saved');
      console.log(result);
      // this._transactionsService.mirrorIEtoF24({reportId: result, transactionId: trx.transactionId}).subscribe(res => {
      //   if(res){
      //     this.getTransactionsPage(this.config.currentPage);
      //     this._dialogService.confirm('Transaction has been successfully added to selected F24 report. ', ConfirmModalComponent, 'Success!', false, ModalHeaderClassEnum.successHeader);
      //   }
      });
    // console.log("reportID; " + result);
    // console.log("transactionId : " + trx.transactionId);
    // this.open(this.content);
  }

  public open(content) {
    this.modalRef = this.modalService.open(content, { size: 'lg', centered: true, windowClass: 'custom-class' });
  }

  goToContacts(){
    this._router.navigate(['/contacts']).then(success => {
      this._messageService.sendMessage({'screen':'contacts', 'action':'highlight-searchbar'});
    });
  }

  goToTransactions(){
    this._router.navigate([`/forms/form/global`], {
      queryParams: { step: 'transactions', transactionCategory: 'receipts', allTransactions: true, searchTransactions:true }
    }).then(success => {
      if(success){
        this._messageService.sendMessage({'screen':'transactions', 'action':'highlight-searchbar'});
      }
    });
    // this.canDeactivate().then(result => {
    //   if (result === true) {
    //     localStorage.removeItem(`form_${this.formType}_saved`);
    //     this._router.navigate([`/forms/form/global`], {
    //       queryParams: { step: 'transactions', transactionCategory: 'receipts', allTransactions: true }
    //     }).then(success => {
    //       this._messageService.sendMessage({'screen':'transactions', 'action':'highlight-searchbar'});
    //     });
    //   }
    // });
  }

  openUsersnap(){
    window.Usersnap.open();
  }

  /**
   * Export all contacts for the committee.
   */
  public exportAllContacts(): void {
    const allContacts = true;
    this._contactsService.getExportContactsData([],
      allContacts).subscribe((res: any) => {
        for (const contact of res.contacts) {
          // TODO have the API omit these fields.
          delete contact.cand_election_year;
          // delete contact.cand_office;
          // delete contact.cand_office_district;
          // delete contact.cand_office_state;
          delete contact.ref_cand_cmte_id;
          delete contact.last_update_date;
        }
        this._exportService.exportCsv(res.contacts, 'export_contacts');
      });
  }
}
