import { Subscription } from 'rxjs/Subscription';
import { Component, ViewEncapsulation, OnInit, ChangeDetectionStrategy, OnDestroy } from '@angular/core';
import { Router, NavigationEnd } from '@angular/router';
import { NgbModal, ModalDismissReasons } from '@ng-bootstrap/ng-bootstrap';
import { environment } from '../../../../environments/environment';
import { MessageService } from '../../services/MessageService/message.service';
import { AuthService } from '../../services/AuthService/auth.service';

@Component({
  selector: 'app-header',
  templateUrl: './header.component.html',
  styleUrls: ['./header.component.scss'],
  encapsulation: ViewEncapsulation.None
})
export class HeaderComponent implements OnInit, OnDestroy {
  

  public menuActive: boolean = false;
  routerSubscription: Subscription;

  constructor(
    private _messageService: MessageService,
    private _authService: AuthService,
    private _router: Router
  ) { }

  ngOnInit(): void {
    this.routerSubscription = this._router
      .events
      .subscribe(val => {
        if(val instanceof NavigationEnd) {
          if(val.url.indexOf('/logout') === 0) {

            let arr: any = [];

            for (let i = 0; i < localStorage.length; i++) {
                 arr.push(localStorage.key(i));
            }

            for (let i = 0; i < arr.length; i++) {
              localStorage.removeItem(arr[i]);
            }

            this._messageService.sendMessage(
              {
                loggedOut: true,
                msg: `You have successfully logged out of the ${environment.appTitle} application.`
              }
            );

            this._authService.doSignOut();
          }
        }
      });
  }
  public notImplemented() {
    alert('Page/Feature not implemented yet');
  }

  ngOnDestroy(): void {
    this.routerSubscription.unsubscribe();
  }
  
  public toggleMenu(): void {
    if(this.menuActive) {
      this.menuActive = false;
    } else {
      this.menuActive = true;
    }
  }
}
