import { Component, EventEmitter, HostListener, Input, OnInit, Output, ViewEncapsulation } from '@angular/core';
import { ActivatedRoute, NavigationEnd, Router } from '@angular/router';

@Component({
  selector: 'app-sidebar',
  templateUrl: './sidebar.component.html',
  styleUrls: ['./sidebar.component.scss'],
  encapsulation: ViewEncapsulation.None
})
export class SidebarComponent implements OnInit {

  @Output() status: EventEmitter<any> = new EventEmitter<any>();

  public iconClass: string = 'close-icon';
  public sidebarVisibleClass: string = 'sidebar-visible';
  public formType: number = null;

  constructor(
    private _router: Router,
    private _activatedRoute: ActivatedRoute 
  ) { }

  ngOnInit(): void {  
    let route: string = this._router.url;

   
    
    this._router
      .events
      .subscribe(val => {
        if(val) {
          if(val instanceof NavigationEnd) {
            if(val.url.indexOf('/forms/form/') === 0) {        
              this._closeNavBar();     
            } else if(val.url.indexOf('/dashboard') === 0) {
              this._openNavBar();   
            } else if(val.url.indexOf('/forms/form/') !== 0) {
              this.formType = null;
            }
          }
        }
      });  
  

  }

  ngDoCheck() {

  }

  public formSelected(form: string) {
    this.formType = parseInt(form);
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
    }, 100);

    this.status.emit({
      showSidebar: false
    });               
  }

  /**
   * Opens the navbar.
   */
  private _openNavBar(): void {
    this.iconClass = 'close-icon';

    setTimeout(() => {
      this.sidebarVisibleClass = 'sidebar-visible';
    }, 100);    

    this.status.emit({
      showSidebar: true
    });   
  }
}
