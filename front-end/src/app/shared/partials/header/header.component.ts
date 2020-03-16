import { Subscription } from 'rxjs/Subscription';
import { Component, ViewEncapsulation, OnInit, OnDestroy, Input, OnChanges } from '@angular/core';
import { Component, ViewEncapsulation, OnInit, Input, OnChanges } from '@angular/core';
import { Router, NavigationEnd } from '@angular/router';
import { NgbModal, ModalDismissReasons } from '@ng-bootstrap/ng-bootstrap';
import { environment } from '../../../../environments/environment';
import { MessageService } from '../../services/MessageService/message.service';
import { AuthService } from '../../services/AuthService/auth.service';
import { ConfirmModalComponent } from '../confirm-modal/confirm-modal.component';
import { FormsService } from '../../services/FormsService/forms.service';
import { DialogService } from '../../services/DialogService/dialog.service';

@Component({
  selector: 'app-header',
  templateUrl: './header.component.html',
  styleUrls: ['./header.component.scss'],
  encapsulation: ViewEncapsulation.None
})
export class HeaderComponent implements OnInit, OnDestroy, OnChanges {
  
  @Input() formType: string;

  public menuActive: boolean = false;
  routerSubscription: Subscription;

  constructor(
    private _messageService: MessageService,
    private _authService: AuthService,
    private _formService: FormsService,
    private _dialogService: DialogService,
    private _router: Router
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
        this._router.navigate([`/forms/form/${this.formType}`], {
          queryParams: { step: 'transactions', transactionCategory: 'receipts', allTransactions: true }
        });
      }
    });
  }
}
