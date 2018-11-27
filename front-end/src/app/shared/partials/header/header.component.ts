import { Component, ViewEncapsulation, OnInit } from '@angular/core';
import { Router } from '@angular/router';
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
export class HeaderComponent implements OnInit {

  public menuActive: boolean = false;

  constructor(
    private _messageService: MessageService,
    private _authService: AuthService
  ) { }

  ngOnInit(): void {}

  /**
   * Logs a user out.
   *
   */
  public logout(): void {
    this._messageService.sendMessage(
      {
        loggedOut: true,
        msg: `You have successfully logged out of the ${environment.appTitle} application.`
      }
    );

    this._authService.doSignOut();
  }

  public toggleMenu(): void {
    if(this.menuActive) {
      this.menuActive = false;
    } else {
      this.menuActive = true;
    }
  }
}
