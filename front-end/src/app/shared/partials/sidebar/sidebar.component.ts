import { Component, EventEmitter, HostListener, Input, OnInit, Output } from '@angular/core';
import { ActivatedRoute, NavigationEnd, Router } from '@angular/router';

@Component({
  selector: 'app-sidebar',
  templateUrl: './sidebar.component.html',
  styleUrls: ['./sidebar.component.scss']
})
export class SidebarComponent implements OnInit {

  @Output() status: EventEmitter<any> = new EventEmitter<any>();

  public showCloseIcon: boolean = false;

  constructor(
    private _router: Router,
    private _activatedRoute: ActivatedRoute 
  ) { }

  ngOnInit(): void {    
    this._router
      .events
      .subscribe(val => {
        if(val) {
          if(val instanceof NavigationEnd) {
            if(val.url.indexOf('/forms/form/') === 0) {
              this.showCloseIcon = false;
              this.status.emit({
                showSidebar: false
              });             
            } 

            if (val.url.indexOf('/dashboard') === 0) {
              this.showCloseIcon = true;

              this.status.emit({
                showSidebar: true
              });               
            }
          }
        }
      });  
  }

  ngDoCheck(): void {
    if(this._router.url.indexOf('/forms/form/') === 0) {
      this.showCloseIcon = false;

      this.status.emit({
        showSidebar: false
      });        
    }
  }

  /**
   * Toggles the sidebar.
   *
   */
  public toggleSideNav(): void {
    if(this.showCloseIcon) {
      this.showCloseIcon = false;

      this.status.emit({
        showSidebar: false
      });       
    } else {
      this.showCloseIcon = true;

      this.status.emit({
        showSidebar: true
      });       
    } 	

    console.log('this.showCloseIcon: ', this.showCloseIcon);
  }
}
