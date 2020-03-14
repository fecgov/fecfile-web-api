import { Component, HostListener, SimpleChanges, OnDestroy, OnInit, HostBinding , ChangeDetectionStrategy } from '@angular/core';
import { Router, NavigationStart, NavigationEnd } from '@angular/router';
import { MessageService } from './shared/services/MessageService/message.service';
import { DialogService } from './shared/services/DialogService/dialog.service';
import { ConfirmModalComponent } from 'src/app/shared/partials/confirm-modal/confirm-modal.component';
import { ModalDismissReasons } from '@ng-bootstrap/ng-bootstrap';
import { UserIdleService } from 'angular-user-idle';
import { SessionService } from './shared/services/SessionService/session.service';
import { formatDate } from '@angular/common';

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.scss']
})
export class AppComponent implements OnInit, OnDestroy{

  @HostBinding('@.disabled')
  public animationsDisabled = true;
  
  routerEventsSubscription: any;
  
  timeStart = false;
  seconds = 1200;

  clientX = 0;
  clientY = 0;
  private timeIsUp:boolean = false;
  timerSubscription: any;
  idlePingSubscription: any;
  timeoutSubscription: any;
  routerEventsSubscriptionOnNgDoCheck: any;

  constructor(
    private userIdle: UserIdleService,
    private _router: Router,
    private _messageService: MessageService,
    private _dialogService: DialogService,
    private _sessionService: SessionService
  ) {}

  ngOnInit() {
    this.restart();
    this.routerEventsSubscription = this._router.events.subscribe(val => {
      if (val instanceof NavigationEnd && val.url !== '/') {
        // Start watching for user inactivity.
        this.userIdle.startWatching();

        // Start watching when user idle is starting.
        this.timerSubscription = this.userIdle.onTimerStart().subscribe(count => {
          this.seconds = this.seconds - 1;
          this.timeStart = true; /* //console.log(count) */
          if (this.timeStart && !this.timeIsUp) {
            // Enhancement: To display countdown timer
            const minutes: number = Math.floor(count / 60);

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
                  this._dialogService.checkIfModalOpen();
                } else if (
                  response === 'cancel' ||
                  response !== ModalDismissReasons.BACKDROP_CLICK ||
                  response !== ModalDismissReasons.ESC
                ) {
                }
              });
          }
        });
        this.idlePingSubscription = this.userIdle.ping$.subscribe(res => {
        });

        // Start watch when time is up.
        this.timeoutSubscription = this.userIdle.onTimeout().subscribe(res => {
          this.timeIsUp = true;
          this._dialogService.checkIfModalOpen();
          this._sessionService.destroy();
          this._dialogService
            .confirm('The session has expired.', ConfirmModalComponent, 'Session Expired', false)
            .then(response => {
              if (
                response === 'okay' ||
                response === 'cancel' ||
                response === ModalDismissReasons.BACKDROP_CLICK ||
                response === ModalDismissReasons.ESC
              ) {
                this._router.navigate(['']);
              }
            });
        });
      }
    });
  }

  ngOnDestroy(): void {
    this.routerEventsSubscription.unsubscribe();
    this.timerSubscription.unsubscribe();
    this.idlePingSubscription.unsubscribe();
    this.timeoutSubscription.unsubscribe();
    this.routerEventsSubscriptionOnNgDoCheck.unsubscribe();
  }
  
  ngDoCheck(): void {
    if (this._router.url === '/') {
      this.stopWatching();
      this._dialogService.checkIfModalOpen();
    }
    this.routerEventsSubscriptionOnNgDoCheck = this._router.events.subscribe(val => {
      let oldUrl = '';
      if (val instanceof NavigationEnd) {
        oldUrl = val.url;
      }
      if (val instanceof NavigationStart) {
        this.stop();
        this._dialogService.checkIfModalOpen();
      }

      // if (this.timeStart && !this.timeIsUp) {
      // }
    });
  }

  stop() {
    this.userIdle.stopTimer();
    this.seconds = 1200;
    this.timeStart = false;
  }

  stopWatching() {
    this.userIdle.stopWatching();
    this.timeIsUp = false;
  }

  startWatching() {
    this.userIdle.startWatching();
  }

  restart() {
    this.userIdle.resetTimer();
    this.timeIsUp = false;
  }

  // @HostListener('document:click', ['$event'])
  // clickout(event) {
  //   this.stop();
  // }

  @HostListener('window:beforeunload', ['$event'])
 beforeunloadHandler(event) {
       localStorage.clear();
       this._sessionService.destroy();
  }

  @HostListener('keypress') onKeyPress() {
    this.stop();
    this._dialogService.checkIfModalOpen();
  }
}
