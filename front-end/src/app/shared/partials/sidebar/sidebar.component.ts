import { Component, EventEmitter, HostListener, Input, OnInit, Output } from '@angular/core';
import { ActivatedRoute, NavigationEnd, Router } from '@angular/router';

@Component({
  selector: 'app-sidebar',
  templateUrl: './sidebar.component.html',
  styleUrls: ['./sidebar.component.scss']
})
export class SidebarComponent implements OnInit {

  @Output() status: EventEmitter<any> = new EventEmitter<any>();

  public iconClass: string = 'bars-icon';
  public sidebarVisibleClass: string = 'sidebar-hidden';
  public formType: string = null;

  constructor(
    private _router: Router,
    private _activatedRoute: ActivatedRoute 
  ) { }

  ngOnInit(): void {   
    let route: string = this._router.url;

    /*if(route) {
      if(route.indexOf('/dashboard') === 0) {
        if(this.iconClass !== 'close-icon') {
          this.iconClass = 'close-icon';

          this.status.emit({
            showSidebar: true
          });               
        }
      }
    }   */    
    
    this._router
      .events
      .subscribe(val => {
        if(val) {
          if(val instanceof NavigationEnd) {
            console.log('val: ', val);
            if(val.url.indexOf('/forms/form/') === 0) {
              console.log('form');
              this._closeNavBar();           
            } else if (val.url.indexOf('/dashboard') === 0) {
              console.log('dashboard: ');
              this._openNavBar();        
            }
          }
        }
      });  

      /*this._activatedRoute
        .params
        .subscribe(params => {
          console.log('params: ', params);
        });*/

      /*this._activatedRoute
        .params
        .subscribe(params => {
          console.log('params: ', params);
          this.formType = params['form_id'];

          console.log('formType:', this.formType);
        });*/
  }

  ngDoCheck(): void {
    console.log('sidebar component: ');
  }

  /**
   * Toggles the sidebar.
   *
   */
  public toggleSideNav(): void {
    if(this.iconClass === 'close-icon') {
      this._closeNavBar();     
    } else {
      this._openNavBar();      
    } 	
  }

  public toggleToolTip(tooltip): void {
    if (tooltip.isOpen()) {
      tooltip.close();
    } else {
      tooltip.open();
    }      
  }    

  /**
   * Closes the navbar.
   */
  private _closeNavBar(): void {
    this.iconClass = 'bars-icon';

    setTimeout(() => {
      this.sidebarVisibleClass = 'sidebar-hidden';
    }, 10);

    this.status.emit({
      showSidebar: false
    });               
  }

  /**
   * Opens the navbar.
   */
  private _openNavBar(): void {
    console.log('_openNavBar:');
    this.iconClass = 'close-icon';

    setTimeout(() => {
      console.log('update visibile class: ');
      this.sidebarVisibleClass = 'sidebar-visible';

      console.log('this.sidebarVisibleClass:', this.sidebarVisibleClass);
    }, 10);    

    this.status.emit({
      showSidebar: true
    });   
  }
}
