import { Component, EventEmitter, HostListener, Input, OnInit, Output } from '@angular/core';
import { ActivatedRoute, NavigationEnd, Router } from '@angular/router';

@Component({
  selector: 'app-sidebar',
  templateUrl: './sidebar.component.html',
  styleUrls: ['./sidebar.component.scss']
})
export class SidebarComponent implements OnInit {

  @Output() status: EventEmitter<any> = new EventEmitter<any>();

  public showSidebar: boolean = true;

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
              this.showSidebar = false;

              this.status.emit({
                showSidebar: this.showSidebar
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
    if(this.showSidebar) {
      this.showSidebar = false;
    } else {
      this.showSidebar = true;
    }

    this.status.emit({
      showSidebar: this.showSidebar
    });  	
  }
}
