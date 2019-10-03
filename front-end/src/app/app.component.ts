import { Component, HostListener, SimpleChanges } from '@angular/core';
import { Router, NavigationStart, NavigationEnd } from '@angular/router';
import { MessageService } from './shared/services/MessageService/message.service';
import { DialogService } from './shared/services/DialogService/dialog.service';
import { ConfirmModalComponent } from 'src/app/shared/partials/confirm-modal/confirm-modal.component';
import { ModalDismissReasons } from '@ng-bootstrap/ng-bootstrap';
import { UserIdleService } from 'angular-user-idle';
import { SessionService } from './shared/services/SessionService/session.service';

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.scss']
})
export class AppComponent {
  timeStart = false;
  seconds = 1200;

  clientX = 0;
  clientY = 0;

  constructor(
    private userIdle: UserIdleService,
    private _router: Router,
    private _messageService: MessageService,
    private _dialogService: DialogService,
    private _sessionService: SessionService
  ) {}

  ngOnInit() {
    this._router.events.subscribe(val => {
      if (val instanceof NavigationEnd && val.url !== '/') {
        // Start watching for user inactivity.
        this.userIdle.startWatching();

        // Start watching when user idle is starting.
        this.userIdle.onTimerStart().subscribe(count => {
          this.seconds = this.seconds - 1;
          this.timeStart = true; /* console.log(count) */
        });
        this.userIdle.ping$.subscribe(res => {
          this._dialogService.checkIfModalOpen();
          this._dialogService
            .confirm(
              'This session will expire unless a response is received within 2 minutes. Click OK to prevent expiration.',
              ConfirmModalComponent,
              'Session Warning',
              false
            )
            .then(response => {
              if (response === 'okay') {
                this.stop();
              } else if (response === 'cancel' ||
              response !== ModalDismissReasons.BACKDROP_CLICK ||
              response !== ModalDismissReasons.ESC) {
              }
            });
        });

        // Start watch when time is up.
        this.userIdle.onTimeout().subscribe(res => {
          this._dialogService.checkIfModalOpen();
          this._dialogService
            .confirm('The session has expired.', ConfirmModalComponent, 'Session Expired', false)
            .then(response => {
              if (response === 'okay' ||
              response === 'cancel' ||
              response === ModalDismissReasons.BACKDROP_CLICK ||
              response === ModalDismissReasons.ESC) {
                this.restart();
                this._sessionService.destroy();
                this._router.navigate(['']);
              }
            });
        });
      }
    });
  }

  ngDoCheck(): void {
    if (this._router.url === '/') {
      this.stopWatching();
      this._dialogService.checkIfModalOpen();
    }
    this._router.events.subscribe(val => {
      let oldUrl = '';
      if (val instanceof NavigationEnd) {
        oldUrl = val.url;
      }
      if (val instanceof NavigationStart && val.url !== oldUrl) {
        this.stop();
      }
    });
  }

  stop() {
    this.userIdle.stopTimer();
    this.seconds = 1200;
    this.timeStart = false;
  }

  stopWatching() {
    this.userIdle.stopWatching();
  }

  startWatching() {
    this.userIdle.startWatching();
  }

  restart() {
    this.userIdle.resetTimer();
  }

  // @HostListener('document:click', ['$event'])
  // clickout(event) {
  //   this.stop();
  // }

  @HostListener('keypress') onKeyPress() {
    this.stop();
  }
}
