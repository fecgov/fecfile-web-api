import { takeUntil } from 'rxjs/operators';
import { MessageService } from './../../shared/services/MessageService/message.service';
import { Router, ActivatedRoute } from '@angular/router';
import { Component, OnInit, OnDestroy } from '@angular/core';
import { NgbPanelChangeEvent } from '@ng-bootstrap/ng-bootstrap';
import { DialogService } from '../../shared/services/DialogService/dialog.service';
import { ModalHeaderClassEnum, ConfirmModalComponent } from 'src/app/shared/partials/confirm-modal/confirm-modal.component';
import { Subject } from 'rxjs';

@Component({
  selector: 'app-personal-key',
  templateUrl: './personal-key.component.html',
  styleUrls: ['./personal-key.component.scss']
})
export class PersonalKeyComponent implements OnInit, OnDestroy {
  accordionExpanded: boolean;
  confirmationMessage: string = "Did you save or print a copy of your Personal Key? You will be asked to enter your Personal Key in the event you are unable to log into the system.";
  successMessage: string = "Password and Personal Key have been created successfully. Proceed to Login.";
  
  personalKey: string = '';
  private onDestroy$ = new Subject();

  constructor(private _router: Router,
    private _dialogService: DialogService, 
    private _activatedRoute: ActivatedRoute, 
    private _messageService: MessageService) {
      this._messageService.getMessage().takeUntil(this.onDestroy$).subscribe(message => {
        if(message && message.action === 'sendPersonalKey'){
          this.personalKey = message.key;
        }
      });
    }

  ngOnInit() {
    // this.personalKey = this._activatedRoute.snapshot.queryParams.key;
  }

  public toggleAccordion($event:NgbPanelChangeEvent,acc){
    if(acc.isExpanded($event.panelId)){
      this.accordionExpanded = true;
    }
    else{
      this.accordionExpanded = false;
    }
  }

  ngOnDestroy(){
    this.onDestroy$.next(true);
  }

  public print(){
    window.print();
  }

  public continue(){
    this._dialogService.confirm(this.confirmationMessage,ConfirmModalComponent,'Attention!',true,ModalHeaderClassEnum.infoHeaderDark,null).then(res => {
      if(res === 'okay'){
        this._dialogService.confirm(this.successMessage,ConfirmModalComponent,'Success!',false,ModalHeaderClassEnum.infoHeaderDark,null).then(res => {
            this._router.navigate(['/dashboard']);
        })
      }
    })
  }

  public getAnotherKey(){

  }

}
