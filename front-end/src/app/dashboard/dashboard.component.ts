import { Component, OnInit } from '@angular/core';
import { SessionService } from '../shared/services/SessionService/session.service';
import { HeaderComponent } from '../shared/partials/header/header.component';
import { SidebarComponent } from '../shared/partials/sidebar/sidebar.component';

@Component({
  selector: 'app-dashboard',
  templateUrl: './dashboard.component.html',
  styleUrls: ['./dashboard.component.scss']
})
export class DashboardComponent implements OnInit {

  constructor(
    private _sessionService: SessionService
  ) { }

  ngOnInit() {
  }

  /**
   * Logs a user out.
   */
  public logout(): void {
    this._sessionService.destroy();
  }

}
