import { Component, Input, OnInit } from '@angular/core';
import { NavigationEnd, Router } from '@angular/router';
import { SessionService } from '../shared/services/SessionService/session.service';
import { MessageService } from '../shared/services/MessageService/message.service';
import { HeaderComponent } from '../shared/partials/header/header.component';
import { SidebarComponent } from '../shared/partials/sidebar/sidebar.component';
import { FormsComponent } from '../forms/forms.component';

@Component({
  selector: 'app-app-layout',
  templateUrl: './app-layout.component.html',
  styleUrls: ['./app-layout.component.scss']
})
export class AppLayoutComponent implements OnInit {

  @Input() status: any;

	public showSideBar: boolean = true;
  public sideBarClass: string = '';
  public toggleMenu: boolean = false;

	constructor(
		private _sessionService: SessionService,
    private _messageService: MessageService,
    private _router: Router
	) { }

	ngOnInit(): void {
    let route: string = this._router.url;

    /*if(route) {
      if(route.indexOf('forms/form/') === 0) {
        this.sideBarClass = '';
      }
    }*/

    this._router
      .events
      .subscribe(val => {
        if(val instanceof NavigationEnd) {
          if(val.url.indexOf('forms/form/') === 0) {
            this.sideBarClass = '';
          } else {
            this.sideBarClass = 'active';
          }
        }
      })
	}

  /**
   * Shows the top nav in tablet and mobile phone view when clicked.
   */
  public toggleTopNav(): void {
    this.toggleMenu = !this.toggleMenu;
  }

  /**
   * Logs a user out.
   */
  public logout(): void {
    this._sessionService.destroy();
  }

  /**
   * Get's message from child components.
   *
   * @param      {Object}  e       The event object.
   */
  public onNotify(e): void {
    this.showSideBar = e.showSidebar;

    if(this.showSideBar) {
      this.sideBarClass = 'active';
    } else {
      this.sideBarClass = '';
    }
  }  
}
