import { Component, HostListener, Input, OnInit } from '@angular/core';
import { NavigationEnd, Router } from '@angular/router';
import { SessionService } from '../shared/services/SessionService/session.service';
import { MessageService } from '../shared/services/MessageService/message.service';
import { ApiService } from '../shared/services/APIService/api.service';
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
  public sideBarClass: string = null;
  public toggleMenu: boolean = false;
  public committeeName: string = '';
  public committeeId: string = '';
  public dashboardClass: string = '';

	constructor(
    private _apiService: ApiService,
		private _sessionService: SessionService,
    private _messageService: MessageService,
    private _router: Router
	) { }

	ngOnInit(): void {
    let route: string = this._router.url;

    this._apiService
      .getCommiteeDetails()
      .subscribe(res => {
        if(res) {
          localStorage.setItem('committee_details', JSON.stringify(res));

          this.committeeName = res.committeename;
          this.committeeId = res.committeeid;
          this._messageService
            .sendMessage({'committee_details_loaded': true});
        }
      });      
  
    this._router
      .events
      .subscribe(val => {
        if(val instanceof NavigationEnd) {
          if(this.toggleMenu) {
            this.toggleMenu = false;
          }
        }
      });
  }

  ngDoCheck(): void {
    let route: string = this._router.url;

    if(route) {
      if(route.indexOf('/dashboard') === 0) {
        if(this.showSideBar) {
          if(this.sideBarClass !== 'dashboard active') {
            this.sideBarClass = 'dashboard active';             
          }          
        }  else {
          this.sideBarClass = '';   
        }
      }
    }    
  }
  
  @HostListener('window:beforeunload', ['$event'])
  unloadNotification($event: any) {
    localStorage.clear();
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
    let route: string = this._router.url;
    this.showSideBar = e.showSidebar;

    if(this.showSideBar) {
      if(route) {
        if(route.indexOf('/dashboard') === 0) {
          this.sideBarClass = 'dashboard active';
        } else {
          this.sideBarClass = 'active';
        }
      }
    } else {
      this.sideBarClass = '';
    }
  }  
}
