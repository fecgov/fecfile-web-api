import { Component, EventEmitter, HostListener, Input, OnInit, Output } from '@angular/core';
import { ActivatedRoute, NavigationEnd, Router } from '@angular/router';

@Component({
  selector: 'app-sidebar',
  templateUrl: './sidebar.component.html',
  styleUrls: ['./sidebar.component.scss']
})
export class SidebarComponent implements OnInit {

  @Output() status: EventEmitter<any> = new EventEmitter<any>();

  public showCloseIcon: boolean = true;

  constructor(
    private _router: Router,
    private _activatedRoute: ActivatedRoute 
  ) { }

  ngOnInit(): void {
    if(this._router.url.indexOf('/forms/form/') === 0) {
      this.showCloseIcon = false;

      this.status.emit({
        showSidebar: this.showCloseIcon
      });        
    }     
    
    this._router
      .events
      .subscribe(val => {
        if(val) {
          if(val instanceof NavigationEnd) {
            if(val.url.indexOf('/forms/form/') === 0) {
              this.showCloseIcon = false;

              this.status.emit({
                showSidebar: this.showCloseIcon
              });             
            }
          }
        }
      });  
  }

  /**
   * Toggles the sidebar.
   *
   */
  public toggleSideNav(): void {
    if(this.showCloseIcon) {
      this.showCloseIcon = false;
    } else {
      this.showCloseIcon = true;
    }

    this.status.emit({
      showSidebar: this.showCloseIcon
    });  	
  }
}
