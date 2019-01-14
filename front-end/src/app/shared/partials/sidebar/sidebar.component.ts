
import { Component, EventEmitter, HostListener, Input, OnInit, Output, ViewEncapsulation } from '@angular/core';
import { ActivatedRoute, NavigationEnd, Router } from '@angular/router';
import { environment } from '../../../../environments/environment';
import { FormsService } from '../../services/FormsService/forms.service';
import { MessageService } from '../../services/MessageService/message.service';
/*import { APIService } from '/interfaces/services/APIService/APIService.ts';*/
import { Icommittee_forms } from '../../interfaces/FormsService/FormsService';
/*import SampleJson from '../../../../api/data.json';*/
/*APIService/APIService.ts*/

@Component({
  selector: 'app-sidebar',
  templateUrl: './sidebar.component.html',
  styleUrls: ['./sidebar.component.scss'],
  encapsulation: ViewEncapsulation.None
})
export class SidebarComponent implements OnInit {

  @Output() status: EventEmitter<any> = new EventEmitter<any>();

  //public formType: number = null;
  public formType: string = '';
  public iconClass: string = 'close-icon';
  public sidebarVisibleClass: string = 'sidebar-visible';
  public screenWidth: number = 0;
  public tooltipPosition: string = 'right';
  public tooltipLeft: string = 'auto';
  public otherFormsHidden: boolean = true;
  public myFormsHidden: boolean = false;
  public committee_forms: Icommittee_forms[];
  public committee_myforms: Icommittee_forms[];
  public committee_otherforms: Icommittee_forms[];


  constructor(
    private _router: Router,
    private _activatedRoute: ActivatedRoute,
    private _formService:FormsService,


  ) { }

  ngOnInit(): void {
    let route: string = this._router.url;

    console.log("accessing form service call side bar ...");

    this._formService.get_filed_form_types()
     .subscribe(res => this.committee_forms = <Icommittee_forms[]> res);

    this._router
      .events
      .subscribe(val => {
        if(val) {
          if(val instanceof NavigationEnd) {
            if(val.url.indexOf('/forms/form/') === 0) {
              this._closeNavBar();
            } else if(val.url.indexOf('/dashboard') === 0) {
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
    this._router
      .events
      .subscribe(val => {
        if(val instanceof NavigationEnd) {
          if(val.url.indexOf(form) >= 1) {
            this.formType = form;
            //form.substring(2);
          }
        }
      });
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
