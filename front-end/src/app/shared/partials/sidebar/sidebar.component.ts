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

  public formType: string = null;
  public iconClass: string = 'close-icon';
  public sidebarVisibleClass: string = 'sidebar-visible';
  public screenWidth: number = 0;
  public tooltipPosition: string = 'right';
  public tooltipLeft: string = 'auto';
  public otherFormsHidden: boolean = false;
  public myFormsHidden: boolean = false;

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
              this.formType = null;
              this._openNavBar();   
            } else if(val.url.indexOf('/forms/form/') === -1) {
              this.formType = null;
            }
          }
        }
      });  
 

    this.screenWidth = window.innerWidth;

    if(this.screenWidth < 768) {
      this.tooltipPosition = 'bottom';
      this.tooltipLeft = '0';
    } else if (this.screenWidth >= 768) {
      this.tooltipPosition = 'right';
      this.tooltipLeft = 'auto';
    } 
  }

  /**
   * Determines placement of tooltips based on screen size.
   *
   * @class      HostListener (name)
   * @param      {Object}  event   The event
   */
  @HostListener('window:resize', ['$event'])
  onResize(event) {
    this.screenWidth = event.target.innerWidth;

    if(this.screenWidth < 768) {
      this.tooltipPosition = 'bottom';
      this.tooltipLeft = '0';
    } else if (this.screenWidth >= 768) {
      this.tooltipPosition = 'right';
      this.tooltipLeft = 'auto';
    }
  }    

  /**
   * Determines which form has been selected.
   *
   * @param      {String}  form    The form
   */
  public formSelected(form: string): void {
    setTimeout(() => {
      this.formType = form;
    }, 225);
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

  /**
   * Toggles the tooltips.
   *
   * @param      {Object}  tooltip  The tooltip.
   */
  public toggleToolTip(tooltip): void {
    if (tooltip.isOpen()) {
      tooltip.close();
    } else {
      tooltip.open();
    }      
  }    

  /**
   * Toggles weather or not the form navigation is visible.
   *
   * @param      {String}  navType  The navigation type
   */
  public toggleFormNav(navType: string): void {
    if(navType === 'other-forms') {
      this.otherFormsHidden = (this.otherFormsHidden) ? false : true;
    } else if (navType === 'my-forms') {
      this.myFormsHidden = (this.myFormsHidden) ? false : true;
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
