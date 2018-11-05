import { Component, Input, OnInit } from '@angular/core';
import { NavigationEnd, Router } from '@angular/router';
import { SessionService } from '../shared/services/SessionService/session.service';
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
  public toggleMenu: boolean = false;

	constructor(
		private _sessionService: SessionService,
    private _router: Router
	) { }

	ngOnInit() {
    let route: string = this._router.url;

    if(route) {
      if(route.indexOf('forms/form/') >= 1) {
        this.showSideBar = false;
      }
    }

    this._router
      .events
      .subscribe(val => {
        if(val instanceof NavigationEnd) {
          if(val.url.indexOf('forms/form/') >= 1) {
            this.showSideBar = false;
          } else {
            this.showSideBar = true;
          }
        }
      })
	}

  /**
   * Show's or hides the sidebar navigation.
   */
  public toggleSideNav(): void {
    this.showSideBar = !this.showSideBar;
  }

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
  }  
}
